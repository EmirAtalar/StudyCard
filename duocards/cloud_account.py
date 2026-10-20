"""Google sign-in and Firebase REST sync, without a user-entered server address."""
import base64
import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from sync_server.service import Service, ServiceError, UUID_RE

CONFIG_PATH = Path(__file__).parent / 'data' / 'firebase_config.json'
MAX_RESPONSE = 32 * 1024 * 1024


class CloudError(Exception):
    pass


class CloudConflict(CloudError):
    pass


def load_config(path=None):
    try:
        return json.loads(Path(path or os.environ.get('STUDYCARD_FIREBASE_CONFIG', CONFIG_PATH)).read_text())
    except (OSError, ValueError):
        return {}


def validate_config(config, desktop=False):
    project = config.get('projectId', '')
    url = urllib.parse.urlsplit(config.get('databaseURL', ''))
    if (not re.fullmatch(r'[a-z][a-z0-9-]{4,62}', project)
            or not re.fullmatch(r'AIza[A-Za-z0-9_-]{30,}', config.get('apiKey', ''))
            or url.scheme != 'https' or url.username or url.password or url.query or url.fragment
            or url.path not in ('', '/') or url.port is not None
            or not url.hostname or not re.fullmatch(r'[a-z0-9.-]+\.(?:firebaseio\.com|firebasedatabase\.app)', url.hostname)):
        raise CloudError('Google sign-in is not available in this build yet. Your offline cards are safe.')
    key = 'desktopClientId' if desktop else 'webClientId'
    if not re.fullmatch(r'[0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com', config.get(key, '')):
        raise CloudError('Google sign-in is not available in this build yet. Your offline cards are safe.')
    return config


def cloud_ready(desktop=True):
    try:
        validate_config(load_config(), desktop)
        return True
    except (CloudError, ValueError, TypeError):
        return False


def http(method, url, body=None, headers=None):
    request = urllib.request.Request(url, body, dict(headers or {}), method=method)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args):
            return None
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            data = response.read(MAX_RESPONSE + 1)
            if len(data) > MAX_RESPONSE:
                raise CloudError('The cloud library is too large to sync in this build.')
            return json.loads(data or 'null'), response.headers.get('ETag')
    except urllib.error.HTTPError as error:
        if error.code == 412:
            raise CloudConflict('Cloud changes arrived during sync. Retrying…') from None
        if error.code in (401, 403):
            raise CloudError('Cloud access was denied. Sign in again or check the project configuration.') from None
        raise CloudError('Google could not complete the request. Please try again.') from None
    except (urllib.error.URLError, OSError, ValueError):
        raise CloudError('Cloud is unreachable. Your changes remain on this device and will be retried.') from None


def oauth_parameters(client_id, redirect, state, verifier):
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return dict(client_id=client_id, redirect_uri=redirect, response_type='code',
                scope='openid email profile', state=state, code_challenge=challenge,
                code_challenge_method='S256', prompt='select_account')


def callback_result(path, expected_state):
    parsed = urllib.parse.urlsplit(path)
    query = urllib.parse.parse_qs(parsed.query)
    if parsed.path != '/callback' or len(query.get('state', [])) != 1 or not hmac.compare_digest(query['state'][0].encode(), expected_state.encode()):
        return None
    if query.get('error'):
        return {'error': 'Google sign-in was canceled.'}
    if len(query.get('code', [])) != 1 or not query['code'][0]:
        return None
    return {'code': query['code'][0]}


def google_sign_in(config, cancel=None, lang='en', browser=webbrowser.open):
    validate_config(config, desktop=True)
    from duocards.ui_localization import ui_text
    cancel = cancel or threading.Event()
    if cancel.is_set():
        raise CloudError('Google sign-in was canceled.')
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    result = {}
    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            value = callback_result(self.path, state)
            if value is None or result:
                self.send_error(400)
                return
            result.update(value)
            text = ui_text('You can close this tab and return to Study Card.', lang)
            page = ('<!doctype html><meta charset="utf-8"><title>Study Card</title><p>' + text + '</p>').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(page)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'")
            self.end_headers()
            self.wfile.write(page)
        def log_message(self, *args):
            pass
    try:
        server = HTTPServer(('127.0.0.1', 0), Callback)
    except OSError:
        raise CloudError('The browser sign-in callback could not start. Please try again.') from None
    with server:
        server.timeout = .5
        redirect = f'http://127.0.0.1:{server.server_port}/callback'
        url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(oauth_parameters(config['desktopClientId'], redirect, state, verifier))
        if not browser(url):
            raise CloudError('The browser could not open. Please try again.')
        deadline = time.monotonic() + 180
        while not result and not cancel.is_set() and time.monotonic() < deadline:
            server.handle_request()
    if cancel.is_set() or result.get('error'):
        raise CloudError('Google sign-in was canceled.')
    if not result:
        raise CloudError('Google sign-in timed out. Please try again.')
    data = urllib.parse.urlencode(dict(client_id=config['desktopClientId'], code=result['code'],
                                      code_verifier=verifier, redirect_uri=redirect, grant_type='authorization_code')).encode()
    if config.get('desktopClientSecret'):
        data += b'&client_secret=' + urllib.parse.quote(config['desktopClientSecret'], safe='').encode()
    tokens, _ = http('POST', 'https://oauth2.googleapis.com/token', data, {'Content-Type': 'application/x-www-form-urlencoded'})
    if cancel.is_set():
        raise CloudError('Google sign-in was canceled.')
    return FirebaseCloud(config).sign_in(tokens.get('access_token', ''), access_token=True)


def merge_library(snapshot, body):
    """Same patch/tombstone protocol as the existing server, under an ETag CAS."""
    snapshot = copy.deepcopy(snapshot or {})
    cursor, changes = body.get('cursor', 0), body.get('changes', [])
    if type(cursor) is not int or cursor < 0 or not isinstance(changes, list) or len(changes) > 500:
        raise CloudError('Invalid cloud sync data.')
    if snapshot and snapshot.get('schema_version') != 1:
        raise CloudError('The cloud library format is not supported by this build.')
    snapshot.setdefault('schema_version', 1)
    snapshot.setdefault('revision', 0)
    records = snapshot.setdefault('records', {})
    if not isinstance(records, dict) or type(snapshot['revision']) is not int:
        raise CloudError('Invalid cloud sync data.')
    def unpack(row):
        return dict(entity=row['entity'], uuid=row['uuid'], revision=row['revision'],
                    deleted=row['deleted'], data=json.loads(row['data_json']))
    def save(entity, ident, data, deleted):
        snapshot['revision'] += 1
        records[ident] = dict(entity=entity, uuid=ident, revision=snapshot['revision'], deleted=deleted,
                             data_json=json.dumps(data, ensure_ascii=False, allow_nan=False, sort_keys=True))
    try:
        for change in sorted(changes, key=lambda c: 0 if isinstance(c, dict) and c.get('entity') == 'deck' else 1):
            if not isinstance(change, dict):
                raise CloudError('Invalid cloud sync data.')
            entity, ident = change.get('entity'), change.get('uuid')
            deleted, patch = change.get('deleted', False), change.get('data', {})
            if entity not in ('deck', 'card') or not isinstance(ident, str) or not UUID_RE.fullmatch(ident) or type(deleted) is not bool:
                raise CloudError('Invalid cloud sync data.')
            old = unpack(records[ident]) if ident in records else None
            if old and old['entity'] != entity:
                raise CloudError('Invalid cloud sync data.')
            if old and old['deleted']:
                continue
            Service.validate(entity, patch)
            data = dict(old['data'] if old else {}, **patch)
            if not deleted:
                Service.validate(entity, data, complete=True)
            if entity == 'card' and not deleted:
                parent = records.get(data['deck_uuid'])
                if not parent or parent['entity'] != 'deck':
                    raise CloudError('The card deck could not sync. Please try again.')
                if parent['deleted']:
                    deleted = True
            if old and old['deleted'] == deleted and old['data'] == data:
                continue
            save(entity, ident, data, deleted)
            if entity == 'deck' and deleted:
                for child in list(records.values()):
                    if child['entity'] == 'card' and not child['deleted']:
                        child_data = json.loads(child['data_json'])
                        if child_data.get('deck_uuid') == ident:
                            save('card', child['uuid'], child_data, True)
        rows = sorted((unpack(row) for row in records.values() if row['revision'] > cursor), key=lambda r: r['revision'])
        page = rows[:500]
        acknowledged = [unpack(records[c['uuid']]) for c in changes if c['uuid'] in records]
        return snapshot, dict(records=page, acknowledged=acknowledged,
                              cursor=page[-1]['revision'] if page else cursor, has_more=len(rows) > 500)
    except (ServiceError, KeyError, TypeError, ValueError) as error:
        raise CloudError('Invalid cloud sync data.') from error


class FirebaseCloud:
    def __init__(self, config=None, request=None):
        self.config = validate_config(config or load_config())
        self.request = request or http

    def sign_in(self, credential, access_token=False):
        if not credential:
            raise CloudError('Google could not complete the request. Please try again.')
        post = urllib.parse.urlencode({'access_token' if access_token else 'id_token': credential, 'providerId': 'google.com'})
        body = dict(postBody=post, requestUri=f"https://{self.config['projectId']}.firebaseapp.com", returnSecureToken=True)
        response, _ = self.request('POST', 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key=' + self.config['apiKey'],
                                   json.dumps(body).encode(), {'Content-Type': 'application/json'})
        if response.get('providerId') != 'google.com' or not response.get('emailVerified'):
            raise CloudError('Google could not complete the request. Please try again.')
        return dict(provider='firebase', server='firebase:' + self.config['projectId'], user_id=response['localId'],
                    email=response['email'], token=response['idToken'], refresh_token=response['refreshToken'],
                    expires=int(time.time()) + int(response['expiresIn']))

    def refresh(self, session):
        if session.get('expires', 0) > time.time() + 60:
            return session
        body = urllib.parse.urlencode(dict(grant_type='refresh_token', refresh_token=session['refresh_token'])).encode()
        value, _ = self.request('POST', 'https://securetoken.googleapis.com/v1/token?key=' + self.config['apiKey'],
                                body, {'Content-Type': 'application/x-www-form-urlencoded'})
        if value.get('user_id') != session['user_id']:
            raise CloudError('This library belongs to another Google account. Sign in with the original account.')
        return dict(session, token=value['id_token'], refresh_token=value['refresh_token'], expires=int(time.time()) + int(value['expires_in']))

    def exchange(self, session, body):
        uid = session['user_id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', uid) or session['server'] != 'firebase:' + self.config['projectId']:
            raise CloudError('This library belongs to another Google account. Sign in with the original account.')
        root = self.config['databaseURL'].rstrip('/') + '/users/' + uid + '/library'
        auth = '?auth=' + urllib.parse.quote(session['token'], safe='')
        if not body.get('changes'):
            revision, _ = self.request('GET', root + '/revision.json' + auth)
            if (revision or 0) == body['cursor']:
                return dict(records=[], acknowledged=[], cursor=body['cursor'], has_more=False)
        for _ in range(5):
            previous, etag = self.request('GET', root + '.json' + auth, headers={'X-Firebase-ETag': 'true'})
            merged, response = merge_library(previous, body)
            if merged['revision'] == (previous or {}).get('revision', 0):
                return response
            if not etag:
                raise CloudError('Google could not complete the request. Please try again.')
            encoded = json.dumps(merged, ensure_ascii=False, allow_nan=False).encode()
            if len(encoded) > MAX_RESPONSE:
                raise CloudError('The cloud library is too large to sync in this build.')
            try:
                self.request('PUT', root + '.json' + auth, encoded, {'Content-Type': 'application/json', 'If-Match': etag})
                return response
            except CloudConflict:
                continue
        raise CloudError('Cloud changes arrived during sync. Please retry.')
