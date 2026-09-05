# Circle to Search - Windows

A fast, phone-like "Circle to Search" for Windows: hotkey → circle or drag a selection anywhere on screen → instant Google Lens visual search / local OCR text / Copy.

No cloud AI, no third-party account needed, 100% private: Windows-native APIs + direct Google Lens in your browser.

---

## Highlights & Features

- ⭕ **Circle / Freeform Lasso**: Draw a smooth glowing loop around any object, image, or text (just like Circle to Search on modern phones).
- ◻️ **Precision Rectangle**: Drag a crystal-clear box with live pixel dimension badges.
- 🖥️ **1-Click Fullscreen**: Instant full-monitor capture.
- 🚀 **Zero-Lag Architecture**: Pre-rendered textures composite at 60–144+ FPS with zero mouse stutter, even on 4K and multi-monitor setups.
- 🔒 **Private Direct Google Lens**: Snips upload directly to Google Lens (`lens.google.com/v3/upload`) with zero third-party cloud hosting leaks.
- ⚡ **Local Windows OCR**: Uses Windows' built-in `Windows.Media.Ocr` engine for instantaneous, offline text recognition.
- 🔄 **Single-Instance IPC**: Double-clicking the Desktop shortcut instantly opens the snip on the already-running background instance with zero startup delay.
- ⚙️ **Customizable Global Hotkey & Auto-Start**: Remap to your preferred keys in Settings, and toggle "Start with Windows".

---

## Requirements

- **Windows 10 / 11** (64-bit)
- **Python 3.10+** (only needed when running from source; standalone built `.exe` needs nothing)
- English (or your language) OCR pack installed: **Settings → Time & Language → Language & region → your language → Options → Handwriting/OCR** (installed by default on most systems).

---

## How to Run

### From Source:
```bat
pip install -r requirements.txt
python main.py
```

### Background / System Tray:
```bat
Start_Circle_Search.bat
```
Starts silently in the Windows system tray (near the clock). Press **Ctrl+Alt+C** anytime to search!

### Standalone Executable:
```bat
build.bat
```
Builds `dist\CircleSearch.exe`.

---

## Usage

1. Press **Ctrl+Alt+C** (or click the tray icon, or double-click the desktop shortcut).
2. Choose your mode from the top bar or keyboard:
   - **`1` or `C`**: ⭕ Circle / Lasso (draw around any object)
   - **`2` or `R`**: ◻️ Rectangle (drag a box)
   - **`3` or `F`**: 🖥️ Full Screen
   - **`Esc` or Right-Click**: Cancel & close
3. When selection completes, the floating action bar appears:
   - **Google Lens**: Direct visual search in your default browser.
   - **Text**: Expand extracted OCR text to edit, copy, or web-search.
   - **Copy**: 1-click copy image or detected text to clipboard.
   - **Save**: Save clean PNG with auto-timestamped filename.

---

## Changing the Hotkey & Settings

Right-click the system tray icon → **Settings…**:
- Click the box and press any key combination (e.g. `Ctrl+Alt+S`, `Win+Shift+Z`, `Ctrl+Shift+C`).
- Check **Start with Windows** to automatically launch into tray on login.
- Click **Reset Default** to restore `Ctrl+Alt+C`.

---

## Architecture

```
main.py            -> App lifecycle, single-instance QLocalServer IPC, signal routing
capture.py         -> Native high-DPI virtual desktop capture, ultra-fast memory buffer conversion
overlay.py         -> Full-screen selection overlay, pre-rendered dimming, smooth neon lasso
toolbar.py         -> Floating action bar, dynamic screen boundary clamping, safe worker threads
ocr.py             -> Cached Windows.Media.Ocr engine with optimized variant pipeline
image_search.py    -> Direct Google Lens v3 upload & search redirect handling
tray.py            -> System tray icon with notifications and quick actions
settings_dialog.py -> Windows virtual-key capture, startup registry integration
config.py          -> Persistent JSON settings + Windows Run key management
```
