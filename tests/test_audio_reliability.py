"""Speech cache compatibility, retry behavior and foreground request isolation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import hashlib
import base64
import json
import tempfile
import threading
import unittest
import urllib.error
from concurrent.futures import Future
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtTest import QTest
from duocards import audio
from duocards.widgets import library_view
from duocards.settings import settings
from duocards.widgets.card_widget import FlashcardWidget


def response(payload=b'ID3voice'):
    result = MagicMock()
    result.__enter__.return_value = result
    result.headers = {'Content-Type': 'audio/mpeg'}
    result.read.return_value = payload
    return result


def rpc_response(payload=b'ID3voice'):
    frame = json.dumps([['wrb.fr', 'jQ1olc', json.dumps([base64.b64encode(payload).decode()]), None, None, None, 'generic']]).encode()
    return response(b")]}'\n\n" + str(len(frame)).encode() + b'\n' + frame + b'\n')


class AudioReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(audio, 'CACHE_DIR', self.directory))
        self.stack.enter_context(patch.dict('sys.modules', {'edge_tts': None}))
        self.player = audio.AudioPlayer()
        self.addCleanup(self.player._prefetch_pool.shutdown, wait=True, cancel_futures=True)

    def cache(self, text, payload=b'ID3voice'):
        path = Path(audio._get_cache_path(text, 'en'))
        path.write_bytes(payload)
        return path

    def legacy(self, text, payload=b'ID3legacy'):
        key = hashlib.md5(f'en_{text.strip().lower()}'.encode()).hexdigest()
        path = Path(self.directory) / (key + '.mp3')
        path.write_bytes(payload)
        return path

    def test_legacy_word_audio_is_recovered_without_internet(self):
        text = "You're welcome"
        old = self.legacy(text)
        with patch.object(audio.urllib.request, 'urlopen') as fetch:
            self.assertTrue(self.player._download(text, 'en'))
        fetch.assert_not_called()
        self.assertEqual(Path(audio._get_cache_path(text, 'en')).read_bytes(), old.read_bytes())
        self.assertTrue(old.exists())

    def test_legacy_long_sentence_is_rebuilt_to_avoid_truncated_audio(self):
        text = 'This example has enough context to explain the complete sentence. ' * 4
        self.legacy(text)
        with patch.object(audio.urllib.request, 'urlopen', return_value=response()) as fetch:
            self.assertTrue(self.player._download(text, 'en'))
        self.assertGreater(fetch.call_count, 1)
        self.assertEqual(Path(audio._get_cache_path(text, 'en')).read_bytes(), b'ID3voice' * fetch.call_count)

    def test_temporary_network_failure_is_retried_and_cached(self):
        with patch.object(audio.urllib.request, 'urlopen', side_effect=[urllib.error.URLError('temporary'), response()]) as fetch, \
                patch.object(audio.time, 'sleep'):
            self.assertTrue(self.player._download('candidate', 'en'))
            self.assertEqual(fetch.call_count, 2)
            self.assertTrue(self.player._download('candidate', 'en'))
            self.assertEqual(fetch.call_count, 2)

    def test_slow_multi_chunk_sentence_has_no_eight_second_cutoff(self):
        text = 'She explains every detail of this example to her colleagues before the meeting. ' * 4
        clock = [0.0]
        def fetch(*args, **kwargs):
            clock[0] += 4
            return response()
        with patch.object(audio.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(audio.urllib.request, 'urlopen', side_effect=fetch):
            self.assertTrue(self.player._download(text, 'en'))
        self.assertGreater(clock[0], 8)
        self.assertEqual(Path(audio._get_cache_path(text, 'en')).read_bytes(),
                         b'ID3voice' * len(list(audio._speech_chunks(text))))

    def test_html_cache_and_html_responses_are_not_played_as_audio(self):
        self.cache('broken', b'<html>Access denied</html>')
        self.legacy('broken', b'<html>Access denied</html>')
        with patch.object(audio.urllib.request, 'urlopen', side_effect=[response(b'<html>Error</html>'), response()]), \
                patch.object(audio.time, 'sleep'):
            self.assertTrue(self.player._download('broken', 'en'))
        self.assertEqual(Path(audio._get_cache_path('broken', 'en')).read_bytes(), b'ID3voice')

    def test_failed_download_never_leaves_partial_cache_and_can_retry(self):
        with patch.object(audio.urllib.request, 'urlopen', side_effect=urllib.error.URLError('offline')), \
                patch.object(audio.time, 'sleep'), self.assertLogs(audio.logger, level='WARNING'):
            self.assertFalse(self.player._prepare('retry', 'en', foreground=True).result())
        self.assertEqual(list(Path(self.directory).iterdir()), [])
        with patch.object(audio.urllib.request, 'urlopen', return_value=response()):
            self.assertTrue(self.player._prepare('retry', 'en', foreground=True).result())

    def test_failed_legacy_endpoint_uses_speech_rpc_and_caches_decoded_audio(self):
        failure = urllib.error.HTTPError('https://translate.google.com/translate_tts', 403, 'Forbidden', {}, None)
        with patch.object(audio.urllib.request, 'urlopen', side_effect=[failure, rpc_response()]) as fetch, \
                patch.object(audio.time, 'sleep'):
            self.assertTrue(self.player._download('cry', 'en'))
        self.assertEqual(fetch.call_count, 2)
        request = fetch.call_args.args[0]
        self.assertIn('/batchexecute', request.full_url)
        body = audio.urllib.parse.parse_qs(request.data.decode())
        call = json.loads(body['f.req'][0])[0][0]
        self.assertEqual(call[0], 'jQ1olc')
        self.assertEqual(json.loads(call[1]), ['cry', 'en', None, 'null'])
        self.assertEqual(Path(audio._get_cache_path('cry', 'en')).read_bytes(), b'ID3voice')

    def test_blocked_google_word_uses_recorded_pronunciation_and_plays_it(self):
        metadata=[dict(word='candidate',phonetics=[dict(audio='https://api.dictionaryapi.dev/media/candidate.mp3')])]
        requests=[]
        def fetch(request,timeout):
            requests.append(request.full_url)
            host=audio.urllib.parse.urlparse(request.full_url).hostname
            if host=='translate.google.com':
                raise urllib.error.HTTPError(request.full_url,403,'Forbidden',{},None)
            if request.full_url.endswith('/entries/en/candidate'):
                return response(json.dumps(metadata).encode())
            if request.full_url.endswith('/media/candidate.mp3'):
                return response(b'ID3recorded')
            self.fail('Unexpected speech request: '+request.full_url)
        self.player.mpv_path='/fake/mpv'
        self.player._generation=1
        states=[]
        self.player.request_state_changed.connect(lambda request,state:states.append(state))
        process=MagicMock()
        process.wait.return_value=0
        with patch.object(audio.urllib.request,'urlopen',side_effect=fetch), \
                patch.object(audio.subprocess,'Popen',return_value=process) as launch:
            self.player._play_worker('candidate','en',1.,1)
            self.assertTrue(self.player._download('candidate','en'))
        self.assertEqual(len(requests),4)
        self.assertEqual(states,['playing','idle'])
        self.assertEqual(Path(audio._get_cache_path('candidate','en')).read_bytes(),b'ID3recorded')
        self.assertEqual(launch.call_args.args[0][-1],audio._get_cache_path('candidate','en'))

    def test_blocked_google_phrase_uses_alternate_host_without_dictionary_lookup(self):
        text='She came into the room and quietly closed the door.'
        requests=[]
        def fetch(request,timeout):
            requests.append(request.full_url)
            host=audio.urllib.parse.urlparse(request.full_url).hostname
            if host=='translate.google.com':
                raise urllib.error.HTTPError(request.full_url,429,'Too Many Requests',{},None)
            self.assertEqual(host,'translate.googleapis.com')
            query=audio.urllib.parse.parse_qs(audio.urllib.parse.urlparse(request.full_url).query)
            self.assertEqual(query['q'],[text])
            self.assertEqual(query['tl'],['en'])
            return response(b'ID3alternate')
        with patch.object(audio.urllib.request,'urlopen',side_effect=fetch):
            self.assertTrue(self.player._download(text,'en'))
            self.assertTrue(self.player._download(text,'en'))
        self.assertEqual(len(requests),3)
        self.assertEqual(Path(audio._get_cache_path(text,'en')).read_bytes(),b'ID3alternate')

    def test_dictionary_recording_must_match_whole_word_and_language(self):
        metadata=[dict(word='other',phonetics=[dict(audio='https://api.dictionaryapi.dev/media/other.mp3')])]
        with patch.object(audio.urllib.request,'urlopen',return_value=response(json.dumps(metadata).encode())) as fetch:
            with self.assertRaises(ValueError):
                audio._fetch_dictionary_audio('candidate','en')
        self.assertEqual(fetch.call_count,1)
        with patch.object(audio.urllib.request,'urlopen') as fetch:
            for text,lang in (('take care','en'),('bonjour','fr')):
                with self.subTest(text=text,lang=lang),self.assertRaises(ValueError):
                    audio._fetch_dictionary_audio(text,lang)
        fetch.assert_not_called()

    def test_dictionary_skips_invalid_recording_and_tries_the_next_one(self):
        metadata=[None,dict(word=None,phonetics=None),dict(word='hello',phonetics=[dict(audio='//api.dictionaryapi.dev/media/broken.mp3'),
                                             dict(audio='https://api.dictionaryapi.dev/media/hello.mp3')])]
        with patch.object(audio.urllib.request,'urlopen',side_effect=[response(json.dumps(metadata).encode()),
                                                                   response(b'<html>Error</html>'),response(b'ID3recorded')]) as fetch:
            self.assertEqual(audio._fetch_dictionary_audio('Hello','en'),b'ID3recorded')
        self.assertEqual(fetch.call_args.args[0].full_url,'https://api.dictionaryapi.dev/media/hello.mp3')

    def test_speech_rpc_preserves_unicode_and_rejects_invalid_audio(self):
        with patch.object(audio.urllib.request, 'urlopen', return_value=rpc_response()) as fetch:
            self.assertEqual(audio._fetch_rpc_audio('ça va bien ?', 'fr'), b'ID3voice')
        body = audio.urllib.parse.parse_qs(fetch.call_args.args[0].data.decode())
        self.assertEqual(json.loads(json.loads(body['f.req'][0])[0][0][1])[:2], ['ça va bien ?', 'fr'])
        with patch.object(audio.urllib.request, 'urlopen', return_value=rpc_response(b'<html>Error</html>')):
            with self.assertRaises(ValueError):
                audio._fetch_rpc_audio('cry', 'en')

    def test_click_promotes_queued_prefetch_while_other_downloads_are_busy(self):
        release = threading.Event()
        started = [threading.Event() for _ in range(3)]
        def download(text, lang):
            if text == 'selected':
                self.cache(text)
                return True
            started[int(text)].set()
            release.wait(3)
            return False
        with patch.object(self.player, '_download', side_effect=download):
            try:
                for index in range(3):
                    self.player._prepare(str(index), 'en')
                self.assertTrue(all(event.wait(1) for event in started))
                queued = self.player._prepare('selected', 'en')
                selected = self.player._prepare('selected', 'en', foreground=True)
                self.assertTrue(selected.result(timeout=.5))
                self.assertTrue(queued.cancelled())
            finally:
                release.set()

    def test_running_prefetch_is_shared_instead_of_downloading_twice(self):
        existing = Future()
        existing.set_running_or_notify_cancel()
        self.player._downloads[('selected', 'en')] = existing
        with patch.object(self.player, '_download') as download:
            self.assertIs(self.player._prepare('selected', 'en', foreground=True), existing)
        download.assert_not_called()

    def test_failed_future_does_not_poison_subsequent_requests(self):
        existing = Future()
        existing.set_exception(RuntimeError('previous worker failed'))
        self.player._downloads[('selected', 'en')] = existing
        with patch.object(audio.urllib.request, 'urlopen', return_value=response()):
            self.assertTrue(self.player._prepare('selected', 'en', foreground=True).result())

    def test_cached_word_plays_even_when_prefetch_queue_is_busy(self):
        self.cache('cached')
        self.player.mpv_path = '/fake/mpv'
        self.player._generation = 1
        process = MagicMock()
        process.wait.return_value = 0
        with patch.object(self.player, '_prepare') as prepare, \
                patch.object(audio.subprocess, 'Popen', return_value=process) as launch:
            self.player._play_worker('cached', 'en', .75, 1)
        prepare.assert_not_called()
        self.assertIn('--speed=0.75', launch.call_args.args[0])

    def test_cancelled_request_stops_waiting_for_download(self):
        pending = Future()
        prepared = threading.Event()
        def prepare(*args, **kwargs):
            prepared.set()
            return pending
        self.player.mpv_path = '/fake/mpv'
        self.player._generation = 1
        with patch.object(self.player, '_prepare', side_effect=prepare), \
                patch.object(audio.subprocess, 'Popen') as launch:
            thread = threading.Thread(target=self.player._play_worker, args=('waiting', 'en', 1, 1), daemon=True)
            thread.start()
            self.assertTrue(prepared.wait(1))
            self.player.stop()
            thread.join(1)
            self.assertFalse(thread.is_alive())
            launch.assert_not_called()


class CardAudioFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        before = settings.get_all()
        self.addCleanup(setattr, settings, '_settings', before)
        settings._settings.update(ui_language='tr', auto_pronounce=False)
        self.widget = FlashcardWidget(is_preview=True)
        self.addCleanup(self.widget.deleteLater)
        self.widget.set_card(dict(id=1, term='hello', definition='merhaba', source_lang='en', target_lang='tr'))

    def test_card_reports_loading_failure_and_success_for_its_request_only(self):
        with patch.object(audio.audio_player, 'play_pronunciation', return_value=42):
            self.widget._play_audio()
        self.assertIn('hazırlanıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(41, 'unavailable')
        self.assertIn('hazırlanıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(42, 'unavailable')
        self.assertIn('İnternet', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(42, 'playing')
        self.assertIn('çalınıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(42, 'idle')
        self.assertTrue(self.widget.lbl_audio_status.isHidden())

    def test_next_card_ignores_failure_from_previous_card(self):
        with patch.object(audio.audio_player, 'play_pronunciation', return_value=42):
            self.widget._play_audio()
        self.widget.set_card(dict(id=2, term='goodbye', definition='hoşça kal', source_lang='en'))
        audio.audio_player.request_state_changed.emit(42, 'unavailable')
        self.assertTrue(self.widget.lbl_audio_status.isHidden())

    def test_sentence_uses_same_feedback_and_preserves_speed(self):
        self.widget._last_sentence_en = 'She said hello to her new colleagues before the meeting.'
        with patch.object(audio.audio_player, 'play_pronunciation', return_value=43) as speak:
            self.widget.play_sentence_audio()
        speak.assert_called_once_with(self.widget._last_sentence_en, lang='en', speed=.9)
        audio.audio_player.request_state_changed.emit(43, 'error')
        self.assertIn('Yeniden', self.widget.lbl_audio_status.text())


class LibraryAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        before = settings.get_all()
        self.addCleanup(setattr, settings, '_settings', before)
        settings._settings.update(ui_language='tr', auto_pronounce=False)
        self.cards = [dict(id=1, term='cry', definition='ağlamak', source_lang='en', target_lang='tr'),
                      dict(id=2, term='bonjour', definition='merhaba', source_lang='fr', target_lang='tr')]
        self.stack.enter_context(patch.object(library_view, 'get_all_cards', return_value=self.cards))
        self.stack.enter_context(patch.object(library_view, 'get_all_decks', return_value=[]))
        self.stack.enter_context(patch('duocards.db.get_distinct_target_languages', return_value=[]))
        self.stack.enter_context(patch.object(library_view.sfx, 'play_click'))
        self.widget = library_view.LibraryView()
        self.addCleanup(self.widget.deleteLater)
        self.widget.reload_cards()

    def button(self, row):
        return next(button for button in self.widget.table.cellWidget(row, 7).findChildren(QPushButton)
                    if button.property('action_btn') == 'audio')

    def test_each_library_row_plays_its_own_word_in_its_source_language(self):
        with patch.object(audio.audio_player, 'play_pronunciation', side_effect=[41, 42]) as speak:
            self.button(0).click()
            speak.assert_called_with('cry', lang='en')
            self.button(1).click()
            speak.assert_called_with('bonjour', lang='fr')
        audio.audio_player.request_state_changed.emit(41, 'unavailable')
        self.assertIn('hazırlanıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(42, 'playing')
        self.assertIn('çalınıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(42, 'idle')
        self.assertTrue(self.widget.lbl_audio_status.isHidden())

    def test_failed_library_audio_is_visible_and_the_same_button_retries(self):
        with patch.object(audio.audio_player, 'play_pronunciation', side_effect=[41, 42]) as speak:
            self.button(0).click()
            audio.audio_player.request_state_changed.emit(41, 'unavailable')
            self.assertIn('İnternet', self.widget.lbl_audio_status.text())
            self.button(0).click()
            self.assertEqual(speak.call_count, 2)
        self.assertIn('hazırlanıyor', self.widget.lbl_audio_status.text())
        audio.audio_player.request_state_changed.emit(41, 'error')
        self.assertIn('hazırlanıyor', self.widget.lbl_audio_status.text())

    def test_library_quiz_uses_the_same_speech_feedback(self):
        self.widget._current_quiz_card = self.cards[1]
        with patch.object(audio.audio_player, 'play_pronunciation', return_value=42) as speak:
            self.widget.btn_q_audio.click()
        speak.assert_called_once_with('bonjour', lang='fr')
        audio.audio_player.request_state_changed.emit(42, 'error')
        self.assertIn('Yeniden', self.widget.lbl_audio_status.text())

    def test_library_audio_status_follows_interface_language(self):
        with patch.object(audio.audio_player, 'play_pronunciation', return_value=42):
            self.button(0).click()
        audio.audio_player.request_state_changed.emit(42, 'unavailable')
        self.widget.update_language('en')
        self.assertIn('Check the connection', self.widget.lbl_audio_status.text())

    def test_row_click_downloads_uncached_audio_via_rpc_and_launches_player(self):
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        player = audio.AudioPlayer()
        player.mpv_path = '/fake/mpv'
        self.addCleanup(player._prefetch_pool.shutdown, wait=True, cancel_futures=True)
        process = MagicMock()
        process.wait.return_value = 0
        failure = urllib.error.URLError('legacy endpoint unavailable')
        with patch.object(audio, 'CACHE_DIR', directory), \
                patch.object(library_view, 'audio_player', player), \
                patch.dict('sys.modules', {'edge_tts': None}), \
                patch.object(audio.time, 'sleep'), \
                patch.object(audio.urllib.request, 'urlopen', side_effect=[failure, failure, rpc_response()]), \
                patch.object(audio.subprocess, 'Popen', return_value=process) as launch:
            widget = library_view.LibraryView()
            self.addCleanup(widget.deleteLater)
            widget.reload_cards()
            button = next(b for b in widget.table.cellWidget(0, 7).findChildren(QPushButton)
                          if b.property('action_btn') == 'audio')
            button.click()
            for _ in range(100):
                if launch.called and widget.lbl_audio_status.isHidden():
                    break
                QTest.qWait(10)
            launch.assert_called_once()
            self.assertEqual(Path(audio._get_cache_path('cry', 'en')).read_bytes(), b'ID3voice')
            self.assertEqual(launch.call_args.args[0][-1], audio._get_cache_path('cry', 'en'))
            self.assertTrue(widget.lbl_audio_status.isHidden())


if __name__ == '__main__':
    unittest.main()
