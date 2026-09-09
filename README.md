<div align="center">

# ⭕ Circle to Search for Windows

**The phone-style "Circle to Search" experience, brought natively to Windows 10 & 11.**

[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D4?logo=windows&logoColor=white)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?logo=qt&logoColor=white)](https://pyside.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com)

**Press <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> → Circle or drag anywhere on screen → Instant Google Lens visual search, local offline OCR text extraction, or 1-click copy.**

[Quick Start](#-quick-start) • [Features](#-features) • [Installation](#-installation-guide) • [Keyboard Shortcuts](#-keyboard-shortcuts) • [Settings](#-customization--settings)

</div>

---

## ✨ Features

- ⭕ **Smart Circle / Lasso Masking**: Draw a smooth neon loop around any object, image, or text. The background is automatically masked so **only the exact item you circled** is sent to Google Lens.
- ◻️ **Precision Rectangle Snip**: Drag a crystal-clear box with live pixel dimension badges.
- 🖥️ **1-Click Fullscreen**: Instant monitor capture with zero delay.
- 🔍 **Instant Google Lens**: Directly renders visual matches, product links, and AI overviews in your default browser.
- ⚡ **Local Windows OCR**: Instant, 100% offline text recognition powered by native `Windows.Media.Ocr`.
- 🚀 **Zero-Lag Compositor**: Pre-rendered textures composited at 60–144+ FPS with zero mouse stutter, even across 4K and multi-monitor setups.
- 🔒 **100% Private**: No user tracking, no third-party accounts, zero telemetry.
- ⌨️ **Global Hotkey & Tray**: Sits silently in your system tray; summon it anywhere with <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd>.
- 🔄 **Single-Instance IPC**: Double-clicking the Desktop shortcut triggers the active background instance with zero startup delay.

---

## 🚀 Quick Start

### Option A: Portable Standalone Executable *(No Python Required!)*

1. Double-click **[`dist\CircleSearch.exe`](dist/CircleSearch.exe)** or run **[`Start_Circle_Search.bat`](Start_Circle_Search.bat)**.
2. The app sits quietly in your system tray (near the clock).
3. Press **<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd>** anytime to search!

> **Want a Desktop Shortcut?** Double-click **[`create_desktop_shortcut.bat`](create_desktop_shortcut.bat)** to instantly add "Circle to Search" to your Desktop and Start Menu.

---

### Option B: 1-Click Automated Setup *(From Source)*

1. Double-click **[`setup.bat`](setup.bat)**.
2. It will automatically:
   - Check your Python installation
   - Install all required libraries (`pip install -r requirements.txt`)
   - Create Desktop & Start Menu shortcuts
   - Launch Circle to Search into the system tray!

---

### Option C: Manual Installation

```bat
# 1. Clone the repository
git clone https://github.com/your-username/circle-search.git
cd circle-search

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create desktop shortcuts
python create_shortcut.py

# 4. Run the app
python main.py --tray
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut / Key | Action |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | **Trigger Circle to Search** (Global, customizable) |
| <kbd>1</kbd> or <kbd>C</kbd> | Switch to **⭕ Circle / Lasso** mode |
| <kbd>2</kbd> or <kbd>R</kbd> | Switch to **◻️ Rectangle** mode |
| <kbd>3</kbd> or <kbd>F</kbd> | Capture **🖥️ Fullscreen** |
| <kbd>Enter</kbd> | Confirm selection |
| <kbd>Esc</kbd> / Right-Click | Cancel & close overlay |

---

## ⚙️ Customization & Settings

Right-click the system tray icon → **Settings…**:

- **Custom Global Hotkey**: Click the input field and press any key combination (e.g. `Ctrl+Alt+S`, `Win+Shift+Z`, `Ctrl+Shift+C`).
- **Start with Windows**: Toggle automatic launch on Windows startup.
- **Preferred Selection Mode**: Choose whether Circle or Rectangle mode is active by default.
- **Reset Default**: Quickly restores default settings (`Ctrl+Shift+S`).

---

## 🛠️ Building Standalone `.exe`

To compile your own standalone single-file executable:

```bat
build.bat
```

The output executable will be created at `dist\CircleSearch.exe`. It bundles Python, PySide6, and all dependencies into a single portable binary that runs on any 64-bit Windows 10/11 PC.

---

## 📂 Project Architecture

```
circle-search/
├── main.py                 # App entry point, single-instance QLocalServer IPC, lifecycle
├── capture.py              # High-DPI virtual desktop framebuffer capture
├── overlay.py              # Full-screen selection overlay, neon lasso, physical crop masking
├── toolbar.py              # Floating action bar, Google Lens dispatch, OCR preview
├── image_search.py         # Google Lens upload & visual search redirect pipeline
├── ocr.py                  # Windows.Media.Ocr native offline text extraction
├── tray.py                 # System tray icon, notifications, quick menu
├── hotkey.py               # Win32 RegisterHotKey worker thread
├── settings_dialog.py      # Hotkey recorder and preference dialog
├── config.py               # Persistent JSON configuration & Windows startup registry
├── requirements.txt        # Python package dependencies
├── setup.bat               # 1-click automated setup script for new PCs
├── Start_Circle_Search.bat # Silent background launcher
├── create_shortcut.py      # Desktop and Start Menu shortcut generator
└── dist/
    └── CircleSearch.exe    # Standalone portable Windows executable
```

---

## ❓ FAQ & Troubleshooting

<details>
<summary><b>1. The hotkey doesn't fire when I press Ctrl+Shift+S</b></summary>
Another application (such as an IDE or screen recording utility) might already be using <code>Ctrl+Shift+S</code>. Right-click the system tray icon, select <b>Settings…</b>, and change the hotkey to any unused combination (e.g. <code>Ctrl+Alt+C</code> or <code>Win+Shift+S</code>).
</details>

<details>
<summary><b>2. How does local OCR work?</b></summary>
The app uses the built-in Windows 10/11 OCR engine (<code>Windows.Media.Ocr</code>), meaning text recognition is instantaneous, 100% offline, and does not send your screen data to external servers. Ensure your language pack has OCR installed in <b>Windows Settings → Time & Language → Language & region</b>.
</details>

<details>
<summary><b>3. Does it support multiple monitors and high-DPI scaling?</b></summary>
Yes! The selection overlay dynamically spans across all connected monitors and adjusts for per-monitor DPI scaling (100%, 125%, 150%, 200%) with pixel-perfect coordinate mapping.
</details>

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more details.

---

<div align="center">
<b>If you find this project useful, please consider giving it a ⭐ star on GitHub!</b>
</div>
