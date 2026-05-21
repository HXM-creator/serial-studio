<p align="center">
  <h1 align="center">Serial Studio</h1>
  <p align="center"><i>Real-time serial plotter & debug tool for embedded systems</i></p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License">
    <img src="https://img.shields.io/badge/STM32-ESP32--IDF-ready-brightgreen" alt="Platforms">
  </p>
</p>

---

Serial Studio is a PyQt6-based desktop tool that connects to your microcontroller over UART and plots sensor data in **real time**. Think of it as a much better Arduino Serial Plotter.

Works great with **[microlog](https://github.com/HXM-creator/microlog)** — send log messages AND numeric data on the same UART stream.

## Features

- Auto-detect serial ports (refreshes every 3s)
- Configurable baud rate (9600 — 921600)
- Real-time multi-channel plotting with pyqtgraph
- Auto-create channels from incoming data
- Toggle channels on/off
- Export data to CSV
- Tolerant parser — skips non-numeric lines, works with mixed log/data output

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

### No MCU handy? Use the test sender:

```bash
# Install a virtual serial pair, or just test on console:
python tools/test_sender.py

# You'll see:
50.1, 30.2, 12.34
52.3, 28.9, 15.67
...
```

For a full end-to-end test, use a virtual serial port pair
([com0com](https://sourceforge.net/projects/com0com/) on Windows,
[socat](https://linux.die.net/man/1/socat) on Linux):

```bash
# Terminal 1: send data to virtual port
python tools/test_sender.py COM3

# Terminal 2: open Serial Studio, connect to COM4
python main.py
```

## Data format

Serial Studio parses lines of text and extracts numeric values.

| Format | Example | Notes |
|--------|---------|-------|
| Comma separated | `12.3, 45.6, 78.9` | 3 channels |
| Space separated | `12.3 45.6 78.9` | Same, any whitespace |
| With labels | `ch1=12.3 ch2=45.6` | Labels are ignored |
| Mixed with text | `[INFO] sensor=12.3` | JSON or log lines work too |

The number of values per line determines the channel count. Channels auto-create on first data.

## Project structure

```
serial-studio/
├── main.py                       # Entry point
├── requirements.txt              # Dependencies
├── LICENSE                       # MIT
├── serial_studio/
│   ├── __init__.py
│   ├── main_window.py            # UI + plotting logic
│   ├── serial_thread.py          # Background serial reader
│   └── parser.py                 # Numeric data parser
└── tools/
    ├── test_sender.py            # Simple sine-wave generator
    └── microlog_sender.py        # Realistic data with log messages
```

## With microlog

microlog users can send both log messages and plot data through the same UART:

```c
log_info("Sensor values: %.1f, %.1f, %.2f", ch1, ch2, ch3);
```

Serial Studio silently skips the `[INFO]` prefix and plots the three numbers.

## License

MIT
