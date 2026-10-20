"""Publication regressions for sentences on arbitrary, manually added cards."""
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from duocards import db, sentence_memory as memory


REAL_REQUEST_EXAMPLES = memory.request_examples


class GeneralSentencePipelineTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.path = self.directory + '/cards.db'
        self.stack.enter_context(patch.object(db, 'DB_DIR', self.directory))
        self.stack.enter_context(patch.object(db, 'DB_PATH', self.path))
        # Tests opt into the real worker individually; setup cannot use the network.
        self.stack.enter_context(patch.object(
            memory, 'request_examples', side_effect=lambda card, force=False: memory.ensure_examples(card)))
        self.stack.enter_context(patch.object(
            memory.urllib.request, 'urlopen', side_effect=AssertionError('Unexpected real network request')))
        self.addCleanup(self.wait_for_workers)
        db.init_db()
        self.deck = db.add_deck('Manual cards')

    def wait_for_workers(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with memory._guard:
                pending = [key for key in memory._pending if key[0] == self.path]
            if not pending:
                return
            time.sleep(.01)
        self.fail('Sentence worker did not finish before database cleanup')

    def card(self, term='bioluminescence', lang='en', sentence='', translation='', target='tr'):
        ident = db.add_card(self.deck, term, 'meaning', example_sentence=sentence,
                            example_translation=translation, source_lang=lang, target_lang=target)
        return db.get_card(ident)

    def corpus(self, term='bioluminescence', lang='en'):
        sentences = (
            [f'The researchers observed {term} near sample {i} during their evening fieldwork.' for i in range(10)]
            if lang == 'en' else
            [f'Das Bild Nummer {i} weckt mein {term} und erinnert mich an die letzte Reise.' for i in range(10)])
        return [dict(text=text, translations={'tr': f'Örnek cümlenin çevirisi {i}.',
                                             'de': f'Übersetzung des Beispiels {i}.'},
                     kind='example', source='tatoeba',
                     url=f'https://tatoeba.org/en/sentences/show/{i + 1}',
                     author='sample-author', license='CC BY 2.0 FR')
                for i, text in enumerate(sentences)]

    def seed(self, card, rows):
        with db.get_connection() as connection:
            memory._store(connection, memory.card_language(card), card['term'], rows)

    def test_arbitrary_manual_card_save_fetches_and_persists_sentence_in_its_language(self):
        for term, lang in (('bioluminescence', 'en'), ('Fernweh', 'de')):
            with self.subTest(lang=lang):
                self.assertEqual(memory.offline_examples(term, lang), [])
                self.assertEqual(memory._local_index().get((lang, memory.word_key(term)), []), [])
                rows = self.corpus(term, lang)
                with patch.object(memory, 'fetch_corpus', return_value=rows) as fetch, patch.object(
                        memory, 'request_examples', side_effect=REAL_REQUEST_EXAMPLES):
                    card = self.card(term, lang)
                    self.wait_for_workers()
                fetch.assert_called_once_with(term, lang, 'tr')
                saved = db.get_card(card['id'])
                self.assertEqual(saved['example_sentence'], rows[0]['text'])
                self.assertEqual(saved['example_translation'], rows[0]['translations']['tr'])
                self.assertEqual(memory.fetch_status(card), 'ready')
                persisted = memory.read_examples(saved)
                self.assertEqual(len(persisted), 10)
                self.assertTrue(all(row['source'] == 'tatoeba' for row in persisted))

    def test_ten_generated_rows_do_not_prevent_real_sentence_lookup(self):
        card = self.card('quasar')
        generated = [dict(text=f'This quasar is in generated example {i}.', translations={},
                          kind='example', source='offline_example') for i in range(10)]
        self.seed(card, generated)
        corpus = self.corpus('quasar')
        with patch.object(memory, 'fetch_corpus', return_value=corpus) as fetch:
            REAL_REQUEST_EXAMPLES(card)
            self.wait_for_workers()
        fetch.assert_called_once_with('quasar', 'en', 'tr')
        self.assertEqual(db.get_card(card['id'])['example_sentence'], corpus[0]['text'])
        self.assertTrue(all(row['source'] == 'tatoeba' for row in memory.read_examples(card)))

    def test_cached_corpus_populates_new_card_without_starting_another_fetch(self):
        card = dict(term='bioluminescence', source_lang='en')
        corpus = self.corpus()
        self.seed(card, corpus)
        with patch.object(memory, 'fetch_corpus') as fetch, patch.object(
                memory, 'request_examples', side_effect=REAL_REQUEST_EXAMPLES):
            saved = self.card(target='de')
            self.wait_for_workers()
        fetch.assert_not_called()
        self.assertEqual(saved['example_sentence'], corpus[0]['text'])
        self.assertEqual(saved['example_translation'], corpus[0]['translations']['de'])
        self.assertEqual(len(memory.read_examples(saved)), 10)

    def test_same_term_in_another_language_does_not_reuse_cached_sentences(self):
        corpus_en = self.corpus('Fernweh', 'en')
        self.seed(dict(term='Fernweh', source_lang='en'), corpus_en)
        corpus_de = self.corpus('Fernweh', 'de')
        with patch.object(memory, 'fetch_corpus', return_value=corpus_de) as fetch, patch.object(
                memory, 'request_examples', side_effect=REAL_REQUEST_EXAMPLES):
            card = self.card('Fernweh', 'de')
            self.wait_for_workers()
        fetch.assert_called_once_with('Fernweh', 'de', 'tr')
        self.assertEqual(db.get_card(card['id'])['example_sentence'], corpus_de[0]['text'])
        self.assertEqual(memory.read_examples(dict(term='Fernweh', source_lang='en'))[0]['text'],
                         corpus_en[0]['text'])

    def test_completion_updates_matching_cards_with_each_cards_translation_language(self):
        first = self.card()
        second = self.card(lang='İngilizce', target='de')
        corpus = self.corpus()
        with patch.object(memory, 'fetch_corpus', return_value=corpus):
            REAL_REQUEST_EXAMPLES(first)
            self.wait_for_workers()
        for card, target in ((first, 'tr'), (second, 'de')):
            with self.subTest(target=target):
                saved = db.get_card(card['id'])
                self.assertEqual(saved['example_sentence'], corpus[0]['text'])
                self.assertEqual(saved['example_translation'], corpus[0]['translations'][target])

    def test_manual_example_is_never_overwritten_by_background_lookup(self):
        sentence = 'I photographed bioluminescence on the beach during our late evening walk.'
        translation = 'Sahilde biyolüminesansın fotoğrafını çektim.'
        card = self.card(sentence=sentence, translation=translation)
        with patch.object(memory, 'fetch_corpus', return_value=self.corpus()):
            REAL_REQUEST_EXAMPLES(card, force=True)
            self.wait_for_workers()
        saved = db.get_card(card['id'])
        self.assertEqual(saved['example_sentence'], sentence)
        self.assertEqual(saved['example_translation'], translation)

    def test_delayed_job_does_not_overwrite_new_manual_sentence_or_changed_identity(self):
        for change in ('manual_sentence', 'term', 'source_lang'):
            with self.subTest(change=change):
                card = self.card()
                entered = threading.Event()
                release = threading.Event()
                corpus = self.corpus()

                def fetch(*args):
                    entered.set()
                    if not release.wait(3):
                        raise TimeoutError('Test did not release sentence fetch')
                    return corpus

                with patch.object(memory, 'fetch_corpus', side_effect=fetch):
                    REAL_REQUEST_EXAMPLES(card, force=True)
                    try:
                        self.assertTrue(entered.wait(2), 'Background fetch did not start')
                        with db.get_connection() as connection:
                            if change == 'manual_sentence':
                                connection.execute(
                                    'UPDATE cards SET example_sentence=?,example_translation=? WHERE id=?',
                                    ('The diver filmed bioluminescence while swimming near the reef after sunset.', 'Dalgıç biyolüminesansı filme aldı.', card['id']))
                            elif change == 'term':
                                connection.execute('UPDATE cards SET term=? WHERE id=?', ('photosynthesis', card['id']))
                            else:
                                connection.execute('UPDATE cards SET source_lang=? WHERE id=?', ('de', card['id']))
                    finally:
                        release.set()
                        self.wait_for_workers()
                saved = db.get_card(card['id'])
                if change == 'manual_sentence':
                    self.assertEqual(saved['example_sentence'], 'The diver filmed bioluminescence while swimming near the reef after sunset.')
                    self.assertEqual(saved['example_translation'], 'Dalgıç biyolüminesansı filme aldı.')
                else:
                    self.assertEqual(saved['example_sentence'], '')
                    self.assertEqual(saved['example_translation'], '')
                # Separate each edit scenario from the successful previous cache.
                with db.get_connection() as connection:
                    connection.execute('DELETE FROM sentence_memory')
                    connection.execute('DELETE FROM sentence_fetches')

    def test_network_failure_does_not_promote_generated_text_to_card_example(self):
        card = self.card('quasar')
        generated = [dict(text=f'This quasar is in generated example {i}.', translations={},
                          kind='example', source='offline_example') for i in range(10)]
        self.seed(card, generated)
        with patch.object(memory, 'fetch_corpus', side_effect=TimeoutError('service timeout')) as fetch:
            REAL_REQUEST_EXAMPLES(card)
            self.wait_for_workers()
        fetch.assert_called_once()
        self.assertEqual(memory.fetch_status(card), 'offline')
        self.assertEqual(memory.fetch_error(card), 'timeout')
        self.assertEqual(db.get_card(card['id'])['example_sentence'], '')
        self.assertEqual(memory.read_examples(card), [])

    def test_forced_search_keeps_better_cached_context_when_new_results_are_short(self):
        card=self.card()
        corpus=self.corpus()
        self.seed(card,corpus)
        short=[dict(text=f'Bioluminescence {i}.',kind='example',source='tatoeba',translations={}) for i in range(10)]
        with patch.object(memory,'fetch_corpus',return_value=short):
            REAL_REQUEST_EXAMPLES(card,force=True)
            self.wait_for_workers()
        self.assertEqual({r['text'] for r in memory.read_examples(card)}, {r['text'] for r in corpus})

    def test_repeated_searches_for_same_word_share_one_worker(self):
        card=self.card()
        entered=threading.Event()
        release=threading.Event()
        def fetch(*args):
            entered.set()
            if not release.wait(3):
                raise TimeoutError('Test did not release sentence fetch')
            return self.corpus()
        with patch.object(memory,'fetch_corpus',side_effect=fetch) as provider:
            REAL_REQUEST_EXAMPLES(card,force=True)
            try:
                self.assertTrue(entered.wait(2))
                for _ in range(3):
                    REAL_REQUEST_EXAMPLES(card,force=True)
                self.assertEqual(memory.fetch_status(card),'loading')
                provider.assert_called_once()
            finally:
                release.set()
                self.wait_for_workers()
        self.assertEqual(memory.fetch_status(card),'ready')


if __name__ == '__main__':
    unittest.main()
