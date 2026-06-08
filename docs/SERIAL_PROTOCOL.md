# Serial Protocol Specification

## Overview

The Serial EPROM Programmer communicates with a hardware device over RS-232/USB-serial. This document specifies the wire-level protocol.

## Connection Parameters

| Parameter | Value |
|-----------|-------|
| Baud Rate | 300–38400 (user selectable, default 9600) |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |
| Flow Control | None |
| Timeout | 3.0 seconds |

## Protocol Overview

The protocol is request-response, synchronous:

1. Host sends command byte + parameters
2. Host sends data (if applicable)
3. Device processes operation
4. Device sends response (if applicable)
5. Repeat

## Commands

### Read Command

**Purpose**: Read data from EPROM into host memory

**Format**:

```
[1 byte]  [2 bytes]      [2 bytes]
R         Address (LE)   Length (LE)
0x52      0x00-0xFFFF    0x0001-0x8000
```

**Example**: Read 256 bytes starting at address 0x0000

```
Byte 0: 0x52           ; 'R' command
Byte 1: 0x00           ; Address low (0x00)
Byte 2: 0x00           ; Address high (0x00)
Byte 3: 0x00           ; Length low (0x00)
Byte 4: 0x01           ; Length high (0x01)
```

**Response**: Device sends N bytes in sequence

```
Byte 0-N: [EPROM data]
```

**Timing**:
- Command transmission: ~5ms @ 9600 baud
- Per-byte read: ~5-50ms (depends on hardware)
- Total for 256 bytes @ 9600: ~1-2 seconds

### Program Command

**Purpose**: Write data to EPROM from host memory

**Format**:

```
[1 byte]  [2 bytes]      [2 bytes]     [N bytes]
P         Address (LE)   Length (LE)   Data
0x50      0x00-0xFFFF    0x0001-0x8000 [bytes]
```

**Example**: Program 32 bytes starting at 0x0100

```
Byte 0: 0x50           ; 'P' command
Byte 1: 0x00           ; Address low (0x00)
Byte 2: 0x01           ; Address high (0x01)
Byte 3: 0x20           ; Length low (0x20 = 32)
Byte 4: 0x00           ; Length high (0x00)
Byte 5-36: [32 data bytes]
```

**Response**: No explicit response (command succeeds if all bytes received)

**Timing**:
- Per-byte program: ~10-100ms (depends on EPROM type)
- Verify time: ~1-2 seconds per 256 bytes
- Total for 256 bytes: 2-5 seconds

## Byte Encoding

### 16-Bit Words (Address, Length)

All multi-byte values use **little-endian** encoding:

```
0x1234 → [0x34, 0x12]  (low byte first, high byte second)
```

**Examples**:

| Value | Low Byte | High Byte |
|-------|----------|-----------|
| 0x0000 | 0x00 | 0x00 |
| 0x0100 | 0x00 | 0x01 |
| 0x1234 | 0x34 | 0x12 |
| 0xFFFF | 0xFF | 0xFF |

### Address Range

Valid address range depends on EPROM type:

| EPROM | Size | Max Address |
|-------|------|-------------|
| 2716 | 2KB | 0x07FF |
| 2732 | 4KB | 0x0FFF |
| 2764 | 8KB | 0x1FFF |
| 27128 | 16KB | 0x3FFF |
| 27256 | 32KB | 0x7FFF |

Addressing beyond max address is hardware-dependent (may wrap or fail silently).

## Error Handling

The protocol has no explicit error codes. Failures manifest as:

1. **Timeout**: No response within 3 seconds
   - Serial port disconnected
   - Device powered off
   - Wrong baud rate
   - Corrupt data on wire

2. **Incomplete read**: Fewer bytes received than requested
   - Connection loss mid-operation
   - Hardware failure

3. **Silent failure**: All bytes received but operation didn't work
   - Device firmware bug
   - Incorrect parameters
   - Hardware timeout

## Typical Timing

### Read 2KB (2716)

```
Send command: ~5ms
Send address+length: ~5ms
Receive 2048 bytes @ 9600: ~1.7 seconds (9600 bits/sec, 10 bits/byte)
Total: ~1.8 seconds
```

### Program 2KB (2716)

```
Send command: ~5ms
Send address+length+data: ~2 seconds
Programming (hardware): ~10 seconds
Total: ~12 seconds
```

### Blank Check 32KB (27256)

```
Same as Read 32KB: ~25 seconds
```

## Handshaking

The protocol assumes a simple request-response model with no handshaking:

- Host sends complete command
- Host waits for response
- Device responds with data or acknowledgment
- No flow control (RTS/CTS not used)

If the host loses synchronization (receives garbage), the only recovery is to:
1. Wait for timeout (3 seconds)
2. Close and reopen serial port
3. Retry command

## Example: Read 256 Bytes from 0x1000

**Host Sends**:
```
0x52 0x00 0x10 0x00 0x01
 R   0x00 0x10 0x00 0x01
     ^^^^^^     ^^^^^^
     Addr      Length
     0x1000    0x0100
```

**Device Responds**:
```
[256 bytes of EPROM data starting at 0x1000]
```

## Example: Program 4 Bytes at 0x0000

**Host Sends**:
```
0x50 0x00 0x00 0x04 0x00 0xAA 0xBB 0xCC 0xDD
 P   0x00 0x00 0x04 0x00  [4 data bytes]
     ^^^^^^     ^^^^^^
     Addr      Length
     0x0000    0x0004
```

**Device Responds**: (none)

## Constraints and Limitations

1. **No checksums**: Corrupted data is not detected
2. **No retries**: Failed operations require manual retry
3. **Blocking**: Host must wait for each operation to complete
4. **No buffering**: Cannot queue multiple commands
5. **Synchronous only**: No interrupt-driven callbacks

## Future Extensions (Not Currently Implemented)

Possible future enhancements to the protocol:

- **Command codes for erase, verify, blank-check** (currently done via read in host)
- **Checksum bytes** (CRC-16 or simple sum)
- **Hardware status codes** (current version, temperature, etc.)
- **Asynchronous notification** (progress interrupts)

## Compatibility

This protocol is compatible with simple, low-cost EPROM programmer designs that:

- Implement serial RS-232 interface
- Support basic read and program operations
- Use little-endian 16-bit addressing
- Implement simple byte-streaming I/O

## Testing

To verify protocol compliance of a device:

```python
from serial_eprom_programmer.programmer import SerialEpromProgrammer

prog = SerialEpromProgrammer('/dev/ttyUSB0', 9600)

# Read 16 bytes from 0x0000
data = prog.read_eprom(0x0000, 16)
print(f"Read: {data.hex()}")

# Program 4 bytes at 0x0000 with pattern
prog.program_eprom(0x0000, b'\xAA\xBB\xCC\xDD')

# Verify by reading back
verify = prog.read_eprom(0x0000, 4)
print(f"Expected: aabbccdd")
print(f"Got:      {verify.hex()}")

prog.close()
```

## References

- RS-232 Serial Communication Standard
- 27-series EPROM Datasheets (Intel, AMD)
- pyserial Documentation: https://pyserial.readthedocs.io/
