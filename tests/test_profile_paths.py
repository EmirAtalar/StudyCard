"""Check that a new checkout cannot load another profile's saved data."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProfilePathsTests(unittest.TestCase):
    def run_in_profile(self, directory, script):
        import sys

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env={**os.environ, "STUDYCARD_HOME": str(directory),
                 "XDG_DATA_HOME": str(directory / "system-data"),
                 "XDG_CONFIG_HOME": str(directory / "system-config"),
                 "XDG_CACHE_HOME": str(directory / "system-cache"),
                 "QT_QPA_PLATFORM": "offscreen",
                 "PYTHONDONTWRITEBYTECODE": "1"},
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return json.loads(result.stdout)

    def test_importing_paths_does_not_create_profile_files(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "unused"
            result = self.run_in_profile(profile, """
import json
from duocards.paths import PROFILE_DIR
from duocards.settings import settings
print(json.dumps({'exists': PROFILE_DIR.exists(),
                  'profile_name': settings.get('profile_name')}))
""")
            self.assertEqual(result, {"exists": False, "profile_name": ""})

    def test_new_profile_has_no_personal_settings_or_study_history(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            self.run_in_profile(first, """
import json
from duocards import db
from duocards.settings import settings
db.init_db()
db.add_deck('Private deck')
settings.set('profile_name', 'Private profile')
print(json.dumps(True))
""")
            result = self.run_in_profile(second, """
import json
from duocards import db
from duocards.paths import PROFILE_DIR
from duocards.settings import settings
from duocards.sync import SyncClient
db.init_db()
with db.get_connection() as connection:
    counts = {table: connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
              for table in ('study_logs', 'timer_sessions', 'quiz_mistakes')}
print(json.dumps({'name': settings.get('profile_name'), 'history': counts,
    'private_deck': any(d['name'] == 'Private deck' for d in db.get_all_decks()),
    'account_file_exists': SyncClient().session_path.exists(),
    'database_in_profile': str(db.DB_PATH).startswith(str(PROFILE_DIR) + '/')}))
""")
            self.assertEqual(result["name"], "")
            self.assertFalse(result["private_deck"])
            self.assertFalse(result["account_file_exists"])
            self.assertTrue(result["database_in_profile"])
            self.assertTrue(all(count == 0 for count in result["history"].values()))

    def test_profiles_use_different_window_sockets(self):
        with tempfile.TemporaryDirectory() as directory:
            script = """
import json
from duocards.paths import IPC_SOCKET_NAME
print(json.dumps(IPC_SOCKET_NAME))
"""
            first = self.run_in_profile(Path(directory) / "first", script)
            second = self.run_in_profile(Path(directory) / "second", script)
            self.assertNotEqual(first, second)
            self.assertNotEqual(first, "study-card-ipc-socket")

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux desktop launcher")
    def test_desktop_integration_keeps_launchers_out_of_the_source_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_in_profile(Path(directory) / "profile with spaces", """
import json
from pathlib import Path
from unittest.mock import patch
from duocards.hotkey import sync_system_shortcut
from duocards.paths import APP_ID, PROFILE_DIR, PROJECT_DIR
from duocards.widgets.settings_view import SettingsView
import os
toggle = PROJECT_DIR / 'toggle.sh'
before = toggle.read_bytes()
with patch('duocards.hotkey.subprocess.run'):
    sync_system_shortcut('Ctrl+Alt+S')
SettingsView._sync_autostart(None, True)
launcher = Path(os.environ['XDG_DATA_HOME']) / 'applications' / (APP_ID + '.desktop')
autostart = Path(os.environ['XDG_CONFIG_HOME']) / 'autostart' / (APP_ID + '.desktop')
expected = 'Exec=env "STUDYCARD_HOME=' + str(PROFILE_DIR) + '" "' + str(PROJECT_DIR / 'run.sh') + '"'
print(json.dumps({'source_unchanged': toggle.read_bytes() == before,
                  'launcher_uses_profile': expected in launcher.read_text(),
                  'autostart_uses_profile': expected + ' --minimized' in autostart.read_text()}))
SettingsView._sync_autostart(None, False)
""")
            self.assertTrue(result["source_unchanged"])
            self.assertTrue(result["launcher_uses_profile"])
            self.assertTrue(result["autostart_uses_profile"])


if __name__ == "__main__":
    unittest.main()
