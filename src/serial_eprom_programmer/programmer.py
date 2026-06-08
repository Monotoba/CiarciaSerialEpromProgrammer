"""Hardware-layer EPROM programmer (no Qt imports)."""

import serial


class SerialEpromProgrammer:
    """Low-level interface to serial EPROM programmer hardware.

    Handles read, program, and protocol operations over RS-232.
    No Qt dependencies — fully testable without QApplication.
    """

    def __init__(self, port: str, baud: int):
        """Initialize serial connection to programmer.

        Args:
            port: Serial port (e.g., '/dev/ttyUSB0', 'COM1')
            baud: Baud rate (e.g., 9600)
        """
        self.serial = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=3.0,
            write_timeout=3.0,
        )

    def close(self) -> None:
        """Close serial port."""
        if self.serial.is_open:
            self.serial.close()

    def send_byte(self, value: int) -> None:
        """Send a single byte."""
        self.serial.write(bytes([value & 0xFF]))

    def recv_byte(self) -> int:
        """Receive a single byte.

        Raises:
            TimeoutError: If no byte received within timeout
        """
        data = self.serial.read(1)
        if len(data) != 1:
            raise TimeoutError("Timed out waiting for byte")
        return data[0]

    def send_word(self, value: int) -> None:
        """Send a 16-bit word in little-endian byte order."""
        self.send_byte(value & 0xFF)
        self.send_byte((value >> 8) & 0xFF)

    def read_eprom(self, base: int, size: int, progress=None) -> bytes:
        """Read EPROM data from hardware.

        Sends 'R' command with address and length, then reads N bytes.

        Args:
            base: Starting address (16-bit)
            size: Number of bytes to read
            progress: Optional callback(bytes_read) for progress updates

        Returns:
            Bytes read from EPROM
        """
        self.send_byte(ord("R"))
        self.send_word(base)
        self.send_word(size)

        out = bytearray()

        for i in range(size):
            out.append(self.recv_byte())
            if progress and (i % 128 == 0 or i == size - 1):
                progress(i + 1)

        return bytes(out)

    def program_eprom(self, base: int, data: bytes, progress=None) -> None:
        """Program EPROM with data.

        Sends 'P' command with address and length, then sends N bytes.

        Args:
            base: Starting address (16-bit)
            data: Bytes to program
            progress: Optional callback(bytes_written) for progress updates
        """
        self.send_byte(ord("P"))
        self.send_word(base)
        self.send_word(len(data))

        for i, b in enumerate(data):
            self.send_byte(b)
            if progress and (i % 128 == 0 or i == len(data) - 1):
                progress(i + 1)

        self.serial.flush()
