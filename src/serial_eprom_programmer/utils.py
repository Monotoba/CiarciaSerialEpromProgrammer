"""Utility functions for EPROM programming."""


def hex_dump(data: bytes, base: int = 0) -> str:
    """Format bytes as hex dump with address column and ASCII representation.

    Args:
        data: Bytes to format
        base: Starting address for display (default 0)

    Returns:
        Formatted hex dump string with 16 bytes per line
    """
    lines: list[str] = []

    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{base + offset:04X}: {hex_part:<47}  {ascii_part}")

    return "\n".join(lines)


def parse_hex_dump(text: str) -> bytes:
    """Parse hex dump text back to bytes.

    Accepts the format produced by hex_dump():
      XXXX: HH HH ... HH  AAAA...

    Args:
        text: Hex dump string

    Returns:
        Bytes parsed from hex dump

    Raises:
        ValueError: If any line is malformed or byte value out of range
    """
    result = bytearray()
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if ':' not in line:
            raise ValueError(f"Line {lineno}: missing address separator")
        _, rest = line.split(':', 1)
        # Hex part ends at first double-space (before ASCII column)
        if '  ' in rest:
            hex_part = rest.split('  ')[0].strip()
        else:
            # No ASCII column, whole rest is hex
            hex_part = rest.strip()
        for token in hex_part.split():
            if len(token) != 2:
                raise ValueError(f"Line {lineno}: bad byte token '{token}'")
            result.append(int(token, 16))
    return bytes(result)
