"""Duplicate entry, meaningful examples, portable backups and language switching."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from duocards import db,sentence_memory
from duocards.audio import AudioPlayer,audio_player
from duocards.card_transfer import export_cards,import_file,read_csv
from duocards.content_rules import useful_sentence
from duocards.settings import settings
from duocards.widgets.add_card_view import AddCardView, DuplicateCardDialog
from duocards.widgets.import_export_view import ImportExportView
from duocards.widgets.universal_module_view import UniversalLanguageModuleView
from duocards.widgets.extensions_view import AVAILABLE_EXTENSIONS
from duocards.widgets.edit_card_dialog import EditCardDialog
from duocards.widgets.library_view import LibraryView
from duocards.widgets.account_panel import AccountPanel, SyncCoordinator, TEXT as ACCOUNT_TEXT
from duocards.main_window import MainWindow

class PolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.directory=self.stack.enter_context(tempfile.TemporaryDirectory())
        old=settings.get_all();self.addCleanup(setattr,settings,'_settings',old)
        settings._settings.update(ui_language='tr',last_source_lang='en',last_target_lang='tr',auto_pronounce=False)
        for obj,key,value in ((db,'DB_DIR',self.directory),(db,'DB_PATH',self.directory+'/cards.db')):self.stack.enter_context(patch.object(obj,key,value))
        self.stack.enter_context(patch.object(settings,'save'))
        self.stack.enter_context(patch.object(sentence_memory,'request_examples',side_effect=lambda card,force=False:sentence_memory.ensure_examples(card)))
        self.stack.enter_context(patch.object(audio_player,'prefetch'))
        self.stack.enter_context(patch.object(audio_player,'play_pronunciation'))
        self.stack.enter_context(patch('duocards.sfx.sfx._play_file'))
        db.init_db();self.deck=db.add_deck('Portable')
    def card(self,word='hello'):
        return db.add_card(self.deck,word,'selam',source_lang='en',target_lang='tr',example_sentence='She said hello to the receptionist before asking for the meeting room.',example_translation='Toplantı odasını sormadan önce resepsiyon görevlisine selam verdi.',phonetic='/həˈləʊ/',notes='Keep this note')
    def test_duplicate_lookup_handles_case_and_unicode_across_decks(self):
        ident=self.card('HELLO');self.assertEqual(db.find_existing_cards(' hello ')[0]['id'],ident)
        self.card('Straße');self.assertEqual(len(db.find_existing_cards('STRASSE')),1)
        self.card('İSTANBUL');self.assertEqual(len(db.find_existing_cards('istanbul')),1)
        self.assertEqual(db.find_existing_cards('hello',exclude_id=ident),[])
    def test_manual_form_shows_existing_and_does_not_save_without_choice(self):
        ident=self.card();view=AddCardView();view.refresh_decks();view.cmb_deck.setCurrentIndex(view.cmb_deck.findData(self.deck));view.input_definition.setText('selam');view.input_term.setText('HELLO')
        self.addCleanup(view.deleteLater);self.addCleanup(view.close)
        self.assertIn('hello',view.lbl_duplicates.text())
        with patch.object(DuplicateCardDialog,'exec',return_value=0):self.assertFalse(view._validate_and_save())
        self.assertEqual(len(db.get_all_cards(self.deck)),1)
        opened=[];view.edit_existing.connect(opened.append);view.btn_edit_existing.click();self.assertEqual(opened,[ident])
    def test_hello_examples_have_context_and_old_short_cache_is_rejected(self):
        card=db.get_card(self.card());rows=sentence_memory.read_examples(card)
        self.assertEqual(len(rows),10)
        self.assertTrue(all(useful_sentence('hello',row['text']) for row in rows))
        self.assertFalse(useful_sentence('hello','Hello.'))
        self.assertFalse(useful_sentence('hello','She said hello.'))
        with db.get_connection() as conn:
            conn.execute("UPDATE sentence_memory SET text='hello' WHERE term_key='hello'")
        recovered=sentence_memory.read_examples(card)
        self.assertTrue(all(useful_sentence("hello",row["text"]) for row in recovered))
        self.assertFalse(any(row["text"]=="hello" for row in recovered))
    def test_csv_json_roundtrip_preserves_current_card_fields_and_progress(self):
        ident=self.card();db.toggle_card_favorite(ident)
        with db.get_connection() as conn:conn.execute("UPDATE cards SET status='learning',repetition_count=2,interval_days=3,ease_factor=2.7,due_date='2030-01-02' WHERE id=?",(ident,))
        original=db.get_card(ident)
        for format in ('csv','json'):
            with self.subTest(format=format):
                path=self.directory+'/backup.'+format;export_cards(path,format,self.deck)
                self.assertEqual(import_file(path,self.deck),{'added':0,'skipped':1,'invalid':0})
                db.delete_card(ident);report=import_file(path,self.deck);self.assertEqual(report['added'],1)
                restored=db.get_all_cards(self.deck)[0];ident=restored['id']
                for key in ('term','definition','source_lang','target_lang','example_sentence','example_translation','phonetic','notes','is_favorite','status','repetition_count','interval_days','due_date'):self.assertEqual(restored[key],original[key],key)
    def test_headerless_legacy_and_quoted_newline_csv_import(self):
        rows=read_csv('hello,selam\nworld,dünya\n');self.assertEqual(len(rows),2);self.assertEqual(rows[0]['term'],'hello')
        rows=read_csv('Deste;Kelime/Kalıp;Anlamı;Kelime Türü\nPortable;hello;selam;Kelime\n');self.assertEqual(rows[0]['term'],'hello')
        rows=read_csv('term,definition,notes\nhello,selam,"line one\nline two"\n');self.assertEqual(rows[0]['notes'],'line one\nline two')
    def test_json_backup_restores_empty_decks(self):
        path=self.directory+'/empty.json'
        Path(path).write_text(json.dumps({'version':2,'decks':[{'name':'Empty deck','description':'Preserve this','icon':'book','color':'#112233'}],'cards':[]}))
        report=import_file(path,self.deck)
        self.assertEqual(report['added'],0)
        deck=next(row for row in db.get_all_decks() if row['name']=='Empty deck')
        self.assertEqual(deck['description'],'Preserve this')
        self.assertEqual(deck['color'],'#112233')

    def test_import_view_languages_change_and_keep_language_codes(self):
        view=ImportExportView();self.addCleanup(view.deleteLater)
        for lang in ('de','es','en','tr'):
            view.update_language(lang);self.assertEqual(view.cmb_source.currentData(),'en');self.assertEqual(view.cmb_target.currentData(),'tr')
            self.assertNotEqual(view.btn_imp_json.text(),'Import JSON backup' if lang!='en' else '')

    def test_legacy_card_editor_localizes_fields_and_saves_stable_codes(self):
        ident=db.add_card(self.deck,'hello','selam',source_lang='İngilizce',target_lang='Türkçe',part_of_speech='İsim')
        for lang,source,target,pos in [('de','Englisch','Türkisch','Nomen'),('es','Inglés','Turco','Sustantivo')]:
            settings._settings['ui_language']=lang
            dialog=EditCardDialog(ident);self.addCleanup(dialog.deleteLater)
            self.assertEqual(dialog.cmb_source_lang.currentText(),source)
            self.assertEqual(dialog.cmb_target_lang.currentText(),target)
            self.assertEqual(dialog.cmb_pos.currentText(),pos)
            dialog._save();card=db.get_card(ident)
            self.assertEqual((card['source_lang'],card['target_lang'],card['part_of_speech']),('en','tr','noun'))
            self.assertEqual(card['definition'],'selam')

    def test_library_feedback_filters_and_account_status_follow_language(self):
        for word in ('hello','world','apple','book'):self.card(word)
        view=LibraryView();self.addCleanup(view.deleteLater);view.show();self.addCleanup(view.close)
        view._show_quiz();current=view._current_quiz_card
        wrong=next(i for i,value in enumerate(view._choices_data) if value!=view._quiz_correct_answer)
        view._on_quiz_answer(wrong)
        coordinator=SyncCoordinator(client=__import__('unittest.mock',fromlist=['Mock']).Mock())
        coordinator.client.session.return_value={};coordinator.timer.stop();coordinator.debounce.stop();self.addCleanup(coordinator.deleteLater)
        panel=AccountPanel();self.addCleanup(panel.deleteLater);panel.attach(coordinator)
        coordinator._complete('sync',{'pending':0,'changed':False})
        for lang,wrong_text,target_name in [('de','Falsch','Türkisch'),('es','Incorrecto','Turco'),('en','Wrong','Turkish'),('tr','Yanlış','Türkçe')]:
            view.update_language(lang);panel.update_language(lang)
            self.assertIs(view._current_quiz_card,current)
            self.assertIn(wrong_text,view.lbl_q_feedback.text())
            self.assertEqual(view.lang_filter.itemText(view.lang_filter.findData('tr')),target_name)
            self.assertEqual(view.quiz_lang_filter.itemText(view.quiz_lang_filter.findData('tr')),target_name)
            self.assertIn(ACCOUNT_TEXT[lang][11],panel.status.text())
    def test_confused_words_quiz_has_only_the_pair_and_context(self):
        ext=next(item for item in AVAILABLE_EXTENSIONS if item['id']=='en_confusing_words')
        view=UniversalLanguageModuleView(ext['id'],ext['titles']['tr'],'EN',ext['dataset_file'],column_titles=ext['column_titles'],titles=ext['titles']);view.show();self.addCleanup(view.close);self.addCleanup(view.deleteLater);view._show_quiz()
        for _ in range(25):
            view._next_quiz();target=view._current_quiz
            self.assertEqual(set(view._choices_data),{target['term'],target['confused_with']})
            self.assertIn('____',view.lbl_q_term.text());self.assertIn('1–2',view.lbl_keyboard_help.text())
            self.assertEqual(sum(not button.isHidden() for button in view.btn_choices),2)
    def test_language_change_keeps_module_question_and_answer_order(self):
        view=UniversalLanguageModuleView('en_phrasal','Phrasal','EN','en_phrasal.json');view.show();self.addCleanup(view.close);self.addCleanup(view.deleteLater);view._show_quiz()
        current=view._current_quiz;before=list(view._choices_data);view.update_language('de')
        self.assertIs(view._current_quiz,current)
        self.assertEqual(view._quiz_correct_answer,current['translations']['de'])
        self.assertNotEqual(before,view._choices_data)
    def test_active_irregular_question_and_feedback_follow_language(self):
        view=UniversalLanguageModuleView('en_verbs','Verbs','EN','en_verbs.json');view.show();self.addCleanup(view.close);self.addCleanup(view.deleteLater)
        real_choice=__import__('random').choice
        with patch('duocards.widgets.universal_module_view.random.choice',side_effect=lambda options:'verb_v2' if options==['verb_v2','verb_v3','verb_v1','meaning'] else real_choice(options)):
            view._show_quiz()
        current=view._current_quiz
        view.input_typed_answer.setText('wrong');view._on_submit_typed_answer()
        for lang,wrong in [('de','Falsch'),('es','Incorrecto'),('en','Wrong'),('tr','Yanlış')]:
            view.update_language(lang)
            self.assertIs(view._current_quiz,current)
            self.assertIn(wrong,view.lbl_q_feedback.text())
            self.assertIn('V2',view.lbl_q_hint.text())
            self.assertEqual(view._quiz_score,0)

    def test_removed_menus_do_not_appear_and_sections_are_reorganized(self):
        self.stack.enter_context(patch.object(MainWindow,'_setup_app_shortcut'));self.stack.enter_context(patch.object(MainWindow,'_setup_tray_icon'))
        window=MainWindow();self.addCleanup(window.deleteLater);window._is_force_quitting=True;self.addCleanup(window.close)
        self.assertNotIn('challenge',window.practice_views);self.assertIn('shadowing',window.practice_views)
        ids={extension['id'] for extension in AVAILABLE_EXTENSIONS};self.assertFalse(ids.intersection({'en_collocations','en_daily_phrases','en_workplace'}))
        for lang in ('de','es','en','tr'):
            window._apply_language(lang)
            for view in window.extension_views.values():
                self.assertEqual(view.table.horizontalHeaderItem(4).text(),'Ses' if lang=='tr' else 'Audio')
    def test_natural_audio_never_falls_back_to_robotic_espeak(self):
        from concurrent.futures import Future
        player=AudioPlayer();player.mpv_path=player.ffplay_path=None;player.espeak_path='/fake/espeak';player._generation=1
        with patch('duocards.audio.subprocess.Popen') as process:
            player._play_worker('hello','en',1,1);process.assert_not_called()
        player._prefetch_pool.shutdown(wait=False,cancel_futures=True)

    def test_long_usage_sentence_speech_is_complete_and_cached(self):
        import urllib.parse
        from unittest.mock import MagicMock
        from duocards import audio
        sentence='She said hello to everyone at the reception before introducing her colleague and explaining why they had travelled across the country to attend this important meeting with their new business partners.'
        parts=[]
        def fetch(request,timeout):
            parts.append(urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)['q'][0])
            response=MagicMock();response.__enter__.return_value=response
            response.headers={'Content-Type':'audio/mpeg'};response.read.return_value=b'ID3voice'
            return response
        player=AudioPlayer();self.addCleanup(player._prefetch_pool.shutdown,wait=False,cancel_futures=True)
        with patch.object(audio,'CACHE_DIR',self.directory+'/audio'),patch.dict('sys.modules',{'edge_tts':None}),patch.object(audio.urllib.request,'urlopen',side_effect=fetch):
            self.assertTrue(player._download(sentence,'en'))
            self.assertGreater(len(parts),1);self.assertEqual(' '.join(parts),sentence)
            self.assertTrue(all(len(part)<=100 for part in parts))
            self.assertEqual(Path(audio._get_cache_path(sentence,'en')).read_bytes(),b'ID3voice'*len(parts))
            count=len(parts);self.assertTrue(player._download(sentence,'en'));self.assertEqual(len(parts),count)

if __name__=='__main__':unittest.main()
