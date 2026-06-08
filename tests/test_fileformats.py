"""Tests for file format loaders and savers."""

from pathlib import Path

import pytest

from serial_eprom_programmer.fileformats import (
    AddressedHexFormat,
    BinaryFormat,
    FileFormatError,
    IntelHexFormat,
    IntelIHex32Format,
    MifFormat,
    MosTapeFormat,
    MotorolaSRecordFormat,
    TektronixHexFormat,
    TiTxtFormat,
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

    def test_srec_roundtrip(self, temp_path):
        """Test saving and loading S-Record file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.srec"
        fmt = MotorolaSRecordFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Motorola S-Record"

    def test_srec_roundtrip_with_base_addr_zero(self, temp_path):
        """Test S-Record with data at address 0x0000."""
        original = bytearray([0xFF] * 64)
        original[0:8] = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]

        path = temp_path / "test.srec"
        fmt = MotorolaSRecordFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 64)

        assert result.data[0:8] == bytes(original[0:8])
        assert result.base_addr == 0


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

    def test_mos_roundtrip(self, temp_path):
        """Test saving and loading MOS tape file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.mos"
        fmt = MosTapeFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "MOS Paper Tape"

    def test_mos_roundtrip_with_base_addr_zero(self, temp_path):
        """Test MOS tape with data at address 0x0000."""
        original = bytearray([0xFF] * 64)
        original[0:8] = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]

        path = temp_path / "test.mos"
        fmt = MosTapeFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 64)

        assert result.data[0:8] == bytes(original[0:8])
        assert result.base_addr == 0


class TestIntelIHex32Format:
    """Test Intel HEX-32 (extended linear addressing) format."""

    def test_ihex32_roundtrip(self, temp_path):
        """Test saving and loading Intel HEX-32 file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.ihex32"
        fmt = IntelIHex32Format()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Intel HEX-32"

    def test_ihex32_extended_addressing(self, temp_path):
        """Test Intel HEX-32 with data above 64KB boundary."""
        original = bytearray([0xFF] * 65536)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[65520:65524] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.ihex32"
        fmt = IntelIHex32Format()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 65536)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[65520:65524] == bytes([0x11, 0x22, 0x33, 0x44])


class TestTektronixHexFormat:
    """Test Tektronix Extended HEX format."""

    def test_tektronix_roundtrip(self, temp_path):
        """Test saving and loading Tektronix HEX file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.tek"
        fmt = TektronixHexFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "Tektronix Extended HEX"


class TestTiTxtFormat:
    """Test Texas Instruments TXT format."""

    def test_ti_txt_roundtrip(self, temp_path):
        """Test saving and loading TI-TXT file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.ti_txt"
        fmt = TiTxtFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "TI-TXT"

    def test_ti_txt_with_comments(self, temp_path):
        """Test TI-TXT parsing with comment lines."""
        path = temp_path / "test.txt"
        content = """; Test file
@0000
AA BB CC DD FF FF FF FF
; More data
11 22 33 44
Q
"""
        path.write_text(content)

        fmt = TiTxtFormat()
        result = fmt.load(path, 256)

        assert result.data[0] == 0xAA
        assert result.data[1] == 0xBB
        assert result.data[8] == 0x11
        assert result.base_addr == 0


class TestMifFormat:
    """Test MIF (Memory Initialization File) format."""

    def test_mif_roundtrip(self, temp_path):
        """Test saving and loading MIF file."""
        original = bytearray([0xFF] * 256)
        original[0:4] = [0xAA, 0xBB, 0xCC, 0xDD]
        original[16:20] = [0x11, 0x22, 0x33, 0x44]

        path = temp_path / "test.mif"
        fmt = MifFormat()

        fmt.save(path, bytes(original), base_addr=0)
        result = fmt.load(path, 256)

        assert result.data[0:4] == bytes([0xAA, 0xBB, 0xCC, 0xDD])
        assert result.data[16:20] == bytes([0x11, 0x22, 0x33, 0x44])
        assert result.format_name == "MIF"


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

    def test_detect_ihex32(self, temp_path):
        """Test detecting Intel HEX-32 by extension."""
        path = temp_path / "test.ihex32"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, IntelIHex32Format)

    def test_detect_tektronix(self, temp_path):
        """Test detecting Tektronix HEX by extension."""
        path = temp_path / "test.tek"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, TektronixHexFormat)

    def test_detect_ti_txt(self, temp_path):
        """Test detecting TI-TXT by extension."""
        path = temp_path / "test.ti_txt"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, TiTxtFormat)

    def test_detect_mif(self, temp_path):
        """Test detecting MIF by extension."""
        path = temp_path / "test.mif"
        path.touch()
        fmt = detect_format(path)
        assert isinstance(fmt, MifFormat)

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
