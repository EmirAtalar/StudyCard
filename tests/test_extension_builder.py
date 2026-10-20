"""Create, reopen, preview and play user extensions without touching the real library."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QDialog, QLabel
from PyQt6.QtTest import QTest
from duocards import db, custom_tables, custom_games, device_backup, sentence_memory, personal_extensions
from duocards.settings import settings, DEFAULT_SETTINGS
from duocards.sfx import sfx
from duocards.audio import audio_player
from duocards.main_window import MainWindow
from duocards.icons import get_icon, PERSONAL_ICONS
from duocards.widgets.studio_dialogs import TextDialog, TableDetailsDialog, ConfirmDialog, StudioDialog, IconPicker
from duocards.widgets.custom_tables_view import CustomTablesView
from duocards.widgets.extensions_view import ExtensionsView, CORE_MENUS
from duocards.widgets.game_studio import GameStudio
from duocards.widgets.game_player import GamePlayer


class BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.folder=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        for obj,key,value in [(db,'DB_DIR',str(self.folder)),(db,'DB_PATH',str(self.folder/'cards.db')),(device_backup,'SETTINGS_FILE',str(self.folder/'settings.json'))]:self.stack.enter_context(patch.object(obj,key,value))
        before=settings.get_all();self.addCleanup(setattr,settings,'_settings',before);settings._settings=dict(DEFAULT_SETTINGS,ui_language='tr')
        for obj,key in [(settings,'save'),(sfx,'_play_file'),(audio_player,'prefetch'),(audio_player,'play_pronunciation'),(MainWindow,'_setup_app_shortcut'),(MainWindow,'_setup_tray_icon')]:self.stack.enter_context(patch.object(obj,key))
        self.stack.enter_context(patch.object(sentence_memory,'request_examples',side_effect=sentence_memory.ensure_examples))
        db.init_db()

    def widget(self,kind,*args):
        view=kind(*args);self.addCleanup(view.deleteLater);self.addCleanup(view.close)
        if isinstance(view,MainWindow):view._is_force_quitting=True
        return view

    def game(self,mode='quiz'):
        game=custom_games.new_game();game.update(name='Kelime oyunumu',mode=mode,shuffle=False,sound=False,question_count=3,
            manual_pairs=[dict(prompt='go',answer='gitmek'),dict(prompt='eat',answer='yemek'),dict(prompt='write',answer='yazmak')])
        return game

    def table(self):
        table=custom_tables.new_table('Kelimelerim');a,b=table['columns'];table['icon']='rocket';table['description']='Kendi kelimelerim'
        table['rows']=[dict(id=str(i),name=str(i+1),cells={a['id']:p,b['id']:answer},muted=[]) for i,(p,answer) in enumerate([('go','gitmek'),('eat','yemek'),('write','yazmak')])]
        custom_tables.save_table(table);return table

    def test_modal_forms_have_the_app_frame_and_keep_input_after_acceptance(self):
        dialog=self.widget(TextDialog,'Column name','Column name','old')
        self.assertTrue(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertTrue(dialog.isModal())
        dialog.input.setText('new');dialog.accept();self.assertEqual(dialog.result(),QDialog.DialogCode.Accepted)
        def enter():
            active=QApplication.activeModalWidget();active.input.setText('Yeni ad');active.accept()
        QTimer.singleShot(20,enter)
        name,ok=TextDialog.get_text(None,'Row name','Row name','old')
        self.assertTrue(ok);self.assertEqual(name,'Yeni ad')

    def test_new_table_dialog_persists_icon_and_appears_in_extensions_immediately(self):
        view=self.widget(CustomTablesView)
        def enter():
            dialog=QApplication.activeModalWidget();dialog.name.setText('Fiiller');dialog.description.setText('Özel fiil listem');dialog.icons.set_value('rocket');dialog.rows.setValue(5);dialog.template.setCurrentIndex(dialog.template.findData('verbs'));dialog.accept()
        QTimer.singleShot(20,enter);ident=view.create()
        saved=custom_tables.list_tables()[0]
        self.assertEqual(saved['id'],ident);self.assertEqual(saved['icon'],'rocket');self.assertEqual(len(saved['rows']),5);self.assertEqual(len(saved['columns']),4)
        extensions=self.widget(ExtensionsView)
        self.assertEqual(extensions.personal_cards[0].document['name'],'Fiiller')
        emitted=[];extensions.open_module_requested.connect(emitted.append);extensions.personal_cards[0].open_button.click()
        self.assertEqual(emitted,['table:'+ident])

    def test_table_metadata_rename_does_not_touch_cells_or_speech(self):
        table=self.table();view=self.widget(CustomTablesView)
        def edit():
            active=QApplication.activeModalWidget();active.name.setText('Yeni tablo');active.icons.set_value('bulb');active.accept()
        QTimer.singleShot(20,edit);view.rename();view.save();updated=custom_tables.list_tables()[0]
        self.assertEqual(updated['icon'],'bulb');self.assertEqual(updated['name'],'Yeni tablo');self.assertEqual(updated['rows'],table['rows']);self.assertEqual(updated['columns'],table['columns'])

    def test_three_game_modes_complete_without_duplicate_scoring(self):
        for mode in custom_games.MODES:
            session=custom_games.GameSession(self.game(mode),rng=random.Random(7))
            if mode in custom_games.BOARD_MODES:
                self.assertFalse(session.match(0,1));self.assertTrue(session.match(0,0));self.assertIsNone(session.match(0,0));self.assertIsNone(session.match(-1,2))
                session.match(1,1);session.match(2,2)
            else:
                while not session.complete:
                    expected,_=custom_games.expected_answer(session.game,session.items[session.index])
                    if mode in custom_games.CHOICE_MODES:self.assertIn(expected,session.choices())
                    self.assertTrue(session.answer(expected));self.assertIsNone(session.answer(expected));session.advance()
            self.assertTrue(session.complete);self.assertEqual(session.correct,3)

    def test_table_game_keeps_working_when_headers_are_renamed(self):
        table=self.table();game=self.game();game.update(source='table',source_id=table['id'],prompt_column=table['columns'][0]['id'],answer_column=table['columns'][1]['id'])
        before=custom_games.questions(game);table['columns'][0]['name']='Fiiller';custom_tables.save_table(table)
        self.assertEqual(custom_games.questions(game),before)
        custom_tables.delete_table(table['id'])
        with self.assertRaisesRegex(ValueError,'unavailable'):custom_games.questions(game)

    def test_ambiguous_question_pools_and_duplicate_matching_answers_are_rejected(self):
        game=self.game();game['manual_pairs'].append(dict(prompt='go',answer='başka'))
        with self.assertRaisesRegex(ValueError,'multiple answers'):custom_games.questions(game)
        game=self.game('matching');game['manual_pairs'][1]['answer']='gitmek'
        with self.assertRaisesRegex(ValueError,'different answer for every'):custom_games.questions(game)

    def test_typed_answers_keep_accents_and_turkish_case_rules(self):
        game=self.game('typing');game.update(question_count=1,manual_pairs=[dict(prompt='city',answer='İSTANBUL')])
        session=custom_games.GameSession(game);self.assertTrue(session.answer('istanbul'))
        game['manual_pairs']=[dict(prompt='year',answer='año')];game['answer_language']='es'
        self.assertFalse(custom_games.GameSession(game).answer('ano'))

    def test_studio_preview_is_playable_and_publish_creates_a_saved_extension(self):
        studio=self.widget(GameStudio,'tr');studio.name.setText('Benim testim')
        for i,pair in enumerate(self.game()['manual_pairs']):
            studio.pairs.setItem(i,0,QTableWidgetItem(pair['prompt']));studio.pairs.setItem(i,1,QTableWidgetItem(pair['answer']))
        studio.show();studio.preview();self.assertIsNotNone(studio.player.session);self.assertTrue(studio.player.preview);self.assertEqual(custom_games.list_games(),[])
        studio.publish();game=custom_games.list_games()[0];self.assertEqual(game['name'],'Benim testim')
        extensions=self.widget(ExtensionsView);self.assertEqual(extensions.personal_cards[0].kind,'game')
        self.assertFalse(studio._dirty)

    def test_player_records_saved_game_once_and_never_records_preview(self):
        game=self.game();custom_games.save_game(game);player=self.widget(GamePlayer,'tr');player.show()
        for preview in (True,False):
            player.start(game,preview)
            while not player.session.complete:
                player.answer(player.session.items[player.session.index]['answer']);player.next()
            player._complete()
            self.assertEqual(custom_games.game_stats(game['id'])['plays'],0 if preview else 1)

    def test_timer_pauses_when_player_is_hidden(self):
        game=self.game('typing');game['time_limit']=2
        player=self.widget(GamePlayer,'tr');player.show();player.start(game,True);QTest.qWait(100);player.hide();left=player._paused_remaining
        QTest.qWait(300);player.show();QTest.qWait(20)
        self.assertFalse(player.session.locked);self.assertGreater(player._deadline-__import__('time').monotonic(),left-.2)

    def test_player_displays_user_text_without_translating_it(self):
        game=self.game('matching');game['manual_pairs']=[dict(prompt='Save',answer='Word'),dict(prompt='Open',answer='Meaning')]
        player=self.widget(GamePlayer,'tr');player.start(game,True)
        self.assertEqual(player.left_buttons[0].text(),'Save');self.assertEqual(player.right_buttons[0].text(),'Word')

    def test_full_device_backup_restores_games_and_play_results(self):
        game=self.game();custom_games.save_game(game);custom_games.record_run(game['id'],2,3,10.5)
        path=self.folder/'games.studycard';device_backup.export_backup(path);custom_games.delete_game(game['id']);device_backup.restore_backup(path)
        self.assertEqual(custom_games.get_game(game['id']),game);self.assertEqual(custom_games.game_stats(game['id'])['plays'],1)

    def test_main_window_routes_personal_extensions_and_has_a_distinct_creator_icon(self):
        table=self.table();game=self.game();custom_games.save_game(game)
        window=self.widget(MainWindow);self.assertEqual(window.nav_tables.text(),'Eklenti kur')
        self.assertFalse(get_icon('maker').isNull());self.assertNotEqual(get_icon('maker').cacheKey(),get_icon('library').cacheKey())
        self.assertIn('maker',[m['id'] for m in CORE_MENUS])
        window._open_extension_module('table:'+table['id']);self.assertIs(window.view_tables.stack.currentWidget(),window.view_tables.editor)
        window._open_extension_module('game:'+game['id']);self.assertIs(window.view_tables.stack.currentWidget(),window.view_tables.player_page)
        self.assertFalse(window.view_tables.player.preview)
        window._open_extension_module('maker');self.assertIs(window.view_tables.stack.currentWidget(),window.view_tables.home_page)

    def test_new_studio_obeys_preferences_without_scaling_text_twice(self):
        settings._settings.update(text_scale=120,theme='graphite',accent_color='#38bdf8')
        window=self.widget(MainWindow)
        style=window.view_tables.styleSheet()
        self.assertIn('font-size: 30.0px',style)
        self.assertNotIn('font-size: 36.0px',style)
        self.assertIn('#38bdf8',style)
        settings._settings.update(text_scale=100,theme='dark_slate',accent_color='#10b981')
        window._apply_preferences()
        self.assertIn('font-size: 25px',window.view_tables.styleSheet())
        self.assertIn('#10b981',window.view_tables.styleSheet())

    def test_personal_extensions_and_creator_can_be_toggled_without_deleting_content(self):
        table=self.table();game=self.game();custom_games.save_game(game)
        window=self.widget(MainWindow)
        table_route='table:'+table['id'];game_route='game:'+game['id']
        self.assertTrue(window.personal_nav_btns[table_route].isHidden())
        for card in window.view_extensions.personal_cards:
            card.toggle_button.click()
        self.assertFalse(window.personal_nav_btns[table_route].isHidden())
        self.assertFalse(window.personal_nav_btns[game_route].isHidden())
        window.show();window.switch_to_extensions();QTest.qWait(100)
        for card in window.view_extensions.personal_cards:
            self.assertGreaterEqual(card.height(),card.minimumSizeHint().height())
        extensions=window.view_extensions
        self.assertGreaterEqual(extensions.lbl_sec_core.y(),extensions.personal_container.y()+extensions.personal_container.height())
        window.personal_nav_btns[table_route].click()
        self.assertIs(window.view_tables.stack.currentWidget(),window.view_tables.editor)
        card=next(c for c in window.view_extensions.personal_cards if c.kind=='table')
        card.toggle_button.click();self.assertTrue(window.personal_nav_btns[table_route].isHidden())
        card.open_button.click();self.assertIs(window.view_tables.stack.currentWidget(),window.view_tables.editor)
        self.assertFalse(personal_extensions.in_menu('table',table['id']))
        maker=next(c for c in window.view_extensions.cards if c.data['id']=='maker')
        maker.btn_toggle.click();self.assertTrue(window.nav_tables.isHidden())
        maker.btn_toggle.click();self.assertFalse(window.nav_tables.isHidden())
        self.assertEqual(custom_tables.list_tables()[0]['id'],table['id'])
        self.assertEqual(custom_games.get_game(game['id']),game)

    def test_menu_choices_survive_a_real_settings_reload(self):
        import duocards.settings as settings_module
        from duocards.settings import SettingsManager
        table=self.table()
        with patch.object(settings_module,'SETTINGS_DIR',str(self.folder)),patch.object(settings_module,'SETTINGS_FILE',str(self.folder/'preferences.json')),patch.object(settings,'save',SettingsManager.save.__get__(settings,SettingsManager)):
            window=self.widget(MainWindow)
            window.view_extensions.personal_cards[0].toggle_button.click()
            loaded=SettingsManager()
            self.assertTrue(loaded.get(personal_extensions.menu_key('table',table['id'])))
            settings._settings=loaded.get_all()
            restarted=self.widget(MainWindow)
            self.assertFalse(restarted.personal_nav_btns['table:'+table['id']].isHidden())

    def test_menu_keys_follow_identity_when_renamed_or_deleted(self):
        table=self.table();settings._settings[personal_extensions.menu_key('table',table['id'])]=True
        window=self.widget(MainWindow);route='table:'+table['id']
        original=window.personal_nav_btns[route]
        table.update(name='Yeni başlık',icon='anchor');custom_tables.save_table(table);window._sync_personal_nav()
        self.assertIs(window.personal_nav_btns[route],original);self.assertEqual(original.text().strip(),'Yeni başlık')
        custom_tables.delete_table(table['id']);window._sync_personal_nav()
        self.assertNotIn(route,window.personal_nav_btns)

    def test_backup_restores_missing_menu_choices_to_their_original_defaults(self):
        table=self.table();path=self.folder/'menu.studycard'
        device_backup.export_backup(path)
        settings._settings.update({personal_extensions.menu_key('table',table['id']):True,'menu_visible_maker':False})
        device_backup.restore_backup(path)
        self.assertFalse(personal_extensions.in_menu('table',table['id']))
        self.assertTrue(settings.get('menu_visible_maker',True))

    def test_thirty_two_icon_choices_render_and_extra_choices_can_be_selected(self):
        self.assertEqual(len(PERSONAL_ICONS),32)
        picker=self.widget(IconPicker)
        for key in PERSONAL_ICONS:
            icon=get_icon(key,24);self.assertFalse(icon.isNull(),key)
            bitmap=icon.pixmap(24,24).toImage()
            self.assertTrue(any(bitmap.pixelColor(x,y).alpha()>0 for x in range(bitmap.width()) for y in range(bitmap.height())),key)
        picker.set_value('anchor');self.assertTrue(picker._expanded);self.assertEqual(picker.value(),'anchor')
        picker.update_language('de');self.assertIn('Anker',picker.buttons['anchor'].toolTip())

    def test_listen_write_and_translate_score_different_expected_texts(self):
        dictation=self.game('audio_dictation');dictation['manual_pairs']=[dict(prompt='go',answer='')]
        self.assertTrue(custom_games.GameSession(dictation).answer('GO'))
        translation=self.game('audio_translation')
        self.assertFalse(custom_games.GameSession(translation).answer('go'))
        self.assertTrue(custom_games.GameSession(translation).answer('gitmek'))
        studio=self.widget(GameStudio,'tr');studio.name.setText('Dinleme');studio.mode.setCurrentIndex(studio.mode.findData('audio_dictation'))
        studio.pairs.setItem(0,0,QTableWidgetItem('go'))
        self.assertEqual(studio.collect()['manual_pairs'],[dict(prompt='go',answer='')])

    def test_audio_games_hide_transcript_and_wait_for_the_current_speech_request(self):
        player=self.widget(GamePlayer,'tr');player.show()
        audio_player.play_pronunciation.return_value=700
        game=self.game('audio_translation');game['time_limit']=10
        player.start(game,True)
        self.assertFalse(any(c.text()=='go' for c in player.findChildren(QLabel) if c.isVisible()))
        audio_player.play_pronunciation.assert_called_with('go','en')
        self.assertFalse(player._timer.isActive())
        audio_player.request_state_changed.emit(699,'playing');audio_player.request_state_changed.emit(699,'idle')
        self.assertFalse(player._timer.isActive())
        audio_player.request_state_changed.emit(700,'playing');self.assertFalse(player._timer.isActive())
        audio_player.request_state_changed.emit(700,'idle');self.assertTrue(player._timer.isActive())
        player.answer('gitmek');self.assertEqual(player.session.correct,1);self.assertFalse(player._timer.isActive())

    def test_memory_cards_match_once_and_wrong_pairs_turn_back_over(self):
        player=self.widget(GamePlayer,'tr');player.show();player.start(self.game('memory'),True)
        first=next(i for i,face in enumerate(player._memory_faces) if face==(0,'prompt'))
        wrong=next(i for i,face in enumerate(player._memory_faces) if face==(1,'answer'))
        player.flip_memory(first);player.flip_memory(wrong);self.assertTrue(player._memory_busy)
        QTest.qWait(750);self.assertFalse(player._memory_busy);self.assertEqual(player.memory_buttons[first].face_label.text(),'?')
        for pair in range(len(player.session.items)):
            positions=[i for i,face in enumerate(player._memory_faces) if face[0]==pair]
            for position in positions:player.flip_memory(position)
        self.assertTrue(player.session.complete);self.assertEqual(player.session.correct,3);self.assertEqual(player.session.mistakes,1)

    def test_word_builder_handles_repeated_letters_undo_and_clear(self):
        game=self.game('word_builder');game.update(question_count=1,manual_pairs=[dict(prompt='letter',answer='mektup')])
        player=self.widget(GamePlayer,'tr');player.start(game,True)
        self.assertFalse(player.word_submit.isEnabled())
        player.add_letter(1);player.add_letter(1);self.assertEqual(player.input_answer.text(),'e')
        player.undo_letter();self.assertEqual(player.input_answer.text(),'')
        player.add_letter(0);player.clear_letters();self.assertEqual(player.letter_order,[])
        for index in range(len(player.letters)):player.add_letter(index)
        self.assertTrue(player.word_submit.isEnabled());player.word_submit.click()
        self.assertEqual(player.session.correct,1)

    def test_all_eight_game_recipes_and_extended_icons_survive_device_backup(self):
        games=[]
        for index,mode in enumerate(custom_games.MODES):
            game=self.game(mode);game['icon']=PERSONAL_ICONS[-index-1];custom_games.save_game(game);games.append(game)
        path=self.folder/'eight-games.studycard';device_backup.export_backup(path)
        for game in games:custom_games.delete_game(game['id'])
        device_backup.restore_backup(path)
        self.assertEqual(len(custom_games.list_games()),8)
        for game in games:self.assertEqual(custom_games.get_game(game['id']),game)

    def test_single_column_tables_can_supply_dictation_questions(self):
        table=self.table();table['columns']=table['columns'][:1]
        for row in table['rows']:row['cells']={table['columns'][0]['id']:row['cells'][table['columns'][0]['id']]}
        custom_tables.save_table(table)
        game=self.game('audio_dictation');game.update(source='table',source_id=table['id'],prompt_column=table['columns'][0]['id'],answer_column=table['columns'][0]['id'])
        self.assertEqual([row['prompt'] for row in custom_games.questions(game)],['go','eat','write'])
        self.assertTrue(custom_games.GameSession(game).answer('go'))


if __name__=='__main__':unittest.main()
