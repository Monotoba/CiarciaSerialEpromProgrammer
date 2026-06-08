# Extending the Serial EPROM Programmer

This guide shows how to add new functionality: EPROM types, file formats, CLI mode, and GUI components.

## Adding a New EPROM Type

### Scenario

You want to support the 27512 (64KB EPROM).

### Implementation

**File**: `src/serial_eprom_programmer/devices.py`

```python
EPROM_TYPES = {
    "2716": EpromType("2716", 2 * 1024),
    # ... existing entries ...
    "27512": EpromType("27512", 64 * 1024),  # Add this line
}
```

**Test**: `tests/test_devices.py`

```python
def test_eprom_27512(self):
    """Test 27512 64KB EPROM."""
    assert "27512" in EPROM_TYPES
    assert EPROM_TYPES["27512"].size == 64 * 1024
```

**Run tests**:
```bash
pytest tests/test_devices.py::TestEpromRegistry::test_eprom_27512 -v
```

**That's it!** The GUI automatically discovers new types.

## Adding a New File Format

### Scenario

You want to support Intel HEX files (`.hex`).

### Implementation

**File**: `src/serial_eprom_programmer/utils.py`

Add loader and saver functions:

```python
def load_hex_file(path: str) -> bytes:
    """Load Intel HEX file and return bytes.
    
    Args:
        path: Path to .hex file
    
    Returns:
        Bytes from HEX file, padded with 0xFF to 64KB max
    """
    buffer = bytearray([0xFF] * 65536)  # Max 64KB
    
    with open(path, 'r') as f:
        for line in f:
            if not line.startswith(':'):
                continue
            # Parse HEX line: :LLAAAATTDD...SS
            # LL = byte count, AAAA = address, TT = type, DD = data, SS = checksum
            byte_count = int(line[1:3], 16)
            address = int(line[3:7], 16)
            record_type = int(line[7:9], 16)
            
            if record_type == 0x00:  # Data record
                for i in range(byte_count):
                    data_byte = int(line[9+i*2:11+i*2], 16)
                    if address + i < len(buffer):
                        buffer[address + i] = data_byte
    
    return bytes(buffer)

def save_hex_file(path: str, data: bytes, start_addr: int = 0) -> None:
    """Save bytes to Intel HEX file.
    
    Args:
        path: Output file path
        data: Bytes to save
        start_addr: Starting address (default 0)
    """
    with open(path, 'w') as f:
        for offset in range(0, len(data), 16):
            chunk = data[offset:offset+16]
            addr = start_addr + offset
            
            # Calculate checksum
            checksum = (len(chunk) + (addr >> 8) + (addr & 0xFF) + 0) % 256
            for byte in chunk:
                checksum = (checksum + byte) % 256
            checksum = (0x100 - checksum) & 0xFF
            
            # Write line: :LLAAAATTDD...SS
            hex_line = f":{len(chunk):02X}{addr:04X}00"
            for byte in chunk:
                hex_line += f"{byte:02X}"
            hex_line += f"{checksum:02X}\n"
            f.write(hex_line)
        
        # End-of-file record
        f.write(":00000001FF\n")
```

**Update GUI**: `src/serial_eprom_programmer/gui/main_window.py`

Modify `load_binary()` to detect file format:

```python
def load_binary(self) -> None:
    """Load binary or HEX file into buffer."""
    filename, _ = QFileDialog.getOpenFileName(
        self, "Load Binary/HEX",
        filter="All Files (*);;Binary (*.bin);;HEX (*.hex)"
    )
    if not filename:
        return
    
    path = pathlib.Path(filename)
    
    if filename.endswith('.hex'):
        from serial_eprom_programmer.utils import load_hex_file
        data = load_hex_file(filename)
    else:
        # Binary file
        data = path.read_bytes()
        if len(data) > self.eprom.size:
            QMessageBox.warning(...)
            return
        # Pad with 0xFF
        data = data + bytes([0xFF] * (self.eprom.size - len(data)))
    
    self.buffer[:] = data
    self.log(f"Loaded {path.name}")
    self.update_hex_view()
```

**Test**: `tests/test_utils.py`

```python
def test_load_hex_file(tmp_path):
    """Test loading Intel HEX file."""
    hex_file = tmp_path / "test.hex"
    hex_file.write_text(":04000000AABBCCDD59\n:00000001FF\n")
    
    from serial_eprom_programmer.utils import load_hex_file
    data = load_hex_file(str(hex_file))
    
    assert data[0] == 0xAA
    assert data[1] == 0xBB
```

## CLI Mode (No GUI)

### Scenario

You want to read an EPROM from a script without opening the GUI.

### Implementation

Create a simple CLI script:

```python
# cli_reader.py
#!/usr/bin/env python3
"""Simple CLI to read EPROM without GUI."""

import argparse
import sys
from pathlib import Path

from serial_eprom_programmer.programmer import SerialEpromProgrammer
from serial_eprom_programmer.devices import EPROM_TYPES

def main():
    parser = argparse.ArgumentParser(description="Read EPROM via serial")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyUSB0)")
    parser.add_argument("eprom", help=f"EPROM type ({', '.join(EPROM_TYPES.keys())})")
    parser.add_argument("-b", "--baud", type=int, default=9600, help="Baud rate (default 9600)")
    parser.add_argument("-o", "--output", help="Output file (default eprom.bin)")
    
    args = parser.parse_args()
    
    if args.eprom not in EPROM_TYPES:
        print(f"Unknown EPROM type: {args.eprom}", file=sys.stderr)
        return 1
    
    size = EPROM_TYPES[args.eprom].size
    output_file = args.output or "eprom.bin"
    
    try:
        print(f"Connecting to {args.port} @ {args.baud} baud...")
        prog = SerialEpromProgrammer(args.port, args.baud)
        
        print(f"Reading {size} bytes from {args.eprom}...")
        data = prog.read_eprom(0, size, progress=lambda n: print(f"  {n}/{size} bytes"))
        
        prog.close()
        
        Path(output_file).write_bytes(data)
        print(f"Saved to {output_file}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Usage**:

```bash
python cli_reader.py /dev/ttyUSB0 27256 -o firmware.bin
python cli_reader.py COM1 2764 -b 19200
```

## Adding a GUI Dialog

### Scenario

You want a settings dialog to save/load last used port and baud rate.

### Implementation

Create new widget: `src/serial_eprom_programmer/gui/settings_dialog.py`

```python
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton
)

class SettingsDialog(QDialog):
    """Settings dialog for port and baud rate."""
    
    def __init__(self, current_port: str, current_baud: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        
        self.port_combo.addItems([current_port])
        self.baud_combo.addItems(["300", "600", "1200", "2400", "4800", "9600", "19200", "38400"])
        self.baud_combo.setCurrentText(str(current_baud))
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_combo)
        layout.addWidget(QLabel("Baud:"))
        layout.addWidget(self.baud_combo)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        
        self.setLayout(layout)
    
    def get_values(self):
        return self.port_combo.currentText(), int(self.baud_combo.currentText())
```

**Add to MainWindow**: `src/serial_eprom_programmer/gui/main_window.py`

```python
from serial_eprom_programmer.gui.settings_dialog import SettingsDialog

# In _build_ui():
settings_btn = QPushButton("Settings")
settings_btn.clicked.connect(self.open_settings)

# Add new method:
def open_settings(self) -> None:
    """Open settings dialog."""
    dialog = SettingsDialog(
        self.port_combo.currentText(),
        int(self.baud_combo.currentText()),
        parent=self
    )
    if dialog.exec():
        port, baud = dialog.get_values()
        self.port_combo.setCurrentText(port)
        self.baud_combo.setCurrentText(str(baud))
```

## Adding Progress Indication

### Scenario

Show real-time progress percentage and speed.

### Implementation

Modify `gui/main_window.py`:

```python
from PySide6.QtWidgets import QLabel
import time

def start_worker(self, action: str) -> None:
    # ... existing code ...
    
    self.start_time = time.time()
    self.progress.setRange(0, len(self.buffer))
    self.progress.setValue(0)
    
    # Add speed label
    self.speed_label = QLabel("0 bytes/sec")
    layout.addWidget(self.speed_label)  # Add to layout
    
    # Connect progress signal
    self.worker.progress.connect(self.update_progress)

def update_progress(self, bytes_done: int) -> None:
    """Update progress bar and show speed."""
    elapsed = time.time() - self.start_time
    if elapsed > 0:
        speed = bytes_done / elapsed
        self.speed_label.setText(f"{speed:.1f} bytes/sec")
    self.progress.setValue(bytes_done)
```

## Testing Extensions

### Test New EPROM Type

```bash
pytest tests/test_devices.py -v
```

### Test New File Format

```bash
pytest tests/test_utils.py::test_load_hex_file -v
```

### Test CLI Mode

```bash
python cli_reader.py --help
python cli_reader.py /dev/null 2716 2>&1 | head -5  # Will error (no device)
```

### Test GUI Changes

```bash
pytest tests/test_gui.py -v
bash scripts/run.sh  # Manual test
```

## Best Practices

1. **Keep layers separate**: Don't add Qt code to `programmer.py`
2. **Test first**: Write tests before implementation
3. **Reuse existing code**: Check utils.py and devices.py first
4. **Document changes**: Update docstrings and comments
5. **Commit frequently**: One feature per commit
6. **Run full test suite**: `pytest tests/ -v` before committing

## Common Patterns

### Progress Callback

```python
def long_operation(self, progress=None) -> bytes:
    """Operation with progress reporting."""
    for i in range(1000):
        # Do work...
        if progress and (i % 100 == 0):
            progress(i)
    if progress:
        progress(1000)  # Final callback
    return result
```

### Error Handling in Worker

```python
def run(self) -> None:
    """Worker run with exception handling."""
    try:
        programmer = SerialEpromProgrammer(...)
        # Do operation...
        self.finished.emit(result)
    except Exception as exc:
        self.failed.emit(str(exc))  # Emit, don't raise
    finally:
        if programmer:
            programmer.close()
```

### Qt Signal/Slot Connection

```python
# Connect signal to slot
self.worker.finished.connect(self.worker_done)
self.worker.failed.connect(self.worker_failed)
self.worker.progress.connect(self.progress.setValue)

# Disconnect when done
self.worker.finished.disconnect()
```

## Getting Help

- Check existing tests for examples
- Review [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for architecture
- Check [SERIAL_PROTOCOL.md](SERIAL_PROTOCOL.md) for protocol details
- View docstrings: `python -c "from serial_eprom_programmer.programmer import SerialEpromProgrammer; help(SerialEpromProgrammer.read_eprom)"`
