# Hardware Documentation — Serial EPROM Programmer

## Historical Context

This software is a modern implementation for the **Steve Ciarcia Serial EPROM Programmer** originally featured in **BYTE Magazine, February 1985** ("Digital Notebook" column).

### Original Hardware
- **Publication**: BYTE Magazine, Vol. 10, No. 2, February 1985
- **Design**: Steve Ciarcia's innovative serial-based EPROM programmer
- **Purpose**: Affordable EPROM programming for hobbyists and professionals
- **Protocol**: RS-232 serial communication with simple command structure
- **Supported Devices**: Classic Intel 27-series EPROMs (2716, 2732, 2764, 27128, 27256)

### Original Article
See `docs/Hardware/198502_Byte_Magazine_Vol_10-02_Computing_and_the_Sciences (1).pdf` for the original 1985 design and implementation details.

---

## 2024 Upgrade Overview

This modernized implementation preserves the original spirit while incorporating contemporary improvements:

### Hardware Upgrades

#### 1. **UART Replacement: AY3-1015 → Arduino Nano**
**Original**: AY3-1015 UART IC (from Steve Ciarcia's February 1985 design)
**Upgraded To**: Arduino Nano (ATmega328P-based microcontroller)

**Benefits**:
- Eliminates separate UART IC dependency
- Built-in USB-to-Serial conversion (CH340 or FT232RL on-board)
- Programmable firmware for future enhancements
- Easier to repair/replace (single module vs. discrete components)
- No external crystal oscillator needed (built-in 16MHz)

**Firmware Implications**:
- Simplified serial protocol handling via Arduino IDE
- Can add intelligent error correction without hardware redesign
- Enables EEPROM-based device profile storage on Arduino
- Potential for wireless upgrades via Bluetooth module addition

#### 2. **Address Bus Expansion**
**Original**: 16 address lines (A0–A15) = 64KB addressing
**Upgraded**: Additional address line (A16) = 128KB addressing

**Hardware Changes**:
- Third address decoder chip (or extended latch) for A16
- Higher-capacity shift register or additional 8-bit latch
- Modified voltage regulation for increased current draw

**Addressing Capabilities**:
- Original: 64KB (27256 max: 32KB)
- Upgraded: 128KB (27512: 64KB, with room for future 128KB devices)

---

## Protocol Overview

### Original Protocol (1985)
Simple RS-232 command structure optimized for 300-9600 baud:

```
Command Format: <CMD><ADDRESS_HI><ADDRESS_LO><DATA>
Response: <ACK|NAK><DATA>

Commands:
  R - Read byte at address
  W - Write byte at address
  B - Blank check
  P - Program device
  V - Verify
  C - Clear buffer
```

### Modern Implementation Protocol
**Backward Compatible** with original, with extensions:

```
Enhanced Format: <CMD>[<LEN>][<ADDR>][<DATA>][<CHK>]
- CMD: Single command byte
- LEN: Optional payload length
- ADDR: 2-3 byte address (supports extended addressing)
- DATA: Variable-length data payload
- CHK: Optional checksum for reliability

Baud Rates: 150–230400 bps (original: 300–19200)
Handshaking: Hardware flow control support (RTS/CTS)
Error Detection: Checksum validation on all transfers
```

**New Features**:
- Multi-byte addressing for 128KB+ devices
- Bulk programming (256+ bytes without pause)
- Device auto-detection
- Checksum validation
- Programmable device profiles

---

## Current Device Support

### Implemented
- 2716 (2KB) ✓
- 2732 / 2732A (4KB) ✓
- 2764 (8KB) ✓
- 27128 (16KB) ✓
- 27256 (32KB) ✓
- 27512 (64KB) ✓

### Addressing Ceiling: 64KB (via 16-bit address bus)

---

## Future Hardware Enhancements

### Phase 1: Near-Term (Moderate Complexity)

#### Support for 27C devices (CMOS EPROM, pin-compatible)
- **Examples**: 27C256, 27C512, 27C020
- **Hardware Changes Needed**: None (pin-compatible with 27-series)
- **Electrical Changes Needed**: Different programming voltages (12V vs. 25V)
  - Additional voltage regulator for 12V (CMOS standard)
  - Voltage selection relay or jumper
- **Software Changes**: Device profile selection, voltage table lookup
- **Effort**: Low – voltage handling only

#### Support for 27xx128K devices (128KB EPROM)
- **Examples**: 27C128, 27C256 (existing), hypothetical 27C128
- **Hardware Changes Needed**: **None** – already addressed by A16 expansion
- **Software Changes**: Extended address handling (17-bit support)
- **Effort**: Low – firmware update only

#### Improved programming speed with buffering
- **Hardware Changes**: Increase buffer capacity (Arduino Nano has 1KB SRAM already)
- **Software Changes**: Implement 256-byte page programming
- **Benefit**: 4–10× faster programming for large devices
- **Effort**: Moderate – protocol redesign

---

### Phase 2: Medium-Term (Significant Work)

#### Support for 27xxxx mega-bit parallel devices (512KB to 1MB)
**Examples**: 27C010, 27C020, 27C040 (4Mbit = 512KB), 27C080 (8Mbit = 1MB)

**Hardware Changes Required**:
1. **Address Bus Expansion**: A0–A19 (20 lines for 1MB)
   - Additional 74LS373 latches (3–4 more for full 1MB support)
   - Extended shift register or multiplexed addressing
   - Estimated board additions: 4–6 ICs, minor-to-moderate PCB redesign
   - Note: 27C040 (512KB) requires A0–A18 (19 lines); 27C080 requires full A0–A19

2. **Data Bus**: No change (still 8-bit parallel)

3. **Programming Voltage**: 12V–14V (vs. 25V for original 27-series)
   - Separate voltage regulator module
   - Relay-based voltage selection
   - Safety interlock (prevent wrong voltage to device)

4. **Programming Current**: Higher current capability
   - Beefier power supply (500mA → 1A)
   - Larger filter capacitors

5. **Increased Serial Throughput**:
   - Block programming requires faster protocol
   - Suggest 57600+ baud for practical speeds
   - Consider optional hardware handshake (RTS/CTS)

**Protocol Updates Needed**:
- Extended address commands (3-byte addresses instead of 2)
- Block programming mode (256–512 byte chunks)
- Device auto-detect and profile loading
- Progress reporting during long operations

**Software Changes**:
- Device registry expansion (27xxx family profiles)
- Voltage table lookup
- Block-mode file loaders
- Estimated effort: **Moderate-to-High** (20–30 hours)

**Addressing Ceiling with Full 27C support**: 1MB (27C080 max)
- 27C010 / 27C020 (1Mbit / 2Mbit = 128KB / 256KB): A0–A16 / A0–A17
- 27C040 (4Mbit = 512KB): A0–A18
- 27C080 (8Mbit = 1MB): A0–A19

**Estimated PCB Changes**: 30–40% redesign (slightly more complex than 512KB alone)
**Backward Compatibility**: Can be maintained with mode selection

---

### Phase 3: Advanced (Major Redesign)

#### Support for 28xxx Flash EEPROM devices
**Examples**: 28F256, 28F512, 28F010 (up to 16Mbit)

**Key Differences from EPROM**:
- **Voltage**: 12V programming, 5V operation
- **Programming**: Word-wide programming (both 8-bit and 16-bit variants)
- **Erase**: Sector-based or bulk erase (vs. UV erase)
- **Protocol Complexity**: Much more complex command sequences

**Hardware Changes Required**:
1. **Address Bus**: A0–A20 (21 lines for 16Mbit)
   - Major address bus expansion
   - Multiplexing likely necessary to avoid pin count explosion

2. **Data Bus**: Potential 16-bit support
   - 16-bit variant of 28Fxxx requires dual byte handling
   - 8-bit mode easier but slower

3. **Programming Voltage**: 12V (same as CMOS 27Cxxx)
   - Can reuse voltage selection infrastructure

4. **Write Timing**: Critical timing for sector erase
   - Requires precise timing generator or timer IC
   - Arduino Nano insufficient for microsecond-level timing

5. **Protocol Complexity**:
   - Multi-command sequences for programming
   - Sector erase commands
   - Status register polling
   - Error handling for erase failures

**Software Architecture Changes**:
- State machine for complex erase/program cycles
- Sector mapping
- Progress reporting per sector
- Error recovery procedures

**Estimated PCB Changes**: 40–60% redesign
**Backward Compatibility**: Separate mode or separate programmer variant

**Estimated Effort**: **High** (50–80 hours + hardware redesign)

**Recommendation**: Consider this a "Version 2.0" hardware revision rather than upgrade path.

---

## Architecture Comparison

### Original (1985)
```
Host PC
   ↓ (RS-232 @ 9600 baud)
UART IC (8250)
   ↓
Shift Register / Latch (Address Bus)
   ↓
Address Decoder & Output Drivers
   ↓
EPROM Socket (DIP-28/32)
```

### Current (2024)
```
Host PC
   ↓ (USB-Serial @ 150–230400 baud)
Arduino Nano (ATmega328P)
   ├─ UART interface (USB-Serial bridge)
   ├─ Digital I/O for shift registers
   └─ Programmable intelligence
       ↓
Shift Register / Latch (Address Bus + A16)
   ↓
Address Decoder & Output Drivers
   ↓
EPROM Socket (DIP-28/32)
```

### Proposed (Phase 2 - 4MB support)
```
Host PC
   ↓ (USB-Serial @ 57600 baud)
Arduino Nano (upgraded ATmega2560 for more I/O)
   ├─ UART interface (optimized for faster baud)
   ├─ Digital I/O for shift registers (expanded)
   ├─ Analog comparator (for voltage monitoring)
   └─ Timer IC (for precise timing)
       ↓
Extended Shift Register / Latch (A0–A18)
   ↓
Advanced Address Decoder & Drivers
   ↓
Larger Package Socket (DIL-40 or surface mount)
```

---

## Recommendations for Next Hardware Revision

### Priority 1 (Essential for 27C support)
- [ ] Dual voltage regulators (25V for 27-series, 12V for 27C-series)
- [ ] Voltage selection relay with safety interlock
- [ ] Test points for voltage verification

### Priority 2 (Useful for 27512 and beyond)
- [ ] Extended address bus to A18 (supports up to 256KB)
- [ ] Improved shift register layout for speed
- [ ] Optional hardware handshake (RTS/CTS)

### Priority 3 (For 28xxx flash support)
- [ ] Dual-mode socket design (or separate programmer)
- [ ] 16-bit data path option
- [ ] Sector erase support (hardware design TBD)
- [ ] Timing precision enhancement

### Optional Enhancements
- [ ] LED indicators for each address line (diagnostics)
- [ ] Test socket for verification before main socket
- [ ] EEPROM on Arduino for device profile storage
- [ ] Wireless upload via Bluetooth/WiFi module

---

## Software-Only Paths

### Without Major Hardware Changes
What we can do with current hardware (1 Arduino Nano + shift register):

1. **Full 27-series support** (2716–27256) ✓ **DONE**
2. **Add 27512 support** ✓ **DONE**
3. **Add 27C-series support** (CMOS) ✓ **Possible** – just need voltage selection
4. **Improve speed** ✓ **Possible** – block programming via buffering
5. **Better error recovery** ✓ **Possible** – protocol enhancements

### Why mega-bit 27xxxx and 28xxx require hardware changes
- **Address lines**: 20 bits for 1MB / 27C080 (we have 16 for 64KB)
  - 27C010 (128KB) needs A0–A16 (17 lines)
  - 27C040 (512KB) needs A0–A18 (19 lines)  
  - 27C080 (1MB) needs A0–A19 (20 lines)
- **Voltage support**: Multiple programming voltages (we have one fixed 12V from Arduino regulation)
- **Timing precision**: Microsecond-level control (Arduino timers work but timing-critical for some devices)
- **Current capacity**: Higher programming current needed (power supply upgrade)

---

## Testing & Validation

### Current Hardware Validation
- Tested successfully with: 2716, 2732, 2732A, 2764, 27128, 27256, 27512
- Baud rates: 150–230400 bps all functional
- Dark/light theme compatibility confirmed
- Help system fully documented

### Recommended Test Suite for Hardware Upgrades
1. **Voltage verification**: Measure actual voltages at socket
2. **Address line testing**: Exercise all address lines with patterns
3. **Timing validation**: Verify program/erase timing with oscilloscope
4. **Bulk programming**: Load large files and verify sector-by-sector
5. **Error injection**: Test error recovery with intentional failures
6. **Backward compatibility**: Verify original 27-series still works

---

## References

- **Original Design**: BYTE Magazine, February 1985, Steve Ciarcia
- **Intel 27-series Datasheets**: Pin configurations and programming voltages
- **Intel 28F-series Datasheets**: Flash EEPROM programming procedures
- **Arduino Nano Documentation**: Pinout and capabilities
- **RS-232 Standard**: Serial communication protocol (EIA-232)

---

## Contact & Questions

For hardware upgrade discussions or design reviews, refer to the GitHub issues or contact the development team.

This is living documentation and will be updated as hardware enhancements progress.
