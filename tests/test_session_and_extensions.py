"""Sayfalar arası oturum devamlılığı ve yeni dil paketlerinin işlev kontrolleri."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from duocards import db
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.audio import audio_player
from duocards.main_window import MainWindow
from duocards.learning_extensions import LEARNING_EXTENSIONS
from duocards.widgets.extensions_view import AVAILABLE_EXTENSIONS


class SessionAndExtensionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        before = settings.get_all()
        self.addCleanup(setattr, settings, '_settings', before)
        settings._settings.update(ui_language='tr', auto_pronounce=False)
        tmp = self.stack.enter_context(tempfile.TemporaryDirectory())
        for obj, name, value in [(db, 'DB_DIR', tmp), (db, 'DB_PATH', tmp+'/cards.db')]:
            self.stack.enter_context(patch.object(obj, name, value))
        self.stack.enter_context(patch.object(settings, 'save'))
        self.stack.enter_context(patch.object(sfx, '_play_file'))
        self.speech = self.stack.enter_context(patch.object(audio_player, 'play_pronunciation'))
        self.stack.enter_context(patch.object(MainWindow, '_setup_app_shortcut'))
        self.stack.enter_context(patch.object(MainWindow, '_setup_tray_icon'))
        self.window = MainWindow()
        self.window.show()
        self.addCleanup(self.close_window)

    def close_window(self):
        self.window._is_force_quitting = True
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def rate(self, rating):
        self.window.view_study._rate_card(rating)
        # Wait for the actual transition; initial layout can delay offscreen frames.
        for _ in range(200):
            QTest.qWait(10)
            if not self.window.view_study._is_transitioning:
                break

    def snapshot(self):
        view = self.window.view_study
        return (
            [c['id'] for c in view.cards_queue],
            [c['id'] for c in view.repeat_queue],
            [c['id'] for c in view.session_failed_cards],
            view.known_count, view.again_count, view.session_total_count,
            view.lbl_counter.text(), view.progress_bar.value(),
            view.card_widget._card_data['id'],
            view.card_widget.is_back_showing(), view.card_widget.input_recall.text(),
            view.stack.currentWidget(),
        )

    def test_navigation_preserves_progress_and_repeat_queue(self):
        view = self.window.view_study
        view.reload_session(custom_cards=db.get_all_cards()[:6], allow_autoplay=False)
        self.rate(1)
        self.rate(3)
        view.card_widget.flip(animated=False)
        view.card_widget.input_recall.setText('yarım kalan cevap')
        before = self.snapshot()
        for navigate in (self.window.switch_to_library, self.window.switch_to_stats,
                         self.window.switch_to_extensions, self.window.switch_to_settings):
            navigate()
            self.window.switch_to_study()
            QTest.qWait(30)
            self.assertEqual(self.snapshot(), before)

    def test_completed_session_is_preserved_and_can_be_restarted(self):
        view = self.window.view_study
        cards = db.get_all_cards()[:2]
        view.reload_session(custom_cards=cards, allow_autoplay=False)
        self.rate(3)
        self.rate(3)
        self.assertIs(view.stack.currentWidget(), view.page_completed)
        known = view.known_count
        self.window.switch_to_library()
        self.window.switch_to_study()
        self.assertIs(view.stack.currentWidget(), view.page_completed)
        self.assertEqual(view.known_count, known)
        view.btn_comp_restart.click()
        self.assertEqual(view.known_count, 0)
        self.assertFalse(view.repeat_queue)

    def test_five_extensions_open_search_quiz_and_play_audio(self):
        self.assertEqual(len(LEARNING_EXTENSIONS), 2)
        self.assertEqual(len({e['id'] for e in AVAILABLE_EXTENSIONS}), len(AVAILABLE_EXTENSIONS))
        for ext in LEARNING_EXTENSIONS:
            with self.subTest(extension=ext['id']):
                card = next(c for c in self.window.view_extensions.cards if c.data['id'] == ext['id'])
                if not settings.get(ext['setting_key'], False):
                    card.btn_toggle.click()
                self.assertFalse(self.window.extension_nav_btns[ext['id']].isHidden())
                card.btn_open.click()
                view = self.window.extension_views[ext['id']]
                self.assertIs(self.window.content_stack.currentWidget(), view)
                expected=26 if ext['id']=='en_confusing_words' else 25
                self.assertEqual(len(view.items), expected)
                self.assertEqual(len({item['term'] for item in view.items}), expected)
                self.assertEqual(view.table.rowCount(), expected)
                for item in view.items:
                    self.assertTrue(item['example'])
                    self.assertTrue(all(item['translations'].get(lang) for lang in ('tr','en','de','es')))
                    self.assertEqual(view._get_audio_text(item), item['term'])
                item = view.items[0]
                view.input_search.setText(item['term'])
                self.assertIn(item, view._visible_items)
                view.input_search.setText('no-such-entry-987654')
                self.assertEqual(view.table.rowCount(), 0)
                view.input_search.clear()
                view._play_item_audio(item)
                self.speech.assert_called_with(item['term'], lang='en')
                for lang in ('tr', 'en', 'de', 'es'):
                    view.update_language(lang)
                    self.assertEqual(view.table.horizontalHeaderItem(2).text(), ext['column_titles'][lang][2])
                    self.assertIn(str(expected), view.input_search.placeholderText())
                    view._show_quiz()
                    view._next_quiz()
                    self.assertEqual(len(view._choices_data), 2 if ext['id']=='en_confusing_words' else 4)
                    self.assertEqual(len(set(view._choices_data)), 2 if ext['id']=='en_confusing_words' else 4)
                    self.assertIn(view._quiz_correct_answer, view._choices_data)
                view._on_quiz_answer(view._choices_data.index(view._quiz_correct_answer))
                self.assertEqual(view._quiz_score, 1)
        QTest.qWait(1500)


if __name__ == '__main__':
    unittest.main()
