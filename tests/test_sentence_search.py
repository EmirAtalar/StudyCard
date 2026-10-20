"""Online search quality, sparse results and Qt source-display regressions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import sqlite3
import tempfile
import unittest
import urllib.error
from contextlib import ExitStack
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from duocards import db, sentence_memory as memory
from duocards.settings import settings
from duocards.widgets.sentence_memory_view import SentenceMemoryView


def example(text, source='tatoeba', translation='', url=''):
    return dict(text=text, kind='example', source=source,
                translations={'tr': translation} if translation else {},
                url=url, author='writer', license='CC BY 2.0 FR')


def sentence(ident, text):
    return dict(id=ident, text=text, lang='eng', translations=[])


class SentenceSearchTests(unittest.TestCase):
    def test_context_and_translation_outrank_short_first_results(self):
        short=[example(f'Opportunity {i}.') for i in range(20)]
        context=[example(f'The opportunity to study abroad helped student {i} become more independent.',
                         translation=f'Çeviri {i}.') for i in range(12)]
        selected=memory._select_online_examples(short+context, 'opportunity', 'en')
        self.assertEqual(len(selected), 10)
        self.assertTrue(all(row in context for row in selected))

    def test_varied_contexts_precede_repeated_wording(self):
        repeated=[example(f'We discussed this opportunity with colleague number {i} during the meeting.')
                  for i in range(20)]
        varied=[example('Studying abroad gave her an opportunity to experience another culture.'),
                example('When the opportunity arose, he finally opened his own bakery.')]
        selected=memory._select_online_examples(repeated+varied, 'opportunity', 'en')
        self.assertTrue(all(row in selected[:3] for row in varied))

    def test_sparse_corpus_rejects_trivial_sentences_without_inventing_more(self):
        rows=[example('An apple.'), example('Eat an apple!')]
        selected=memory._select_online_examples(rows, 'apple', 'en')
        self.assertEqual(selected,[])

    def test_duplicates_merge_translations_and_filter_wrong_words(self):
        rows=[example('She ate an apple after she finished her homework at school.', translation='Bir elma yedi.'),
              dict(example('She ate an apple after she finished her homework at school!'), translations={'de': 'Sie aß einen Apfel.'}),
              example('She ate pineapple.'), {'text': None}, {'text': 'apple', 'translations': []}]
        selected=memory._select_online_examples(rows, 'apple', 'en')
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['translations'], {'tr': 'Bir elma yedi.', 'de': 'Sie aß einen Apfel.'})

    def test_api_gathers_candidates_beyond_first_ten(self):
        items=[sentence(i+1, f'The apple in basket number {i} was picked from our garden.') for i in range(50)]
        with patch.object(memory, '_load_json', return_value={'data': items}) as load:
            rows=memory._fetch_tatoeba('apple', 'en')
        self.assertEqual(len(rows), 50)
        load.assert_called_once()
        query=parse_qs(urlparse(load.call_args.args[0]).query)
        self.assertEqual(query['word_count'], ['8-35'])
        self.assertNotIn('trans:lang', query)  # Missing translations cannot hide matches.

    def test_length_is_relaxed_when_context_query_is_empty(self):
        payload={'data': [sentence(1, 'I eat an apple every morning before I go to work.')]}
        with patch.object(memory, '_load_json', side_effect=[{'data': []}, payload, payload]) as load:
            rows=memory._fetch_tatoeba('apple', 'en')
        self.assertEqual([row['text'] for row in rows], ['I eat an apple every morning before I go to work.'])
        queries=[parse_qs(urlparse(call.args[0]).query) for call in load.call_args_list]
        self.assertIn('word_count', queries[0])
        self.assertNotIn('word_count', queries[1])
        self.assertEqual(queries[-1]['q'], ['apple'])

    def test_http_400_uses_simple_query_and_retains_quality_filters(self):
        error=urllib.error.HTTPError('https://api.tatoeba.org', 400, 'Bad query', {}, None)
        with patch.object(memory, '_load_json', side_effect=[error, {'data': [sentence(1, 'This is important because it helps us prepare for the examination.')]}]) as load:
            rows=memory._fetch_tatoeba('İmportant', 'en')
        self.assertEqual(len(rows), 1)
        query=parse_qs(urlparse(load.call_args.args[0]).query)
        self.assertEqual(query['q'], ['important'])
        self.assertEqual(query['is_unapproved'], ['no'])
        self.assertEqual(query['lang'], ['eng'])

    def test_pagination_can_add_richer_results_after_ten_matches(self):
        first=[sentence(i+1, f'I have an apple number {i}.') for i in range(10)]
        richer='The apple tree in our garden produces enough fruit for everyone.'
        next_url='https://api.tatoeba.org/v1/sentences?after=next'
        with patch.object(memory, '_load_json', side_effect=[{'data': first, 'paging': {'next': next_url}},
                                                            {'data': [sentence(11, richer)]}]) as load:
            rows=memory._fetch_tatoeba('apple', 'en')
        self.assertEqual(load.call_count, 2)
        self.assertEqual(memory._select_online_examples(rows, 'apple', 'en')[0]['text'], richer)

    def test_pagination_error_preserves_results_already_received(self):
        payload={'data': [sentence(1, 'An apple grows on this tree in the garden behind our house.')],
                 'paging': {'next': 'https://api.tatoeba.org/v1/sentences?after=next'}}
        with patch.object(memory, '_load_json', side_effect=[payload, TimeoutError()]):
            rows=memory._fetch_tatoeba('apple', 'en')
        self.assertEqual(len(rows), 1)

    def test_pagination_never_follows_another_host(self):
        items=[sentence(i+1, f'This apple in box number {i} came from our garden.') for i in range(10)]
        with patch.object(memory, '_load_json', return_value={'data': items, 'paging': {'next': 'https://other.example/v1/sentences'}}) as load:
            self.assertEqual(len(memory._fetch_tatoeba('apple', 'en')), 10)
        load.assert_called_once()

    def test_empty_paginated_search_reserves_requests_for_relaxed_queries(self):
        calls=[]
        def response(url):
            calls.append(url)
            return {'data': [], 'paging': {'next': 'https://api.tatoeba.org/v1/sentences?after='+str(len(calls))}}
        with patch.object(memory,'_load_json',side_effect=response):
            self.assertEqual(memory._fetch_tatoeba('apple','en'),[])
        self.assertEqual(len(calls),4)
        self.assertEqual(parse_qs(urlparse(calls[-1]).query)['q'],['apple'])

    def test_dictionary_context_can_replace_ten_trivial_corpus_matches(self):
        short=[example(f'Opportunity {i}.') for i in range(10)]
        context=example('She took the opportunity to ask the director about future projects.', 'dictionary')
        with patch.object(memory, '_fetch_tatoeba', return_value=short), \
                patch.object(memory, '_fetch_dictionary', return_value=[context]), \
                patch.object(memory, '_fetch_wikipedia', return_value=[]), \
                patch.object(memory, '_fetch_legacy', return_value=[]):
            rows=memory.fetch_corpus('opportunity', 'en')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['text'], context['text'])

    def test_malformed_tatoeba_entries_do_not_discard_valid_entries(self):
        items=[{'id': 1, 'text': 12, 'lang': 'eng'}, {'text': 'An apple.'},
               sentence(2, 'I ate an apple while waiting for the train at the station.'), dict(sentence(3, 'Another apple.'), is_unapproved=True)]
        self.assertEqual(len(memory._tatoeba_rows(items, 'apple', 'en', 'tr')), 1)

    def test_wikipedia_request_obeys_extract_api_limits_and_keeps_complete_sentences(self):
        def response(url):
            query=parse_qs(urlparse(url).query)
            # TextExtracts supports at most 1200 characters and requires
            # exintro for multiple article extracts in one request.
            self.assertLessEqual(int(query['exchars'][0]),1200)
            self.assertEqual(query['exintro'],['1'])
            return {'query': {'pages': [{'pageid': 1,'title': 'Apple',
                'fullurl': 'https://en.wikipedia.org/wiki/Apple',
                'extract': 'An apple is the fruit of a tree. It contains fiber.\nThe apple tree grows in many parts of the world. This apple'}]}}
        with patch.object(memory,'_load_json',side_effect=response):
            rows=memory._fetch_wikipedia('apple','en')
        self.assertEqual(len(rows),2)
        self.assertTrue(all(row['source']=='wikipedia' and row['text'].endswith('.') for row in rows))
        self.assertTrue(all(row['url']=='https://en.wikipedia.org/wiki/Apple' for row in rows))

    def test_typographic_apostrophes_match_without_matching_other_words(self):
        self.assertTrue(memory.term_pattern("you're welcome").search('You’re welcome to join us for dinner.'))
        self.assertTrue(memory.term_pattern('well-known').search('She is a well‑known author.'))
        self.assertFalse(memory.term_pattern('apple').search('I like pineapple.'))


class SentenceSourceViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        stack=ExitStack()
        self.addCleanup(stack.close)
        directory=stack.enter_context(tempfile.TemporaryDirectory())
        stack.enter_context(patch.object(db, 'DB_DIR', directory))
        stack.enter_context(patch.object(db, 'DB_PATH', directory+'/cards.db'))
        stack.enter_context(patch.object(memory, 'request_examples', side_effect=lambda card, force=False: memory.ensure_examples(card)))
        stack.enter_context(patch('duocards.widgets.sentence_memory_view.request_examples', side_effect=lambda card, force=False: memory.ensure_examples(card)))
        old=settings.get_all()
        self.addCleanup(setattr, settings, '_settings', old)
        settings._settings.update(ui_language='tr')
        db.init_db()
        deck=db.add_deck('Source display')
        self.card=db.get_card(db.add_card(deck, 'quasar', 'kuasar', source_lang='en'))

    def save(self, source='wikipedia', url='https://en.wikipedia.org/wiki/Quasar'):
        row=example('The quasar emits light from the center of the distant galaxy.', source, url=url)
        with db.get_connection() as conn:
            memory._store(conn, 'en', 'quasar', [row])

    def view(self):
        view=SentenceMemoryView()
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        view.current_card=self.card
        view._poll()
        return view

    def test_saved_wikipedia_results_render_in_every_ui_language(self):
        self.save()
        view=self.view()
        for lang in ('tr', 'en', 'de', 'es'):
            view.update_language(lang)
            self.assertEqual(view.table.item(0, 2).text(), 'Wikipedia')
            self.assertIn('/wiki/Quasar', view.table.item(0, 2).toolTip())

    def test_unknown_sources_render_without_crashing(self):
        self.save('New sentence corpus')
        self.assertEqual(self.view().table.item(0, 2).text(), 'New sentence corpus')

    def test_source_changes_redraw_unchanged_sentence_text(self):
        self.save('tatoeba', 'https://tatoeba.org/en/sentences/show/1')
        view=self.view()
        self.save()
        view._poll()
        self.assertEqual(view.table.item(0, 2).text(), 'Wikipedia')
        self.assertIn('/wiki/Quasar', view.table.item(0, 2).toolTip())

    def test_busy_database_during_poll_keeps_rows_and_recovers(self):
        self.save()
        view=self.view()
        with patch('duocards.widgets.sentence_memory_view.read_examples', side_effect=sqlite3.OperationalError('database is locked')):
            view._poll()
        self.assertEqual(view.table.rowCount(), 1)
        self.assertEqual(view.lbl_status.text(), view.msg('storage'))
        view._poll()
        self.assertNotEqual(view.lbl_status.text(), view.msg('storage'))

    def test_search_button_handles_database_error_in_qt_callback(self):
        view=self.view()
        with patch('duocards.widgets.sentence_memory_view.request_examples', side_effect=sqlite3.OperationalError('database is locked')):
            with self.assertLogs('duocards.widgets.sentence_memory_view', level='ERROR'):
                QTest.mouseClick(view.btn_fetch, Qt.MouseButton.LeftButton)
        self.assertEqual(view.lbl_status.text(), view.msg('storage'))
        self.assertTrue(view.btn_fetch.isEnabled())


if __name__ == '__main__':
    unittest.main()
