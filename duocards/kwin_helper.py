"""
Study Card - KWin & Wayland Pencere Yöneticisi Entegrasyonu
KDE Plasma 6 (Wayland & X11) ortamında pencerelerin 'Her Zaman En Üstte' (Always on Top)
kalmasını ve pencerelerin masaüstünün istenen konumuna (örneğin sağ alt köşeye)
yerleştirilmesini işletim sistemi ve pencere yöneticisi düzeyinde garantiler.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time


def is_wayland() -> bool:
    return sys.platform.startswith("linux") and (
        os.environ.get("XDG_SESSION_TYPE") == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))
    )


def is_kwin_session() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    if os.environ.get("QT_QPA_PLATFORM", "").split(":", 1)[0] in {"offscreen", "minimal"}:
        return False
    desktops = os.environ.get("XDG_CURRENT_DESKTOP", "").upper().split(":")
    return bool(set(desktops) & {"KDE", "PLASMA"}) or bool(os.environ.get("KDE_SESSION_VERSION"))


def _qdbus_binary():
    for name in ("qdbus6", "qdbus-qt6", "qdbus"):
        binary = shutil.which(name)
        if binary:
            return binary
    for binary in ("/usr/lib/qt6/bin/qdbus", "/usr/lib64/qt6/bin/qdbus"):
        if os.access(binary, os.X_OK):
            return binary
    return None


def run_kwin_script(js_code: str, script_name: str = "study_card_kwin") -> bool:
    """KWin Scripting API üzerinden anında JavaScript kodu çalıştırır ve temizler."""
    if not is_kwin_session():
        return False
    qdbus_bin = _qdbus_binary()
    if qdbus_bin is None:
        return False
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js_code)
            tmp_path = f.name

        unique_name = f"{script_name}_{int(time.time() * 1000)}"
        
        load_out = subprocess.run(
            [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", tmp_path, unique_name],
            capture_output=True, text=True, timeout=2
        )
        if load_out.returncode != 0:
            return False
            
        sid = load_out.stdout.strip()
        subprocess.run(
            [qdbus_bin, "org.kde.KWin", f"/Scripting/Script{sid}", "org.kde.kwin.Script.run"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
        )
        subprocess.run(
            [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", unique_name],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
        )
        return True
    except Exception:
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def set_kwin_keep_above(title_substring: str, enabled: bool):
    """
    KDE Plasma KWin pencere yöneticisinde pencerenin her zaman en üstte kalmasını
    hem çalışan pencere üzerinde hem de kalıcı KWin kurallarında anında günceller.
    """
    if not is_kwin_session():
        return
    # 1. KWin kurallarını ~/.config/kwinrulesrc dosyasına yaz
    try:
        kwrite_bin = shutil.which("kwriteconfig6")
        rule_id = "study-card-mini-rule"
        if kwrite_bin:
            val = "true" if enabled else "false"
            rule_mode = "2" if enabled else "0"  # 2: Force, 0: Do Not Affect
            
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", "General", "--key", "rules", rule_id], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", rule_id, "--key", "Description", "Study Card Mini Always On Top"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", rule_id, "--key", "title", title_substring], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", rule_id, "--key", "titlematch", "2"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", rule_id, "--key", "above", val], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([kwrite_bin, "--file", "kwinrulesrc", "--group", rule_id, "--key", "aboverule", rule_mode], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Reconfigure çağrısı kuralları yeniler
            qdbus_bin = _qdbus_binary()
            if qdbus_bin:
                subprocess.run([qdbus_bin, "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Çalışan pencere üzerinde anında bellekte keepAbove değerini güncelle
    bool_str = "true" if enabled else "false"
    js = f"""
    var windows = workspace.stackingOrder;
    for (var i = 0; i < windows.length; ++i) {{
        var win = windows[i];
        if (win.caption && win.caption.indexOf("{title_substring}") !== -1) {{
            win.keepAbove = {bool_str};
        }}
    }}
    """
    run_kwin_script(js, "keep_above_updater")


def position_kwin_bottom_right(title_substring: str, width: int = 320, height: int = 68, margin_right: int = 16, margin_bottom: int = 16):
    """
    Wayland ortamında KWin pencere yöneticisi üzerinden pencereyi ekranın sağ alt köşesine konumlandırır
    ve en üstte kalmasını sağlar.
    """
    if not is_kwin_session():
        return
    js = f"""
    var windows = workspace.stackingOrder;
    for (var i = 0; i < windows.length; ++i) {{
        var win = windows[i];
        if (win.caption && win.caption.indexOf("{title_substring}") !== -1) {{
            var screenGeo = workspace.clientArea(0, win);
            var targetX = screenGeo.x + screenGeo.width - {width + margin_right};
            var targetY = screenGeo.y + screenGeo.height - {height + margin_bottom};
            win.frameGeometry = {{ x: targetX, y: targetY, width: {width}, height: {height} }};
            win.keepAbove = true;
        }}
    }}
    """
    run_kwin_script(js, "bottom_right_positioner")
