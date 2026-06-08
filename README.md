# Serial EPROM Programmer

A PySide6 desktop application for reading, programming, verifying, and managing classic 27xx-series EPROMs via a serial port connection.

## Features

- **Support for 6 EPROM Types**: 2716, 2732, 2732A, 2764, 27128, 27256
- **Cross-platform GUI**: Built with PySide6, runs on Linux, macOS, Windows
- **Four-function operation**: Read, blank-check, program, verify
- **Hex dump view**: Real-time hex/ASCII display of buffer contents
- **Binary file I/O**: Load and save binary images
- **Progress tracking**: Real-time progress bars during long operations
- **Serial port management**: Auto-detect and refresh available ports
- **Configurable parameters**: Baud rate, base address selection
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

- **[USER_GUIDE.md](docs/USER_GUIDE.md)** — Step-by-step usage, wiring, troubleshooting
- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** — Architecture, testing, extending the code
- **[SERIAL_PROTOCOL.md](docs/SERIAL_PROTOCOL.md)** — Hardware protocol specification
- **[EXTENDING.md](docs/EXTENDING.md)** — How to add devices, file formats, GUI components

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

| Type | Size | Address Range |
|------|------|---------------|
| 2716 | 2 KB | 0x0000-0x07FF |
| 2732 / 2732A | 4 KB | 0x0000-0x0FFF |
| 2764 | 8 KB | 0x0000-0x1FFF |
| 27128 | 16 KB | 0x0000-0x3FFF |
| 27256 | 32 KB | 0x0000-0x7FFF |

## License

MIT

## Author

Randy Morgan <rmorgan62@gmail.com>

## Contributing

Contributions welcome! Please see [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for setup and testing.
