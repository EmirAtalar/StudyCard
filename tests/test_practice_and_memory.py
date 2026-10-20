"""AI kaldırma, kalıcı cümle hafızası ve kullanıcı kartlarıyla pratik regresyonları."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from duocards import db, sentence_memory as memory
from duocards.settings import settings, SettingsManager
from duocards.audio import audio_player, AudioPlayer
from duocards.sfx import sfx
from duocards.practice import make_cloze, normalize_answer, daily_results, mistake_ids, record_attempt
from duocards.widgets.practice_view import PracticeView
from duocards.widgets.sentence_memory_view import SentenceMemoryView
from duocards.main_window import MainWindow
REAL_REQUEST_EXAMPLES = memory.request_examples


class AppFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack=ExitStack()
        self.addCleanup(self.stack.close)
        before=settings.get_all()
        self.addCleanup(setattr,settings,'_settings',before)
        settings._settings.update(ui_language='tr',auto_pronounce=False)
        self.tmp=self.stack.enter_context(tempfile.TemporaryDirectory())
        for obj,key,value in ((db,'DB_DIR',self.tmp),(db,'DB_PATH',self.tmp+'/cards.db')):
            self.stack.enter_context(patch.object(obj,key,value))
        self.stack.enter_context(patch.object(settings,'save'))
        self.speech=self.stack.enter_context(patch.object(audio_player,'play_pronunciation'))
        self.stack.enter_context(patch.object(audio_player,'prefetch'))
        self.stack.enter_context(patch.object(audio_player,'stop'))
        self.stack.enter_context(patch.object(sfx,'_play_file'))
        # Kart ekleme aynı kalıcı motoru çalıştırır, test sırasında ağa çıkmaz.
        self.stack.enter_context(patch.object(memory,'request_examples',side_effect=lambda card,force=False:memory.ensure_examples(card)))
        self.stack.enter_context(patch('duocards.widgets.practice_view.request_examples',side_effect=lambda card,force=False:memory.ensure_examples(card)))
        db.init_db()
        self.deck=db.add_deck('Test Destesi')
        self.other=db.add_deck('Başka Deste')

    def card(self,term='apple',meaning='elma',sentence='I ate an apple after finishing my homework this afternoon.',lang='en',deck=None):
        ident=db.add_card(deck or self.deck,term,meaning,example_sentence=sentence,
                          source_lang=lang,target_lang='tr')
        return db.get_card(ident)

    def view(self,kind):
        view=PracticeView(kind)
        view.show()
        view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(self.deck))
        view.reload_cards(force=True)
        if kind == 'shadowing':
            for _ in range(100):
                QTest.qWait(10)
                if not view._pool_loading:
                    break
        self.addCleanup(view.close)
        self.addCleanup(view.deleteLater)
        return view


class SentenceMemoryTests(AppFixture):
    def test_add_card_immediately_saves_ten_examples_and_survives_reload(self):
        card=self.card()
        rows=memory.read_examples(card)
        self.assertEqual(len(rows),10)
        self.assertEqual(len({row['text'] for row in rows}),10)
        self.assertTrue(all(memory.term_pattern('apple').search(row['text']) for row in rows))
        self.assertTrue(any(row['text']==card['example_sentence'] and row['source']=='user' for row in rows))
        self.assertEqual(rows,memory.read_examples(db.get_card(card['id'])))

    def test_unknown_words_never_receive_placeholder_sentences(self):
        for lang in memory.TEMPLATES:
            with self.subTest(lang=lang):
                card=self.card('cacheword','anlam','',lang)
                self.assertEqual(memory.read_examples(card),[])

    def test_manual_examples_replace_exercises_without_duplicates(self):
        card=self.card()
        memory.add_example(card,'An apple is on the plate next to the homemade bread.','Tabakta bir elma var.')
        memory.add_example(card,'An apple is on the plate next to the homemade bread.','Tabakta bir elma var.')
        rows=memory.read_examples(card)
        self.assertEqual(len(rows),10)
        self.assertEqual(sum(row['text']=='An apple is on the plate next to the homemade bread.' for row in rows),1)
        self.assertEqual(rows[0]['translations']['tr'],'Tabakta bir elma var.')
        with self.assertRaises(ValueError):
            memory.add_example(card,'I ate a banana before leaving home for the morning meeting.')

    def test_editing_term_and_language_creates_correct_new_memory(self):
        card=self.card()
        db.update_card(card['id'],self.deck,'pomme','elma','İsim','Je mange une pomme pendant ma pause après le cours.','','','',source_lang='fr')
        updated=db.get_card(card['id'])
        rows=memory.read_examples(updated)
        self.assertEqual(len(rows),10)
        self.assertTrue(all(memory.term_pattern('pomme','fr').search(r['text']) for r in rows))
        self.assertFalse(any('I learned' in r['text'] for r in rows))

    def test_tatoeba_parser_checks_language_and_whole_words_and_keeps_sources(self):
        payload={'data':[
            dict(id=1,text='I eat an apple every morning before I go to work.',lang='eng',owner='author',license='CC BY 2.0 FR',
                 translations=[dict(lang='tur',text='Bir elma yiyorum.')]),
            dict(id=2,text='I like pineapple.',lang='eng',translations=[]),
            dict(id=3,text='apple is not French.',lang='fra',translations=[]),
        ]}
        response=MagicMock()
        response.read.return_value=json.dumps(payload).encode()
        with patch.object(memory.urllib.request,'urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value=response
            rows=memory.fetch_corpus('apple','en','tr')
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['translations']['tr'],'Bir elma yiyorum.')
            self.assertEqual(rows[0]['author'],'author')
            self.assertIn('/show/1',rows[0]['url'])
            self.assertIn('lang=eng',urlopen.call_args_list[0].args[0].full_url)
            self.assertIn('sort=relevance',urlopen.call_args_list[0].args[0].full_url)

    def test_background_fetch_replaces_exercises_and_offline_failure_keeps_memory(self):
        card=self.card('cacheword','anlam','')
        function=REAL_REQUEST_EXAMPLES
        corpus=[dict(text=f'We use cacheword in example number {i} while learning complete sentences.',translations={},kind='example',source='tatoeba',
                     url=f'https://tatoeba.org/en/sentences/show/{i}') for i in range(10)]
        with patch.object(memory,'fetch_corpus',return_value=corpus):
            function(card,force=True)
            self.wait_for_job(card)
        self.assertTrue(all(r['kind']=='example' for r in memory.read_examples(card)))
        with patch.object(memory,'fetch_corpus',side_effect=OSError('offline')):
            function(card,force=True)
            self.wait_for_job(card)
        self.assertEqual(memory.fetch_status(card),'offline')
        self.assertEqual(len(memory.read_examples(card)),10)

    def wait_for_job(self,card):
        deadline=time.monotonic()+2
        while memory.fetch_status(card)=='loading' and time.monotonic()<deadline:
            time.sleep(.01)
        self.assertNotEqual(memory.fetch_status(card),'loading')

    def test_interrupted_loading_request_can_restart_without_force(self):
        card=self.card('restartword','anlam','')
        with db.get_connection() as conn:
            conn.execute('INSERT OR REPLACE INTO sentence_fetches VALUES (?,?,?,?,?)',
                         ('en','restartword',time.time(),'loading',''))
        with patch.object(memory,'fetch_corpus',return_value=[] ) as fetch:
            REAL_REQUEST_EXAMPLES(card)
            self.wait_for_job(card)
            fetch.assert_called_once()
        self.assertEqual(memory.fetch_status(card),'partial')

    def test_http_failure_uses_alternate_tatoeba_endpoint(self):
        payload={'results':[dict(id=9,text='I eat an apple every morning before I go to work.',lang='eng',
                                user={'username':'writer'},
                                translations=[[dict(lang='tur',text='Bir elma yiyorum.')]])]}
        error=memory.urllib.error.HTTPError('https://api.tatoeba.org',503,'Unavailable',{},None)
        with patch.object(memory,'_fetch_tatoeba',side_effect=error), patch.object(memory,'_load_json',return_value=payload) as load, patch.object(memory,'_fetch_dictionary',return_value=[]):
            rows=memory.fetch_corpus('apple','en','tr')
        self.assertEqual(rows[0]['translations']['tr'],'Bir elma yiyorum.')
        self.assertIn('tatoeba.org/en/api_v0/search',load.call_args.args[0])
        error.close()

    def test_dictionary_is_used_when_tatoeba_has_no_examples(self):
        payload=[{'meanings':[{'definitions':[{'example':'I eat an apple every morning before I go to work.'},
                                              {'example':'I eat pineapple.'}]}],
                  'license':{'name':'CC BY-SA 3.0'}}]
        with patch.object(memory,'_fetch_tatoeba',return_value=[]), patch.object(memory,'_fetch_legacy',return_value=[]), patch.object(memory,'_load_json',return_value=payload):
            rows=memory.fetch_corpus('apple','en','tr')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['source'],'dictionary')
        self.assertEqual(rows[0]['translations'],{})

    def test_all_provider_errors_remain_errors_not_empty_results(self):
        error=memory.urllib.error.HTTPError('https://api.tatoeba.org',429,'Rate limited',{},None)
        with patch.object(memory,'_fetch_tatoeba',side_effect=error), patch.object(memory,'_fetch_legacy',side_effect=error), patch.object(memory,'_fetch_dictionary',side_effect=error):
            with self.assertRaises(memory.urllib.error.HTTPError):
                memory.fetch_corpus('apple','en','tr')
        self.assertEqual(memory._error_code(error),'http_429')
        error.close()

    def test_current_vocabulary_gets_ten_usage_sentences_without_network(self):
        for word in ('opportunity','explanation','readily','probably','store','back up','although','horizontal','function','equals','derivative','tangent line'):
            with self.subTest(word=word):
                card=self.card(word,'anlam','')
                rows=memory.ensure_examples(card)
                self.assertGreater(len(rows),0)
                self.assertLessEqual(len(rows),10)
                self.assertTrue(all(r['kind']=='example' for r in rows))
                self.assertEqual(len({r['text'] for r in rows}),len(rows))
                self.assertTrue(all(memory.term_pattern(word).search(r['text']) for r in rows))
                self.assertFalse(any('word “' in r['text'] for r in rows))

    def test_offline_upgrade_replaces_old_hidden_exercises(self):
        card=self.card('opportunity','anlam','')
        with db.get_connection() as conn:
            conn.execute('DELETE FROM sentence_memory WHERE term_key=?',('opportunity',))
            memory._store(conn,'en','opportunity',[
                dict(text=t.format(word='opportunity'),kind='practice',source='practice')
                for t in memory.TEMPLATES['en'].split('|')])
        rows=memory.ensure_examples(card)
        self.assertGreater(len(rows),0)
        self.assertTrue(all(r['kind']=='example' for r in rows))

    def test_english_dotted_i_and_phrase_placeholders_are_searchable(self):
        self.assertTrue(memory.term_pattern('İmportant','en').search('This is important because it helps us prepare for the examination.'))
        self.assertTrue(memory.term_pattern('It takes ... about','en').search('It takes us about ten minutes.'))
        card=self.card('İmportant','önemli','')
        self.assertTrue(all(r['kind']=='example' for r in memory.ensure_examples(card)))

    def test_http_400_retries_with_simple_api_query(self):
        error=memory.urllib.error.HTTPError('https://api.tatoeba.org',400,'Bad request',{},None)
        payload={'data':[dict(id=1,text='This is important because it helps us prepare for the examination.',lang='eng',translations=[])]}
        with patch.object(memory,'_load_json',side_effect=[error,payload]) as load:
            rows=memory._fetch_tatoeba('İmportant','en')
        self.assertEqual(len(rows),1)
        self.assertIn('q=important',load.call_args.args[0])
        self.assertIn('limit=50',load.call_args.args[0])

    def test_short_provider_results_are_combined_and_deduplicated(self):
        def row(i):
            return dict(text=f'I ate an apple at table {i} while waiting for the bus.',translations={},kind='example',source='tatoeba')
        with patch.object(memory,'_fetch_tatoeba',return_value=[row(i) for i in range(4)]),patch.object(memory,'_fetch_legacy',return_value=[row(i) for i in range(3,8)]),patch.object(memory,'_fetch_dictionary',return_value=[row(i) for i in range(7,12)]):
            rows=memory.fetch_corpus('apple','en')
        self.assertEqual(len(rows),10)
        self.assertEqual(len({r['text'] for r in rows}),10)

    def test_offline_examples_are_authored_and_contextual(self):
        from duocards.offline_examples import examples
        from duocards.content_rules import useful_sentence
        for lang,word in [('en','hello'),('en','apple'),('de','Apfel'),('fr','pomme'),('es','manzana')]:
            rows=examples(word,lang)
            self.assertEqual(len(rows),10)
            self.assertTrue(all(useful_sentence(word,row['text'],lang) for row in rows))
        self.assertEqual(examples('unknownword987','en'),[])

    def test_database_context_closes_connection(self):
        with db.get_connection() as conn:
            conn.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute('SELECT 1')


class PracticeTests(AppFixture):
    def test_cloze_never_masks_a_different_word_or_substring(self):
        self.assertIsNone(make_cloze(dict(term='cat',source_lang='en'),'We catch the bus.'))
        left,word,right=make_cloze(dict(term='cat',source_lang='en'),'The cat sleeps.')
        self.assertEqual(word,'cat')
        self.assertEqual(left+'[blank]'+right,'The [blank] sleeps.')
        self.assertEqual(make_cloze(dict(term='猫',source_lang='ja'),'私は猫が好きです。')[1],'猫')

    def test_answer_normalization_preserves_accents_and_turkish_case(self):
        self.assertNotEqual(normalize_answer('año'),normalize_answer('ano'))
        self.assertNotEqual(normalize_answer('schön'),normalize_answer('schon'))
        self.assertEqual(normalize_answer('İSTANBUL','tr'),normalize_answer('istanbul','tr'))
        self.assertEqual(normalize_answer('  take   a break. '),'take a break')

    def test_answer_normalization_accepts_dotted_i_without_losing_turkish_distinctions(self):
        for lang in (None, 'en', 'tr'):
            for value in ('İnto', 'INTO' if lang != 'tr' else 'İNTO', 'I\u0307nto', 'i\u0307nto'):
                with self.subTest(lang=lang, value=value):
                    self.assertEqual(normalize_answer(value, lang), normalize_answer('into', lang))
        self.assertEqual(normalize_answer('IŞIK', 'tr'), normalize_answer('ışık', 'tr'))
        self.assertNotEqual(normalize_answer('sık', 'tr'), normalize_answer('sik', 'tr'))

    def test_mistakes_accepts_lowercase_answer_for_dotted_capital_i(self):
        card=self.card('İnto','içine','')
        record_attempt(card,'writing','wrong',card['term'],False)
        view=self.view('mistakes')
        self.assertEqual(view.current_card['id'],card['id'])
        self.assertEqual(view._expected,'İnto')
        view.input_spelling.setText('into')
        view._submit_answer()
        self.assertEqual(view.score,1)
        self.assertEqual(view._feedback_key,'correct')
        with db.get_connection() as conn:
            attempt=conn.execute("SELECT correct,answer,expected FROM practice_attempts WHERE mode='mistakes'").fetchone()
            self.assertEqual(tuple(attempt),(1,'into','İnto'))
            self.assertEqual(conn.execute('SELECT wrong_count FROM quiz_mistakes WHERE card_id=?',(card['id'],)).fetchone()[0],1)

    def test_filters_preserve_deck_and_use_word_language(self):
        en=self.card()
        fr=self.card('pomme','elma','Je mange une pomme pendant ma pause après le cours.','fr')
        self.card('banana','muz','I ate a banana before leaving home for the morning meeting.','en',self.other)
        view=self.view('dictation')
        view.cmb_lang.setCurrentIndex(view.cmb_lang.findData('fr'))
        self.assertEqual([c['id'] for c in view._cards_pool],[fr['id']])
        view.reload_cards()
        self.assertEqual(view.cmb_deck.currentData(),self.deck)
        self.assertEqual(view.cmb_lang.currentData(),'fr')
        self.assertEqual(view.current_card['id'],fr['id'])
        empty=db.add_deck('Boş Deste')
        view.filters.refresh()
        view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(empty))
        self.assertIsNone(view.current_card)
        self.assertFalse(view.btn_play_audio.isEnabled())

    def test_dictation_blank_and_partial_answers_are_not_correct(self):
        self.card('accept','kabul etmek','I accept your offer.')
        view=self.view('dictation')
        view._set_mode('translate')
        view.input_spelling.setText('')
        view._submit_answer()
        self.assertFalse(view._quiz_locked)
        view.input_spelling.setText('kabul')
        view._submit_answer()
        self.assertEqual(view.score,0)
        self.assertTrue(view._quiz_locked)
        self.assertTrue(mistake_ids())
        view._submit_answer()
        self.assertEqual(view._completed,1)

    def test_feedback_cannot_be_skipped_before_reading_delay(self):
        self.card()
        view=self.view('writing')
        view.input_spelling.setText('incorrect')
        view._submit_answer()
        card_id=view.current_card['id']
        self.assertTrue(view.btn_next.isEnabled())
        self.assertIn('apple',view.lbl_feedback.text())
        view._enter()
        self.assertIsNone(view.current_card)
        view._feedback_until=0
        view._next_item()
        self.assertIsNone(view.current_card)

    def test_dictation_synonyms_and_spelling_and_progress(self):
        self.card('accept','kabul etmek; onaylamak','I accept your offer.')
        view=self.view('dictation')
        view._set_mode('translate')
        view.input_spelling.setText('onaylamak')
        view._submit_answer()
        self.assertEqual(view.score,1)
        view._feedback_until=0
        view._next_item()
        self.assertIsNone(view.current_card)
        self.assertEqual(view.progress_bar.value(),100)
        view._set_mode('word')
        view.input_spelling.setText('ACCEPT')
        view._submit_answer()
        self.assertEqual(view.score,1)

    def test_cloze_single_card_uses_typing_and_multiple_cards_use_real_options(self):
        self.card()
        view=self.view('cloze')
        self.assertFalse(view.typing_container.isHidden())
        self.assertTrue(view.choices_container.isHidden())
        self.assertEqual(view._expected.lower(),'apple')
        view.input_spelling.setText('apple')
        view._submit_answer()
        self.assertEqual(view.score,1)
        self.card('banana','muz','I ate a banana after finishing my homework this afternoon.')
        view.reload_cards(force=True)
        self.assertEqual(len(view._choices_data),2)
        self.assertEqual({v.lower() for v in view._choices_data},{'apple','banana'})
        self.assertFalse(any('Option' in v for v in view._choices_data))
        view._on_choice_clicked(view._choices_data.index(view._expected))
        self.assertEqual(view.score,1)

    def test_cloze_invalid_sentences_do_not_make_arbitrary_questions(self):
        self.card('unknownword987','anlam','This sentence has no target.')
        view=self.view('cloze')
        self.assertIsNone(view.current_card)
        self.assertIn('kullanım cümlesi yok',view.lbl_prompt.text())

    def test_cloze_html_and_long_text_are_escaped(self):
        self.card('cacheword','anlam','<b>cacheword</b> appears in this example while we study a complete sentence.')
        view=self.view('cloze')
        self.assertIn('&lt;b&gt;',view.lbl_prompt.text())
        self.assertNotIn('<b>',view.lbl_prompt.text())

    def test_sentence_dictation_uses_sentence_language_and_cancelled_autoplay(self):
        self.card('pomme','elma','Je mange une pomme pendant ma pause après le cours.','fr')
        view=self.view('dictation')
        view._set_mode('sentence')
        self.assertIn(view._expected,[row['text'] for row in memory.read_examples(view.current_card) if row['kind']=='example'])
        view._play_audio_slow()
        self.speech.assert_called_with(view._expected,lang='fr',speed=.75)
        self.speech.reset_mock()
        view.hide()
        QTest.qWait(300)
        self.speech.assert_not_called()

    def test_writing_results_are_persistent_and_leave_srs_unchanged(self):
        card=self.card()
        before=db.get_card(card['id'])
        view=self.view('writing')
        view.input_spelling.setText('wrong')
        view._submit_answer()
        self.assertIn(card['id'],mistake_ids())
        after=db.get_card(card['id'])
        self.assertEqual(before['repetition_count'],after['repetition_count'])
        self.assertEqual(before['due_date'],after['due_date'])
        mistakes=self.view('mistakes')
        self.assertEqual(mistakes.current_card['id'],card['id'])

    def test_favorites_only_show_starred_cards_and_can_remove_them(self):
        one=self.card()
        self.card('banana','muz','I ate a banana before leaving home for the morning meeting.')
        db.toggle_card_favorite(one['id'])
        view=self.view('favorites')
        self.assertEqual([c['id'] for c in view._cards_pool],[one['id']])
        view._remove_favorite()
        self.assertIsNone(view.current_card)
        self.assertFalse(db.get_card(one['id'])['is_favorite'])

    def test_shadowing_uses_context_and_advances_without_typing(self):
        self.card()
        view=self.view('shadowing')
        self.assertGreaterEqual(len(view.lbl_prompt.text().split()),8)
        self.assertTrue(view.input_spelling.isHidden())
        view._submit_answer()
        self.assertEqual(view._completed,1)
        QTest.qWait(400)
        self.assertIsNone(view.current_card)

    def test_main_window_has_five_menus_and_no_ai_widgets(self):
        self.stack.enter_context(patch.object(MainWindow,'_setup_app_shortcut'))
        self.stack.enter_context(patch.object(MainWindow,'_setup_tray_icon'))
        window=MainWindow()
        window.show()
        try:
            self.assertFalse(hasattr(window,'view_ai'))
            self.assertFalse(hasattr(window,'nav_ai'))
            self.assertFalse(hasattr(window.view_settings,'input_ai_key'))
            self.assertEqual(len(window.practice_views),5)
            for key in window.practice_views:
                window.switch_to_practice(key)
                self.assertIs(window.content_stack.currentWidget(),window.practice_views[key])
            bank=window.practice_views['sentence_memory']
            self.assertGreaterEqual(bank.table.rowCount(),1)
            self.assertNotIn('challenge',window.practice_views)
            self.assertTrue(all(row['kind']=='example' for row in bank.rows))
        finally:
            window._is_force_quitting=True
            window.close()
            window.deleteLater()

    def test_language_change_updates_current_question_and_feedback(self):
        self.card()
        view=self.view('writing')
        view.input_spelling.setText('wrong')
        view._submit_answer()
        for lang,prompt,feedback in [('de','Schreibe','Richtige Antwort:'),('es','Escribe','Respuesta correcta:'),('en','Write','Correct answer:'),('tr','Bu anlama','Doğru cevap:')]:
            view.update_language(lang)
            self.assertIn(prompt,view.lbl_instruction.text())
            self.assertIn(feedback,view.lbl_feedback.text())
            self.assertIn('apple',view.lbl_feedback.text())

    def test_sentence_memory_count_validation_and_errors_are_localized(self):
        card=self.card()
        view=SentenceMemoryView()
        self.addCleanup(view.deleteLater)
        view.current_card=card
        with db.get_connection() as conn:
            conn.execute('INSERT OR REPLACE INTO sentence_fetches VALUES (?,?,?,?,?)',
                         ('en','apple',time.time(),'offline','http_503'))
        for lang,count in [('de','Beispielsätze'),('es','ejemplos de uso'),('tr','kullanım örneği'),('en','usage examples')]:
            view.update_language(lang)
            self.assertIn(count,view.lbl_count.text())
            self.assertIn('503',view.lbl_status.text())
            view.input_example.setText('No target word.')
            view._add()
            self.assertEqual(view.lbl_status.text(),view.msg('invalid'))

    def test_offline_memory_is_visible_and_usable_in_cloze_and_sentence_listening(self):
        card=self.card('opportunity','fırsat','')
        bank=SentenceMemoryView()
        self.addCleanup(bank.deleteLater)
        bank.filters.cmb_deck.setCurrentIndex(bank.filters.cmb_deck.findData(self.deck))
        bank.reload_cards()
        self.assertEqual(bank.table.rowCount(),len(memory.read_examples(card)))
        self.assertEqual(bank.table.item(0,2).text(),'Çevrimdışı örnek')
        cloze=self.view('cloze')
        self.assertIsNotNone(cloze.current_card)
        self.assertEqual(cloze._expected.casefold(),'opportunity')
        listening=self.view('dictation')
        listening._set_mode('sentence')
        self.assertIsNotNone(listening.current_card)
        self.assertIn('opportunity',listening._expected.casefold())

    def test_match_game_obeys_filters_and_ignores_old_round_callbacks(self):
        for i in range(4):
            self.card(f'word{i}',f'anlam{i}','')
        from duocards.widgets.match_game_view import MatchGameView
        view=MatchGameView()
        self.addCleanup(view.close)
        self.addCleanup(view.deleteLater)
        view.show()
        view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(self.deck))
        old=view._round_generation
        first=view._all_tiles[0]
        second=next(t for t in view._all_tiles if t.pair_id==first.pair_id and t.is_term!=first.is_term)
        view._on_tile_clicked(first)
        view._on_tile_clicked(second)
        view._start_new_game()
        self.assertGreater(view._round_generation,old)
        QTest.qWait(450)
        self.assertEqual(view.matched_pairs,0)
        view.hide()
        self.assertFalse(view._timer.isActive())
        empty=db.add_deck('Oyun için boş deste')
        view.refresh_filters()
        view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(empty))
        self.assertEqual(view.total_pairs,0)
        self.assertFalse(view._all_tiles)


class SettingsMigrationTests(unittest.TestCase):
    def test_legacy_ai_keys_and_endpoints_are_removed(self):
        from duocards import settings as module
        with tempfile.TemporaryDirectory() as tmp:
            filename=Path(tmp)/'settings.json'
            filename.write_text(json.dumps(dict(ai_api_key='test-only',ai_enabled=True,ollama_host='test',menu_visible_ai=True,sfx_volume=30)))
            with patch.object(module,'SETTINGS_FILE',str(filename)),patch.object(module,'SETTINGS_DIR',tmp):
                manager=SettingsManager()
                data=json.loads(filename.read_text())
                self.assertEqual(manager.get('sfx_volume'),30)
                self.assertFalse(any(k.startswith(('ai_','ollama_')) or k=='menu_visible_ai' for k in data))


class AudioTests(unittest.TestCase):
    def test_stale_request_does_not_launch_any_player(self):
        player=AudioPlayer()
        player._generation=2
        with patch('duocards.audio.subprocess.Popen') as launch:
            player._play_worker('old word','en',1.,1)
            launch.assert_not_called()

    def test_stop_terminates_playing_process_without_waiting_for_lock(self):
        player=AudioPlayer()
        player.mpv_path='/fake/mpv'
        player.ffplay_path=player.espeak_path=None
        player._generation=1
        launched,release=threading.Event(),threading.Event()
        fake=MagicMock()
        fake.poll.return_value=None
        def wait():
            launched.set()
            release.wait(2)
            return 0
        fake.wait.side_effect=wait
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)/'voice.mp3'
            cache.write_bytes(b'ID3test')
            with patch('duocards.audio._get_cache_path',return_value=str(cache)),patch('duocards.audio.subprocess.Popen',return_value=fake):
                thread=threading.Thread(target=player._play_worker,args=('word','en',1.,1))
                thread.start()
                self.assertTrue(launched.wait(1))
                player.stop()
                fake.terminate.assert_called_once()
                release.set()
                thread.join(1)
                self.assertFalse(thread.is_alive())
