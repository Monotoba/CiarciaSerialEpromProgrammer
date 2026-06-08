"""Help dialog for Serial EPROM Programmer."""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class HelpDialog(QDialog):
    """Help dialog with tabbed interface."""

    def __init__(self, parent=None):
        """Initialize help dialog."""
        super().__init__(parent)
        self.setWindowTitle("Help — Serial EPROM Programmer")
        self.resize(700, 600)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build dialog UI."""
        layout = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_about_tab(), "About")
        tabs.addTab(self._create_formats_tab(), "File Formats")
        tabs.addTab(self._create_tips_tab(), "Tips & Tricks")
        tabs.addTab(self._create_keyboard_tab(), "Keyboard Shortcuts")
        layout.addWidget(tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _create_about_tab(self) -> QWidget:
        """Create About tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        text = QLabel(
            "<b>Serial EPROM Programmer</b><br><br>"
            "A modern, enterprise-grade application for reading, programming, "
            "and verifying EPROM chips via serial connection.<br><br>"
            "<b>Version:</b> 1.0<br>"
            "<b>License:</b> MIT<br><br>"
            "<b>Features:</b><br>"
            "• Support for classic EPROMs (2716–27512)<br>"
            "• Multiple file formats (Intel HEX, Motorola S-Record, Binary, and more)<br>"
            "• Real-time buffer editing<br>"
            "• Buffer fill operations (0xFF, 0x00)<br>"
            "• Dark and light theme support<br>"
            "• Serial communication via USB or direct RS-232<br><br>"
            "<b>Architecture:</b> Modular design with hardware, thread, GUI, and entry-point layers"
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()

        return widget

    def _create_formats_tab(self) -> QWidget:
        """Create File Formats tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        text = QLabel(
            "<b>Supported File Formats</b><br><br>"
            "<b>Standard Formats:</b><br>"
            "• <b>Intel HEX</b> (.hex, .ihx) — Universal standard, used by Arduino, PIC, AVR<br>"
            "• <b>Binary</b> (.bin, .rom, .epr) — Raw data, simplest format<br>"
            "• <b>Motorola S-Record</b> (.mot, .srec) — Motorola/Freescale standard<br>"
            "• <b>Addressed Hex Dump</b> (.ahex) — Monitor program text format<br><br>"
            "<b>Extended Formats:</b><br>"
            "• <b>Intel IHEX-32</b> (.ihex32) — 32-bit addressing for large flash<br>"
            "• <b>Tektronix HEX</b> (.tek) — Vintage test equipment format<br>"
            "• <b>TI-TXT</b> (.txt) — Texas Instruments microcontrollers<br>"
            "• <b>MIF</b> (.mif) — FPGA memory initialization (Xilinx/Altera)<br><br>"
            "<b>Historical Formats:</b><br>"
            "• <b>MOS Paper Tape</b> (.mos) — 1976 hobbyist computers (KIM-1, Apple I)<br><br>"
            "The application automatically detects format by file extension."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()

        return widget

    def _create_tips_tab(self) -> QWidget:
        """Create Tips & Tricks tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        text = QLabel(
            "<b>Tips & Tricks</b><br><br>"
            "<b>Buffer Management:</b><br>"
            "• Use 'Fill FF' to erase the buffer (default EPROM state)<br>"
            "• Use 'Fill 00' to fill with zeros for testing<br>"
            "• 'Edit Buffer' lets you modify individual bytes without reloading<br><br>"
            "<b>Programming Workflow:</b><br>"
            "1. Load firmware file (auto-detects format by extension)<br>"
            "2. Review data in hex view<br>"
            "3. Select correct EPROM type and serial port<br>"
            "4. Click 'Program EPROM' and confirm<br>"
            "5. Click 'Verify EPROM' to confirm success<br><br>"
            "<b>File Format Selection:</b><br>"
            "• Arduino/AVR → Intel HEX (.hex)<br>"
            "• PIC → Intel HEX (.hex)<br>"
            "• Motorola 68K → S-Record (.srec)<br>"
            "• TI MCU → TI-TXT (.txt)<br>"
            "• FPGA → MIF (.mif)<br>"
            "• Unknown → Binary (.bin)<br><br>"
            "<b>Troubleshooting:</b><br>"
            "• Check baud rate matches programmer (default 9600)<br>"
            "• Verify serial port in dropdown (use 'Refresh Ports')<br>"
            "• Try 'Blank Check' before programming used EPROMs"
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()

        return widget

    def _create_keyboard_tab(self) -> QWidget:
        """Create Keyboard Shortcuts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Create monospace font for shortcuts
        font = QFont("Monospace", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)

        text = QLabel(
            "<b>Keyboard Shortcuts</b><br><br>"
            "<b>File Operations:</b><br>"
            "No shortcuts assigned (use mouse for now)<br><br>"
            "<b>EPROM Operations:</b><br>"
            "• R - Read EPROM<br>"
            "• P - Program EPROM<br>"
            "• V - Verify EPROM<br>"
            "• B - Blank Check<br><br>"
            "<b>Buffer Operations:</b><br>"
            "• E - Edit Buffer<br>"
            "• F - Fill FF<br>"
            "• Z - Fill 00 (mnemonic: Zero)<br><br>"
            "<b>Note:</b> Shortcuts are planned for a future release.<br>"
            "Currently, use the button interface."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()

        return widget
