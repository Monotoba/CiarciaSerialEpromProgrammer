# 1.0.0a1 — experimental host-software alpha

This first alpha is for evaluating the Python/PySide6 desktop host and contributing
software improvements. Physical programmer compatibility is unvalidated. Matching
Arduino firmware is not included, and the hardware expansion documents are proposals.

## Available software

- EPROM profiles for 2716–27512; profiles do not establish electrical compatibility.
- Serial read/program and host-side blank-check/verify.
- Hex/ASCII editing, fills, file conversion, progress, logs, and themes.
- Installable GUI package with wheel launch checks on Linux, macOS, and Windows.
- Transfers split into at most 32 KiB commands, with address-boundary guards.
- BSD-2-Clause for original project work; historical BYTE material is excluded.

## Installation

With Python 3.10 or newer, install the release wheel using:

```sh
python -m pip install serial_eprom_programmer-1.0.0a1-py3-none-any.whl
serial-eprom-programmer
```

PySide6 and pyserial are installed as dependencies. Linux also needs the Qt runtime
libraries listed in the README. No PyPI publication is part of this release plan.

## Limits and validation

Serial tests use mocks. Programming progress measures bytes sent, not confirmed
programmed cells; there is no program ACK/NAK or wire checksum. Consecutive command
support and pacing must be confirmed with the actual firmware before hardware use.
The host address space is 16-bit. Independent file-format interoperability, theme
preferences, and built-in help still need broader validation.

Local alpha validation on 2026-10-07: 130 tests passed with 73.49% combined
statement/branch coverage; Ruff passed; wheel and source distribution built; the
wheel GUI launched outside the checkout; both packages include LICENSE/NOTICE
and exclude historical PDFs. The version-consistency test checks runtime against
installed distribution metadata. CI results are recorded in the preparation PR.

Artifact checksums are added
to the GitHub release when the final packages are built from the merged release commit.
