"""Tests for SerialEpromProgrammer hardware layer."""

from unittest.mock import MagicMock, patch

import pytest

from serial_eprom_programmer.programmer import SerialEpromProgrammer


class TestSerialEpromProgrammer:
    """Test SerialEpromProgrammer class."""

    @patch("serial.Serial")
    def test_programmer_init(self, mock_serial_class):
        """Test programmer initialization."""
        mock_serial_class.return_value = MagicMock()
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)
        assert prog.serial is not None
        mock_serial_class.assert_called_once()

    @patch("serial.Serial")
    def test_programmer_init_configuration(self, mock_serial_class):
        """Test that programmer is initialized with correct serial config."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        call_kwargs = mock_serial_class.call_args[1]
        assert call_kwargs["port"] == "/dev/ttyUSB0"
        assert call_kwargs["baudrate"] == 9600
        assert call_kwargs["timeout"] == 3.0

    @patch("serial.Serial")
    def test_send_byte(self, mock_serial_class):
        """Test sending a single byte."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.send_byte(0x42)
        mock_serial.write.assert_called_with(b"\x42")

    @patch("serial.Serial")
    def test_send_byte_masks_to_8bits(self, mock_serial_class):
        """Test that send_byte masks to 8 bits."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.send_byte(0x1FF)  # 9 bits, should mask to 0xFF
        mock_serial.write.assert_called_with(b"\xFF")

    @patch("serial.Serial")
    def test_recv_byte(self, mock_serial_class):
        """Test receiving a single byte."""
        mock_serial = MagicMock()
        mock_serial.read.return_value = b"\x42"
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        result = prog.recv_byte()
        assert result == 0x42
        mock_serial.read.assert_called_with(1)

    @patch("serial.Serial")
    def test_recv_byte_timeout(self, mock_serial_class):
        """Test that recv_byte raises TimeoutError on empty read."""
        mock_serial = MagicMock()
        mock_serial.read.return_value = b""
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        with pytest.raises(TimeoutError):
            prog.recv_byte()

    @patch("serial.Serial")
    def test_send_word(self, mock_serial_class):
        """Test sending a 16-bit word (little-endian)."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.send_word(0x1234)
        calls = [c[0][0] for c in mock_serial.write.call_args_list]
        assert calls == [b"\x34", b"\x12"]  # Little-endian

    @patch("serial.Serial")
    def test_read_eprom(self, mock_serial_class):
        """Test reading EPROM data."""
        mock_serial = MagicMock()
        mock_serial.read.side_effect = [b"\xAA"] * 10
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        data = prog.read_eprom(0x0000, 10)
        assert data == b"\xAA" * 10
        assert mock_serial.write.call_count == 5  # R cmd + 2 addr bytes + 2 len bytes
        assert mock_serial.read.call_count == 10

    @patch("serial.Serial")
    def test_read_eprom_protocol(self, mock_serial_class):
        """Test read_eprom sends correct protocol."""
        mock_serial = MagicMock()
        mock_serial.read.return_value = b"\x00"
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.read_eprom(0x0100, 5)

        write_calls = [c[0][0] for c in mock_serial.write.call_args_list]
        assert write_calls[0] == b"R"  # Command
        assert write_calls[1] == b"\x00"  # Address low
        assert write_calls[2] == b"\x01"  # Address high
        assert write_calls[3] == b"\x05"  # Length low
        assert write_calls[4] == b"\x00"  # Length high

    @patch("serial.Serial")
    def test_read_eprom_with_progress(self, mock_serial_class):
        """Test read_eprom progress callback."""
        mock_serial = MagicMock()
        mock_serial.read.side_effect = [b"\x00"] * 300
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        progress_values = []
        prog.read_eprom(0x0000, 300, progress=lambda x: progress_values.append(x))

        assert len(progress_values) > 0
        assert 300 in progress_values

    @patch("serial.Serial")
    def test_program_eprom(self, mock_serial_class):
        """Test programming EPROM."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        data = bytes([0xFF, 0xFE, 0xFD])
        prog.program_eprom(0x0000, data)

        assert mock_serial.write.call_count == 8  # P + 2 addr bytes + 2 len bytes + 3 data bytes
        assert mock_serial.flush.called

    @patch("serial.Serial")
    def test_program_eprom_protocol(self, mock_serial_class):
        """Test program_eprom sends correct protocol."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        data = b"\xAA"
        prog.program_eprom(0x0200, data)

        write_calls = [c[0][0] for c in mock_serial.write.call_args_list]
        assert write_calls[0] == b"P"  # Command
        assert write_calls[1] == b"\x00"  # Address low
        assert write_calls[2] == b"\x02"  # Address high
        assert write_calls[3] == b"\x01"  # Length low
        assert write_calls[4] == b"\x00"  # Length high
        assert write_calls[5] == b"\xAA"  # Data

    @patch("serial.Serial")
    def test_program_eprom_with_progress(self, mock_serial_class):
        """Test program_eprom progress callback."""
        mock_serial = MagicMock()
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        data = bytes([i % 256 for i in range(300)])
        progress_values = []
        prog.program_eprom(0x0000, data, progress=lambda x: progress_values.append(x))

        assert len(progress_values) > 0
        assert 300 in progress_values

    @patch("serial.Serial")
    def test_close(self, mock_serial_class):
        """Test closing the serial port."""
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.close()
        mock_serial.close.assert_called_once()

    @patch("serial.Serial")
    def test_close_already_closed(self, mock_serial_class):
        """Test closing when already closed."""
        mock_serial = MagicMock()
        mock_serial.is_open = False
        mock_serial_class.return_value = mock_serial
        prog = SerialEpromProgrammer("/dev/ttyUSB0", 9600)

        prog.close()
        mock_serial.close.assert_not_called()
