"""Main window for Serial EPROM Programmer GUI."""

import pathlib

import serial.tools.list_ports
from PySide6.QtCore import QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from serial_eprom_programmer.devices import EPROM_TYPES
from serial_eprom_programmer.utils import hex_dump, parse_hex_dump
from serial_eprom_programmer.worker import Worker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window and UI."""
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

        self._edit_mode = False
        self._pre_edit_text: str = ""
        self._edit_lockout_widgets: list = []

        self._build_ui()
        self.refresh_ports()
        self.update_hex_view()

    def _build_ui(self) -> None:
        """Build the user interface."""
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
        self.edit_btn = QPushButton("Edit Buffer")
        self.cancel_btn = QPushButton("Cancel Edit")

        load_btn.clicked.connect(self.load_binary)
        save_btn.clicked.connect(self.save_binary)
        fill_btn.clicked.connect(self.fill_ff)
        dump_btn.clicked.connect(self.update_hex_view)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.cancel_btn.clicked.connect(self._cancel_edit)
        self.cancel_btn.setVisible(False)

        file_row.addWidget(load_btn)
        file_row.addWidget(save_btn)
        file_row.addWidget(fill_btn)
        file_row.addWidget(dump_btn)
        file_row.addWidget(self.edit_btn)
        file_row.addWidget(self.cancel_btn)

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
        font = QFont("Monospace", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.hex_view.setFont(font)
        layout.addWidget(QLabel("Buffer"))
        layout.addWidget(self.hex_view, stretch=4)

        self.log_view.setReadOnly(True)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_view, stretch=1)

        self._edit_lockout_widgets = [
            load_btn, fill_btn, read_btn, blank_btn, program_btn, verify_btn,
            self.eprom_combo, refresh_btn,
        ]

        self.setCentralWidget(root)

    def refresh_ports(self) -> None:
        """Refresh list of available serial ports."""
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
        """Select EPROM type and reset buffer."""
        self.eprom = EPROM_TYPES[name]
        self.buffer = bytearray([0xFF] * self.eprom.size)
        self.log(f"Selected {self.eprom.name}, {self.eprom.size} bytes")
        self.update_hex_view()

    def base_addr(self) -> int:
        """Parse base address from input field (hex)."""
        text = self.base_edit.text().strip().replace("$", "")
        return int(text, 16)

    def load_binary(self) -> None:
        """Load binary file into buffer."""
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
        """Save buffer to binary file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Binary")
        if not filename:
            return

        pathlib.Path(filename).write_bytes(bytes(self.buffer))
        self.log(f"Saved {len(self.buffer)} bytes")

    def fill_ff(self) -> None:
        """Fill buffer with 0xFF."""
        self.buffer[:] = bytes([0xFF]) * len(self.buffer)
        self.log("Buffer filled with FF")
        self.update_hex_view()

    def update_hex_view(self) -> None:
        """Update hex dump display."""
        try:
            base = self.base_addr()
        except ValueError:
            base = 0

        self.hex_view.setPlainText(hex_dump(bytes(self.buffer), base))

    def confirm_program(self) -> None:
        """Show confirmation dialog before programming."""
        reply = QMessageBox.question(
            self,
            "Confirm Programming",
            "Program the EPROM with the current buffer?",
        )

        if reply == QMessageBox.Yes:
            self.start_worker("program")

    def start_worker(self, action: str) -> None:
        """Start a worker thread for the given action.

        Args:
            action: Operation type ('read', 'blank', 'program', 'verify')
        """
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
        """Handle completed worker operation.

        Args:
            action: Operation that completed
            result: Operation result (varies by action)
        """
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
        """Handle worker failure.

        Args:
            message: Error message
        """
        self.log(f"ERROR: {message}")
        QMessageBox.critical(self, "Operation failed", message)

    def cleanup_worker(self) -> None:
        """Clean up worker thread references."""
        self.worker = None
        self.thread = None

    def log(self, text: str) -> None:
        """Append text to log view.

        Args:
            text: Message to log
        """
        self.log_view.appendPlainText(text)

    def toggle_edit_mode(self) -> None:
        """Toggle between edit and view mode."""
        if not self._edit_mode:
            self._enter_edit_mode()
        else:
            self._apply_edits()

    def _enter_edit_mode(self) -> None:
        """Enter edit mode — allow direct hex editing."""
        self._pre_edit_text = self.hex_view.toPlainText()
        self._edit_mode = True
        self.hex_view.setReadOnly(False)
        self.hex_view.setStyleSheet("background-color: #fffbe6;")
        self.edit_btn.setText("Apply Edits")
        self.cancel_btn.setVisible(True)
        self._set_edit_controls_enabled(False)
        self.log("Edit mode: modify hex bytes, then click Apply Edits.")

    def _apply_edits(self) -> None:
        """Apply edits from hex view back to buffer."""
        text = self.hex_view.toPlainText()
        try:
            new_data = parse_hex_dump(text)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid hex data", str(exc))
            return
        if len(new_data) != len(self.buffer):
            QMessageBox.warning(
                self, "Size mismatch",
                f"Edited buffer is {len(new_data)} bytes, expected {len(self.buffer)}."
            )
            return
        self.buffer[:] = new_data
        self._exit_edit_mode()
        self.update_hex_view()
        self.log(f"Buffer updated from edits ({len(new_data)} bytes).")

    def _cancel_edit(self) -> None:
        """Cancel edits and restore original display."""
        self.hex_view.setPlainText(self._pre_edit_text)
        self._exit_edit_mode()
        self.log("Edit cancelled.")

    def _exit_edit_mode(self) -> None:
        """Exit edit mode — return to view-only."""
        self._edit_mode = False
        self.hex_view.setReadOnly(True)
        self.hex_view.setStyleSheet("")
        self.edit_btn.setText("Edit Buffer")
        self.cancel_btn.setVisible(False)
        self._set_edit_controls_enabled(True)

    def _set_edit_controls_enabled(self, enabled: bool) -> None:
        """Disable/enable operation buttons during edit mode.

        Args:
            enabled: True to enable, False to disable
        """
        for widget in self._edit_lockout_widgets:
            widget.setEnabled(enabled)
