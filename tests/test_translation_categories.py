"""Translation suggestions must belong to the requested dictionary entry."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import io
import unittest
from unittest.mock import patch

from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QApplication

from duocards import translator


DICTIONARY_HTML = """
<div class="entry-body">
  <div class="pr entry-body__el">
    <span class="pos dpos">noun</span>
    <div class="def-block"><span class="trans dtrans">iş</span></div>
    <div class="def-block"><span class="trans dtrans">eser</span></div>
  </div>
  <div class="pr entry-body__el">
    <span class="pos dpos">verb</span>
    <div class="def-block"><span class="trans dtrans">çalışmak</span></div>
    <div class="def-block"><span class="trans dtrans">işlemek</span></div>
    <div class="pr phrase-block">
      <div class="def-block"><span class="trans dtrans">iş başında</span></div>
    </div>
    <div class="pr phrasal-verb-block">
      <span class="pos dpos">phrasal verb</span>
      <div class="def-block"><span class="trans dtrans">çözmek</span></div>
    </div>
  </div>
  <div class="pr entry-body__el">
    <span class="pos dpos">adverb</span>
    <div class="def-block"><span class="trans dtrans">hızla</span></div>
  </div>
</div>
<span class="trans">Unrelated page content</span>
"""


class TranslationCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def fetch(self, category=""):
        with patch.object(translator.urllib.request, "urlopen", return_value=io.BytesIO(DICTIONARY_HTML.encode())):
            return translator.fetch_cambridge_translation("work", "tr", category)

    def test_dictionary_returns_only_the_requested_entry_including_nested_entries(self):
        for category, meanings, pos in (
            ("noun", ["iş", "eser"], "noun"),
            ("verb", ["çalışmak", "işlemek"], "verb"),
            ("phrasal_verb", ["çözmek"], "phrasal verb"),
            ("phrase", ["iş başında"], "phrase"),
            ("adverb", ["hızla"], "adverb"),
        ):
            with self.subTest(category=category):
                result = self.fetch(category)
                self.assertEqual(result["translation"], meanings[0])
                self.assertEqual(result["translations"], meanings)
                self.assertEqual(result["pos"], pos)

    def test_automatic_mode_keeps_the_first_dictionary_sense(self):
        for category in ("", "word"):
            result = self.fetch(category)
            self.assertEqual((result["translation"], result["pos"]), ("iş", "noun"))

    def test_missing_dictionary_type_never_returns_the_first_unrelated_sense(self):
        self.assertIsNone(self.fetch("adjective"))

    def test_selected_type_is_forwarded_to_cambridge(self):
        sense = dict(translation="çalışmak", pos="verb")
        with patch.object(translator, "fetch_cambridge_translation", return_value=sense) as fetch:
            with patch.object(translator, "fetch_mymemory_translation") as fallback:
                self.assertEqual(translator.fetch_translation_sync("work", "tr", "en", "verb"), sense)
        fetch.assert_called_once_with("work", "tr", "verb")
        fallback.assert_not_called()

    def test_turkish_fallback_selects_the_matching_noun_or_infinitive_alternative(self):
        for category, expected in (("noun", "iş"), ("verb", "çalışmak")):
            with self.subTest(category=category):
                result = dict(translation="iş / çalışmak", translations=["iş / çalışmak"], error=None)
                with patch.object(translator, "fetch_cambridge_translation", return_value=None):
                    with patch.object(translator, "fetch_mymemory_translation", return_value=result):
                        result = translator.fetch_translation_sync("work", "tr", "en", category)
                self.assertEqual(result["translation"], expected)
                self.assertEqual(result["pos"], category)

    def test_unavailable_type_reports_failure_instead_of_using_an_unverified_translation(self):
        result = dict(translation="iş", translations=["iş"], error=None)
        with patch.object(translator, "fetch_cambridge_translation", return_value=None):
            with patch.object(translator, "fetch_mymemory_translation", return_value=result):
                result = translator.fetch_translation_sync("work", "tr", "en", "verb")
        self.assertEqual(result["translation"], "")
        self.assertEqual(result["error"], "part_of_speech_not_found")

    def test_background_worker_emits_the_selected_sense_and_finishes_normally(self):
        result = dict(translation="çalışmak", pos="verb")
        with patch.object(translator, "fetch_cambridge_translation_sync", return_value=result) as fetch:
            worker = translator.TranslationWorker("work", "tr", "en", "verb")
            ready = QSignalSpy(worker.result_ready)
            stopped = QSignalSpy(worker.finished)
            worker.start()
            if not ready:
                self.assertTrue(ready.wait(2000))
            self.assertTrue(worker.wait(2000))
            self.app.processEvents()
        self.assertEqual(ready[0][0], result)
        self.assertEqual(len(stopped), 1)
        fetch.assert_called_once_with("work", "tr", "en", "verb")


if __name__ == "__main__":
    unittest.main()
