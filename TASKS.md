# CiarciaSerialEpromProgrammer — Task Checklist

**Last updated**: 2026-06-08

## Phase 1: Project Scaffolding — COMPLETE ✅

- ✅ Create `pyproject.toml` with metadata, dependencies, tool configs
- ✅ Create `requirements.txt` with runtime dependencies (PySide6, pyserial)
- ✅ Create `requirements-dev.txt` with dev dependencies (pytest, pytest-qt, pytest-cov, ruff, mypy)
- ✅ Create `.gitignore` for Python, venv, IDE artifacts
- ✅ Create `setup.sh` — Python version check, venv creation, pip/uv upgrade, git init
- ✅ Create `scripts/run.sh` — Venv activation + app launch
- ✅ Create `scripts/test.sh` — Venv activation + pytest with coverage
- ✅ Make setup.sh, run.sh, test.sh executable (chmod +x)
- ✅ Create `MEMORY.md` — Architecture decisions, extensibility points
- ✅ Create `STATUS.md` — Progress tracking document
- ✅ Create `TASKS.md` — This task checklist
- ✅ Initialize git repo and commit Phase 1 (pending full test)

---

## Phase 2: Refactoring into Modular Package — IN PROGRESS 🔄

### Package Structure
- ⏳ Create `src/serial_eprom_programmer/` directory
- ⏳ Create `src/serial_eprom_programmer/__init__.py` with public API exports
- ⏳ Create `src/serial_eprom_programmer/devices.py`:
  - ⏳ Define `EpromType` frozen dataclass
  - ⏳ Define `EPROM_TYPES` dict with all 6 chip types
- ⏳ Create `src/serial_eprom_programmer/utils.py`:
  - ⏳ Move `hex_dump()` function
- ⏳ Create `src/serial_eprom_programmer/programmer.py`:
  - ⏳ Move `SerialEpromProgrammer` class
  - ⏳ Ensure ZERO Qt imports
- ⏳ Create `src/serial_eprom_programmer/worker.py`:
  - ⏳ Move `Worker` class from main file
  - ⏳ Import from programmer.py
- ⏳ Create `src/serial_eprom_programmer/gui/__init__.py`
- ⏳ Create `src/serial_eprom_programmer/gui/main_window.py`:
  - ⏳ Move `MainWindow` class from main file
  - ⏳ Import from worker.py, devices.py, utils.py
- ⏳ Create `src/serial_eprom_programmer/gui/widgets.py` (empty, ready for future components)
- ⏳ Create `src/serial_eprom_programmer/main.py`:
  - ⏳ Thin entry point: imports MainWindow, creates QApplication, runs main()
- ⏳ Backup original: `src/SerialEromPrgDriver.py.bak`
- ⏳ Test imports:
  - ⏳ `python -c "from serial_eprom_programmer.devices import EpromType, EPROM_TYPES"`
  - ⏳ `python -c "from serial_eprom_programmer.utils import hex_dump"`
  - ⏳ `python -c "from serial_eprom_programmer.programmer import SerialEpromProgrammer"`
  - ⏳ `python -c "from serial_eprom_programmer.worker import Worker"`
  - ⏳ `python -c "from serial_eprom_programmer.gui.main_window import MainWindow"`
  - ⏳ `python -c "from serial_eprom_programmer.main import main"`
- ⏳ Verify app still runs: `bash scripts/run.sh` (smoke test, no serial hardware needed)
- ⏳ Commit Phase 2 with message: "P2: refactor into package — devices, utils, programmer, worker, gui"

---

## Phase 3: Test Suite — PENDING ⏳

### Test Infrastructure
- ⏳ Create `tests/__init__.py`
- ⏳ Create `tests/conftest.py`:
  - ⏳ `tmp_bin_file` fixture (temporary binary file with known content)
  - ⏳ Mock serial factory fixture
- ⏳ Create `pytest.ini` or add pytest config to `pyproject.toml` (already done)

### Unit Tests
- ⏳ Create `tests/test_devices.py`:
  - ⏳ Test `EpromType` dataclass instantiation
  - ⏳ Test `EPROM_TYPES` dict keys and sizes
  - ⏳ Test that all 6 known chips are present
- ⏳ Create `tests/test_utils.py`:
  - ⏳ Test `hex_dump()` with known byte patterns
  - ⏳ Verify hex formatting (uppercase, two digits)
  - ⏳ Verify address offsets
  - ⏳ Verify ASCII substitution (non-printable → '.')
- ⏳ Create `tests/test_programmer.py`:
  - ⏳ Mock `serial.Serial`
  - ⏳ Test `send_byte()` writes exactly 1 byte
  - ⏳ Test `recv_byte()` reads 1 byte, raises TimeoutError on empty
  - ⏳ Test `send_word()` writes 2 bytes (little-endian)
  - ⏳ Test `read_eprom()` sends 'R', address, length, receives N bytes
  - ⏳ Test `program_eprom()` sends 'P', address, length, sends N bytes
  - ⏳ Test progress callback is called correctly
  - ⏳ Test `close()` closes serial port
- ⏳ Create `tests/test_worker.py`:
  - ⏳ Mock `SerialEpromProgrammer`
  - ⏳ Test `Worker.run()` with action="read" emits finished(data)
  - ⏳ Test `Worker.run()` with action="blank" emits finished(errors)
  - ⏳ Test `Worker.run()` with action="program" emits finished(None)
  - ⏳ Test `Worker.run()` with action="verify" emits finished(errors)
  - ⏳ Test `Worker.run()` with invalid action raises ValueError
  - ⏳ Test `Worker.run()` exception emits failed(message)

### GUI Tests
- ⏳ Create `tests/test_gui.py`:
  - ⏳ Use pytest-qt `qtbot` fixture
  - ⏳ Test `MainWindow` instantiation
  - ⏳ Test `refresh_ports()` populates port combo
  - ⏳ Test `select_eprom()` changes buffer size
  - ⏳ Test `base_addr()` parses hex correctly
  - ⏳ Test `load_binary()` / `save_binary()` with tmp_bin_file fixture
  - ⏳ Test `fill_ff()` resets buffer
  - ⏳ Test `update_hex_view()` shows hex dump
  - ⏳ Test `start_worker()` guard prevents concurrent operations
  - ⏳ Smoke test: open window, click buttons, check no crashes

### Coverage Report
- ⏳ Run `bash scripts/test.sh`
- ⏳ Verify ≥80% line coverage (target all modules)
- ⏳ Generate HTML report in `htmlcov/`
- ⏳ All tests pass (exit code 0)
- ⏳ Commit Phase 3 with message: "P3: test suite — 80%+ coverage, all passing"

---

## Phase 4: Documentation — PENDING ⏳

### Documentation Files
- ⏳ Create `README.md` at project root:
  - ⏳ Project title and one-liner
  - ⏳ Features overview
  - ⏳ Supported EPROM types
  - ⏳ Quick-start (clone, setup.sh, run.sh)
  - ⏳ Links to docs/
  - ⏳ License, author info
- ⏳ Create `docs/USER_GUIDE.md`:
  - ⏳ Installation instructions (setup.sh)
  - ⏳ Hardware wiring (serial port pinout, voltage levels)
  - ⏳ Supported EPROM types with part numbers
  - ⏳ Step-by-step usage:
    - ⏳ Connect hardware
    - ⏳ Select serial port
    - ⏳ Select EPROM type
    - ⏳ Load binary file / fill buffer
    - ⏳ Read / Program / Verify
  - ⏳ Troubleshooting: common issues and solutions
  - ⏳ FAQ
- ⏳ Create `docs/DEVELOPER_GUIDE.md`:
  - ⏳ Project structure overview (package layout)
  - ⏳ Setting up dev environment (setup.sh, venv)
  - ⏳ Running tests (bash scripts/test.sh)
  - ⏳ Code style (ruff, mypy)
  - ⏳ How to add a new EPROM type
  - ⏳ How to add a new serial command
  - ⏳ Module responsibilities (devices, utils, programmer, worker, gui)
  - ⏳ Testing strategy and coverage
  - ⏳ Git workflow and commit naming
- ⏳ Create `docs/SERIAL_PROTOCOL.md`:
  - ⏳ Wire-level protocol specification
  - ⏳ Command format (single-byte commands)
  - ⏳ Read command: byte sequence, timing
  - ⏳ Program command: byte sequence, timing
  - ⏳ Address/length encoding (little-endian 16-bit words)
  - ⏳ Baud rate options and defaults
  - ⏳ Timeout behavior (3.0s configured)
  - ⏳ Example: pseudo-code for read/program
- ⏳ Create `docs/EXTENDING.md`:
  - ⏳ How to add a new EPROM type (code example)
  - ⏳ How to add a new file format (Intel HEX, Motorola S-record)
  - ⏳ How to add GUI components (widgets.py)
  - ⏳ How to add a CLI mode (example code)
  - ⏳ How to add a new serial command
  - ⏳ Extension examples with full code snippets

### Documentation Verification
- ⏳ All markdown files are valid
- ⏳ All code examples compile/run correctly
- ⏳ Links in docs are correct (relative paths)
- ⏳ User guide is complete and clear
- ⏳ Developer guide covers all modules
- ⏳ Extending guide has runnable examples
- ⏳ Commit Phase 4 with message: "P4: docs — user guide, developer guide, protocol spec, extending guide"

---

## Final Verification — PENDING ⏳

- ⏳ Clone repo to clean directory
- ⏳ Run `bash setup.sh` — should complete without errors
- ⏳ Run `bash scripts/run.sh` — app window should open, port list populates
- ⏳ Run `bash scripts/test.sh` — all tests pass, ≥80% coverage
- ⏳ Test imports:
  - ⏳ `python -c "from serial_eprom_programmer.programmer import SerialEpromProgrammer"`
  - ⏳ `python -c "from serial_eprom_programmer.main import main"`
  - ⏳ Verify NO errors
- ⏳ Manual test (no hardware needed):
  - ⏳ Open app window
  - ⏳ Select EPROM type (2716, 2732, etc.)
  - ⏳ Load binary file (create test binary in tmp/)
  - ⏳ Verify hex view updates correctly
  - ⏳ Check log output is clear

---

## Summary

| Phase | Status | Items | Completed |
|-------|--------|-------|-----------|
| 1 | ✅ COMPLETE | 11 | 11 |
| 2 | 🔄 IN PROGRESS | 28 | 0 |
| 3 | ⏳ PENDING | 30 | 0 |
| 4 | ⏳ PENDING | 22 | 0 |
| Final | ⏳ PENDING | 11 | 0 |
| **TOTAL** | | 102 | 11 |

**Progress**: 11/102 items (10.8%)

---

## Notes for Power Outage Recovery

In case of interruption:
1. Check `STATUS.md` for current phase and completion percentage
2. Check this `TASKS.md` for what was last being worked on
3. Check git log for last commit: `git log --oneline | head -5`
4. Resume from the first uncompleted task in the current phase
5. All state is tracked here and in `.git`

---

## Commit History Template

```
P1: project scaffolding — pyproject, setup.sh, gitignore
P2: refactor into package — devices, utils, programmer, worker, gui
P3: test suite — 80%+ coverage, all passing
P4: docs — user guide, developer guide, protocol spec, extending guide
```
