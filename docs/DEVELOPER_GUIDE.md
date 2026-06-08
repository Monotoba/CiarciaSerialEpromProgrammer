# Developer Guide — Serial EPROM Programmer

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Development Setup](#development-setup)
3. [Code Organization](#code-organization)
4. [Running Tests](#running-tests)
5. [Adding New EPROM Types](#adding-new-eprom-types)
6. [Adding New Commands](#adding-new-commands)
7. [Code Style](#code-style)
8. [Extending the GUI](#extending-the-gui)

## Project Architecture

The application is structured in layers from hardware to UI:

### Layer 1: Hardware (`programmer.py`)

**Purpose**: Low-level serial communication with EPROM programmer

**Key Features**:
- No Qt dependencies (fully testable)
- Sends/receives bytes over RS-232
- Implements read, program operations
- Progress callbacks for long operations

**Classes**:
- `SerialEpromProgrammer`: Main hardware interface

### Layer 2: Thread Adapter (`worker.py`)

**Purpose**: Bridge between hardware layer and Qt

**Key Features**:
- Runs hardware operations in background thread
- Emits Qt signals (finished, failed, progress)
- Wraps exceptions into signal emissions
- Implements all four operations: read, blank-check, program, verify

**Classes**:
- `Worker(QObject)`: Thread worker with signal/slot interface

### Layer 3: GUI (`gui/main_window.py`)

**Purpose**: User interface for all operations

**Key Features**:
- PySide6 widgets (combos, buttons, text areas)
- File I/O (load/save binary)
- Worker thread management
- Status logging

**Classes**:
- `MainWindow(QMainWindow)`: Main application window

### Layer 4: Entry Point (`main.py`)

**Purpose**: Application bootstrap

**Key Features**:
- Creates QApplication
- Shows MainWindow
- Runs event loop

**Functions**:
- `main()`: Entry point

### Support Modules

**`devices.py`**: EPROM type registry
- `EpromType`: Frozen dataclass (name, size)
- `EPROM_TYPES`: Dict mapping chip names to specs

**`utils.py`**: Utility functions
- `hex_dump()`: Format bytes as hex/ASCII display

## Development Setup

### Clone and Install

```bash
git clone https://github.com/yourusername/CiarciaSerialEpromProgrammer.git
cd CiarciaSerialEpromProgrammer
bash scripts/setup.sh
```

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Deactivate (when done)

```bash
deactivate
```

## Code Organization

### Directory Structure

```
CiarciaSerialEpromProgrammer/
├── .git/                      # Git repository
├── .venv/                     # Virtual environment (created by setup.sh)
├── src/
│   └── serial_eprom_programmer/
│       ├── __init__.py        # Public API re-exports
│       ├── devices.py         # EPROM type definitions
│       ├── utils.py           # hex_dump utility
│       ├── programmer.py      # Hardware layer (NO Qt)
│       ├── worker.py          # Qt thread adapter
│       ├── main.py            # Entry point (owns QApplication)
│       └── gui/
│           ├── __init__.py
│           ├── main_window.py # MainWindow GUI
│           └── widgets.py     # Reusable widgets (future)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared pytest fixtures
│   ├── test_devices.py        # Device registry tests
│   ├── test_utils.py          # Hex dump tests
│   ├── test_programmer.py     # Hardware layer tests (mocked serial)
│   ├── test_worker.py         # Worker thread tests
│   └── test_gui.py            # GUI smoke tests
├── docs/
│   ├── USER_GUIDE.md          # User documentation
│   ├── DEVELOPER_GUIDE.md     # This file
│   ├── SERIAL_PROTOCOL.md     # Hardware protocol spec
│   └── EXTENDING.md           # Extension examples
├── scripts/
│   ├── setup.sh               # Environment setup
│   ├── run.sh                 # Run application
│   └── test.sh                # Run test suite
├── pyproject.toml             # Project metadata and configs
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Development dependencies
├── .gitignore                 # Git ignore rules
├── MEMORY.md                  # Architecture decisions
├── STATUS.md                  # Build status
├── TASKS.md                   # Task checklist
└── README.md                  # Project overview
```

### Import Rules

- **devices.py**: No external imports beyond stdlib
- **utils.py**: No external imports beyond stdlib
- **programmer.py**: `import serial` only, NO Qt
- **worker.py**: `from programmer import *`, PySide6.QtCore
- **gui/main_window.py**: `from worker import *`, full PySide6
- **main.py**: `from gui import *`, creates QApplication

## Running Tests

### Run All Tests

```bash
bash scripts/test.sh
```

### Run Specific Test File

```bash
source .venv/bin/activate
pytest tests/test_programmer.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_programmer.py::TestSerialEpromProgrammer -v
```

### Run Specific Test

```bash
pytest tests/test_programmer.py::TestSerialEpromProgrammer::test_send_byte -v
```

### View Coverage Report

After running tests, open the HTML coverage report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Goals

- **Overall**: ≥80%
- **programmer.py**: 100% (critical for hardware layer)
- **worker.py**: 100% (thin adapter, fully testable)
- **devices.py**: 100% (simple data definitions)
- **utils.py**: 100% (utility functions)
- **gui/main_window.py**: ≥60% (UI coverage is lower, smoke tests ok)

## Adding New EPROM Types

### Quick Add

Edit `src/serial_eprom_programmer/devices.py`:

```python
EPROM_TYPES = {
    # ... existing types ...
    "27512": EpromType("27512", 64 * 1024),  # 64KB chip
}
```

### With Tests

Add to `tests/test_devices.py`:

```python
def test_eprom_27512(self):
    """Test 27512 64KB EPROM."""
    assert "27512" in EPROM_TYPES
    assert EPROM_TYPES["27512"].size == 64 * 1024
```

Run tests to verify:
```bash
pytest tests/test_devices.py -v
```

## Adding New Commands

### Example: Add "Erase" Command

**Step 1**: Add method to `SerialEpromProgrammer` in `programmer.py`

```python
def erase_eprom(self, progress=None) -> None:
    """Erase entire EPROM (send 'E' command)."""
    self.send_byte(ord("E"))
    # Wait for response, emit progress, etc.
    # See read_eprom() for progress callback pattern
```

**Step 2**: Add test in `tests/test_programmer.py`

```python
@patch("serial.Serial")
def test_erase_eprom(self, mock_serial_class):
    """Test erase operation."""
    mock_serial = MagicMock()
    mock_serial_class.return_value = mock_serial
    prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)
    
    prog.erase_eprom()
    
    assert mock_serial.write.called
    # Verify 'E' command was sent
    assert mock_serial.write.call_args_list[0][0][0] == b"E"
```

**Step 3**: Add action to `Worker` in `worker.py`

```python
elif self.action == "erase":
    programmer.erase_eprom(progress=self.progress.emit)
    self.finished.emit(None)
```

**Step 4**: Add test in `tests/test_worker.py`

```python
@patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
def test_worker_erase_action(self, mock_programmer_class):
    """Test worker erase action."""
    mock_programmer = MagicMock()
    mock_programmer_class.return_value = mock_programmer
    
    worker = Worker("erase", "/dev/ttyUSB0", 9600, 0x0000, b"")
    finished_result = []
    worker.finished.connect(lambda x: finished_result.append(x))
    
    worker.run()
    
    assert len(finished_result) == 1
    mock_programmer.erase_eprom.assert_called_once()
```

**Step 5**: Add UI button to `MainWindow` in `gui/main_window.py`

```python
erase_btn = QPushButton("Erase EPROM")
erase_btn.clicked.connect(lambda: self.start_worker("erase"))
action_row.addWidget(erase_btn)
```

**Step 6**: Handle result in `worker_done()`

```python
elif action == "erase":
    self.log("Erase complete.")
```

**Step 7**: Test the full workflow

```bash
pytest tests/ -v
bash scripts/run.sh  # Manual test
```

## Code Style

### Python Style

Follow PEP 8 (enforced by ruff):

```bash
source .venv/bin/activate
ruff check src/ tests/
```

### Type Hints

Use type hints for function signatures:

```python
def hex_dump(data: bytes, base: int = 0) -> str:
    """Format bytes as hex dump."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def read_eprom(self, base: int, size: int, progress=None) -> bytes:
    """Read EPROM data from hardware.
    
    Args:
        base: Starting address (16-bit)
        size: Number of bytes to read
        progress: Optional callback(bytes_read) for progress updates
    
    Returns:
        Bytes read from EPROM
    """
```

### Comments

Keep comments minimal. Only explain WHY, not WHAT:

```python
# Wait for hardware acknowledgment (typical 100ms)
time.sleep(0.1)

# WRONG: "Set the buffer to 0xFF" — this is obvious from code
self.buffer[:] = bytes([0xFF]) * len(self.buffer)
```

## Extending the GUI

### Adding a New Widget

1. Create class in `gui/widgets.py`
2. Inherit from appropriate PySide6 class (QWidget, QDialog, etc.)
3. Add to `MainWindow._build_ui()` or create new view
4. Test with pytest-qt

### Example: Custom EPROM Selector

```python
# gui/widgets.py
from PySide6.QtWidgets import QComboBox
from serial_eprom_programmer.devices import EPROM_TYPES

class EpromSelector(QComboBox):
    """Custom EPROM type selector."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItems(EPROM_TYPES.keys())
        self.setToolTip("Select EPROM chip type")
```

## Common Development Tasks

### Run linter and type checker

```bash
source .venv/bin/activate
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

### View what changed

```bash
git diff src/serial_eprom_programmer/programmer.py
```

### Make a new commit

```bash
git add src/ tests/
git commit -m "Description of change"
```

### Review coverage for specific file

```bash
open htmlcov/serial_eprom_programmer_programmer_py.html
```

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [pyserial Documentation](https://pyserial.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Serial Protocol Spec](SERIAL_PROTOCOL.md)
