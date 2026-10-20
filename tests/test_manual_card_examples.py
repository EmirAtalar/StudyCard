"""Manual entry searches arbitrary words and never attaches stale example results."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from contextlib import ExitStack
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel

from duocards import db, sentence_memory
from duocards.audio import audio_player
from duocards.languages import get_language_name
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.translator import TranslationWorker
from duocards.widgets.add_card_view import AddCardView, DuplicateCardDialog, EXAMPLE_TEXT


class ManualCardExamplesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        before = settings.get_all()
        self.addCleanup(setattr, settings, "_settings", before)
        settings._settings.update(ui_language="tr", last_source_lang="en", last_target_lang="tr")
        self.stack.enter_context(patch.object(settings, "save"))
        self.stack.enter_context(patch.object(sfx, "_play_file"))
        self.speech = self.stack.enter_context(patch.object(audio_player, "play_pronunciation"))
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(db, "DB_DIR", directory))
        self.stack.enter_context(patch.object(db, "DB_PATH", directory + "/cards.db"))
        db.init_db()
        self.deck = db.add_deck("Manual examples")
        self.rows, self.statuses, self.errors = {}, {}, {}
        self.request = self.stack.enter_context(patch.object(sentence_memory, "request_examples", side_effect=self.queue))
        self.stack.enter_context(patch.object(sentence_memory, "read_examples", side_effect=lambda card: self.rows.get(self.key(card), [])))
        self.stack.enter_context(patch.object(sentence_memory, "fetch_status", side_effect=lambda card: self.statuses.get(self.key(card), "local")))
        self.stack.enter_context(patch.object(sentence_memory, "fetch_error", side_effect=lambda card: self.errors.get(self.key(card), "")))
        self.view = AddCardView()
        self.addCleanup(self.view.deleteLater)
        self.addCleanup(self.view.close)
        self.view.refresh_decks()
        self.view.cmb_deck.setCurrentIndex(self.view.cmb_deck.findData(self.deck))
        self.view._example_debounce.setInterval(30)
        self.view.show()

    @staticmethod
    def key(card):
        return (card["term"], sentence_memory.card_language(card))

    def queue(self, card, force=False):
        self.statuses[self.key(card)] = "loading"
        return self.rows.get(self.key(card), [])

    @staticmethod
    def example(text, translation="", source="tatoeba", kind="example"):
        return dict(text=text, translations={"tr": translation}, source=source, kind=kind,
                    url="https://tatoeba.org/en/sentences/show/1", author="writer", license="CC BY 2.0 FR")

    def word(self, term):
        self.view.input_term.setText(term)
        self.view._request_examples()

    def test_new_word_is_searched_automatically_after_typing_without_audio(self):
        self.view._example_debounce.setInterval(1000)
        self.view.input_term.setText("mellif")
        QTest.qWait(10)
        self.view.input_term.setText("mellifluous")
        self.assertFalse(self.request.called)
        QTest.qWait(1100)
        self.request.assert_called_once_with(dict(term="mellifluous", source_lang="en", target_lang="tr"), force=False)
        self.assertIn("aranıyor", self.view.lbl_examples_status.text())
        self.assertFalse(self.view.btn_retry_examples.isEnabled())
        self.speech.assert_not_called()

    def test_preview_excludes_templates_and_requires_the_current_word(self):
        self.word("mellifluous")
        genuine = "Her mellifluous voice filled the room as she read the poem aloud."
        self.rows[("mellifluous", "en")] = [
            self.example("I learned mellifluous today.", source="practice", kind="practice"),
            self.example("This mellifluous is generated.", source="offline_example"),
            self.example("An unrelated example."),
            self.example(genuine, "Tatlı sesi odayı doldurdu."),
        ]
        self.statuses[("mellifluous", "en")] = "partial"
        self.view._refresh_examples()
        self.assertEqual(self.view.lbl_example_sentence.text(), genuine)
        self.assertEqual(self.view.lbl_example_translation.text(), "Tatlı sesi odayı doldurdu.")
        self.assertEqual(len(self.view._example_rows), 1)
        self.assertIn("writer", self.view.lbl_example_source.text())

    def test_typing_and_language_changes_never_show_a_previous_response(self):
        self.word("mellifluous")
        self.rows[("mellifluous", "en")] = [self.example("Her mellifluous voice filled the room as she read the poem aloud.")]
        self.view.input_term.setText("silencio")
        self.view._refresh_examples()
        self.assertEqual(self.view.lbl_example_sentence.text(), "")
        self.view.cmb_source_lang.setCurrentText(get_language_name("es", "tr"))
        self.view._request_examples()
        self.rows[("silencio", "es")] = [self.example("El silencio llenó la sala después de que todos terminaron de hablar.", "Sessizlik odayı doldurdu.")]
        self.statuses[("silencio", "es")] = "ready"
        self.view._refresh_examples()
        self.assertEqual(self.view.lbl_example_sentence.text(), "El silencio llenó la sala después de que todos terminaron de hablar.")
        self.view.cmb_source_lang.setCurrentText(get_language_name("it", "tr"))
        self.view._refresh_examples()
        self.assertEqual(self.view.lbl_example_sentence.text(), "")
        self.view._request_examples()
        self.assertEqual(self.request.call_args.args[0]["source_lang"], "it")

    def test_target_change_clears_previous_translation_and_fetches_new_target(self):
        self.word("silence")
        self.rows[("silence", "en")] = [self.example("The silence was comforting after a long and noisy day at work.", "Sessizlik rahatlatıcıydı.")]
        self.view._refresh_examples()
        self.view.cmb_target_lang.setCurrentText(get_language_name("de", "tr"))
        self.assertEqual(self.view.lbl_example_translation.text(), "")
        self.view._request_examples()
        self.assertEqual(self.request.call_args.args[0]["target_lang"], "de")
        self.assertEqual(self.view.lbl_example_translation.text(), "")

    def test_saving_preserves_the_selected_real_example_and_translation(self):
        self.word("silence")
        self.view.input_definition.setText("sessizlik")
        self.rows[("silence", "en")] = [self.example("The silence was comforting after a long and noisy day at work."),
                                          self.example("We sat in silence while watching the sun set over the lake.", "Sessizce oturduk.")]
        self.statuses[("silence", "en")] = "ready"
        self.view._refresh_examples()
        self.view.cmb_example.setCurrentIndex(1)
        self.assertEqual(self.view.input_example_sentence.text(), 'We sat in silence while watching the sun set over the lake.')
        self.assertEqual(self.view.input_example_translation.text(), 'Sessizce oturduk.')
        self.assertTrue(self.view._validate_and_save())
        card = db.get_all_cards(self.deck)[0]
        self.assertEqual(card["example_sentence"], "We sat in silence while watching the sun set over the lake.")
        self.assertEqual(card["example_translation"], "Sessizce oturduk.")
        self.assertEqual(self.view._saved_example_state, "ready")

    def test_save_while_fetching_keeps_card_and_reports_background_work(self):
        self.word("mellifluous")
        self.view.input_definition.setText("kulağa hoş gelen")
        self.view._save_and_new()
        card = db.get_all_cards(self.deck)[0]
        self.assertEqual(card["term"], "mellifluous")
        self.assertEqual(card["example_sentence"], "")
        self.assertEqual(self.view._saved_example_state, "pending")
        self.assertIn("arka planda", self.view.lbl_feedback.text())
        self.assertEqual(self.view.input_term.text(), "")

    def test_empty_result_and_network_error_are_distinct_and_retry_forces_search(self):
        self.word("mellifluous")
        key = ("mellifluous", "en")
        self.statuses[key] = "partial"
        self.view._refresh_examples()
        empty = self.view.lbl_examples_status.text()
        self.assertIn("bulunamadı", empty)
        self.statuses[key], self.errors[key] = "offline", "connection"
        self.view._refresh_examples()
        self.assertNotEqual(empty, self.view.lbl_examples_status.text())
        self.view.btn_retry_examples.click()
        self.assertTrue(self.request.call_args.kwargs["force"])

    def test_ui_language_switch_preserves_source_and_localizes_example_messages(self):
        self.word("mellifluous")
        for lang in ("en", "de", "es", "tr"):
            with self.subTest(lang=lang):
                self.view.update_language(lang)
                self.assertEqual(self.view.lbl_examples_title.text(), EXAMPLE_TEXT[lang]["title"])
                self.assertEqual(self.view.lbl_examples_status.text(), EXAMPLE_TEXT[lang]["loading"])
                self.assertEqual(self.view._example_card()["source_lang"], "en")

    def test_partial_language_name_does_not_silently_search_english(self):
        self.view.input_term.setText("silencio")
        self.view.cmb_source_lang.setEditText("Ge")
        self.view._request_examples()
        self.request.assert_not_called()
        self.assertIn("listeden", self.view.lbl_examples_status.text())

    def click_category(self, key):
        next(button for button in self.view.pos_group.buttons()
             if button.property("category_key") == key).click()

    def suggestion(self):
        self.view._fetch_translation_suggestion()
        return self.view._trans_worker

    def test_manual_type_is_passed_to_translation_and_saved_without_auto_override(self):
        with patch.object(TranslationWorker, "start"):
            for category, meaning in (("noun", "iş"), ("verb", "çalışmak")):
                with self.subTest(category=category):
                    self.view.input_term.clear()
                    self.click_category(category)
                    self.view.input_term.setText("work")
                    worker = self.suggestion()
                    self.assertEqual(worker.part_of_speech, category)
                    worker.result_ready.emit(dict(translation=meaning, pos="adjective", source="Dictionary"))
                    self.assertEqual(self.view._selected_pos_key, category)
                    self.assertEqual(self.view.input_definition.text(), meaning)
        self.assertTrue(self.view._validate_and_save())
        card = db.get_all_cards(self.deck)[0]
        self.assertEqual((card["part_of_speech"], card["definition"]), ("Fiil", "çalışmak"))

    def test_changing_auto_detected_type_fetches_its_meaning_and_word_restores_auto(self):
        self.view.input_term.setText("work")
        with patch.object(TranslationWorker, "start"):
            worker = self.suggestion()
            self.assertEqual(worker.part_of_speech, "")
            worker.result_ready.emit(dict(translation="iş", pos="noun"))
            self.assertEqual(self.view._selected_pos_key, "noun")
            self.click_category("verb")
            self.assertEqual(self.view.input_definition.text(), "")
            worker = self.view._trans_worker
            self.assertEqual(worker.part_of_speech, "verb")
            worker.result_ready.emit(dict(translation="çalışmak", pos="verb"))
            self.assertEqual(self.view.input_definition.text(), "çalışmak")
            self.click_category("word")
            worker = self.view._trans_worker
            self.assertEqual(worker.part_of_speech, "")
            worker.result_ready.emit(dict(translation="iş", pos="noun"))
            self.assertEqual(self.view._selected_pos_key, "noun")
            self.assertIsNone(self.view._manual_pos_key)

    def test_old_type_result_cannot_replace_the_new_selection(self):
        self.view.input_term.setText("work")
        with patch.object(TranslationWorker, "start"):
            self.click_category("noun")
            noun_worker = self.suggestion()
            self.click_category("verb")
            verb_worker = self.view._trans_worker
            noun_worker.result_ready.emit(dict(translation="iş", pos="noun"))
            self.assertEqual(self.view.input_definition.text(), "")
            self.assertFalse(self.view.btn_suggest.isEnabled())
            verb_worker.result_ready.emit(dict(translation="çalışmak", pos="verb"))
            self.assertEqual(self.view.input_definition.text(), "çalışmak")
            self.assertEqual(self.view._selected_pos_key, "verb")
            self.assertTrue(self.view.btn_suggest.isEnabled())

    def test_translation_response_does_not_overwrite_a_new_word_language_or_manual_meaning(self):
        with patch.object(TranslationWorker, "start"):
            changes = (
                lambda: self.view.input_term.setText("book"),
                lambda: self.view.cmb_target_lang.setCurrentText(get_language_name("de", "tr")),
                lambda: self.view.cmb_source_lang.setCurrentText(get_language_name("de", "tr")),
                lambda: self.view.input_definition.setText("Kendi anlamım"),
            )
            for change in changes:
                with self.subTest(change=change):
                    self.view.input_term.setText("work")
                    self.view.input_definition.clear()
                    worker = self.suggestion()
                    change()
                    expected = self.view.input_definition.text()
                    worker.result_ready.emit(dict(translation="iş", pos="noun"))
                    self.assertEqual(self.view.input_definition.text(), expected)
                    self.assertTrue(self.view.btn_suggest.isEnabled())

    def test_missing_selected_sense_does_not_leave_the_old_generated_meaning(self):
        self.view.input_term.setText("work")
        with patch.object(TranslationWorker, "start"):
            self.suggestion().result_ready.emit(dict(translation="iş", pos="noun"))
            self.click_category("verb")
            self.view._trans_worker.result_ready.emit(dict(translation="", error="part_of_speech_not_found"))
        self.assertEqual(self.view.input_definition.text(), "")
        self.assertEqual(self.view._selected_pos_key, "verb")
        self.assertIn("Fiil türüne ait çeviri bulunamadı", self.view.lbl_feedback.text())

    def test_background_lookup_updates_the_form_and_releases_finished_workers(self):
        def lookup(text, target_lang, source_lang, category):
            return dict(translation={"noun": "iş", "verb": "çalışmak"}[category], pos=category)

        self.view.input_term.setText("work")
        with patch("duocards.translator.fetch_cambridge_translation_sync", side_effect=lookup) as fetch:
            for category, meaning in (("noun", "iş"), ("verb", "çalışmak")):
                self.click_category(category)
                if category == "noun":
                    self.suggestion()
                for _ in range(40):
                    if not self.view._translation_workers:
                        break
                    QTest.qWait(25)
                self.assertFalse(self.view._translation_workers)
                self.assertEqual(self.view.input_definition.text(), meaning)
                self.assertEqual(self.view._selected_pos_key, category)
        self.assertEqual(fetch.call_count, 2)

    def test_duplicate_warning_localizes_both_legacy_and_stable_saved_types(self):
        db.add_card(self.deck, "work", "çalışmak", part_of_speech="Fiil", source_lang="en", target_lang="tr")
        db.add_card(self.deck, "work", "iş", part_of_speech="noun", source_lang="en", target_lang="tr")
        self.view.input_term.setText("WORK")
        self.assertIn("fiil hali", self.view.lbl_duplicates.text())
        self.assertIn("isim hali", self.view.lbl_duplicates.text())
        self.assertIn("çalışmak", self.view.lbl_duplicates.text())
        for lang, noun, verb in (("en", "Noun", "Verb"), ("de", "Nomen", "Verb"), ("es", "Sustantivo", "Verbo")):
            self.view.update_language(lang)
            self.assertIn(noun, self.view.lbl_duplicates.text())
            self.assertIn(verb, self.view.lbl_duplicates.text())

    def test_duplicate_dialog_matches_preferences_and_cancel_or_accept_controls_saving(self):
        db.add_card(self.deck, "work", "çalışmak", part_of_speech="verb", source_lang="en", target_lang="tr")
        self.view.input_term.setText("work")
        self.view.input_definition.setText("iş")
        self.click_category("noun")
        settings._settings.update(theme="graphite", accent_color="#38bdf8")
        seen = []

        def choose(accept):
            dialog = QApplication.activeModalWidget()
            seen.append(dialog)
            self.assertIsInstance(dialog, DuplicateCardDialog)
            self.assertTrue(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
            self.assertIn("#202024", dialog.styleSheet())
            self.assertIn("#38bdf8", dialog.styleSheet())
            text = "\n".join(label.text() for label in dialog.findChildren(QLabel))
            self.assertIn("fiil hali", text)
            self.assertIn("İsim olarak yeni bir kart", text)
            self.assertTrue(dialog.cancel_button.isDefault())
            self.assertFalse(dialog.submit_button.isDefault())
            (dialog.submit_button if accept else dialog.cancel_button).click()

        QTimer.singleShot(0, lambda: choose(False))
        self.assertFalse(self.view._validate_and_save())
        self.assertEqual(len(db.get_all_cards(self.deck)), 1)
        QTimer.singleShot(0, lambda: choose(True))
        self.assertTrue(self.view._validate_and_save())
        self.assertEqual(len(db.get_all_cards(self.deck)), 2)
        self.assertEqual(len(seen), 2)


if __name__ == "__main__":
    unittest.main()
