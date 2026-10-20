"""Platform boundaries, login launchers and native sound effects."""

import os
from pathlib import Path
import plistlib
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QCloseEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget

from duocards import autostart, hotkey, kwin_helper
from duocards.paths import APP_ID, PROFILE_DIR
from duocards.settings import settings
from duocards.sfx import SFXPlayer
from duocards.main_window import MainWindow
from duocards.widgets.title_bar import CustomTitleBar


class WindowWithoutPages(MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self._manual_resize = None
        self.view_tables = Mock()
        self.tray_icon = None
        self._is_force_quitting = False


class AutostartTests(unittest.TestCase):
    def test_linux_uses_xdg_autostart_and_can_disable_it(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch("duocards.autostart.sys.platform", "linux"), \
                patch.dict(os.environ, {"XDG_CONFIG_HOME": directory}):
            path = Path(directory) / "autostart" / f"{APP_ID}.desktop"
            self.assertFalse(autostart.is_enabled())
            self.assertTrue(autostart.set_enabled(True))
            self.assertIn(f'STUDYCARD_HOME={PROFILE_DIR}', path.read_text())
            self.assertTrue(autostart.is_enabled())
            autostart.set_enabled(False)
            self.assertFalse(path.exists())

    def test_macos_writes_a_launch_agent_with_separate_arguments(self):
        with tempfile.TemporaryDirectory(prefix="studycard mac ") as directory, \
                patch("duocards.autostart.sys.platform", "darwin"), \
                patch("duocards.autostart.Path.home", return_value=Path(directory)), \
                patch("duocards.autostart.sys.executable", "/Python With Spaces/bin/python3"):
            path = Path(directory) / "Library" / "LaunchAgents" / f"com.studycard.{APP_ID}.plist"
            self.assertFalse(autostart.is_enabled())
            self.assertTrue(autostart.set_enabled(True))
            job = plistlib.loads(path.read_bytes())
            self.assertEqual(job["Label"], f"com.studycard.{APP_ID}")
            self.assertEqual(job["ProgramArguments"][0], "/Python With Spaces/bin/python3")
            self.assertEqual(job["ProgramArguments"][-1], "--minimized")
            self.assertEqual(job["EnvironmentVariables"]["STUDYCARD_HOME"], str(PROFILE_DIR))
            self.assertTrue(job["RunAtLoad"])
            self.assertTrue(autostart.is_enabled())
            autostart.set_enabled(False)
            self.assertFalse(path.exists())

    def test_other_platforms_do_not_create_linux_login_files(self):
        with patch("duocards.autostart.sys.platform", "win32"):
            self.assertIsNone(autostart.autostart_path())
            self.assertFalse(autostart.set_enabled(True))


class DesktopPlatformTests(unittest.TestCase):
    def test_macos_does_not_open_linux_input_devices_or_write_desktop_entries(self):
        listener = hotkey.GlobalHotkeyListener()
        with patch("duocards.hotkey.sys.platform", "darwin"), \
                patch("duocards.hotkey.glob.glob") as devices, \
                patch("duocards.hotkey.pathlib.Path.mkdir") as mkdir, \
                patch("duocards.hotkey.subprocess.run") as command:
            self.assertFalse(listener.set_shortcut("Ctrl+Alt+S"))
            self.assertEqual(listener._open_devices(), [])
            hotkey.sync_system_shortcut("Ctrl+Alt+S")
            devices.assert_not_called()
            mkdir.assert_not_called()
            command.assert_not_called()

    def test_kwin_commands_are_skipped_on_macos_and_gnome(self):
        for platform, desktop in (("darwin", "KDE"), ("linux", "GNOME")):
            with self.subTest(platform=platform, desktop=desktop), \
                    patch("duocards.kwin_helper.sys.platform", platform), \
                    patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": desktop}, clear=True), \
                    patch("duocards.kwin_helper.subprocess.run") as command:
                self.assertFalse(kwin_helper.run_kwin_script("print('unused')"))
                kwin_helper.set_kwin_keep_above("Study Card Mini", True)
                kwin_helper.position_kwin_bottom_right("Study Card Mini")
                command.assert_not_called()

    def test_qt_headless_sessions_do_not_change_kwin_settings(self):
        with patch("duocards.kwin_helper.sys.platform", "linux"), \
                patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE", "QT_QPA_PLATFORM": "offscreen"}), \
                patch("duocards.kwin_helper.subprocess.run") as command:
            self.assertFalse(kwin_helper.run_kwin_script("print('unused')"))
            command.assert_not_called()

    def test_qdbus6_is_found_on_desktops_without_a_qdbus_alias(self):
        with patch("duocards.kwin_helper.shutil.which", side_effect=lambda name: "/qt/bin/qdbus6" if name == "qdbus6" else None):
            self.assertEqual(kwin_helper._qdbus_binary(), "/qt/bin/qdbus6")


class NativeSoundAndWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_sound_effects_reuse_the_native_player_and_update_volume(self):
        player = SFXPlayer()
        self.addCleanup(player.deleteLater)
        with patch("duocards.sfx.QSoundEffect") as sound, \
                patch.dict(settings._settings, {"sfx_enabled": True, "sfx_volume": 25}):
            player.play_click()
            self.assertEqual(sound.call_count, 1)
            self.assertTrue(sound.return_value.setSource.call_args.args[0].toLocalFile().endswith("click.wav"))
            sound.return_value.setVolume.assert_called_with(0.25)
            settings._settings["sfx_volume"] = 60
            player.play_click()
            self.assertEqual(sound.call_count, 1)
            sound.return_value.setVolume.assert_called_with(0.6)
            self.assertEqual(sound.return_value.play.call_count, 2)

    def test_disabled_sounds_and_missing_files_do_not_create_audio_players(self):
        player = SFXPlayer()
        self.addCleanup(player.deleteLater)
        with patch("duocards.sfx.QSoundEffect") as sound, \
                patch.dict(settings._settings, {"sfx_enabled": False}):
            player.play_click()
            settings._settings["sfx_enabled"] = True
            player._play_file("missing-effect.wav")
            sound.assert_not_called()

    def test_audio_requests_from_a_worker_return_to_the_qt_thread(self):
        player = SFXPlayer()
        self.addCleanup(player.deleteLater)
        with patch("duocards.sfx.QSoundEffect") as sound, \
                patch.dict(settings._settings, {"sfx_enabled": True}):
            worker = threading.Thread(target=player.play_click)
            worker.start()
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            sound.assert_not_called()
            self.app.processEvents()
            sound.return_value.play.assert_called_once()

    def test_title_bar_can_drag_when_native_window_movement_is_unavailable(self):
        window = QWidget()
        self.addCleanup(window.deleteLater)
        title_bar = CustomTitleBar(window)
        handle = Mock()
        handle.startSystemMove.return_value = False
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress, QPointF(10, 10), QPointF(100, 100),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        )
        with patch.object(window, "windowHandle", return_value=handle):
            title_bar.mousePressEvent(event)
        self.assertIsNotNone(title_bar._drag_pos)

    def test_window_resizes_when_the_platform_cannot_start_native_resizing(self):
        window = WindowWithoutPages()
        self.addCleanup(window.deleteLater)
        window.setMinimumSize(100, 80)
        window.setGeometry(100, 100, 300, 200)
        start = window.mapToGlobal(window.rect().bottomRight())
        handle = Mock()
        handle.startSystemResize.return_value = False
        press = QMouseEvent(
            QEvent.Type.MouseButtonPress, QPointF(299, 199), QPointF(start),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        )
        with patch.object(window, "windowHandle", return_value=handle):
            window.mousePressEvent(press)
        move = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(349, 229), QPointF(start.x() + 50, start.y() + 30),
            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        )
        window.mouseMoveEvent(move)
        self.assertEqual((window.width(), window.height()), (350, 230))

    def test_background_setting_does_not_hide_the_app_without_a_system_tray(self):
        window = WindowWithoutPages()
        self.addCleanup(window.deleteLater)
        event = QCloseEvent()
        with patch.dict(settings._settings, {"run_in_background": True}), \
                patch("duocards.main_window.global_hotkey.stop"):
            window.closeEvent(event)
        self.assertTrue(event.isAccepted())


if __name__ == "__main__":
    unittest.main()
