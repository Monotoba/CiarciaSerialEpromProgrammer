# CiarciaSerialEpromProgrammer — Design & Architecture Memory

## Project Overview
Serial EPROM programmer GUI for reading/programming classic 27xx-series EPROMs (2716-27256) via RS-232/USB-serial port. Built with PySide6. Supports read, blank-check, program, and verify operations.

## Architecture Decisions

### 1. **Modular Package Structure**
- **Rationale**: Single 460-line file is unmaintainable and untestable. Separates concerns.
- **Structure**:
  - `devices.py` — EPROM type registry (frozen dataclasses)
  - `utils.py` — Utility functions (hex_dump)
  - `programmer.py` — Hardware layer (zero Qt imports, fully testable)
  - `worker.py` — QThread worker (thin adapter to programmer)
  - `gui/main_window.py` — PySide6 UI (MainWindow class)
  - `main.py` — Entry point (owns QApplication)

### 2. **Zero Qt in Hardware Layer**
- **Rationale**: `SerialEpromProgrammer` class has no Qt imports. Allows:
  - Unit testing without QApplication
  - CLI usage without GUI
  - Mocking serial.Serial for protocol tests
- **Implication**: Worker class is the bridge to Qt signals/slots

### 3. **Device Registry via Dict**
- **Rationale**: Adding support for new EPROM chips = one dict entry in `devices.py`
- **Future extensibility**: Designers add tuples, not code

### 4. **Frozen Dataclass for EpromType**
- **Rationale**: Immutable, prevents accidental mutation of type definitions
- **Fields**: `name` (str), `size` (int, in bytes)

### 5. **Testing Strategy**
- Mock `serial.Serial` at the import level (unittest.mock.patch)
- Protocol verification: assert exact byte sequences written
- Signal verification: use pytest-qt `qtbot` for GUI tests
- Target: ≥80% line coverage

## File Organization Rules

### Package Hierarchy
```
src/serial_eprom_programmer/
├── __init__.py         (re-exports public API)
├── devices.py          (EPROM_TYPES registry, EpromType dataclass)
├── utils.py            (hex_dump function)
├── programmer.py       (SerialEpromProgrammer class, NO Qt)
├── worker.py           (Worker(QObject), thread wiring)
└── gui/
    ├── __init__.py
    ├── main_window.py  (MainWindow(QMainWindow))
    └── widgets.py      (future: reusable components)
src/serial_eprom_programmer/main.py  (entry point, owns QApplication)
```

### Import Rules
- `devices.py` — no external imports beyond stdlib
- `utils.py` — no external imports beyond stdlib
- `programmer.py` — `import serial` only, zero Qt
- `worker.py` — `from programmer import *`, PySide6.QtCore
- `gui/main_window.py` — `from worker import *`, full PySide6
- `main.py` — imports gui only, creates QApplication
- Tests — use unittest.mock, pytest, pytest-qt as needed

## Serial Protocol Overview

See `docs/SERIAL_PROTOCOL.md` for full spec. Quick reference:
- **Read**: Send `R` (0x52), address (LE 16-bit), length (LE 16-bit), receive N bytes
- **Program**: Send `P` (0x50), address (LE 16-bit), length (LE 16-bit), send N bytes
- **Timeout**: 3.0s configured in SerialEpromProgrammer.__init__
- **Baud rates**: Defaults to 9600, user selectable (300–38400)

## Extensibility Points

### Adding a New EPROM Type
Edit `devices.py`:
```python
EPROM_TYPES["27512"] = EpromType("27512", 64 * 1024)
```

### Adding a New File Format (Intel HEX, Motorola S-record)
1. Add loader/saver functions to `utils.py`
2. Call from `MainWindow.load_binary()` / `MainWindow.save_binary()`
3. Test in `tests/test_utils.py`

### Adding a New Serial Command
1. Add method to `SerialEpromProgrammer` in `programmer.py`
2. Add action to `Worker` in `worker.py`
3. Add UI button to `MainWindow` in `gui/main_window.py`
4. Add tests in `tests/test_programmer.py` and `tests/test_worker.py`

### CLI Mode (No GUI)
```python
from serial_eprom_programmer.programmer import SerialEpromProgrammer
prog = SerialEpromProgrammer('/dev/ttyUSB0', 9600)
data = prog.read_eprom(0x0000, 2048)
```

## Test Coverage Strategy

| Module | Test File | Approach |
|--------|-----------|----------|
| devices.py | test_devices.py | Direct instantiation, dict validation |
| utils.py | test_utils.py | Call hex_dump with known bytes, assert output format |
| programmer.py | test_programmer.py | Mock serial.Serial, verify byte sequences |
| worker.py | test_worker.py | Mock SerialEpromProgrammer, verify signal emission |
| gui/main_window.py | test_gui.py | pytest-qt qtbot, smoke tests (no actual serial) |

**Coverage Target**: ≥80% line coverage (all path coverage in programmer.py)

## Known Limitations & Future Enhancements

- **Current**: Binary file format only (no Intel HEX, S-record)
- **Future**: Add hex format loaders/savers in `utils.py`
- **Current**: No automatic verify-after-program
- **Future**: Add checkbox to MainWindow for "Verify After Program"
- **Current**: Hardcoded baud rate list
- **Future**: User-configurable baud rate in settings dialog
- **Current**: No help/manual in GUI
- **Future**: Add Help menu linking to `docs/USER_GUIDE.md`

## Commit Strategy

- **P1**: Scaffolding (pyproject, setup.sh, gitignore)
- **P2**: Refactor & modularize (split file, create package)
- **P3**: Tests (80%+ coverage, all passing)
- **P4**: Documentation (user guide, developer guide, protocol spec, extending guide)

Each phase = one git commit with clear message.

## State Recovery

In case of power outage/loss:
- `MEMORY.md` — This file (architecture, decisions, extensibility points)
- `STATUS.md` — Current build/test/doc state (what's done, what's pending)
- `TASKS.md` — Detailed task checklist (which tasks completed, which failed)
- `.git` repo — Full commit history
- All sources committed to git after each phase

## Development Environment

- **Python**: 3.10+
- **OS**: Linux (tested), macOS/Windows supported
- **Dependencies**: PySide6 6.5+, pyserial 3.5+
- **Dev deps**: pytest 7.4+, pytest-qt 4.2+, pytest-cov 4.1+, ruff 0.1+, mypy 1.5+
- **Virtual environment**: `.venv` (created by setup.sh)
