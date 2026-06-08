"""Tests for utility functions."""

from serial_eprom_programmer.utils import hex_dump, parse_hex_dump


class TestHexDump:
    """Test hex_dump function."""

    def test_hex_dump_single_line(self):
        """Test hex dump with data less than 16 bytes."""
        data = bytes([0x00, 0x01, 0x02, 0x03])
        result = hex_dump(data)
        assert "0000:" in result
        assert "00 01 02 03" in result

    def test_hex_dump_multiple_lines(self):
        """Test hex dump with data spanning multiple lines."""
        data = bytes(range(32))
        result = hex_dump(data)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("0000:")
        assert lines[1].startswith("0010:")

    def test_hex_dump_address_offset(self):
        """Test hex dump with custom base address."""
        data = bytes([0xAA, 0xBB])
        result = hex_dump(data, base=0x1000)
        assert "1000:" in result

    def test_hex_dump_hex_formatting(self):
        """Test that hex bytes are uppercase and two digits."""
        data = bytes([0x0F, 0xFF, 0x10])
        result = hex_dump(data)
        assert "0F" in result
        assert "FF" in result
        assert "10" in result
        assert "f" not in result.split(":")[1]  # No lowercase hex

    def test_hex_dump_ascii_representation(self):
        """Test ASCII representation in hex dump."""
        data = b"Hello"
        result = hex_dump(data)
        assert "Hello" in result

    def test_hex_dump_non_printable_as_dot(self):
        """Test that non-printable characters are shown as dots."""
        data = bytes([0x00, 0x01, 0x41, 0x7F])  # Includes 'A' (0x41) and DEL (0x7F)
        result = hex_dump(data)
        ascii_part = result.split()[-1]
        assert "." in ascii_part
        assert "A" in ascii_part

    def test_hex_dump_16_bytes_per_line(self):
        """Test that exactly 16 bytes appear per line."""
        data = bytes(range(48))
        result = hex_dump(data)
        lines = result.split("\n")
        assert len(lines) == 3
        for line in lines:
            # Count hex bytes on each line (space-separated pairs)
            hex_part = line.split(":")[1].split("  ")[0]
            byte_count = len(hex_part.split())
            assert byte_count == 16

    def test_hex_dump_empty_data(self):
        """Test hex dump with empty data."""
        result = hex_dump(b"")
        assert result == ""

    def test_hex_dump_full_address_range(self):
        """Test hex dump with large offset."""
        data = bytes([0xFF, 0xFE])
        result = hex_dump(data, base=0xFFFF)
        assert "FFFF:" in result


class TestParseHexDump:
    """Test parse_hex_dump function."""

    def test_parse_hex_dump_roundtrip(self):
        """Test that hex_dump then parse_hex_dump returns original bytes."""
        original = bytes([0x00, 0x01, 0x02, 0xFF, 0xFE])
        dumped = hex_dump(original)
        parsed = parse_hex_dump(dumped)
        assert parsed == original

    def test_parse_hex_dump_with_offset(self):
        """Test that base address doesn't affect parsed bytes."""
        data = bytes([0xAA, 0xBB, 0xCC])
        dumped_0 = hex_dump(data, base=0x0000)
        dumped_1000 = hex_dump(data, base=0x1000)

        parsed_0 = parse_hex_dump(dumped_0)
        parsed_1000 = parse_hex_dump(dumped_1000)

        assert parsed_0 == parsed_1000 == data

    def test_parse_hex_dump_empty(self):
        """Test parsing empty hex dump."""
        result = parse_hex_dump("")
        assert result == b""

    def test_parse_hex_dump_single_line(self):
        """Test parsing single line hex dump."""
        dumped = "0000: AA BB CC DD  ....".rstrip()
        result = parse_hex_dump(dumped)
        assert result == bytes([0xAA, 0xBB, 0xCC, 0xDD])

    def test_parse_hex_dump_multiple_lines(self):
        """Test parsing multi-line hex dump."""
        data = bytes(range(32))
        dumped = hex_dump(data)
        parsed = parse_hex_dump(dumped)
        assert parsed == data

    def test_parse_hex_dump_invalid_token_too_long(self):
        """Test error on token with more than 2 chars."""
        invalid = "0000: AAA BBB  ......".rstrip()
        try:
            parse_hex_dump(invalid)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "bad byte token" in str(exc).lower()

    def test_parse_hex_dump_invalid_token_too_short(self):
        """Test error on single-char token."""
        invalid = "0000: A B C D  ....".rstrip()
        try:
            parse_hex_dump(invalid)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "bad byte token" in str(exc).lower()

    def test_parse_hex_dump_missing_separator(self):
        """Test error on line without colon separator."""
        invalid = "0000 AA BB CC DD  ....".rstrip()
        try:
            parse_hex_dump(invalid)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "separator" in str(exc).lower()

    def test_parse_hex_dump_invalid_hex_value(self):
        """Test error on invalid hex digit."""
        invalid = "0000: ZZ 01 02 03  ....".rstrip()
        try:
            parse_hex_dump(invalid)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

    def test_parse_hex_dump_whitespace_handling(self):
        """Test that standard whitespace is handled correctly."""
        # Standard spacing from hex_dump output
        dumped = "0000: AA BB CC DD  ....".rstrip()
        result = parse_hex_dump(dumped)
        assert result == bytes([0xAA, 0xBB, 0xCC, 0xDD])

    def test_parse_hex_dump_large_data(self):
        """Test round-trip with 2KB buffer (typical EPROM size)."""
        data = bytes([0xFF] * 2048)
        dumped = hex_dump(data)
        parsed = parse_hex_dump(dumped)
        assert parsed == data
        assert len(parsed) == 2048
