"""Load and save preferences for the current profile."""

import os
import json
from typing import Any, Dict
from duocards.paths import CONFIG_DIR

SETTINGS_DIR = str(CONFIG_DIR)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "ui_language": "en",  # Varsayılan dil: İngilizce
    "sfx_enabled": True,
    "sfx_volume": 80,
    "auto_pronounce": False,
    "pronounce_trigger": "flip",  # 'flip' (kart çevrildiğinde), 'appear' (kelime ilk çıktığında) veya 'both'
    "daily_goal": 10,
    "theme": "dark_slate",
    "widget_enabled": False,
    "daily_notification_enabled": False,
    "notification_time": "20:00",
    "autostart_enabled": False,
    "app_shortcut": "Ctrl+Alt+S",
    "profile_name": "",
    "accent_color": "#10b981",
    "text_scale": 100,
    "reduced_motion": False,
    "speech_speed": 1.0,
    "speech_volume": 100,
    "audio_prefetch": True,
    "practice_autoplay": True,
    "practice_auto_next": True,
    "practice_advance_ms": 300,
    "session_size": 50,
    "shuffle_cards": True,
    "show_phonetics": True,
    "show_card_notes": True,
    "startup_page": "study",
    "run_in_background": False,
}


class SettingsManager:
    def __init__(self):
        self._settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cleaned = {k: v for k, v in data.items()
                               if not k.startswith(("ai_", "ollama_")) and k != "menu_visible_ai"}
                    self._settings.update(cleaned)
                    if cleaned != data:
                        self.save()
            except Exception:
                pass

    def save(self):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.save()

    def update(self, values):
        self._settings.update(values)
        self.save()

    def get_all(self) -> Dict[str, Any]:
        return dict(self._settings)


settings = SettingsManager()
