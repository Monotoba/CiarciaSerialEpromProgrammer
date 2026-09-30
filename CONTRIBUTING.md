# Contributing

Contributions are welcome, especially reproducible bug reports, file-format
fixtures, GUI tests, and documented hardware compatibility results.

## Set up and validate

```bash
git clone https://github.com/Monotoba/CiarciaSerialEpromProgrammer.git
cd CiarciaSerialEpromProgrammer
bash scripts/setup.sh
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen python -m pytest
ruff check src/ tests/ scripts/check_wheel.py
python -m pip wheel . --no-deps --wheel-dir dist
QT_QPA_PLATFORM=offscreen python scripts/check_wheel.py
```

On Windows, create a venv with `py -m venv .venv`, activate it with
`.venv\Scripts\Activate.ps1`, and run `python -m pip install -e ".[dev]"`.
Set `$env:QT_QPA_PLATFORM = "offscreen"` in PowerShell before the test commands.
The build check expects exactly one wheel in `dist/`; remove old wheels first.

## Submit a change

Open an issue describing the problem or feature, then submit a focused pull
request. Prefer refactoring existing code and preserve working behavior.
Include regression tests for code changes and describe validation in the PR.
Keep hardware I/O mocked in automated tests; real hardware checks must be
identified separately. CI runs Python 3.10–3.12 on Linux, macOS, and Windows.

For a bug, include OS, Python/PySide6 versions, selected device, file format,
steps to reproduce, expected/actual results, and logs. For hardware results,
include the schematic/firmware revision, exact chip part number, voltage and
programming settings, and independent read-back evidence. A serial mock passing
does not establish physical compatibility.

## Scope and licensing

The current host supports the protocol in [docs/SERIAL_PROTOCOL.md](docs/SERIAL_PROTOCOL.md).
Consult [docs/FEATURE_STATUS.md](docs/FEATURE_STATUS.md) before adding hardware claims.
Contributions to original project code/documentation are under BSD-2-Clause.
See [NOTICE](NOTICE) for the third-party historical material exclusion.
