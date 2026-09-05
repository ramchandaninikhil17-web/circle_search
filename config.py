r"""Settings: hotkey config + user prefs, persisted to %APPDATA%\CircleSearch\settings.json"""
import json
import os
import winreg

APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
CONFIG_DIR = os.path.join(APPDATA, "CircleSearch")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# win32con MOD_* values
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_APP_NAME = "CircleToSearchWindows"

DEFAULT_SETTINGS = {
    # Unique combo: Ctrl+Alt+C
    "hotkey_mods": MOD_CONTROL | MOD_ALT | MOD_NOREPEAT,
    "hotkey_vk": 0x43,  # 'C'
    "hotkey_label": "Ctrl+Alt+C",
    "auto_open_browser": True,
    "keep_screenshots": False,
    "ocr_min_chars_for_text_suggestion": 2,
    "preferred_mode": "circle",  # "circle" or "rect"
    "start_with_windows": False,
}


def is_autostart_enabled() -> bool:
    """Checks if Circle to Search is registered in Windows Startup registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, REG_APP_NAME)
            return bool(val)
    except OSError:
        return False


def set_autostart_enabled(enabled: bool) -> bool:
    """Registers or unregisters Circle to Search in Windows Startup."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
            if enabled:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                vbs_path = os.path.join(base_dir, "run.vbs")
                if os.path.exists(vbs_path):
                    cmd = f'wscript.exe "{vbs_path}"'
                else:
                    main_py = os.path.join(base_dir, "main.py")
                    cmd = f'pythonw.exe "{main_py}" --tray'
                winreg.SetValueEx(key, REG_APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, REG_APP_NAME)
                except OSError:
                    pass
        return True
    except Exception:
        return False


def _clean_label(label: str, vk: int) -> str:
    if not label or any(ord(c) < 32 for c in label):
        letter = chr(vk) if (0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39) else "C"
        return f"Ctrl+Alt+{letter}"
    return label


def load_settings() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    merged = dict(DEFAULT_SETTINGS)
    merged["start_with_windows"] = is_autostart_enabled()

    if not os.path.exists(CONFIG_FILE):
        save_settings(merged)
        return merged
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged.update(data)
        merged["start_with_windows"] = is_autostart_enabled()
        merged["hotkey_label"] = _clean_label(merged.get("hotkey_label", ""), merged.get("hotkey_vk", 0x43))
        return merged
    except Exception:
        return merged


def save_settings(settings: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
