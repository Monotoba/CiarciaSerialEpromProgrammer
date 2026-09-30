# CiarciaSerialEpromProgrammer — verification status

Last checked: 2026-09-30

## Work in progress

No GitHub release has been published. A release decision is pending the remaining
checks below. The previous completion percentages and deployment-ready statements
were not supported by a completed clean-install and hardware validation record.

## Verified locally

Environment: Linux, Python 3.12.14, PySide6/Qt 6.11.2; Qt offscreen platform.

- Clean-clone setup completed with `bash scripts/setup.sh`.
- All 129 tests passed, including GUI tests; combined statement/branch coverage
  was 73.49%. Serial communication tests use mocks.
- Ruff passed for `src/`, `tests/`, and `scripts/check_wheel.py`.
- A built wheel imported the entry point and opened the GUI in an isolated
  subprocess outside the checkout.
- Fixed package discovery to include the GUI subpackage.
- Fixed three GUI tests that blocked on modal dialogs. The tests now mock the
  dialog methods and verify the expected messages.

## CI results and further changes

Linux now runs the complete GUI suite with pytest-qt, rather than uninstalling
pytest-qt and excluding GUI tests. Every platform builds and checks a wheel.
A 15-minute job timeout prevents unbounded waits, and matrix jobs run independently.
The packaging/dialog/EGL fixes passed all nine OS/Python matrix jobs and lint
on GitHub (run 36718482321). The later transfer-boundary changes require a fresh
CI run.

## Remaining checks

- Confirm the new GitHub Actions results on Linux, macOS, and Windows.
- Review documented features against the code and test coverage.
- Validate split 64 KiB transfers with compatible physical firmware.
  Host framing now uses two 32 KiB commands and rejects address overflow.
- Validate hardware compatibility, voltages, and programming behavior on a
  documented physical configuration; no hardware validation was performed here.
- Resolve license documentation and add a license file. README and package
  metadata currently declare MIT; GitHub does not recognize a repository license.
- Add GitHub description/topics and contributor guidance.
- Decide on release version and status after validation.
