"""Qt worker thread for EPROM operations."""

from PySide6.QtCore import QObject, Signal, Slot

from serial_eprom_programmer.programmer import SerialEpromProgrammer


class Worker(QObject):
    """QObject worker for running EPROM operations in a background thread.

    Signals:
        finished: Emitted with result when operation completes
        failed: Emitted with error message on failure
        progress: Emitted with bytes_processed during operation
    """

    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, action: str, port: str, baud: int, base: int, buffer: bytes):
        """Initialize worker.

        Args:
            action: Operation type ('read', 'blank', 'program', 'verify')
            port: Serial port
            baud: Baud rate
            base: Base address for operation
            buffer: Data buffer (for program) or size placeholder (for read/verify)
        """
        super().__init__()
        self.action = action
        self.port = port
        self.baud = baud
        self.base = base
        self.buffer = buffer

    @Slot()
    def run(self) -> None:
        """Execute the worker action. Designed to run in a QThread."""
        programmer = None

        try:
            programmer = SerialEpromProgrammer(self.port, self.baud)

            if self.action == "read":
                data = programmer.read_eprom(
                    self.base,
                    len(self.buffer),
                    progress=self.progress.emit,
                )
                self.finished.emit(data)

            elif self.action == "blank":
                data = programmer.read_eprom(
                    self.base,
                    len(self.buffer),
                    progress=self.progress.emit,
                )
                errors = [(self.base + i, b) for i, b in enumerate(data) if b != 0xFF]
                self.finished.emit(errors)

            elif self.action == "program":
                programmer.program_eprom(
                    self.base,
                    self.buffer,
                    progress=self.progress.emit,
                )
                self.finished.emit(None)

            elif self.action == "verify":
                data = programmer.read_eprom(
                    self.base,
                    len(self.buffer),
                    progress=self.progress.emit,
                )
                errors = [
                    (self.base + i, want, got)
                    for i, (want, got) in enumerate(zip(self.buffer, data))
                    if want != got
                ]
                self.finished.emit(errors)

            else:
                raise ValueError(f"Unknown action: {self.action}")

        except Exception as exc:
            self.failed.emit(str(exc))

        finally:
            if programmer is not None:
                programmer.close()
