#!/usr/bin/env python3
"""
serial_eprom_gui.py

Clean-room PySide6 GUI host utility for a serial EPROM programmer.

Requires:
    pip install PySide6 pyserial
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

import serial
import serial.tools.list_ports

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class EpromType:
    name: str
    size: int


EPROM_TYPES = {
    "2716": EpromType("2716", 2 * 1024),
    "2732": EpromType("2732", 4 * 1024),
    "2732A": EpromType("2732A", 4 * 1024),
    "2764": EpromType("2764", 8 * 1024),
    "27128": EpromType("27128", 16 * 1024),
    "27256": EpromType("27256", 32 * 1024),
}


def hex_dump(data: bytes, base: int = 0) -> str:
    lines: list[str] = []

    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{base + offset:04X}: {hex_part:<47}  {ascii_part}")

    return "\n".join(lines)


class SerialEpromProgrammer:
    def __init__(self, port: str, baud: int):
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
        if self.serial.is_open:
            self.serial.close()

    def send_byte(self, value: int) -> None:
        self.serial.write(bytes([value & 0xFF]))

    def recv_byte(self) -> int:
        data = self.serial.read(1)
        if len(data) != 1:
            raise TimeoutError("Timed out waiting for byte")
        return data[0]

    def send_word(self, value: int) -> None:
        self.send_byte(value & 0xFF)
        self.send_byte((value >> 8) & 0xFF)

    def read_eprom(self, base: int, size: int, progress=None) -> bytes:
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
        self.send_byte(ord("P"))
        self.send_word(base)
        self.send_word(len(data))

        for i, b in enumerate(data):
            self.send_byte(b)
            if progress and (i % 128 == 0 or i == len(data) - 1):
                progress(i + 1)

        self.serial.flush()


class Worker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, action: str, port: str, baud: int, base: int, buffer: bytes):
        super().__init__()
        self.action = action
        self.port = port
        self.baud = baud
        self.base = base
        self.buffer = buffer

    @Slot()
    def run(self) -> None:
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial EPROM Programmer")
        self.resize(950, 700)

        self.eprom = EPROM_TYPES["2716"]
        self.buffer = bytearray([0xFF] * self.eprom.size)
        self.thread: QThread | None = None
        self.worker: Worker | None = None

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.eprom_combo = QComboBox()
        self.base_edit = QLineEdit("0000")
        self.progress = QProgressBar()
        self.hex_view = QPlainTextEdit()
        self.log_view = QPlainTextEdit()

        self._build_ui()
        self.refresh_ports()
        self.update_hex_view()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        config = QGroupBox("Connection / EPROM")
        grid = QGridLayout(config)

        self.baud_combo.addItems(["300", "600", "1200", "2400", "4800", "9600", "19200", "38400"])
        self.baud_combo.setCurrentText("9600")

        self.eprom_combo.addItems(EPROM_TYPES.keys())
        self.eprom_combo.currentTextChanged.connect(self.select_eprom)

        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.refresh_ports)

        grid.addWidget(QLabel("Port"), 0, 0)
        grid.addWidget(self.port_combo, 0, 1)
        grid.addWidget(refresh_btn, 0, 2)

        grid.addWidget(QLabel("Baud"), 1, 0)
        grid.addWidget(self.baud_combo, 1, 1)

        grid.addWidget(QLabel("EPROM"), 2, 0)
        grid.addWidget(self.eprom_combo, 2, 1)

        grid.addWidget(QLabel("Base Hex"), 3, 0)
        grid.addWidget(self.base_edit, 3, 1)

        layout.addWidget(config)

        file_row = QHBoxLayout()

        load_btn = QPushButton("Load Binary")
        save_btn = QPushButton("Save Binary")
        fill_btn = QPushButton("Fill FF")
        dump_btn = QPushButton("Refresh Dump")

        load_btn.clicked.connect(self.load_binary)
        save_btn.clicked.connect(self.save_binary)
        fill_btn.clicked.connect(self.fill_ff)
        dump_btn.clicked.connect(self.update_hex_view)

        file_row.addWidget(load_btn)
        file_row.addWidget(save_btn)
        file_row.addWidget(fill_btn)
        file_row.addWidget(dump_btn)

        layout.addLayout(file_row)

        action_row = QHBoxLayout()

        read_btn = QPushButton("Read EPROM")
        blank_btn = QPushButton("Blank Check")
        program_btn = QPushButton("Program EPROM")
        verify_btn = QPushButton("Verify EPROM")

        read_btn.clicked.connect(lambda: self.start_worker("read"))
        blank_btn.clicked.connect(lambda: self.start_worker("blank"))
        program_btn.clicked.connect(self.confirm_program)
        verify_btn.clicked.connect(lambda: self.start_worker("verify"))

        action_row.addWidget(read_btn)
        action_row.addWidget(blank_btn)
        action_row.addWidget(program_btn)
        action_row.addWidget(verify_btn)

        layout.addLayout(action_row)

        layout.addWidget(self.progress)

        self.hex_view.setReadOnly(True)
        self.hex_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(QLabel("Buffer"))
        layout.addWidget(self.hex_view, stretch=4)

        self.log_view.setReadOnly(True)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_view, stretch=1)

        self.setCentralWidget(root)

    def refresh_ports(self) -> None:
        current = self.port_combo.currentText()
        self.port_combo.clear()

        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["/dev/ttyUSB0", "/dev/ttyS0", "COM1"]

        self.port_combo.addItems(ports)

        if current:
            index = self.port_combo.findText(current)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def select_eprom(self, name: str) -> None:
        self.eprom = EPROM_TYPES[name]
        self.buffer = bytearray([0xFF] * self.eprom.size)
        self.log(f"Selected {self.eprom.name}, {self.eprom.size} bytes")
        self.update_hex_view()

    def base_addr(self) -> int:
        text = self.base_edit.text().strip().replace("$", "")
        return int(text, 16)

    def load_binary(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Load Binary")
        if not filename:
            return

        path = pathlib.Path(filename)
        data = path.read_bytes()

        if len(data) > self.eprom.size:
            QMessageBox.warning(
                self,
                "File too large",
                f"File is {len(data)} bytes, EPROM size is {self.eprom.size} bytes.",
            )
            return

        self.buffer[:] = bytes([0xFF]) * self.eprom.size
        self.buffer[: len(data)] = data
        self.log(f"Loaded {len(data)} bytes from {path.name}")
        self.update_hex_view()

    def save_binary(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Save Binary")
        if not filename:
            return

        pathlib.Path(filename).write_bytes(bytes(self.buffer))
        self.log(f"Saved {len(self.buffer)} bytes")

    def fill_ff(self) -> None:
        self.buffer[:] = bytes([0xFF]) * len(self.buffer)
        self.log("Buffer filled with FF")
        self.update_hex_view()

    def update_hex_view(self) -> None:
        try:
            base = self.base_addr()
        except ValueError:
            base = 0

        self.hex_view.setPlainText(hex_dump(bytes(self.buffer), base))

    def confirm_program(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Programming",
            "Program the EPROM with the current buffer?",
        )

        if reply == QMessageBox.Yes:
            self.start_worker("program")

    def start_worker(self, action: str) -> None:
        if self.thread is not None:
            QMessageBox.information(self, "Busy", "An operation is already running.")
            return

        try:
            base = self.base_addr()
        except ValueError:
            QMessageBox.warning(self, "Bad base address", "Base address must be hexadecimal.")
            return

        port = self.port_combo.currentText().strip()
        baud = int(self.baud_combo.currentText())

        if not port:
            QMessageBox.warning(self, "No port", "Select a serial port first.")
            return

        self.progress.setRange(0, len(self.buffer))
        self.progress.setValue(0)
        self.log(f"Starting {action}...")

        self.thread = QThread()
        self.worker = Worker(action, port, baud, base, bytes(self.buffer))
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(lambda result, a=action: self.worker_done(a, result))
        self.worker.failed.connect(self.worker_failed)

        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup_worker)

        self.thread.start()

    def worker_done(self, action: str, result: object) -> None:
        if action == "read":
            self.buffer[:] = result
            self.update_hex_view()
            self.log("Read complete.")

        elif action == "blank":
            errors = result
            if not errors:
                self.log("Blank check OK.")
            else:
                self.log(f"Blank check failed: {len(errors)} non-blank bytes.")
                for addr, value in errors[:50]:
                    self.log(f"${addr:04X}: ${value:02X}")

        elif action == "program":
            self.log("Program data sent.")

        elif action == "verify":
            errors = result
            if not errors:
                self.log("Verify OK.")
            else:
                self.log(f"Verify failed: {len(errors)} mismatches.")
                for addr, want, got in errors[:50]:
                    self.log(f"${addr:04X}: want ${want:02X}, got ${got:02X}")

    def worker_failed(self, message: str) -> None:
        self.log(f"ERROR: {message}")
        QMessageBox.critical(self, "Operation failed", message)

    def cleanup_worker(self) -> None:
        self.worker = None
        self.thread = None

    def log(self, text: str) -> None:
        self.log_view.appendPlainText(text)


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
