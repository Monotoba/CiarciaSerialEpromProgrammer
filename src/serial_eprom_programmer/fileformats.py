"""Multi-format file I/O for EPROM programming (1970s-present).

Supported formats:
- Intel HEX (.hex, .ihx) — universal standard since 1973
- Motorola S-Record (.mot, .srec, .s19, .s28, .sx) — since 1974
- Addressed Hex Dump (.ahex) — monitor program format, hex editor text
- MOS Paper Tape (.mos, .papertape) — KIM-1, Apple I, SYM-1 (1976+)
- Raw Binary (.bin, .rom, .epr) — simple raw data
"""

from dataclasses import dataclass
from pathlib import Path


class FileFormatError(ValueError):
    """Raised when file format is invalid or cannot be parsed."""
    pass


@dataclass
class LoadResult:
    """Result of loading a file."""
    data: bytes
    base_addr: int
    format_name: str


class FileFormat:
    """Base class for file format handlers."""

    extensions: set[str]
    name: str

    def load(self, path: Path, buf_size: int) -> LoadResult:
        """Load file and return bytes.

        Args:
            path: File path
            buf_size: EPROM capacity in bytes (for validation)

        Returns:
            LoadResult with data, base address, and format name

        Raises:
            FileFormatError: If file is invalid or data too large
        """
        raise NotImplementedError

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        """Save bytes to file.

        Args:
            path: Output file path
            data: Bytes to save
            base_addr: Starting address for formats that support it
        """
        raise NotImplementedError


class BinaryFormat(FileFormat):
    """Raw binary format (.bin, .rom, .epr)."""

    extensions = {".bin", ".rom", ".epr"}
    name = "Binary"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        data = path.read_bytes()
        if len(data) > buf_size:
            raise FileFormatError(
                f"File is {len(data)} bytes, EPROM capacity is {buf_size} bytes"
            )
        return LoadResult(data, 0, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        path.write_bytes(data)


class IntelHexFormat(FileFormat):
    """Intel HEX format (.hex, .ihx). Format: :LLAAAATTDD...CC"""

    extensions = {".hex", ".ihx"}
    name = "Intel HEX"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF

        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith(':'):
                raise FileFormatError(f"Line {lineno}: missing ':' prefix")
            if len(line) < 11:
                raise FileFormatError(f"Line {lineno}: record too short")

            try:
                byte_count = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                expected_len = 11 + byte_count * 2

                if len(line) != expected_len:
                    raise FileFormatError(f"Line {lineno}: invalid length")

                data_hex = line[9 : 9 + byte_count * 2]
                if len(data_hex) != byte_count * 2:
                    raise FileFormatError(f"Line {lineno}: data length mismatch")

                data_bytes = bytes.fromhex(data_hex)

                # Verify checksum
                checksum_calc = (byte_count + (address >> 8) + (address & 0xFF) +
                                record_type + sum(data_bytes)) & 0xFF
                checksum_calc = (0x100 - checksum_calc) & 0xFF
                checksum_file = int(line[-2:], 16)

                if checksum_calc != checksum_file:
                    raise FileFormatError(
                        f"Line {lineno}: checksum mismatch "
                        f"(expected {checksum_file:02X}, got {checksum_calc:02X})"
                    )

                if record_type == 0x00:  # Data
                    if address + byte_count > buf_size:
                        raise FileFormatError(
                            f"Line {lineno}: data at 0x{address:04X} exceeds EPROM size"
                        )
                    data[address : address + byte_count] = data_bytes
                    base_addr = min(base_addr, address)

                elif record_type == 0x01:  # End of file
                    break

                elif record_type in (0x02, 0x04):  # Extended segment/linear address
                    raise FileFormatError(
                        f"Line {lineno}: extended addressing (>64KB) not supported"
                    )

            except FileFormatError:
                raise
            except ValueError as exc:
                raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            addr = base_addr + offset
            byte_count = len(chunk)
            record_type = 0x00

            payload = bytearray([byte_count, (addr >> 8) & 0xFF, addr & 0xFF, record_type])
            payload.extend(chunk)

            checksum = (sum(payload) & 0xFF)
            checksum = (0x100 - checksum) & 0xFF

            line = f":{payload.hex().upper()}{checksum:02X}"
            lines.append(line)

        lines.append(":00000001FF")  # EOF record
        path.write_text('\n'.join(lines) + '\n')


class IntelIHex32Format(FileFormat):
    """Intel HEX with extended linear addressing (.ihex32, .hex32). Supports >64KB devices."""

    extensions = {".ihex32", ".hex32"}
    name = "Intel HEX-32"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFFFFFF
        upper_addr = 0

        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith(':'):
                raise FileFormatError(f"Line {lineno}: missing ':' prefix")
            if len(line) < 11:
                raise FileFormatError(f"Line {lineno}: record too short")

            try:
                byte_count = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                expected_len = 11 + byte_count * 2

                if len(line) != expected_len:
                    raise FileFormatError(f"Line {lineno}: invalid length")

                data_hex = line[9 : 9 + byte_count * 2]
                if len(data_hex) != byte_count * 2:
                    raise FileFormatError(f"Line {lineno}: data length mismatch")

                data_bytes = bytes.fromhex(data_hex)

                # Verify checksum
                checksum_calc = (byte_count + (address >> 8) + (address & 0xFF) +
                                record_type + sum(data_bytes)) & 0xFF
                checksum_calc = (0x100 - checksum_calc) & 0xFF
                checksum_file = int(line[-2:], 16)

                if checksum_calc != checksum_file:
                    raise FileFormatError(
                        f"Line {lineno}: checksum mismatch "
                        f"(expected {checksum_file:02X}, got {checksum_calc:02X})"
                    )

                if record_type == 0x00:  # Data
                    full_addr = upper_addr | address
                    if full_addr + byte_count > buf_size:
                        raise FileFormatError(
                            f"Line {lineno}: data at 0x{full_addr:08X} exceeds EPROM size"
                        )
                    data[full_addr : full_addr + byte_count] = data_bytes
                    base_addr = min(base_addr, full_addr)

                elif record_type == 0x01:  # End of file
                    break

                elif record_type == 0x04:  # Extended linear address
                    upper_addr = (int(data_hex[0:4], 16)) << 16

                elif record_type == 0x05:  # Start linear address
                    pass

                elif record_type in (0x02, 0x03):  # Extended segment (deprecated)
                    raise FileFormatError(
                        f"Line {lineno}: extended segment addressing not supported"
                    )

            except FileFormatError:
                raise
            except ValueError as exc:
                raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFFFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        current_upper = None

        for offset in range(0, len(data), 16):
            addr = base_addr + offset
            chunk = data[offset : offset + 16]
            byte_count = len(chunk)

            # Emit extended linear address record if upper bits changed
            upper = (addr >> 16) & 0xFFFF
            if upper != current_upper:
                current_upper = upper
                payload = bytearray([upper >> 8, upper & 0xFF])
                checksum = (2 + sum(payload) + 0x04) & 0xFF
                checksum = (0x100 - checksum) & 0xFF
                lines.append(f":02000004{payload.hex().upper()}{checksum:02X}")

            # Emit data record
            lower_addr = addr & 0xFFFF
            record_type = 0x00
            payload = bytearray([
                byte_count,
                (lower_addr >> 8) & 0xFF,
                lower_addr & 0xFF,
                record_type,
            ])
            payload.extend(chunk)

            checksum = (sum(payload) & 0xFF)
            checksum = (0x100 - checksum) & 0xFF

            line = f":{payload.hex().upper()}{checksum:02X}"
            lines.append(line)

        lines.append(":00000001FF")  # EOF record
        path.write_text('\n'.join(lines) + '\n')


class TektronixHexFormat(FileFormat):
    """Tektronix Extended HEX format (.tek, .tektronix). Similar to Intel HEX but uses % prefix."""

    extensions = {".tek", ".tektronix", ".hex_tek"}
    name = "Tektronix Extended HEX"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF

        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith('%'):
                raise FileFormatError(f"Line {lineno}: missing '%' prefix")
            if len(line) < 11:
                raise FileFormatError(f"Line {lineno}: record too short")

            try:
                byte_count = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                expected_len = 11 + byte_count * 2

                if len(line) != expected_len:
                    raise FileFormatError(f"Line {lineno}: invalid length")

                data_hex = line[9 : 9 + byte_count * 2]
                if len(data_hex) != byte_count * 2:
                    raise FileFormatError(f"Line {lineno}: data length mismatch")

                data_bytes = bytes.fromhex(data_hex)

                # Verify checksum (same as Intel HEX)
                checksum_calc = (byte_count + (address >> 8) + (address & 0xFF) +
                                record_type + sum(data_bytes)) & 0xFF
                checksum_calc = (0x100 - checksum_calc) & 0xFF
                checksum_file = int(line[-2:], 16)

                if checksum_calc != checksum_file:
                    raise FileFormatError(
                        f"Line {lineno}: checksum mismatch "
                        f"(expected {checksum_file:02X}, got {checksum_calc:02X})"
                    )

                if record_type == 0x00:  # Data
                    if address + byte_count > buf_size:
                        raise FileFormatError(
                            f"Line {lineno}: data at 0x{address:04X} exceeds EPROM size"
                        )
                    data[address : address + byte_count] = data_bytes
                    base_addr = min(base_addr, address)

                elif record_type == 0x01:  # End of file
                    break

            except FileFormatError:
                raise
            except ValueError as exc:
                raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            addr = base_addr + offset
            byte_count = len(chunk)
            record_type = 0x00

            payload = bytearray([byte_count, (addr >> 8) & 0xFF, addr & 0xFF, record_type])
            payload.extend(chunk)

            checksum = (sum(payload) & 0xFF)
            checksum = (0x100 - checksum) & 0xFF

            line = f"%{payload.hex().upper()}{checksum:02X}"
            lines.append(line)

        lines.append("%00000001FF")  # EOF record
        path.write_text('\n'.join(lines) + '\n')


class TiTxtFormat(FileFormat):
    """Texas Instruments TXT format (.txt).

    Format: @AAAA or @ AAAA sets address, then data bytes.
    """

    extensions = {".txt", ".ti_txt"}
    name = "TI-TXT"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF
        current_addr = 0

        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith(';') or line.upper() == 'Q':
                continue

            if line.startswith('@') or line.startswith('@ '):
                # Address directive: @AAAA or @ AAAA
                try:
                    addr_str = line[1:].strip()
                    if not addr_str:
                        raise FileFormatError(f"Line {lineno}: invalid address directive")
                    current_addr = int(addr_str, 16)
                    base_addr = min(base_addr, current_addr)
                except ValueError as exc:
                    raise FileFormatError(f"Line {lineno}: invalid address: {exc}")
            else:
                # Data line: space-separated hex bytes
                try:
                    hex_values = line.split()
                    for hex_byte in hex_values:
                        if len(hex_byte) != 2:
                            msg = f"Line {lineno}: invalid hex byte (need 2 chars)"
                            raise FileFormatError(msg)
                        byte_val = int(hex_byte, 16)
                        if current_addr >= buf_size:
                            raise FileFormatError(
                                f"Line {lineno}: data at 0x{current_addr:04X} exceeds EPROM size"
                            )
                        data[current_addr] = byte_val
                        current_addr += 1
                except FileFormatError:
                    raise
                except ValueError as exc:
                    raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        current_addr = base_addr

        for offset in range(0, len(data), 16):
            # Emit address directive
            lines.append(f"@{current_addr:04X}")

            # Collect 16 bytes of data (or less if at end)
            chunk = data[offset : offset + 16]
            hex_bytes = ' '.join(f"{byte:02X}" for byte in chunk)
            lines.append(hex_bytes)

            current_addr += len(chunk)

        # Terminator record
        lines.append("Q")
        path.write_text('\n'.join(lines) + '\n')


class MotorolaSRecordFormat(FileFormat):
    """Motorola S-Record format (.mot, .srec, .s19, .s28, .sx). Format: STTNNAAAADDDD...SS"""

    extensions = {".mot", ".srec", ".s19", ".s28", ".sx"}
    name = "Motorola S-Record"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF

        for lineno, line in enumerate(lines, 1):
            line = line.strip().upper()
            if not line:
                continue
            if not line.startswith('S'):
                raise FileFormatError(f"Line {lineno}: missing 'S' prefix")

            try:
                record_type = int(line[1], 16)
                byte_count = int(line[2:4], 16)
                expected_len = 4 + byte_count * 2

                if len(line) != expected_len:
                    raise FileFormatError(f"Line {lineno}: invalid length for S{record_type}")

                # Skip header and count records
                if record_type == 0:  # Header
                    continue
                elif record_type == 5:  # Count record
                    continue
                elif record_type == 1:  # 16-bit address
                    addr_len = 2
                elif record_type == 2:  # 24-bit address
                    addr_len = 3
                elif record_type == 3:  # 32-bit address
                    addr_len = 4
                elif record_type in (7, 8, 9):  # End record
                    break
                else:
                    raise FileFormatError(f"Line {lineno}: unsupported record type S{record_type}")

                # Extract payload
                payload_end = 4 + (byte_count - 1) * 2
                payload_hex = line[4:payload_end]
                payload = bytes.fromhex(payload_hex)

                # Last byte is checksum
                checksum_file = int(line[-2:], 16)
                checksum_calc = (sum(bytearray([byte_count]) + payload) ^ 0xFF) & 0xFF

                if checksum_calc != checksum_file:
                    raise FileFormatError(
                        f"Line {lineno}: checksum mismatch "
                        f"(expected {checksum_file:02X}, got {checksum_calc:02X})"
                    )

                if record_type in (1, 2, 3):  # Data records
                    address = int(payload_hex[: addr_len * 2], 16)
                    record_data = payload[addr_len:-1]

                    if address + len(record_data) > buf_size:
                        raise FileFormatError(
                            f"Line {lineno}: data at 0x{address:04X} exceeds EPROM size"
                        )

                    data[address : address + len(record_data)] = record_data
                    base_addr = min(base_addr, address)

            except FileFormatError:
                raise
            except ValueError as exc:
                raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []

        # Header record (S0: includes address + data + checksum in byte count)
        header = bytearray([0x00, 0x00])
        header.extend(b"EPROM")
        byte_count = len(header) + 1  # +1 for checksum
        checksum = (sum(header) ^ 0xFF) & 0xFF
        lines.append(f"S0{byte_count:02X}{header.hex().upper()}{checksum:02X}")

        # Data records (S1 format: 16-bit address)
        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            addr = base_addr + offset
            record_payload = bytearray([addr >> 8, addr & 0xFF])
            record_payload.extend(chunk)

            byte_count = len(record_payload) + 1  # +1 for checksum
            checksum = (byte_count + sum(record_payload)) ^ 0xFF
            checksum &= 0xFF

            line = f"S1{byte_count:02X}{record_payload.hex().upper()}{checksum:02X}"
            lines.append(line)

        # End record (S9)
        end_payload = bytearray([base_addr >> 8, base_addr & 0xFF])
        byte_count = len(end_payload) + 1
        checksum = (byte_count + sum(end_payload)) ^ 0xFF
        checksum &= 0xFF
        lines.append(f"S9{byte_count:02X}{end_payload.hex().upper()}{checksum:02X}")

        path.write_text('\n'.join(lines) + '\n')


class AddressedHexFormat(FileFormat):
    """Addressed hex dump format (.ahex). Format: AAAA: HH HH HH ... (various spacing accepted)."""

    extensions = {".ahex", ".asc", ".hex_text"}
    name = "Addressed Hex Dump"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        from serial_eprom_programmer.utils import parse_hex_dump

        text = path.read_text()
        try:
            # parse_hex_dump returns bytes starting from address 0
            # We need to detect the actual base address from the first line
            base_addr = 0
            for line in text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                try:
                    addr_str = line.split(':')[0].strip()
                    base_addr = int(addr_str, 16)
                    break
                except ValueError:
                    continue

            data = parse_hex_dump(text)

            if len(data) > buf_size:
                raise FileFormatError(
                    f"Data is {len(data)} bytes, EPROM capacity is {buf_size} bytes"
                )

            # Pad with 0xFF to EPROM size
            padded = bytearray([0xFF] * buf_size)
            padded[:len(data)] = data
            return LoadResult(bytes(padded), base_addr, self.name)

        except FileFormatError:
            raise
        except Exception as exc:
            raise FileFormatError(f"Failed to parse addressed hex dump: {exc}")

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        from serial_eprom_programmer.utils import hex_dump

        text = hex_dump(data, base_addr)
        path.write_text(text + '\n')


class MosTapeFormat(FileFormat):
    """MOS Technology paper tape format (.mos, .papertape). Format: ;NNAAAADDDD...CC"""

    extensions = {".mos", ".papertape"}
    name = "MOS Paper Tape"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        lines = path.read_text().strip().split('\n')
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF
        record_count = 0

        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith(';'):
                raise FileFormatError(f"Line {lineno}: missing ';' prefix")

            try:
                byte_count = int(line[1:3], 16)
                address = int(line[3:7], 16)

                # Skip terminator record (byte_count=0x00 and address=0x0000)
                if byte_count == 0x00 and address == 0x0000:
                    continue

                data_end = 7 + byte_count * 2
                if len(line) < data_end + 2:
                    raise FileFormatError(f"Line {lineno}: record too short")

                data_hex = line[7:data_end]
                record_data = bytes.fromhex(data_hex)
                checksum_file = int(line[data_end : data_end + 2], 16)

                # Verify checksum (sum of address + data, mod 256)
                checksum_calc = (
                    (address >> 8) + (address & 0xFF) + sum(record_data)
                ) & 0xFF

                if checksum_calc != checksum_file:
                    raise FileFormatError(
                        f"Line {lineno}: checksum mismatch "
                        f"(expected {checksum_file:02X}, got {checksum_calc:02X})"
                    )

                if address + len(record_data) > buf_size:
                    raise FileFormatError(
                        f"Line {lineno}: data at 0x{address:04X} exceeds EPROM size"
                    )

                data[address : address + len(record_data)] = record_data
                base_addr = min(base_addr, address)
                record_count += 1

            except FileFormatError:
                raise
            except ValueError as exc:
                raise FileFormatError(f"Line {lineno}: invalid hex data: {exc}")

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        record_count = 0

        for offset in range(0, len(data), 16):
            chunk = data[offset : offset + 16]
            addr = base_addr + offset
            byte_count = len(chunk)

            checksum = ((addr >> 8) + (addr & 0xFF) + sum(chunk)) & 0xFF

            line = (
                f";{byte_count:02X}{addr:04X}"
                f"{chunk.hex().upper()}"
                f"{checksum:02X}"
            )
            lines.append(line)
            record_count += 1

        # Terminator: ;0000NNSS (NN = record count, SS = checksum of count)
        checksum = (0x00 + 0x00 + record_count) & 0xFF
        lines.append(f";0000{record_count:04X}{checksum:02X}")

        path.write_text('\n'.join(lines) + '\n')


class MifFormat(FileFormat):
    """MIF (Memory Initialization File) format (.mif).

    Used for FPGA and block RAM initialization.
    """

    extensions = {".mif"}
    name = "MIF"

    def load(self, path: Path, buf_size: int) -> LoadResult:
        content = path.read_text()
        data = bytearray([0xFF] * buf_size)
        base_addr = 0xFFFF
        in_content = False
        current_addr = 0

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue

            if line.upper().startswith('CONTENT BEGIN'):
                in_content = True
                continue

            if not in_content:
                continue

            if line.upper().startswith('END'):
                break

            # Parse content lines with address directive and data
            if '@' in line and ':' in line:
                # Line like: @XXXX : value, value, value;
                try:
                    parts = line.split(':')
                    addr_part = parts[0].strip()
                    if addr_part.startswith('@'):
                        addr_str = addr_part[1:].strip()
                        current_addr = int(addr_str, 16)
                        base_addr = min(base_addr, current_addr)

                    # Parse values after colon
                    if len(parts) > 1:
                        val_part = parts[1].strip().rstrip(';')
                        hex_values = val_part.replace(',', ' ').split()
                        for hex_val in hex_values:
                            hex_val = hex_val.strip()
                            if hex_val:
                                byte_val = int(hex_val, 16)
                                if current_addr < buf_size:
                                    data[current_addr] = byte_val
                                    current_addr += 1
                except (ValueError, IndexError):
                    pass

        if base_addr == 0xFFFF:
            base_addr = 0

        return LoadResult(bytes(data), base_addr, self.name)

    def save(self, path: Path, data: bytes, base_addr: int = 0) -> None:
        lines = []
        lines.append("-- MIF file generated by Serial EPROM Programmer")
        lines.append("WIDTH=8;")
        lines.append(f"DEPTH={len(data)};")
        lines.append("")
        lines.append("CONTENT BEGIN")
        lines.append(f"  @{base_addr:04X}  :  {data[0]:02X};")

        for offset in range(1, len(data)):
            byte_val = data[offset]
            current_addr = base_addr + offset
            if offset % 16 == 0:
                lines.append(f"  @{current_addr:04X}  :  {byte_val:02X};")
            else:
                # Continue on same line if still in sequence
                lines[-1] = lines[-1].rstrip(';') + f", {byte_val:02X};"

        lines.append("END;")
        path.write_text('\n'.join(lines) + '\n')


# Registry of all formats
ALL_FORMATS = [
    IntelHexFormat(),
    IntelIHex32Format(),
    MotorolaSRecordFormat(),
    TektronixHexFormat(),
    TiTxtFormat(),
    AddressedHexFormat(),
    MosTapeFormat(),
    MifFormat(),
    BinaryFormat(),
]


def detect_format(path: Path) -> FileFormat:
    """Detect format by file extension.

    Args:
        path: File path

    Returns:
        FileFormat handler for the detected format

    Raises:
        FileFormatError: If format cannot be detected
    """
    suffix = path.suffix.lower()

    for fmt in ALL_FORMATS:
        if suffix in fmt.extensions:
            return fmt

    supported = ", ".join(
        e for fmt in ALL_FORMATS for e in sorted(fmt.extensions)
    )
    raise FileFormatError(
        f"Unknown file format: {suffix}. Supported: {supported}"
    )


def load_file(path: Path, buf_size: int) -> LoadResult:
    """Auto-detect and load a file.

    Args:
        path: File to load
        buf_size: EPROM capacity for validation

    Returns:
        LoadResult with data, base address, and format name

    Raises:
        FileFormatError: If file is invalid
    """
    fmt = detect_format(path)
    return fmt.load(path, buf_size)


def save_file(path: Path, data: bytes, base_addr: int = 0, fmt: FileFormat | None = None) -> None:
    """Save file, auto-detecting format from extension if not specified.

    Args:
        path: Output file path
        data: Bytes to save
        base_addr: Base address for formats that support it
        fmt: Optional explicit format (if None, detected from extension)

    Raises:
        FileFormatError: If format cannot be determined
    """
    if fmt is None:
        fmt = detect_format(path)

    fmt.save(path, data, base_addr)
