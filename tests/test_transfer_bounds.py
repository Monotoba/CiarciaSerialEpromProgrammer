"""Protocol boundary regressions without physical programmer hardware."""

from unittest.mock import patch

import pytest

from serial_eprom_programmer.programmer import SerialEpromProgrammer


class RecordingSerial:
    def __init__(self):
        self.sent = bytearray()
        self.received = 0
        self.flushes = 0

    def write(self, data):
        self.sent.extend(data)
        return len(data)

    def read(self, size):
        assert size == 1
        value = self.received % 256
        self.received += 1
        return bytes([value])

    def flush(self):
        self.flushes += 1


@pytest.fixture
def connection():
    serial = RecordingSerial()
    with patch("serial.Serial", return_value=serial):
        yield SerialEpromProgrammer("test", 9600), serial


@pytest.mark.parametrize("action", ["read", "program"])
@pytest.mark.parametrize("base,size", [(-1, 1), (65536, 1), (0, 0), (0, -1),
                                      (65535, 2), (1, 65536), (0, 65537)])
def test_invalid_range_sends_nothing(connection, action, base, size):
    programmer, serial = connection
    with pytest.raises(ValueError):
        if action == "read":
            programmer.read_eprom(base, size)
        else:
            programmer.program_eprom(base, bytes(max(0, size)))
    assert not serial.sent


def test_full_27512_read_uses_two_nonzero_lengths(connection):
    programmer, serial = connection
    progress = []
    data = programmer.read_eprom(0, 65536, progress.append)
    assert data == bytes(range(256)) * 256
    assert serial.sent == b"R\x00\x00\x00\x80R\x00\x80\x00\x80"
    assert progress == sorted(progress)
    assert progress[-1] == 65536


def test_full_27512_program_uses_two_commands(connection):
    programmer, serial = connection
    progress = []
    data = bytes(range(256)) * 256
    programmer.program_eprom(0, data, progress.append)
    assert serial.sent == (
        b"P\x00\x00\x00\x80" + data[:32768]
        + b"P\x00\x80\x00\x80" + data[32768:]
    )
    assert serial.flushes == 2
    assert progress == sorted(progress)
    assert progress[-1] == 65536


@pytest.mark.parametrize("action", ["read", "program"])
def test_last_address_is_valid(connection, action):
    programmer, serial = connection
    if action == "read":
        assert programmer.read_eprom(65535, 1) == b"\x00"
        assert serial.sent == b"R\xff\xff\x01\x00"
    else:
        programmer.program_eprom(65535, b"\xAA")
        assert serial.sent == b"P\xff\xff\x01\x00\xAA"
