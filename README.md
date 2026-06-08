# Serial EPROM Programmer

[![Tests](https://github.com/Monotoba/CiarciaSerialEpromProgrammer/actions/workflows/tests.yml/badge.svg)](https://github.com/Monotoba/CiarciaSerialEpromProgrammer/actions/workflows/tests.yml)
[![Lint](https://github.com/Monotoba/CiarciaSerialEpromProgrammer/actions/workflows/lint.yml/badge.svg)](https://github.com/Monotoba/CiarciaSerialEpromProgrammer/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A modern, enterprise-grade PySide6 desktop application for reading, programming, verifying, and managing classic EPROM devices. This software is a contemporary reimplementation of the iconic **Steve Ciarcia Serial EPROM Programmer** originally featured in BYTE Magazine, February 1985.

## About This Software

This project modernizes Ciarcia's original design by:
- **Replacing the AY3-1015 UART IC** with an Arduino Nano microcontroller (ATmega328P)
- **Expanding addressing** with an additional address line (A16) for 128KB capacity
- **Supporting 7 EPROM types** including the high-capacity 27512 (64KB)
- **Multi-format file support** for programs from 1970s-era computers to modern microcontrollers
- **Professional dark/light themes** and comprehensive built-in help system

See **[HARDWARE.md](docs/HARDWARE.md)** for detailed information about:
- Original 1985 design and Steve Ciarcia's article
- Modern hardware upgrades (UART replacement, address expansion)
- Protocol enhancements and backwards compatibility
- Roadmap for future hardware revisions (27C, 28F support)

## Features

- **Support for 7 EPROM Types**: 2716, 2732, 2732A, 2764, 27128, 27256, 27512
- **Multi-Format File Support**: Intel HEX, Motorola S-Record, Addressed Hex, TI-TXT, MIF, Binary, and more
- **Cross-platform GUI**: Built with PySide6, runs on Linux, macOS, Windows
- **Four-function operation**: Read, blank-check, program, verify
- **Buffer editing**: Direct hex editing with validation
- **Hex dump view**: Real-time hex/ASCII display with customizable base address
- **Multi-format file I/O**: Load/save with automatic format detection by extension
- **Progress tracking**: Real-time progress bars during long operations
- **Serial port management**: Auto-detect and refresh available ports
- **Configurable parameters**: 12 baud rates (150–230400), base address selection
- **Theme support**: System, dark, and light modes with persistent preferences
- **Comprehensive help**: Built-in ? button with 5 help tabs
- **Comprehensive logging**: Detailed operation results and error reporting

## Requirements

- **Python**: 3.10 or higher
- **Hardware**: RS-232 or USB-serial programmer device (see [Serial Protocol](docs/SERIAL_PROTOCOL.md))
- **OS**: Linux, macOS, or Windows

## Quick Start

### Installation

```bash
git clone <repo>
cd CiarciaSerialEpromProgrammer
bash scripts/setup.sh
```

### Running the Application

```bash
bash scripts/run.sh
```

The application window will open. Connect your EPROM programmer device to a serial port, and you're ready to begin.

### Running Tests

```bash
bash scripts/test.sh
```

All tests will run with coverage reporting. Results appear in the terminal and in `htmlcov/index.html`.

## Documentation

### User Documentation
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** — Step-by-step usage, wiring, troubleshooting, all supported file formats
- **[HARDWARE.md](docs/HARDWARE.md)** — Hardware history, upgrades, future expansion roadmap

### Developer Documentation
- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** — Architecture, testing, extending the code
- **[SERIAL_PROTOCOL.md](docs/SERIAL_PROTOCOL.md)** — Hardware protocol specification
- **[EXTENDING.md](docs/EXTENDING.md)** — How to add devices, file formats, GUI components

### Historical Reference
- **[docs/Hardware/](docs/Hardware/)** — Original Steve Ciarcia article from BYTE Magazine, February 1985

## Architecture Overview

The application is organized into modular layers:

```
gui/main_window.py       ← User interface (PySide6)
        ↓
    worker.py            ← Thread adapter (Qt signals/slots)
        ↓
programmer.py            ← Hardware layer (pure Python, testable)
        ↓
serial.Serial (pyserial) ← RS-232 communication
```

Each layer is independent and testable. See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for details.

## Supported EPROM Types

| Type | Size | Address Range | Year |
|------|------|---------------|------|
| 2716 | 2 KB | 0x0000-0x07FF | 1974 |
| 2732 / 2732A | 4 KB | 0x0000-0x0FFF | 1976 |
| 2764 | 8 KB | 0x0000-0x1FFF | 1982 |
| 27128 | 16 KB | 0x0000-0x3FFF | 1984 |
| 27256 | 32 KB | 0x0000-0x7FFF | 1986 |
| 27512 | 64 KB | 0x0000-0xFFFF | 1987 |

## Supported File Formats

9 classic and modern formats with auto-detection:

| Format | Extensions | Use Case | Era |
|--------|-----------|----------|-----|
| Intel HEX | .hex, .ihx | Arduino, PIC, AVR (universal standard) | 1973+ |
| Intel IHEX-32 | .ihex32, .hex32 | Large flash (>64KB) | 1998+ |
| Motorola S-Record | .mot, .srec | Motorola 6800, 68000, automotive | 1974+ |
| Tektronix HEX | .tek, .tektronix | Test equipment | 1970s-90s |
| Addressed Hex | .ahex, .asc | Monitor programs, hex editors | 1970s+ |
| TI-TXT | .txt, .ti_txt | Texas Instruments MCU | 1990s+ |
| MOS Paper Tape | .mos, .papertape | KIM-1, Apple I (1976+) | 1976-80s |
| MIF | .mif | FPGA block RAM (Xilinx, Altera) | 1990s+ |
| Binary | .bin, .rom, .epr | Raw data | All |

## License

MIT

## Author

Randy Morgan <rmorgan62@gmail.com>

## Contributing

Contributions welcome! Please see [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for setup and testing.
