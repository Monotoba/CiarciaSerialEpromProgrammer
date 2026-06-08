# User Guide — Serial EPROM Programmer

## Table of Contents

1. [Installation](#installation)
2. [Hardware Setup](#hardware-setup)
3. [Starting the Application](#starting-the-application)
4. [Main Window Overview](#main-window-overview)
5. [Step-by-Step Usage](#step-by-step-usage)
6. [Supported File Formats](#supported-file-formats)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Installation

### System Requirements

- Python 3.10 or higher
- RS-232 or USB-serial programmer device
- Linux, macOS, or Windows

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/CiarciaSerialEpromProgrammer.git
   cd CiarciaSerialEpromProgrammer
   ```

2. **Run the setup script**:
   ```bash
   bash scripts/setup.sh
   ```
   
   This will:
   - Check Python version (3.10+)
   - Create a virtual environment (`.venv`)
   - Install all dependencies (PySide6, pyserial)
   - Initialize git repository

3. **Verify installation**:
   ```bash
   bash scripts/run.sh
   ```
   
   The application window should open.

## Hardware Setup

### Serial Connection

Your EPROM programmer device must communicate via RS-232/USB-serial. Typical setup:

1. **USB Cable**: Connect programmer to computer via USB-to-serial adapter (if needed)
2. **Power**: Supply appropriate power to programmer (usually 5V, 12V, or 28V depending on device)
3. **EPROM Socket**: Insert EPROM into programmer socket

### Port Identification

- **Linux**: `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyS0` (serial ports)
- **macOS**: `/dev/cu.usbserial-*` (USB serial adapters)
- **Windows**: `COM1`, `COM2`, `COM3`, etc.

To list available ports on Linux:
```bash
ls /dev/tty* | grep -E 'USB|S[0-9]'
```

### Voltage Levels

Classic EPROMs require different voltage levels for programming:

| EPROM Type | Vcc (Operating) | Vpp (Programming) |
|-----------|-----------------|-------------------|
| 2716/2732 | 5V | 25V |
| 2764/27128 | 5V | 12.5V |
| 27256 | 5V | 12.75V |

Your programmer device must supply appropriate voltages. Consult your programmer's manual.

## Starting the Application

```bash
bash scripts/run.sh
```

Or activate the virtual environment and run directly:
```bash
source .venv/bin/activate
python -m serial_eprom_programmer.main
```

## Main Window Overview

The application window has five main sections:

### 1. Connection / EPROM (Top Group)

- **Port**: Select serial port from dropdown
  - Click "Refresh Ports" to rescan for connected devices
- **Baud**: Serial communication speed
  - Standard options: 300, 600, 1200, 2400, 4800, 9600 (default), 19200, 38400
  - Your programmer must match the selected baud rate
- **EPROM**: Chip type selector
  - 2716 (2KB), 2732 (4KB), 2732A (4KB), 2764 (8KB), 27128 (16KB), 27256 (32KB), 27512 (64KB)
  - Selection determines buffer size and valid address range
- **Base Hex**: Starting address in hexadecimal (0000-FFFF for ≤64KB, up to FFFFFFFF for IHEX-32)
  - Example: `1000` means operations start at address 0x1000
  - Prefix with `$` optional: `$1000` is same as `1000`

### 2. File and Buffer Operations (Buttons)

- **Load File**: Open a file and load its contents into the buffer
  - Auto-detects format by file extension (see Supported File Formats below)
  - Buffer is pre-filled with 0xFF (EPROM default state)
  - File must fit within EPROM size
  - Base address automatically updated if file specifies one
- **Save File**: Write buffer contents to a file
  - Format auto-detected from file extension
  - Supported formats: Intel HEX, Motorola S-Record, Binary, Addressed Hex, and more
  - Saves entire buffer (even if file was smaller than EPROM)
- **Fill FF**: Reset entire buffer to 0xFF
  - Use before programming to erase working buffer
- **Refresh Dump**: Update hex view from current buffer
  - Automatically refreshed after load/fill, but can be manual
- **Edit Buffer**: Toggle edit mode to modify individual bytes directly
  - Click to enter edit mode (hex view turns light yellow, background highlight)
  - Modify hex values directly in the hex dump (2-character hex pairs like `FF`, `AA`, etc.)
  - Destructive operations (Read, Program, Blank Check, Verify, Load, Fill) are disabled during edit mode
  - **Apply Edits**: Click to validate and apply changes to the buffer
    - Size must match EPROM capacity
    - Hex values must be valid (00-FF)
  - **Cancel Edit**: Click to discard changes and return to view mode
    - Buffer remains unchanged

### 3. Operations (Buttons)

- **Read EPROM**: Read entire EPROM contents into buffer
  - Replaces buffer with data from hardware
  - Progress bar shows bytes read
- **Blank Check**: Verify entire EPROM is blank (all 0xFF)
  - Reports addresses of any non-blank bytes
  - Up to 50 non-blank addresses displayed
- **Program EPROM**: Write buffer contents to EPROM
  - Confirmation dialog required
  - Progress bar shows bytes written
  - Actual programming time depends on EPROM type
- **Verify EPROM**: Read and compare with buffer
  - Reports addresses where read ≠ buffer
  - Useful after programming to verify success

### 4. Progress Bar

Shows bytes processed during read/program/verify operations. Range is 0 to EPROM size.

### 5. Buffer Display (Hex Dump)

Shows current buffer contents as hex + ASCII:
- **Address Column** (left): Memory addresses
- **Hex Column** (middle): Byte values in hexadecimal (00-FF)
- **ASCII Column** (right): Printable characters, non-printable shown as '.'

Example:
```
0000: 4D 5A 90 00 03 00 00 00  MZ......
0010: 04 00 00 00 FF FF 00 00  ........
```

### 6. Log Pane

Displays status messages and operation results:
- "Selected 27256, 32768 bytes" — EPROM change
- "Loaded 256 bytes from firmware.bin" — File load
- "Program data sent." — Operation completed
- "ERROR: Port not found" — Failures with details

## Step-by-Step Usage

### Reading an EPROM

1. Select the correct **EPROM** type (e.g., 2764)
2. Select the **Port** (click Refresh if needed)
3. Click **Read EPROM**
4. Watch the progress bar complete
5. Verify "Read complete." in the log
6. View data in the hex dump
7. Click **Save Binary** to save to disk

### Programming an EPROM

1. Click **Load Binary** to load your firmware file
2. Review data in hex dump (verify correct content)
3. Click **Fill FF** if you want to reload and reprogram
4. Select **EPROM** type
5. Select **Port**
6. Click **Program EPROM**
7. Confirm in the dialog
8. Watch progress bar
9. Verify "Program data sent." in log
10. Click **Verify EPROM** to confirm programming succeeded
11. Log should show "Verify OK." on success

### Verifying an EPROM

After programming:
1. Ensure buffer still contains expected data (check hex dump)
2. Click **Verify EPROM**
3. Progress bar runs through entire EPROM
4. Log shows "Verify OK." on success or lists mismatches

### Blank Checking

Before programming a used EPROM:
1. Click **Blank Check**
2. Progress bar runs through entire EPROM
3. Log shows "Blank check OK." if all 0xFF, or lists non-blank addresses

### Editing the Buffer Directly

To modify individual bytes in the buffer without reloading a file:

1. Click **Edit Buffer** button
   - Hex view background turns light yellow
   - "Edit Buffer" button changes to "Apply Edits"
   - "Cancel Edit" button appears
   - All operation buttons are disabled (grayed out)

2. Edit the hex values directly:
   - Click in the hex dump area to edit
   - Modify 2-character hex pairs (e.g., change `FF` to `AA`)
   - Example: `0000: FF FF FF FF` → `0000: AA BB CC DD`
   - Do NOT edit the address column (left side) or ASCII column (right side)

3. When finished editing:
   - Click **Apply Edits** to validate and save changes to buffer
     - Checks that hex values are valid (00-FF)
     - Checks that edited buffer size matches EPROM capacity
     - Shows error dialog if validation fails
   - OR click **Cancel Edit** to discard changes
     - Restores the original hex dump
     - Buffer remains unchanged

4. After applying edits:
   - Hex view returns to normal (white background)
   - "Apply Edits" button changes back to "Edit Buffer"
   - "Cancel Edit" button disappears
   - All operation buttons are re-enabled
   - Proceed to **Program EPROM** to write changes to hardware

## Supported File Formats

The application supports multiple file formats for loading and saving EPROM data. The format is auto-detected by file extension.

### Standard Formats

**Intel HEX** (.hex, .ihx)
- Universal standard since 1973
- Used by: Arduino, PIC, AVR, ARM compilers, MPLAB, avr-gcc
- Format: `:LLAAAATTDD...CC` (colon-prefixed hex records)
- Supports checksums and addressing
- Limited to 64KB (use Intel IHEX-32 for larger devices)

**Binary** (.bin, .rom, .epr)
- Raw binary data
- No formatting or checksums
- Simplest and fastest format
- Ideal for small programs or kernels

**Motorola S-Record** (.mot, .srec, .s19, .s28, .sx)
- Motorola/Freescale standard since 1974
- Used by: 6800/6809, 68000, ColdFire, NXP automotive ECU
- Format: `STTNNAAAA[DD...]SS` (S-prefix records)
- Includes checksums and address validation
- Supports multiple record types (16-bit, 24-bit, 32-bit addressing)

**Addressed Hex Dump** (.ahex, .asc)
- Monitor program text format
- Format: `AAAA: HH HH HH ...` (address followed by hex bytes)
- Matches the hex view display in the application
- Tolerant parser (handles various spacing)

### Extended Formats (1990s-present)

**Intel IHEX-32** (.ihex32, .hex32)
- Extended Intel HEX with linear addressing (Type 0x04 records)
- Supports full 32-bit addressing (up to 4GB)
- Auto-emits extended address records when crossing 64KB boundaries
- Used for: ARM Cortex-M flash, modern microcontrollers
- Fully compatible with Intel HEX readers

**Tektronix Extended HEX** (.tek, .tektronix, .hex_tek)
- Test equipment and historical development tools
- Similar to Intel HEX but uses `%` prefix instead of `:`
- Format: `%LLAAAATTDD...CC`
- Used by: older Tektronix logic analyzers, vintage test equipment

**TI-TXT** (.txt, .ti_txt)
- Texas Instruments microcontroller format
- Used by: MSP430, TM4C (ARM Cortex-M4), other TI MCUs
- Format: Address directive `@XXXX` followed by space-separated hex pairs
- Supports non-contiguous memory blocks (gaps)
- Terminator record: `Q`

**MIF (Memory Initialization File)** (.mif)
- Xilinx/Altera FPGA block RAM initialization format
- Header: WIDTH, DEPTH specifications
- Format: `@address : value, value, ... ;`
- Content between `CONTENT BEGIN` and `END;`
- Auto-formats with 16 bytes per address block

### Historical Formats (1970s-80s)

**MOS Technology Paper Tape** (.mos, .papertape)
- KIM-1, Apple I, SYM-1, AIM-65 hobbyist computers (1976+)
- 6502-era systems
- Format: `;NNAAAADDDD...CC` (semicolon-prefixed records)
- Includes record count and checksum
- Terminator record with record count

### Choosing the Right Format

| Your Device | Recommended Format | Alternative |
|-----------|-------------------|------------|
| Arduino/ATmega | Intel HEX (.hex) | Binary (.bin) |
| PIC Microcontroller | Intel HEX (.hex) | S-Record (.srec) |
| ARM Cortex-M (flash >64KB) | Intel IHEX-32 (.ihex32) | Intel HEX (.hex) |
| 6502-based (Apple I, KIM-1) | Binary (.bin) | MOS Tape (.mos) |
| Motorola 68K/ColdFire | S-Record (.srec) | Intel HEX (.hex) |
| Texas Instruments MCU | TI-TXT (.txt) | Intel HEX (.hex) |
| FPGA Block RAM | MIF (.mif) | Intel HEX (.hex) |
| Generic/Unknown | Binary (.bin) | Addressed Hex (.ahex) |

## Troubleshooting

### "No port selected"

**Problem**: Error message when clicking Read/Program/Verify

**Solution**:
1. Click **Refresh Ports** to rescan
2. Connect programmer to USB/serial
3. Click **Refresh Ports** again
4. Select port from dropdown
5. Try operation again

### "Timed out waiting for byte"

**Problem**: Serial communication timeout after few seconds

**Solution**:
1. Verify port is correct (try other ports)
2. Check baud rate matches programmer (try 9600)
3. Verify programmer is powered on
4. Check USB/serial cable connection
5. Try a different USB port on computer

### "File too large"

**Problem**: File larger than selected EPROM size

**Solution**:
1. Check loaded file size and EPROM size in hex dump top-left
2. Select larger EPROM type if available (e.g., 27256 instead of 2764)
3. Or split large file to fit in smaller EPROM

### Verify fails but programming appeared successful

**Problem**: "Verify failed" but earlier said "Program data sent"

**Solution**:
1. Check programmer power supply (weak power can fail programming)
2. Try programming again (some EPROMs need multiple passes)
3. Check EPROM socket for loose chip
4. Try a different EPROM (current one may be bad)

### Port disappears after disconnect

**Problem**: Port was available, then vanished

**Solution**:
- Normal behavior for USB-serial adapters
- Click **Refresh Ports** to rescan
- Reconnect cable and refresh again

### Application crashes on startup

**Problem**: Window doesn't appear

**Solution**:
1. Check Python version: `python3 --version` (needs 3.10+)
2. Reinstall: `bash scripts/setup.sh`
3. Activate venv: `source .venv/bin/activate`
4. Run again: `python -m serial_eprom_programmer.main`

## FAQ

**Q: Can I use this with a parallel port programmer?**
A: No, this application only supports serial/USB-serial connections. Check your programmer documentation.

**Q: What's the difference between 2732 and 2732A?**
A: Both are 4KB EPROMs with identical programming protocols. Use either type selector.

**Q: Can I change baud rate while connected?**
A: Not recommended. Disconnect, change rate, then select port again.

**Q: Will an incorrect voltage damage the EPROM?**
A: Yes. Always verify your programmer supplies correct voltages. Check programmer manual before power-on.

**Q: Is it safe to pull power during programming?**
A: No. Always let programming complete and verify successfully.

**Q: How long does programming take?**
A: Depends on EPROM size and programmer speed, typically 1-30 seconds per chip.

**Q: Can I program multiple EPROMs in sequence?**
A: Yes. Read success in log, swap chip, repeat.

**Q: What's the maximum file size I can load?**
A: Limited by EPROM type. Max is 32KB (27256).
