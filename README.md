# SideDock

A lightweight, always-on-top clock overlay for Windows. The clock floats transparently over your desktop and is fully **click-through** — it never interferes with your workflow.

Controlled entirely from the **system tray**.

## Features

- 🕐 **Always-on-top clock** — stays visible over all windows
- 📊 **Real-time stats** — optional CPU usage, RAM usage, and download speed (in MB/s)
- 👻 **Click-through** — the overlay never captures mouse or keyboard input
- 🎨 **Customizable** — adjust text opacity, color, font size, position, and toggle stats visibility
- 🚀 **Start with Windows** — optional auto-launch on login
- 💾 **Persistent settings** — your preferences are saved to `config.json`
- 🔇 **Minimal footprint** — no taskbar icon, no Alt-Tab entry

## Getting Started

### Prerequisites

- Python 3.8+ (for running from source)
- Windows 10/11

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run from source

```bash
python main.py
```

### Configuration

Copy the example config to get started:

```bash
copy config.example.json config.json
```

If no `config.json` exists, the app creates one with default values on first run.

#### Config options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `opacity` | float | `0.5` | Text opacity (0.05 – 1.0) |
| `color` | string | `"#FFFFFF"` | Text color as hex |
| `font_size` | int | `48` | Font size in points (16 – 200) |
| `pos_x` | int/null | `null` | X position in pixels (`null` = top-right) |
| `pos_y` | int/null | `null` | Y position in pixels (`null` = top-right) |
| `time_format` | string | `"%H:%M:%S"` | Python `strftime` format string |
| `show_stats` | boolean | `true` | Show CPU, RAM, and Download speed (in MB/s) |

## Building the `.exe`

Build a standalone executable with PyInstaller (no Python required to run):

```bash
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name SideDock main.py
```

The executable will be at `dist/SideDock.exe`. Copy `config.json` (or `config.example.json` renamed) next to it:

```bash
copy config.example.json dist\config.json
```

### Distributing

Ship the `dist/` folder containing:
- `SideDock.exe`
- `config.json`

That's it — fully portable, no installation needed.

## Usage

1. **Launch** `SideDock.exe` (or `python main.py`)
2. A clock appears in the top-right corner of your screen
3. **Right-click** the system tray icon (small clock) to access:
   - **Options** — opens the settings panel to customize appearance and position
   - **Close** — exits the application
4. Enable **Start with Windows** in Options to auto-launch on login

## Project Structure

```
SideDock/
├── main.py              # App entry point, window setup, clock loop
├── settings.py          # Options dialog UI
├── tray.py              # System tray icon and menu
├── startup.py           # Windows startup registry manager
├── config.json          # User settings (gitignored)
├── config.example.json  # Default settings template
├── requirements.txt     # Python dependencies
└── .gitignore
```

## License

MIT
