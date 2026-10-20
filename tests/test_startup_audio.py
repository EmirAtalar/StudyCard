"""Açılış ve gizli ekran sesleri için ağ/veritabanından yalıtılmış kontroller."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from duocards import db
from duocards.settings import settings
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.main_window import MainWindow
from duocards.widgets.settings_view import SettingsView


class StartupAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.original_settings = settings.get_all()
        self.addCleanup(setattr, settings, '_settings', self.original_settings)
        settings._settings.update(ai_enabled=True, auto_pronounce=True,
                                  pronounce_trigger='both', ai_provider='groq')
        self.save = patch.object(settings, 'save').start()
        self.prefetch = patch.object(audio_player, 'prefetch').start()
        self.addCleanup(patch.stopall)

    def test_loading_settings_is_read_only_and_silent(self):
        before = settings.get_all()
        with patch.object(sfx, '_play_file') as sound:
            view = SettingsView()
            view.load_values()
            self.assertEqual(settings.get_all(), before)
            self.save.assert_not_called()
            sound.assert_not_called()
            view.deleteLater()

    def test_hidden_pages_defer_speech_downloads_until_they_are_shown(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(db, 'DB_DIR', tmp), \
                patch.object(db, 'DB_PATH', tmp + '/cards.db'), \
                patch.object(sfx, '_play_file'), \
                patch.object(audio_player, 'play_pronunciation'), \
                patch.object(MainWindow, '_setup_app_shortcut'), \
                patch.object(MainWindow, '_setup_tray_icon'):
            window = MainWindow()
            try:
                self.prefetch.assert_not_called()
                window.show()
                QTest.qWait(50)
                allowed={card['term'] for card in window.view_study.cards_queue[:3]}
                self.assertTrue(self.prefetch.called)
                self.assertTrue(all(call.args[0] in allowed for call in self.prefetch.call_args_list))
                window.switch_to_settings()
                self.prefetch.reset_mock()
                window.view_dictation.reload_cards(force=True)
                self.prefetch.assert_not_called()
                window.switch_to_dictation()
                QTest.qWait(50)
                self.assertTrue(self.prefetch.called)
            finally:
                window._is_force_quitting = True
                window.close()
                window.deleteLater()

    def test_startup_and_hidden_dictation_are_silent(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(db, 'DB_DIR', tmp), \
                patch.object(db, 'DB_PATH', tmp + '/cards.db'), \
                patch.object(sfx, '_play_file') as sound, \
                patch.object(audio_player, 'play_pronunciation') as speech, \
                patch.object(MainWindow, '_setup_app_shortcut'), \
                patch.object(MainWindow, '_setup_tray_icon'):
            window = MainWindow()
            try:
                window.show()
                QTest.qWait(600)
                sound.assert_not_called()
                speech.assert_not_called()
                window.switch_to_dictation()
                QTest.qWait(350)
                self.assertEqual(speech.call_count, 1)
                window.view_dictation._next_item()
                window.switch_to_study(allow_autoplay=False)
                QTest.qWait(350)
                self.assertEqual(speech.call_count, 1)
                window.view_study.card_widget._play_audio()
                self.assertEqual(speech.call_count, 2)
            finally:
                window._is_force_quitting = True
                window.close()
                window.deleteLater()


if __name__ == '__main__':
    unittest.main()
