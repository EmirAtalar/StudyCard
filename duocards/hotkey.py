"""
Study Card - Global Klavye Kısayolu Yöneticisi (Evdev & KWin Wayland/X11 Entegrasyonu).
Uygulama arka planda, simge durumunda veya başka bir pencere odaktayken
kullanıcının seçtiği kısayolu (örn: Ctrl+Alt+S, F9, F10) anında yakalar
ve pencereyi öne getirir / odaklar.
"""

import glob
import os
import struct
import select
import threading
import subprocess
import pathlib
import sys
from typing import Set, Tuple, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from duocards.kwin_helper import run_kwin_script, is_wayland


# Linux input event format
EV_KEY = 0x01
EVENT_FMT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FMT)

# Tuş Kodları (linux/input-event-codes.h)
KEYS = {
    "space": 57, "tab": 15, "enter": 28, "return": 28, "esc": 1, "escape": 1,
    "backspace": 14, "delete": 111, "home": 102, "end": 107,
    "pgup": 104, "pgdown": 109, "up": 103, "down": 108, "left": 105, "right": 106,
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20, "y": 21, "u": 22, "i": 23, "o": 24,
    "p": 25, "a": 30, "s": 31, "d": 32, "f": 33, "g": 34, "h": 35, "j": 36, "k": 37,
    "l": 38, "z": 44, "x": 45, "c": 46, "v": 47, "b": 48, "n": 49, "m": 50,
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63, "f6": 64, "f7": 65, "f8": 66,
    "f9": 67, "f10": 68, "f11": 87, "f12": 88,
}

MODS = {
    "ctrl": (29, 97), "control": (29, 97),
    "shift": (42, 54),
    "alt": (56, 100),
    "meta": (125, 126), "super": (125, 126),
}
ALL_MOD_CODES = {code for pair in MODS.values() for code in pair}


def parse_shortcut(text: str) -> Tuple[Optional[Set[str]], Optional[int]]:
    """'Ctrl+Alt+S' -> ({'ctrl', 'alt'}, 31)"""
    parts = [p.strip().lower() for p in str(text).split("+") if p.strip()]
    if not parts:
        return None, None
    mods = set()
    key = None
    for part in parts:
        if part in MODS:
            mods.add("ctrl" if part == "control" else "super" if part == "meta" else part)
        else:
            k = KEYS.get(part)
            if k is not None:
                key = k
    if key is None:
        return None, None
    return mods, key


class GlobalHotkeyListener(QObject):
    """
    Linux /dev/input üzerinden arka planda tuş kombinasyonunu dinleyen
    ve masaüstünün herhangi bir yerinden basıldığında anında tetiklenen servis.
    """
    triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._target_mods: Set[str] = set()
        self._target_key: Optional[int] = None
        self._current_shortcut_str = ""

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_shortcut(self, shortcut_str: str) -> bool:
        """Kısayolu günceller ve dinleyiciyi başlatır/yeniler."""
        self.stop()
        self._current_shortcut_str = shortcut_str.strip()
        if not self._current_shortcut_str or not sys.platform.startswith("linux"):
            return False

        mods, key = parse_shortcut(self._current_shortcut_str)
        if key is None:
            return False

        self._target_mods = mods or set()
        self._target_key = key

        devices = self._open_devices()
        if not devices:
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, args=(devices,), daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Dinleyiciyi temizce durdurur."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _open_devices(self):
        if not sys.platform.startswith("linux"):
            return []
        fds = []
        for path in sorted(glob.glob("/dev/input/event*")):
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
                fds.append(fd)
            except OSError:
                continue
        return fds

    def _loop(self, fds):
        held_mod_codes = set()
        try:
            while not self._stop_event.is_set():
                ready, _, _ = select.select(fds, [], [], 0.15)
                for fd in ready:
                    try:
                        data = os.read(fd, EVENT_SIZE * 64)
                    except (BlockingIOError, OSError):
                        continue
                    for offset in range(0, len(data) - EVENT_SIZE + 1, EVENT_SIZE):
                        _s, _us, etype, code, value = struct.unpack(
                            EVENT_FMT, data[offset:offset + EVENT_SIZE]
                        )
                        if etype != EV_KEY:
                            continue

                        # Değiştirici tuşlar (Ctrl, Alt, Shift, Super)
                        if code in ALL_MOD_CODES:
                            if value:
                                held_mod_codes.add(code)
                            else:
                                held_mod_codes.discard(code)
                        elif value == 1:  # Tuşa basıldı
                            if code == self._target_key:
                                if self._mods_match(held_mod_codes, self._target_mods):
                                    self.triggered.emit()
        finally:
            for fd in fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

    @staticmethod
    def _mods_match(held_codes: Set[int], wanted_mods: Set[str]) -> bool:
        for mod_name, code_pair in MODS.items():
            if mod_name in ("control", "super"):
                continue
            is_pressed = any(c in held_codes for c in code_pair)
            should_be_pressed = (mod_name in wanted_mods)
            if is_pressed != should_be_pressed:
                return False
        return True


def toggle_app_window(window=None):
    """
    Wayland ve X11 ortamında Study Card penceresini öne getirir veya simge durumuna küçültür.
    """
    # Gizli / arka plandaki pencereyi önce görünür kıl
    if window:
        try:
            if not window.isVisible():
                window.showNormal()
                window.raise_()
                window.activateWindow()
        except Exception:
            pass

    # 1. KWin Scripting ile Wayland üzerinde güvenli odaklama ve getirme
    js = """
    var windows = workspace.stackingOrder;
    for (var i = 0; i < windows.length; ++i) {
        var win = windows[i];
        if (win && win.caption && win.caption.indexOf("Study Card") !== -1 && 
            win.caption.indexOf("Notification") === -1 && 
            win.caption.indexOf("Widget") === -1 &&
            win.caption.indexOf("Mini") === -1) {
            if (workspace.activeWindow === win && !win.minimized) {
                win.minimized = true;
            } else {
                win.minimized = false;
                workspace.activeWindow = win;
            }
            break;
        }
    }
    """
    run_kwin_script(js, "study_card_toggle")

    # 2. Qt pencere metotları
    if window:
        try:
            if window.isMinimized() or not window.isVisible():
                window.showNormal()
            window.raise_()
            window.activateWindow()
        except Exception:
            pass


def sync_system_shortcut(shortcut_str: str):
    """Register a desktop launcher and KDE shortcut for this profile."""
    if not sys.platform.startswith("linux"):
        return
    from duocards.paths import APP_ID, PROFILE_DIR, PROJECT_DIR

    val = shortcut_str.strip()
    data_dir = os.environ.get("XDG_DATA_HOME") or pathlib.Path.home() / ".local/share"
    apps_dir = pathlib.Path(data_dir) / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_name = f"{APP_ID}.desktop"
    desktop_file = apps_dir / desktop_name
    launcher = PROJECT_DIR / "run.sh"
    icon_file = PROJECT_DIR / "assets" / "icon.png"

    content = f"""[Desktop Entry]
Type=Application
Name=Study Card
Comment=Study Card Flashcards Desktop App
Exec=env "STUDYCARD_HOME={PROFILE_DIR}" "{launcher}"
Icon={icon_file if icon_file.exists() else "accessories-dictionary"}
Terminal=false
Categories=Utility;Education;
StartupNotify=false
X-KDE-GlobalAccel-CommandShortcut=true
"""
    try:
        desktop_file.write_text(content, encoding="utf-8")
        os.chmod(str(desktop_file), 0o755)
    except Exception:
        pass

    # 3. KDE Plasma kglobalshortcutsrc ve kbuildsycoca6
    kwrite_bin = "/usr/bin/kwriteconfig6"
    if os.path.exists(kwrite_bin):
        try:
            sc_val = val if val else "none"
            subprocess.run([
                kwrite_bin, "--notify", "--file", "kglobalshortcutsrc",
                "--group", "services", "--group", desktop_name,
                "--key", "_launch", sc_val
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists("/usr/bin/kbuildsycoca6"):
                subprocess.run(["/usr/bin/kbuildsycoca6"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


# Global Singleton Listener
global_hotkey = GlobalHotkeyListener()
