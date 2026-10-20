"""Gerçek tuş olaylarıyla soru-cevap, odak ve kısayol kapsamı kontrolleri."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from unittest.mock import patch
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from duocards import db
from duocards.practice import record_attempt
from duocards.main_window import MainWindow
from duocards.learning_extensions import LEARNING_EXTENSIONS
from duocards.widgets.match_game_view import MatchGameView
from test_practice_and_memory import AppFixture


class QuizKeyboardTests(AppFixture):
    def focus(self, view):
        view.activateWindow()
        QTest.qWait(20)
        view._keyboard.focus_answer()
        self.app.processEvents()

    def press(self, key, modifiers=Qt.KeyboardModifier.NoModifier):
        target = QApplication.focusWidget()
        self.assertIsNotNone(target)
        QTest.keyClick(target, Qt.Key(key), modifiers)
        self.app.processEvents()

    def finish_feedback(self, view):
        view._feedback_timer.stop()
        view._feedback_until = 0
        view._unlock_feedback()

    def window(self):
        self.stack.enter_context(patch.object(MainWindow, '_setup_app_shortcut'))
        self.stack.enter_context(patch.object(MainWindow, '_setup_tray_icon'))
        window = MainWindow()
        window.show()
        window.activateWindow()
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        window._is_force_quitting = True
        QTest.qWait(20)
        return window

    def test_typing_letters_numbers_and_spaces_does_not_trigger_shortcuts(self):
        self.card('share space 1234', 'örnek')
        view = self.view('writing')
        self.focus(view)
        self.assertIs(QApplication.focusWidget(), view.input_spelling)
        QTest.keyClicks(view.input_spelling, 'share space 1234')
        self.assertEqual(view.input_spelling.text(), 'share space 1234')
        self.assertFalse(view._quiz_locked)
        self.speech.assert_not_called()
        self.press(Qt.Key.Key_Return)
        self.assertEqual(view.score, 1)
        self.assertEqual(view._completed, 1)
        self.finish_feedback(view)
        self.press(Qt.Key.Key_Enter, Qt.KeyboardModifier.KeypadModifier)
        self.assertIsNone(view.current_card)
        self.press(Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)
        self.assertIs(QApplication.focusWidget(), view.input_spelling)
        self.assertEqual(view._completed, 0)

    def test_audio_hint_and_slow_audio_work_without_leaving_answer_input(self):
        self.card()
        view = self.view('writing')
        self.focus(view)
        QTest.keyClicks(view.input_spelling, 'app')
        self.press(Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        self.speech.assert_called_with('apple', lang='en', speed=1.0)
        self.press(Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        self.speech.assert_called_with('apple', lang='en', speed=0.75)
        self.press(Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(view.lbl_hint.isVisible())
        self.assertEqual(view.input_spelling.text(), 'app')
        self.assertIs(QApplication.focusWidget(), view.input_spelling)
        self.assertEqual(view._completed, 0)

    def test_all_card_practice_kinds_accept_keyboard_answers(self):
        cards = [self.card(), self.card('banana', 'muz', 'I ate a banana before leaving home for the morning meeting.')]
        for card in cards:
            db.toggle_card_favorite(card['id'])
            record_attempt(card, 'writing', 'wrong', card['term'], False)
        for kind in ('writing', 'mistakes', 'dictation', 'cloze', 'favorites'):
            with self.subTest(kind=kind):
                view = self.view(kind)
                self.focus(view)
                if view.typing_container.isVisible():
                    QTest.keyClicks(view.input_spelling, view._expected)
                    self.press(Qt.Key.Key_Enter)
                else:
                    index = view._choices_data.index(view._expected)
                    self.press(Qt.Key.Key_1 + index)
                self.assertEqual(view.score, 1)
                self.assertEqual(view._completed, 1)
                self.finish_feedback(view)
                self.assertFalse(view._quiz_locked)
                if view.typing_container.isVisible():
                    self.assertIs(QApplication.focusWidget(), view.input_spelling)
                else:
                    self.assertIn(QApplication.focusWidget(), view.btn_choices)
                view.hide()

    def test_choice_navigation_invalid_numbers_and_enter(self):
        self.card()
        self.card('banana', 'muz', 'I ate a banana before leaving home for the morning meeting.')
        view = self.view('cloze')
        self.focus(view)
        first = QApplication.focusWidget()
        self.assertIs(first, view.btn_choices[0])
        self.press(Qt.Key.Key_Right)
        self.assertIs(QApplication.focusWidget(), view.btn_choices[1])
        self.press(Qt.Key.Key_4)
        self.assertEqual(view._completed, 0)
        view.btn_choices[view._choices_data.index(view._expected)].setFocus()
        self.press(Qt.Key.Key_Return)
        self.assertEqual(view.score, 1)

    def test_feedback_wait_is_preserved_and_held_keys_cannot_skip_question(self):
        self.card()
        self.card('banana', 'muz', 'I ate a banana before leaving home for the morning meeting.')
        view = self.view('cloze')
        self.focus(view)
        self.press(Qt.Key.Key_1 + view._choices_data.index(view._expected))
        answered = view.current_card['id']
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space, Qt.Key.Key_1):
            self.press(key)
        self.assertEqual(view.current_card['id'], answered)
        self.assertEqual(view._completed, 1)
        self.assertFalse(view.btn_next.isEnabled())
        QTest.qWait(400)
        self.assertNotEqual(view.current_card['id'], answered)
        current=view.current_card['id']
        held = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return,
                         Qt.KeyboardModifier.NoModifier, '', True)
        QApplication.sendEvent(QApplication.focusWidget(), held)
        self.assertEqual(view.current_card['id'], current)
        self.assertEqual(view._completed,1)

    def test_enter_on_audio_button_and_filters_preserves_their_actions(self):
        self.card()
        self.card('banana', 'muz', 'I ate a banana before leaving home for the morning meeting.')
        view = self.view('cloze')
        self.focus(view)
        view.btn_play_audio.setFocus()
        self.press(Qt.Key.Key_Return)
        self.speech.assert_called_once()
        self.assertEqual(view._completed, 0)
        view.cmb_deck.setFocus()
        previous = view.cmb_deck.currentIndex()
        self.press(Qt.Key.Key_Up)
        self.assertEqual(view.cmb_deck.currentIndex(), previous - 1)
        self.assertEqual(view._completed, 0)

    def test_new_language_packs_and_library_quiz_use_same_keys(self):
        for i in range(4):
            self.card(f'word{i}', f'meaning{i}', '')
        window = self.window()
        views = []
        window.switch_to_library()
        window.view_library._show_quiz()
        views.append(window.view_library)
        for ext in LEARNING_EXTENSIONS:
            window.switch_to_extension(ext['id'])
            view = window.extension_views[ext['id']]
            view._show_quiz()
            views.append(view)
        for view in views:
            window.content_stack.setCurrentWidget(view)
            self.focus(view)
            self.assertIn('1–2' if getattr(view,'module_id','')=='en_confusing_words' else '1–4', view.lbl_keyboard_help.text())
            self.press(Qt.Key.Key_1 + view._choices_data.index(view._quiz_correct_answer))
            self.assertEqual(view._quiz_score, 1)
            self.press(Qt.Key.Key_1)
            self.assertEqual(view._quiz_score, 1)
            self.finish_feedback(view)
            self.press(Qt.Key.Key_Space)
            self.assertFalse(view._quiz_locked)
            self.assertIn(QApplication.focusWidget(), view.btn_choices)
            self.press(Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)
            self.assertEqual(view._quiz_score, 0)

    def test_irregular_verbs_typing_enter_and_focus(self):
        window = self.window()
        window.switch_to_extension('en_verbs')
        view = window.extension_views['en_verbs']
        view._show_quiz()
        choose = __import__('random').choice
        def typing_mode(options):
            return 'verb_v2' if options == ['verb_v2', 'verb_v3', 'verb_v1', 'meaning'] else choose(options)
        with patch('duocards.widgets.universal_module_view.random.choice', side_effect=typing_mode):
            view._next_quiz()
            self.focus(view)
            self.assertIs(QApplication.focusWidget(), view.input_typed_answer)
            view.input_typed_answer.setText(view._quiz_correct_answer)
            self.press(Qt.Key.Key_Return)
            self.assertEqual(view._quiz_score, 1)
            self.finish_feedback(view)
            self.press(Qt.Key.Key_Return)
            self.assertIs(QApplication.focusWidget(), view.input_typed_answer)

    def test_hidden_feedback_and_quiz_table_do_not_capture_keys_or_focus(self):
        self.card()
        window = self.window()
        window.switch_to_practice('writing')
        view = window.practice_views['writing']
        self.focus(view)
        view.input_spelling.setText(view._expected)
        self.press(Qt.Key.Key_Return)
        window.switch_to_add()
        window.view_add_card.input_term.setFocus()
        QTest.keyClicks(window.view_add_card.input_term, 'share 1234')
        self.assertEqual(window.view_add_card.input_term.text(), 'share 1234')
        self.finish_feedback(view)
        self.assertIs(QApplication.focusWidget(), window.view_add_card.input_term)
        window.switch_to_extension('en_phrasal')
        module = window.extension_views['en_phrasal']
        module._show_table()
        module.input_search.setFocus()
        QTest.keyClicks(module.input_search, 'share 1234')
        self.assertEqual(module.input_search.text(), 'share 1234')
        self.assertIsNone(module._current_quiz)

    def test_match_game_selects_and_matches_tiles_from_keyboard(self):
        for i in range(4):
            self.card(f'word{i}', f'meaning{i}', '')
        view = MatchGameView()
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        view.show()
        view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(self.deck))
        self.focus(view)
        first = QApplication.focusWidget()
        self.assertIn(first, view._all_tiles)
        self.press(Qt.Key.Key_Return)
        self.assertIs(view._selected_tile, first)
        second = next(tile for tile in view._all_tiles
                      if tile.pair_id == first.pair_id and tile.is_term != first.is_term)
        for _ in view._all_tiles:
            if QApplication.focusWidget() is second:
                break
            self.press(Qt.Key.Key_Right)
        self.assertIs(QApplication.focusWidget(), second)
        self.press(Qt.Key.Key_Return)
        QTest.qWait(450)
        self.assertTrue(first.is_matched)
        self.assertTrue(second.is_matched)
        self.assertIn(QApplication.focusWidget(), view._keyboard.available_buttons())

    def test_keyboard_help_changes_with_question_state_and_language(self):
        self.card()
        view = self.view('writing')
        self.focus(view)
        for lang, check, listen in (('tr', 'kontrol', 'dinle'), ('en', 'check', 'listen'),
                                    ('de', 'prüfen', 'anhören'), ('es', 'comprobar', 'escuchar')):
            view.update_language(lang)
            self.assertIn(check, view.lbl_help.text())
            self.assertIn(listen, view.lbl_help.text())
            self.assertIn('Ctrl+H', view.btn_hint.text())
        view.input_spelling.setText(view._expected)
        self.press(Qt.Key.Key_Return)
        self.assertIn('Continúa', view.lbl_help.text())
        self.finish_feedback(view)
        self.assertIsNone(view.current_card)
        self.assertIn('nueva sesión', view.lbl_help.text())
