# Feature implementation and validation

Reviewed 2026-09-30 against the current source and test suite.

| Feature | Implementation | Validation and limits |
|---|---|---|
| Seven EPROM profiles, 2716–27512 | `devices.py` registry and GUI selector | Registry and selection tests; profiles do not establish electrical compatibility |
| Read/program | `programmer.py`, `worker.py` | Mocked serial tests; no physical programmer validation |
| Full 64 KiB transfer | Two commands of at most 32 KiB each | Boundary regression tests; firmware must support consecutive commands |
| Blank-check/verify | Host reads and compares bytes | Worker tests; no dedicated device command or program acknowledgment |
| Hex/ASCII view, editing, fills | `gui/main_window.py`, `utils.py` | GUI edit/fill and hex-dump tests |
| Nine file formats | Binary, Intel HEX/IHEX-32, S-record, Tektronix HEX, TI-TXT, addressed hex, MOS tape, MIF handlers | Format detection and round-trip tests; not exhaustive interoperability testing |
| File dialogs | Load/save use the extension dispatcher | Some formats require All Files selection; dialog filters do not enumerate every supported extension |
| Port refresh and baud selector | GUI and pyserial port enumeration | GUI smoke tests; available baud rates depend on hardware/firmware |
| Progress and logs | Worker signals and GUI display | Worker and GUI tests; program progress measures bytes sent, not confirmed programmed cells |
| System/dark/light themes | `config.py`, `gui/theme_manager.py` | Implemented; persistent preferences and theme behavior need dedicated tests |
| Built-in help | `gui/help_dialog.py` | Implemented; content and navigation need dedicated tests |
| Installable GUI package | Package discovery includes GUI; wheel smoke script | Wheel import/launch tested on all CI platforms |
| Arduino replacement and A16 expansion | Hardware proposals | No firmware or validated circuit supplied; host addressing remains 16-bit |
| Checksums, ACK/NAK, RTS/CTS, automatic chip identification | Not implemented in serial protocol | File-format checksums are separate from wire-protocol validation |

## Next implementation and validation order

1. Obtain a documented firmware/hardware configuration and confirm read framing,
   split transfers, and timing. This is necessary before claims of compatibility.
2. Establish program completion/error semantics with that firmware; add explicit
   host support and tests if an acknowledgment or pacing mechanism is needed.
3. Add fixtures from independent tools for each file format and test nonzero
   base addresses, malformed inputs, and capacity boundaries.
4. Add dedicated theme/settings/help tests and include all supported formats in
   the file dialogs.
5. Add device families or extended addressing only alongside firmware, electrical
   requirements, and tests. A device name in the registry is not sufficient.

An experimental host-software prerelease can describe these limits. A hardware-
validated release requires reproducible physical evidence.
