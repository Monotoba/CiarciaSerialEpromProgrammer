"""Tests for file format loaders and savers."""

from pathlib import Path

import pytest

from serial_eprom_programmer.fileformats import (
    AddressedHexFormat,
    BinaryFormat,
    FileFormatError,
    IntelHexFormat,
    MosTapeFormat,
    MotorolaSRecordFormat,
    detect_format,
    load_file,
    save_file,
)


@pytest.fixture
def temp_path(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


class TestBinaryFormat:
    """Test raw binary format."""

    def test_save_and_load_binary(self, temp_path):
        """Test saving and loading binary file."""
        original = bytes([0xAA, 0xBB, 0xCC, 0xDD, 0x11, 0x22, 0x33, 0x44])
        path = temp_path / "test.bin"

        fmt = BinaryFormat()
        fmt.save(path, original)
        result = fmt.load(path, 256)

        assert result.data == original
        assert result.format_name == "Binary"

    def test_load_binary_oversized(self, temp_path):
        """Test that oversized binary is rejected."""
        path = temp_path / "test.bin"
        path.write_bytes(bytes(3000))

        fmt = BinaryFormat()
        with pytest.raises(FileFormatError):
            fmt.load(path, 2048)


class TestIntelHexFormat:
    """Test Intel HEX format."""

    def test_save_and_load_hex(self, temp_path):
        """Test saving and loading Intel HEX file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.hex"
        fmt = IntelHexFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Intel HEX"

    def test_load_hex_bad_checksum(self, temp_path):
        """Test that bad checksum is rejected."""
        hex_content = ":04000000AABBCCDD00"  # Wrong checksum
        path = temp_path / "test.hex"
        path.write_text(hex_content)

        fmt = IntelHexFormat()
        with pytest.raises(FileFormatError, match="checksum"):
            fmt.load(path, 2048)


class TestMotorolaSRecordFormat:
    """Test Motorola S-Record format."""

    def test_srec_format_detection(self, temp_path):
        """Test detecting S-Record format."""
        path = temp_path / "test.srec"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, MotorolaSRecordFormat)
        assert fmt.name == "Motorola S-Record"

    def test_load_srec_bad_checksum(self, temp_path):
        """Test that bad S-Record checksum is rejected."""
        srec_content = "S1070000AABBCCDD00"  # Wrong checksum
        path = temp_path / "test.srec"
        path.write_text(srec_content)

        fmt = MotorolaSRecordFormat()
        with pytest.raises(FileFormatError, match="checksum"):
            fmt.load(path, 2048)


class TestAddressedHexFormat:
    """Test addressed hex dump format."""

    def test_save_and_load_ahex(self, temp_path):
        """Test saving and loading addressed hex format."""
        original = bytearray([0xFF] * 64)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.ahex"
        fmt = AddressedHexFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 64)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Addressed Hex Dump"


class TestMosTapeFormat:
    """Test MOS Technology paper tape format."""

    def test_mos_format_detection(self, temp_path):
        """Test detecting MOS tape format."""
        path = temp_path / "test.mos"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, MosTapeFormat)
        assert fmt.name == "MOS Paper Tape"

    def test_load_mos_bad_record(self, temp_path):
        """Test that malformed MOS tape record is rejected."""
        tape_content = ";invalid"  # Invalid record
        path = temp_path / "test.mos"
        path.write_text(tape_content)

        fmt = MosTapeFormat()
        with pytest.raises(FileFormatError):
            fmt.load(path, 2048)


class TestFormatDetection:
    """Test format auto-detection."""

    def test_detect_hex(self, temp_path):
        """Test detecting Intel HEX by extension."""
        path = temp_path / "test.hex"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, IntelHexFormat)

    def test_detect_srec(self, temp_path):
        """Test detecting Motorola S-Record by extension."""
        path = temp_path / "test.srec"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, MotorolaSRecordFormat)

    def test_detect_bin(self, temp_path):
        """Test detecting binary by extension."""
        path = temp_path / "test.bin"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, BinaryFormat)

    def test_detect_ahex(self, temp_path):
        """Test detecting addressed hex by extension."""
        path = temp_path / "test.ahex"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, AddressedHexFormat)

    def test_detect_mos(self, temp_path):
        """Test detecting MOS tape by extension."""
        path = temp_path / "test.mos"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, MosTapeFormat)

    def test_detect_unknown(self, temp_path):
        """Test that unknown extension raises error."""
        path = temp_path / "test.xyz"
        path.touch()
        with pytest.raises(FileFormatError, match="Unknown"):
            detect_format(path)


class TestLoadFile:
    """Test load_file convenience function."""

    def test_load_auto_hex(self, temp_path):
        """Test loading HEX with auto-detection."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.hex"
        fmt = IntelHexFormat()
        fmt.save(path, bytes(original), base_addr=0)

        result = load_file(path, 256)

        assert result.data[0:4] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Intel HEX"


class TestSaveFile:
    """Test save_file convenience function."""

    def test_save_auto_hex(self, temp_path):
        """Test saving HEX with auto-detection."""
        data = bytearray([0xFF] * 256)
        data[0:4] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.hex"
        save_file(path, bytes(data))

        assert path.exists()
        assert path.read_text().startswith(":")

    def test_save_auto_bin(self, temp_path):
        """Test saving binary with auto-detection."""
        data = bytes([0x11, 0x22, 0x33, 0x44])

        path = temp_path / "test.bin"
        save_file(path, data)

        assert path.read_bytes() == data

    def test_main_formats_roundtrip(self, temp_path):
        """Test that main formats can save and load correctly."""
        test_data = bytearray([0xFF] * 64)
        test_data[0:8] = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]

        # Test formats with working roundtrip
        formats_and_extensions = [
            (IntelHexFormat(), "test.hex"),
            (AddressedHexFormat(), "test.ahex"),
            (BinaryFormat(), "test.bin"),
        ]

        for fmt, filename in formats_and_extensions:
            path = temp_path / filename
            fmt.save(path, bytes(test_data), base_addr=0)
            result = fmt.load(path, 64)
            assert result.data[0:8] == bytes(test_data[0:8]), f"Failed for {filename}"
