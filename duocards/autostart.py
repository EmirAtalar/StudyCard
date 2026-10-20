"""Login launchers for Linux desktops and macOS."""

import os
from pathlib import Path
import plistlib
import sys

from duocards.paths import APP_ID, PROFILE_DIR, PROJECT_DIR


def autostart_path():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "LaunchAgents" / f"com.studycard.{APP_ID}.plist"
    if sys.platform.startswith("linux"):
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        return config_dir / "autostart" / f"{APP_ID}.desktop"
    return None


def is_enabled():
    path = autostart_path()
    return path is not None and path.is_file()


def set_enabled(enabled):
    path = autostart_path()
    if path is None:
        return False
    if not enabled:
        path.unlink(missing_ok=True)
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        # Use the current interpreter so launchd does not depend on a shell's PATH.
        job = {
            "Label": f"com.studycard.{APP_ID}",
            "ProgramArguments": [sys.executable, str(PROJECT_DIR / "main.py"), "--minimized"],
            "WorkingDirectory": str(PROJECT_DIR),
            "EnvironmentVariables": {
                "STUDYCARD_HOME": str(PROFILE_DIR),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
            },
            "RunAtLoad": True,
        }
        path.write_bytes(plistlib.dumps(job))
    else:
        path.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Study Card\n"
            f'Exec=env "STUDYCARD_HOME={PROFILE_DIR}" "{PROJECT_DIR / "run.sh"}" --minimized\n'
            "Icon=accessories-dictionary\n"
            "Terminal=false\n"
            "Categories=Utility;Education;\n"
            "StartupNotify=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
    return True
