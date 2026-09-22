REMEMEBER TO CLICK "INSERT" AFTER RUNING rhythia_auto.py, OTWHERWISE THE MENU WONT SHOW UP !!


# Rhythia Auto

Auto-play overlay for Rhythia — loads a `.sspm` map file and simulates mouse clicks in sync with the music. Comes with a clean UI panel that toggles with a single hotkey.

> ⚠️ **Disclaimer:** Use at your own risk. Automated play in ranked or online modes is against the game's rules and may result in a ban. The author is not responsible for any consequences.

---

## Features

- Reads `.sspm` map files and extracts note timings
- Automatic mouse clicking synced to the music
- Clean overlay UI with gradient background and animated status indicator
- Toggle the panel on/off with the **Insert** key
- Timing offset for fine-tuning accuracy (± 5 ms steps)
- Playback speed control — 0.75x to 1.45x, plus custom values
- Progress bar showing the current position in the song
- Note counter showing how many notes were loaded
- Scrollable speed list with mouse wheel support
- Standalone `.exe` build support via PyInstaller

---

## Requirements

- **Windows 10 or 11**
- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
  - ⚠️ During installation, **check "Add python.exe to PATH"**
- **Rhythia** installed on Steam

---

## Installation

### Option 1 — Automatic (recommended)

1. Download or clone this repository.
2. Double-click **`install.bat`**.
3. The script will check your Python installation and install all dependencies.
4. Done.

### Option 2 — Manual

```bash
pip install -r requirements.txt
