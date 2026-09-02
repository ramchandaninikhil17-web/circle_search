# Circle to Search - Windows

A local, phone-like "Circle to Search" for Windows: hotkey → drag a
selection anywhere on screen → instant Google Lens visual search / OCR text / Copy.
No cloud AI, no API keys, no backend - just Windows-native APIs + your
browser.

## Requirements
- Windows 10/11
- Python 3.10+ (only needed to build/run from source; the built .exe needs nothing)
- English (or your language) OCR pack installed: **Settings → Time & Language
  → Language & region → your language → Options → Install (Handwriting/OCR)**.
  This ships by default on most systems.

## Run from source
```
pip install -r requirements.txt
python main.py
```

## Build a standalone .exe (no Python needed to run it)
```
build.bat
```
Output: `dist\CircleSearch.exe`. Optionally drop a shortcut to it in
`shell:startup` to launch it at login (still idle-light: one tray icon + one
blocked hotkey thread).

## Using it
1. Press the hotkey (default **Ctrl+Alt+Shift+C** - a three-modifier combo
   chosen specifically so it won't collide with Windows, Office, browser, or
   most app shortcuts, which almost never use three modifiers at once) or click the tray icon.
2. Drag a rectangle around anything on screen.
3. A small toolbar appears next to the selection:
   - **Google Lens** - uploads the crop directly to Google Lens and opens the results page in your default browser.
   - **Text** - shows OCR'd text (auto-highlighted if confident text was
     found) with Copy / Search Google.
   - **Copy** - copies the image (or OCR'd text if already read) to the clipboard.
   - **✕** or **Esc** or **right-click** - cancel.
4. Nothing is written to disk. Screenshots exist only in memory for the
   current selection and are dropped when the toolbar closes.

## Changing the hotkey
Tray icon → **Settings…** → click the box → press your new combo (must
include Ctrl/Alt/Shift/Win) → Save. Takes effect immediately, no restart.

### About the Copilot key
Windows does not currently expose a public API to intercept the dedicated
Copilot key directly as a global hotkey. The reliable, non-hacky path:
remap it in Windows to send a normal shortcut, then use that shortcut here:

**Settings → Bluetooth & devices → Keyboard (or via `Copilot+ key` policy /
`HKCU\Software\Microsoft\Windows\CurrentVersion\WinKeyRemap` on machines that
expose it) → set the Copilot key to launch/send `Ctrl+Alt+Shift+C`** (or
whatever you configured above). Once remapped, pressing the physical Copilot
key triggers this tool. This avoids fragile low-level keyboard hooks that
fight with Windows' own handling of that key.

## Architecture
```
hotkey.py          -> Win32 RegisterHotKey, blocks on GetMessage (no polling)
capture.py         -> DPI-aware Qt native virtual-desktop grab, multi-monitor safe
overlay.py         -> frameless translucent QWidget, 1:1 pixel-perfect selection
toolbar.py         -> floating action bar, async Google Lens worker & OCR thread
ocr.py             -> Windows.Media.Ocr via winrt (or winsdk) - fully local
image_search.py    -> Google Lens v3 upload & search redirect handling
tray.py            -> system tray icon/menu with click activation
settings_dialog.py -> hotkey remapping UI
config.py          -> settings persisted to %APPDATA%\CircleSearch\settings.json
main.py            -> wires it all together
```

## Design notes / guarantees
- **No background capture loop.** The screen is only grabbed the instant the
  hotkey fires.
- **No telemetry, history, or saved screenshots** unless you explicitly flip
  "Keep screenshots" in Settings.
- **Multi-monitor & High-DPI**: capture uses Qt's native multi-monitor grabber
  with Per-Monitor DPI Aware V2, so selections stay 1:1 pixel-accurate on
  100%, 125%, 150%, 200% displays with zero zooming or cut-off edges.
- **Graceful failure**: OCR failures return empty text; upload failures copy
  the image to the clipboard and open Google Lens so you can instantly press Ctrl+V.
- **Local & Private**: No cloud AI, no database, no backend.
