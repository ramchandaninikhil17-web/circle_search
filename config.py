r"""Settings: hotkey config + user prefs, persisted to %APPDATA%\CircleSearch\settings.json"""
import json
import os

APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
CONFIG_DIR = os.path.join(APPDATA, "CircleSearch")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# win32con MOD_* values
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

DEFAULT_SETTINGS = {
    # Unique triple-modifier combo: virtually guaranteed to not collide with
    # Windows, Office, or browser shortcuts (those almost never use 3 mods).
    "hotkey_mods": MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
    "hotkey_vk": 0x43,  # 'C' (for "Circle")
    "hotkey_label": "Ctrl+Alt+C",
    "auto_open_browser": True,
    "keep_screenshots": False,
    "ocr_min_chars_for_text_suggestion": 4,
}


def load_settings() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
