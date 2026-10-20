"""Executable mobile rules and the desktop SQLite interchange contract."""
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'android'


class AndroidModelTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'A JDK is required')
    def test_all_game_modes_and_speech_plan_on_jvm(self):
        with tempfile.TemporaryDirectory() as directory:
            source = ANDROID / 'app/src/main/java/com/studycard/app'
            subprocess.run(['javac', '--release', '8', '-d', directory,
                            str(source / 'GameEngine.java'), str(source / 'TableSpeechPlan.java'),
                            str(ANDROID / 'tools/ModelTests.java')], check=True, capture_output=True)
            result = subprocess.run(['java', '-cp', directory, 'com.studycard.app.ModelTests'],
                                    check=True, capture_output=True, text=True)
            self.assertIn('63 assertions', result.stdout)

    def test_mobile_export_schema_can_be_opened_by_desktop(self):
        from duocards import db, device_backup
        from duocards.custom_tables import new_table
        from duocards.custom_games import new_game
        import zipfile
        source = (ANDROID / 'app/src/main/java/com/studycard/app/DesktopBackup.java').read_text()
        schema = re.search(r'String\[\] sql\s*=\s*\{(.*?)\};', source, re.S).group(1)
        statements = [json.loads('"' + value + '"') for value in re.findall(r'"((?:[^"\\]|\\.)*)"', schema)]
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / 'library.sqlite'
            with sqlite3.connect(snapshot) as connection:
                for statement in statements:
                    connection.execute(statement)
                connection.execute("INSERT INTO decks(id,name) VALUES(1,'Mobile deck')")
                connection.execute("INSERT INTO cards(id,deck_id,term,definition,source_lang,target_lang,status,due_date,created_at) VALUES(1,1,'apple','elma','en','tr','new','2026-10-14','2026-10-14')")
                connection.execute("INSERT INTO study_logs(card_id,rating,reviewed_at) VALUES(1,3,'2026-10-14')")
                connection.execute("INSERT INTO practice_attempts(card_id,mode,correct,answer,expected,practiced_at,day) VALUES(1,'typing',1,'elma','elma','2026-10-14','2026-10-14')")
                connection.execute("INSERT INTO timer_sessions(mode,duration_seconds,notes,created_at) VALUES('timer',1500,'Focus','2026-10-14')")
                table = new_table('Mobile table')
                connection.execute('INSERT INTO custom_tables(id,name,data) VALUES(?,?,?)', (table['id'], table['name'], json.dumps(table)))
                game = new_game()
                game.update(name='Mobile game', mode='audio_dictation', source='library', source_id='1')
                connection.execute('INSERT INTO custom_games(id,name,data) VALUES(?,?,?)', (game['id'], game['name'], json.dumps(game)))
                counts = {name: connection.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                          for name in ('cards', 'decks', 'study_logs', 'timer_sessions', 'practice_attempts')}
            archive = Path(directory) / 'mobile.studycard'
            with zipfile.ZipFile(archive, 'w') as output:
                output.write(snapshot, 'library.sqlite')
                output.writestr('manifest.json', json.dumps(dict(format='studycard-device-backup', version=1, counts=counts)))
                output.writestr('settings.json', json.dumps({'personal_menu_game_' + game['id']: True, 'speech_speed': 1.25}))
            self.assertEqual(device_backup.inspect_backup(archive)['counts'], counts)
            with patch.object(db, 'DB_PATH', str(snapshot)), patch.object(db, 'DB_DIR', directory):
                db.init_db()
            with sqlite3.connect(snapshot) as connection:
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM cards').fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT generation,baseline FROM sync_items WHERE entity='card'").fetchone(), (1, '{}'))
                connection.execute("UPDATE cards SET notes='Opened on desktop' WHERE id=1")
                self.assertEqual(connection.execute("SELECT generation FROM sync_items WHERE entity='card'").fetchone()[0], 2)
                connection.execute('PRAGMA foreign_keys=ON')
                connection.commit()
                connection.execute('PRAGMA foreign_keys=ON')
                connection.execute('DELETE FROM decks WHERE id=1')
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM cards').fetchone()[0], 0)
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM study_logs').fetchone()[0], 0)
                self.assertIsNone(connection.execute('SELECT card_id FROM practice_attempts').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
