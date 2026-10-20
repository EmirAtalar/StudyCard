"""Offline recovery, speech selection, editable examples and responsive imitation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from duocards import db, custom_tables, device_backup, sentence_memory
from duocards.audio import audio_player
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.widgets.custom_tables_view import CustomTablesView
from duocards.widgets.practice_view import PracticeView
from duocards.widgets.settings_view import SettingsView
from duocards.main_window import MainWindow


class NewFeaturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.folder = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.object(db, 'DB_DIR', str(self.folder)))
        self.stack.enter_context(patch.object(db, 'DB_PATH', str(self.folder/'library.db')))
        self.stack.enter_context(patch.object(device_backup, 'SETTINGS_FILE', str(self.folder/'settings.json')))
        before = settings.get_all()
        self.addCleanup(setattr, settings, '_settings', before)
        from duocards.settings import DEFAULT_SETTINGS
        settings._settings = dict(DEFAULT_SETTINGS, ui_language='tr')
        self.stack.enter_context(patch.object(settings, 'save'))
        self.stack.enter_context(patch.object(sfx, '_play_file'))
        self.stack.enter_context(patch.object(audio_player, 'prefetch'))
        self.stack.enter_context(patch.object(audio_player, 'play_pronunciation'))
        self.stack.enter_context(patch.object(sentence_memory, 'request_examples', side_effect=sentence_memory.ensure_examples))
        db.init_db()
        self.deck = db.add_deck('Kişisel deste')

    def card(self):
        return db.add_card(self.deck, 'silence', 'sessizlik', source_lang='en', target_lang='tr', example_sentence='We sat in silence while watching the sun set over the lake.', example_translation='Gölü izlerken sessizce oturduk.')

    def view(self, klass, *args):
        view = klass(*args)
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        return view

    def test_backup_roundtrip_preserves_all_history_tables_and_preferences(self):
        ident = self.card()
        db.record_study_result(ident, 3)
        from duocards.practice import record_attempt
        record_attempt(db.get_card(ident), 'writing', 'silence', 'silence', True)
        db.add_timer_session('stopwatch', 123, 'Odaklanma')
        table = custom_tables.new_table('Fiiller', 'verbs')
        table['rows'][0]['cells'][table['columns'][0]['id']] = 'go'
        custom_tables.save_table(table)
        settings._settings.update(profile_name='Emir', text_scale=115, speech_speed=.8)
        path = self.folder/'full.studycard'
        device_backup.export_backup(path)
        with db.get_connection() as conn:
            original = {r['name']: [tuple(x) for x in conn.execute('SELECT * FROM "'+r['name']+'"')] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        db.delete_deck(self.deck)
        settings._settings['profile_name'] = 'Changed'
        _, recovery = device_backup.restore_backup(path)
        self.assertTrue(Path(recovery).is_file())
        self.assertEqual(settings.get('profile_name'), 'Emir')
        self.assertEqual(custom_tables.list_tables()[0], table)
        with db.get_connection() as conn:
            for name, records in original.items():
                self.assertEqual([tuple(x) for x in conn.execute('SELECT * FROM "'+name+'"')], records, name)

    def test_invalid_backup_does_not_touch_the_library(self):
        ident = self.card()
        path = self.folder/'broken.studycard'
        path.write_bytes(b'broken')
        with self.assertRaises(ValueError):
            device_backup.restore_backup(path)
        self.assertEqual(db.get_card(ident)['term'], 'silence')
        self.assertFalse((self.folder/'backups').exists())

    def test_failed_settings_write_rolls_back_database_and_preferences(self):
        ident = self.card()
        path = self.folder/'full.studycard'
        device_backup.export_backup(path)
        with db.get_connection() as conn:
            conn.execute('UPDATE cards SET term=?,definition=? WHERE id=?', ('updated','güncel',ident))
        before = settings.get_all()
        with patch.object(device_backup.os, 'replace', side_effect=lambda src, dest: (_ for _ in ()).throw(OSError('settings failed')) if str(dest).endswith('settings.json') else os.rename(src, dest)):
            with self.assertRaises(OSError):
                device_backup.restore_backup(path)
        self.assertEqual(db.get_card(ident)['term'], 'updated')
        self.assertEqual(settings.get_all(), before)

    def test_malformed_preferences_are_rejected_before_restoration(self):
        ident = self.card()
        path = self.folder/'full.studycard'
        device_backup.export_backup(path)
        with zipfile.ZipFile(path) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        entries['settings.json'] = json.dumps({'ui_language':'tr','notification_time':'99:99','session_size':10.5})
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        with self.assertRaises(ValueError):
            device_backup.restore_backup(path)
        self.assertEqual(db.get_card(ident)['term'], 'silence')
        self.assertFalse((self.folder/'backups').exists())

    def test_loading_backup_refreshes_the_window_and_invalidates_old_sessions(self):
        self.card()
        self.stack.enter_context(patch.object(MainWindow, '_setup_app_shortcut'))
        self.stack.enter_context(patch.object(MainWindow, '_setup_tray_icon'))
        window = self.view(MainWindow)
        window._is_force_quitting = True
        path = self.folder/'full.studycard'
        device_backup.export_backup(path)
        table = custom_tables.new_table('After backup')
        custom_tables.save_table(table)
        window.view_tables.refresh()
        window.view_study.reload_session(allow_autoplay=False)
        device_backup.restore_backup(path)
        window._backup_restored()
        self.assertIsNone(window.view_tables.document)
        self.assertFalse(window.view_study._session_initialized)
        window.switch_to_study(allow_autoplay=False)
        self.assertTrue(window.view_study._session_initialized)

    def test_speech_order_skip_muted_empty_and_column_reading(self):
        table = custom_tables.new_table('Özel')
        a, b = table['columns']
        a['speech_order'], b['speech_order'] = 2, 1
        table['rows'] = [dict(id='one', name='Bir', cells={a['id']:'go', b['id']:'gitmek'}, muted=[]), dict(id='two', name='İki', cells={a['id']:'eat', b['id']:'yemek'}, muted=[b['id']])]
        self.assertEqual(custom_tables.speech_items(table), [('gitmek','tr'), ('go','en'), ('eat','en')])
        table['reading_order'] = 'columns'
        self.assertEqual(custom_tables.speech_items(table), [('gitmek','tr'), ('go','en'), ('eat','en')])
        a['speech_order'] = 0
        table['repeat'] = 2
        self.assertEqual(custom_tables.speech_items(table), [('gitmek','tr')]*2)

    def test_editing_and_spreadsheet_paste_survive_reopening(self):
        table = custom_tables.new_table('Kelime listem')
        custom_tables.save_table(table)
        view = self.view(CustomTablesView)
        view.table.item(0, 0).setText('go')
        QApplication.clipboard().setText('go\tgitmek\neat\tyemek')
        view.table.setCurrentCell(0, 0)
        from PyQt6.QtCore import Qt
        QTest.keyClick(view.table, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        view.save()
        stored = custom_tables.list_tables()[0]
        self.assertEqual(len(stored['rows']), 2)
        self.assertEqual(stored['rows'][1]['cells'][stored['columns'][1]['id']], 'yemek')

    def test_imitation_loading_returns_without_waiting_and_discards_stale_results(self):
        self.card()
        view = self.view(PracticeView, 'shadowing')
        gate = threading.Event()
        entered = threading.Event()
        def slow(cards, cancelled):
            entered.set()
            gate.wait(2)
            if not cancelled.is_set():
                yield cards[0], [dict(text=cards[0]['example_sentence'], translations={})]
        with patch.object(sentence_memory, 'available_examples', slow):
            start = time.monotonic()
            view.reload_cards(force=True)
            self.assertLess(time.monotonic()-start, .5)
            self.assertTrue(entered.wait(.5))
            self.assertTrue(view._pool_loading)
            view.invalidate_session()
            gate.set()
            QTest.qWait(100)
            self.assertIsNone(view.current_card)
            self.assertEqual(view._remaining, [])

    def test_preferences_are_persisted_and_search_localized(self):
        view = self.view(SettingsView)
        view.extra_controls['profile_name'][0].setText('Emir')
        view.extra_controls['session_size'][0].setValue(25)
        view.extra_controls['speech_speed'][0].setValue(.7)
        with patch.object(view, '_sync_autostart'), patch.object(view, '_sync_desktop_shortcut'):
            view._save_settings()
        self.assertEqual(settings.get('session_size'), 25)
        self.assertEqual(settings.get('speech_speed'), .7)
        view.update_language('de')
        self.assertEqual(view.search_settings.placeholderText(), 'Einstellungen suchen…')
        self.assertEqual(view.extra_controls['theme'][0].itemText(0), 'Schiefer')

    def test_window_has_offline_backup_and_no_active_cloud_coordinator(self):
        self.stack.enter_context(patch.object(MainWindow, '_setup_app_shortcut'))
        self.stack.enter_context(patch.object(MainWindow, '_setup_tray_icon'))
        window = self.view(MainWindow)
        window._is_force_quitting = True
        self.assertFalse(hasattr(window, 'sync_coordinator'))
        self.assertFalse(hasattr(window.view_settings, 'account_panel'))
        window.switch_to_tables()
        self.assertIs(window.content_stack.currentWidget(), window.view_tables)


if __name__ == '__main__':
    unittest.main()
