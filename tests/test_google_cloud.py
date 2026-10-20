"""Google auth boundaries and two offline SQLite libraries sharing a cloud account."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import base64
import copy
import hashlib
import io
import json
import tempfile
import time
import unittest
import urllib.parse
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch, Mock

from PyQt6.QtWidgets import QApplication, QLineEdit
from duocards import db, cloud_account
from duocards.cloud_account import CloudError, CloudConflict, FirebaseCloud, merge_library, oauth_parameters, callback_result, validate_config
from duocards.sync import SyncClient, SyncError, config
from duocards.ui_localization import localize_tree
from duocards.widgets.account_panel import AccountPanel, SyncCoordinator

CONFIG = dict(projectId='studycard-test', apiKey='AIza'+'x'*35,
              databaseURL='https://studycard-test-default-rtdb.europe-west1.firebasedatabase.app',
              webClientId='123-web.apps.googleusercontent.com', desktopClientId='123-desktop.apps.googleusercontent.com')


class MemoryCloud:
    def __init__(self):
        self.snapshot = None
        self.version = 0
        self.calls = []
        self.before_put = None
        self.refresh_uid = 'google-user'
    def request(self, method, url, body=None, headers=None):
        self.calls.append((method, urllib.parse.urlsplit(url).path))
        if 'securetoken.googleapis.com' in url:
            return dict(user_id=self.refresh_uid, id_token='refreshed-token', refresh_token='new-refresh', expires_in='3600'), None
        if 'identitytoolkit.googleapis.com' in url:
            return dict(providerId='google.com', emailVerified=True, localId='google-user', email='learner@example.com',
                        idToken='token', refreshToken='refresh', expiresIn='3600'), None
        if method == 'GET':
            if '/revision.json' in url:
                return (self.snapshot or {}).get('revision'), None
            return copy.deepcopy(self.snapshot), '"'+str(self.version)+'"'
        if self.before_put:
            action, self.before_put = self.before_put, None
            action()
        if headers['If-Match'] != '"'+str(self.version)+'"':
            raise CloudConflict('race')
        self.snapshot = json.loads(body)
        self.version += 1
        return copy.deepcopy(self.snapshot), None


class GoogleCloudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.remote = MemoryCloud()
        self.cloud = FirebaseCloud(CONFIG, self.remote.request)
        self.clients = {name: SyncClient(self.folder/(name+'-session.json'), cloud_factory=lambda:self.cloud) for name in ('pc','phone')}
        for name in self.clients:
            with self.device(name):
                db.init_db()
                self.clients[name].bind_google_account(self.cloud.sign_in('google-id-token'))
    @contextmanager
    def device(self, name):
        with patch.object(db,'DB_DIR',str(self.folder)),patch.object(db,'DB_PATH',str(self.folder/(name+'.db'))),patch('duocards.sentence_memory.request_examples'):
            yield
    def sync(self,name):
        with self.device(name):return self.clients[name].sync()
    def add(self,name,term='google-word'):
        with self.device(name):return db.add_card(db.get_all_decks()[0]['id'],term,'anlam',source_lang='en',target_lang='tr',notes='first note')
    def card(self,name,term='google-word'):
        with self.device(name):return next(card for card in db.get_all_cards() if card['term']==term)
    def edit(self,name,**fields):
        card=self.card(name)
        with self.device(name),db.get_connection() as conn:
            conn.execute('UPDATE cards SET '+','.join(key+'=?' for key in fields)+' WHERE id=?',list(fields.values())+[card['id']])
    def pair(self):self.sync('pc');self.sync('phone');self.sync('pc')
    def test_google_cloud_add_edit_favorite_and_review_between_devices(self):
        ident=self.add('phone');self.pair();self.assertEqual(self.card('pc')['notes'],'first note')
        self.edit('pc',definition='changed on PC');self.sync('pc');self.sync('phone')
        self.assertEqual(self.card('phone')['definition'],'changed on PC')
        with self.device('phone'):
            db.toggle_card_favorite(ident);db.record_study_result(ident,3)
        self.sync('phone');self.sync('pc')
        self.assertEqual((self.card('pc')['is_favorite'],self.card('pc')['repetition_count']),(1,1))
    def test_offline_field_edits_merge_and_deleted_deck_does_not_resurrect(self):
        self.add('phone');self.pair();self.edit('pc',definition='PC meaning');self.edit('phone',notes='phone note');self.pair()
        for name in self.clients:self.assertEqual((self.card(name)['definition'],self.card(name)['notes']),('PC meaning','phone note'))
        self.edit('phone',notes='offline unsent')
        with self.device('pc'):db.delete_deck(self.card('pc')['deck_id'])
        self.sync('pc');self.sync('phone')
        with self.device('phone'),db.get_connection() as conn:
            self.assertFalse(any(c['term']=='google-word' for c in db.get_all_cards()))
            recovered=[json.loads(row[0]) for row in conn.execute("SELECT data FROM sync_recovery WHERE entity='card'")]
            self.assertEqual(next(row for row in recovered if row.get('term')=='google-word')['notes'],'offline unsent')
            self.assertEqual(self.clients['phone'].pending_count(),0)
    def test_etag_conflict_retries_without_losing_other_device_field(self):
        self.add('phone');self.pair();self.edit('pc',definition='concurrent meaning');self.edit('phone',notes='concurrent note')
        self.remote.before_put=lambda:self.sync('pc')
        self.sync('phone');self.sync('pc')
        for name in self.clients:self.assertEqual((self.card(name)['definition'],self.card(name)['notes']),('concurrent meaning','concurrent note'))
    def test_lost_cloud_response_can_retry_without_creating_duplicate_records(self):
        self.add('phone')
        request=self.remote.request
        def lost(method,*args,**kwargs):
            value=request(method,*args,**kwargs)
            if method=='PUT':raise CloudError('offline')
            return value
        with patch.object(self.cloud,'request',side_effect=lost),self.assertRaises(CloudError):self.sync('phone')
        revision=self.remote.snapshot['revision'];self.sync('phone')
        self.assertEqual(self.remote.snapshot['revision'],revision)
        self.sync('pc');self.assertEqual(self.card('pc')['term'],'google-word')
    def test_offline_queue_and_session_refresh_survive_restart(self):
        self.add('phone');client=self.clients['phone'];session=client.session();session['expires']=0;client.save_session(session)
        with patch.object(self.cloud,'request',side_effect=CloudError('offline')),self.assertRaises(CloudError):self.sync('phone')
        with self.device('phone'):
            self.assertGreater(client.pending_count(),0)
            restarted=SyncClient(client.session_path,cloud_factory=lambda:self.cloud);restarted.sync()
            self.assertEqual(restarted.session()['token'],'refreshed-token')
        self.sync('pc');self.assertEqual(self.card('pc')['term'],'google-word')
    def test_refresh_cannot_switch_uid_and_library_cannot_switch_account(self):
        client=self.clients['phone'];session=client.session();session['expires']=0;client.save_session(session)
        self.remote.refresh_uid='someone-else'
        with self.assertRaises(CloudError):self.sync('phone')
        self.assertEqual(client.session()['token'],'token')
        with self.device('phone'),self.assertRaises(SyncError):client.bind_google_account(dict(session,user_id='other-account'))
        self.assertEqual(client.session()['user_id'],'google-user')
    def test_unchanged_cloud_poll_reads_only_revision(self):
        self.pair();self.remote.calls.clear();self.sync('pc')
        self.assertEqual(self.remote.calls,[('GET','/users/google-user/library/revision.json')])
    def test_legacy_same_email_migrates_and_logout_keeps_library(self):
        self.add('phone');self.pair();ident=self.card('phone')['id']
        with self.device('phone'),db.get_connection() as conn:
            conn.execute("UPDATE sync_config SET value='https://legacy.example|old-user' WHERE key='account'")
        with self.device('phone'):
            self.clients['phone'].bind_google_account(self.cloud.sign_in('token'))
            self.assertEqual(db.get_card(ident)['term'],'google-word')
            self.assertGreater(self.clients['phone'].pending_count(),0)
            self.clients['phone'].logout();self.assertEqual(self.clients['phone'].session(),{})
            self.assertEqual(db.get_card(ident)['term'],'google-word')
    def test_google_panel_has_no_server_or_password_and_all_languages_update(self):
        view=AccountPanel();self.addCleanup(view.deleteLater)
        self.assertFalse(view.findChildren(QLineEdit))
        for lang,button in [('tr','Google ile giriş yap'),('en','Sign in with Google'),('de','Mit Google anmelden'),('es','Iniciar sesión con Google')]:
            view.update_language(lang);self.assertEqual(view.google.text(),button)
        with patch('duocards.widgets.account_panel.cloud_ready',return_value=False):
            view.refresh();self.assertFalse(view.google.isEnabled());self.assertFalse(view.availability.isHidden())
    def test_configuration_rejects_credentials_redirects_and_foreign_database_hosts(self):
        self.assertEqual(validate_config(CONFIG,True),CONFIG)
        for url in ('http://studycard.firebaseio.com','https://evil.example','https://user:password@studycard.firebaseio.com','https://studycard.firebaseio.com/path','https://studycard.firebaseio.com?token=x'):
            with self.subTest(url=url),self.assertRaises(CloudError):validate_config(dict(CONFIG,databaseURL=url),True)
        with self.assertRaises(CloudError):validate_config({},True)
    def test_pkce_and_callback_reject_wrong_state_duplicate_code_and_wrong_path(self):
        verifier='random-verifier';params=oauth_parameters(CONFIG['desktopClientId'],'http://127.0.0.1:1234/callback','state',verifier)
        self.assertEqual(params['code_challenge'],base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode())
        self.assertEqual(params['scope'],'openid email profile')
        self.assertEqual(callback_result('/callback?state=state&code=code','state'),{'code':'code'})
        for value in ('/callback?state=wrong&code=x','/wrong?state=state&code=x','/callback?state=state&code=x&code=y','/callback?state=%C3%84&code=x'):
            self.assertIsNone(callback_result(value,'state'))
        self.assertEqual(callback_result('/callback?state=state&error=access_denied','state'),{'error':'Google sign-in was canceled.'})
    def test_google_id_token_exchanged_server_side_without_trusting_its_claims(self):
        seen=[]
        def capture(method,url,body=None,headers=None):seen.append(json.loads(body));return self.remote.request(method,url,body,headers)
        session=FirebaseCloud(CONFIG,capture).sign_in('opaque-id-token')
        post=urllib.parse.parse_qs(seen[0]['postBody'])
        self.assertEqual(post,{'id_token':['opaque-id-token'],'providerId':['google.com']})
        self.assertEqual(session['user_id'],'google-user');self.assertNotIn('password',session)

    def test_desktop_browser_callback_exchanges_code_with_pkce_then_firebase(self):
        query={};posts=[];pages=[]
        def browser(url):query.update(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query));return True
        class Server:
            def __init__(self,address,handler):self.handler=handler;self.server_port=12345
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def handle_request(self):
                path='/callback?'+urllib.parse.urlencode({'state':query['state'][0],'code':'authorization-code'})
                raw=('GET '+path+' HTTP/1.1\r\nHost: 127.0.0.1:12345\r\nConnection: close\r\n\r\n').encode()
                class Socket:
                    def __init__(self):self.output=io.BytesIO()
                    def makefile(self,*args):return io.BytesIO(raw)
                    def sendall(self,value):self.output.write(value)
                socket=Socket();self.handler(socket,('127.0.0.1',1000),self);pages.append(socket.output.getvalue())
        def request(method,url,body=None,headers=None):
            posts.append((url,body))
            if url=='https://oauth2.googleapis.com/token':return {'access_token':'google-access-token'},None
            return self.remote.request(method,url,body,headers)
        with patch.object(cloud_account,'HTTPServer',Server),patch.object(cloud_account,'http',side_effect=request):
            account=cloud_account.google_sign_in(CONFIG,browser=browser,lang='de')
        self.assertEqual(account['user_id'],'google-user')
        code=urllib.parse.parse_qs(posts[0][1].decode())
        self.assertEqual(code['code'],['authorization-code'])
        self.assertEqual(query['code_challenge'][0],base64.urlsafe_b64encode(hashlib.sha256(code['code_verifier'][0].encode()).digest()).rstrip(b'=').decode())
        assertion=urllib.parse.parse_qs(json.loads(posts[1][1])['postBody'])
        self.assertEqual(assertion['access_token'],['google-access-token'])
        self.assertIn('Du kannst diesen Tab',pages[0].decode())


if __name__=='__main__':unittest.main()
