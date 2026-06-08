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
