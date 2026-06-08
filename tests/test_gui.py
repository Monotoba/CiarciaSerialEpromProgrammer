"""Tests for GUI components (smoke tests with pytest-qt)."""

from unittest.mock import MagicMock, patch

import pytest

from serial_eprom_programmer.devices import EPROM_TYPES
from serial_eprom_programmer.gui.main_window import MainWindow


@pytest.mark.qt
class TestMainWindow:
    """Test MainWindow class (smoke tests)."""

    def test_main_window_creation(self, qtbot):
        """Test MainWindow instantiation."""
        window = MainWindow()
        qtbot.addWidget(window)
        assert window is not None
        assert window.windowTitle() == "Serial EPROM Programmer"

    def test_main_window_initial_eprom(self, qtbot):
        """Test initial EPROM type."""
        window = MainWindow()
        qtbot.addWidget(window)
        assert window.eprom.name == "2716"
        assert window.eprom.size == 2048

    def test_main_window_buffer_initialized(self, qtbot):
        """Test that buffer is initialized to 0xFF."""
        window = MainWindow()
        qtbot.addWidget(window)
        assert len(window.buffer) == 2048
        assert window.buffer[0] == 0xFF

    def test_select_eprom(self, qtbot):
        """Test selecting different EPROM type."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.select_eprom("27256")
        assert window.eprom.name == "27256"
        assert window.eprom.size == 32768
        assert len(window.buffer) == 32768

    def test_base_addr_parsing(self, qtbot):
        """Test base address hex parsing."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.base_edit.setText("1000")
        assert window.base_addr() == 0x1000

    def test_base_addr_with_dollar_sign(self, qtbot):
        """Test base address parsing with $ prefix."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.base_edit.setText("$2000")
        assert window.base_addr() == 0x2000

    def test_base_addr_invalid(self, qtbot):
        """Test invalid base address raises ValueError."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.base_edit.setText("ZZZZ")
        with pytest.raises(ValueError):
            window.base_addr()

    def test_fill_ff(self, qtbot):
        """Test filling buffer with 0xFF."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.buffer[0] = 0x00
        window.fill_ff()
        assert window.buffer[0] == 0xFF

    def test_update_hex_view(self, qtbot):
        """Test hex view update."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.buffer[0] = 0xAA
        window.update_hex_view()
        hex_text = window.hex_view.toPlainText()
        assert "AA" in hex_text

    def test_log_message(self, qtbot):
        """Test logging messages."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.log("Test message")
        log_text = window.log_view.toPlainText()
        assert "Test message" in log_text

    def test_port_combo_not_empty(self, qtbot):
        """Test that port combo has entries after refresh."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.port_combo.count() > 0

    def test_baud_combo_has_standard_rates(self, qtbot):
        """Test that baud combo has standard rates."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.baud_combo.findText("9600") >= 0
        assert window.baud_combo.findText("19200") >= 0

    def test_eprom_combo_all_types(self, qtbot):
        """Test that EPROM combo has all types."""
        window = MainWindow()
        qtbot.addWidget(window)

        for chip_name in EPROM_TYPES.keys():
            assert window.eprom_combo.findText(chip_name) >= 0

    @patch("serial_eprom_programmer.gui.main_window.QFileDialog.getOpenFileName")
    def test_load_binary(self, mock_dialog, qtbot, tmp_bin_file):
        """Test loading a binary file."""
        mock_dialog.return_value = (str(tmp_bin_file), "")

        window = MainWindow()
        qtbot.addWidget(window)

        window.load_binary()
        # File should have 256 bytes (0-255)
        assert window.buffer[0] == 0x00
        assert window.buffer[1] == 0x01

    @patch("serial_eprom_programmer.gui.main_window.QFileDialog.getSaveFileName")
    def test_save_binary(self, mock_dialog, qtbot, tmp_path):
        """Test saving a binary file."""
        tmp_file = tmp_path / "test_save.bin"
        mock_dialog.return_value = (str(tmp_file), "")

        window = MainWindow()
        qtbot.addWidget(window)
        window.buffer[0] = 0xAA

        window.save_binary()
        assert tmp_file.exists()
        assert tmp_file.read_bytes()[0] == 0xAA

    def test_start_worker_guard_no_port(self, qtbot):
        """Test start_worker guards against missing port."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.port_combo.clear()

        # Should not raise, but will show message dialog
        window.start_worker("read")
        assert window.thread is None

    def test_start_worker_invalid_base(self, qtbot):
        """Test start_worker guards against invalid base address."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.base_edit.setText("ZZZZ")

        window.start_worker("read")
        assert window.thread is None

    def test_start_worker_guard_concurrent(self, qtbot):
        """Test start_worker prevents concurrent operations."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Simulate an active thread
        window.thread = MagicMock()

        window.start_worker("read")
        # Should not create a new thread while one is running
        assert window.thread is not None

    def test_cleanup_worker(self, qtbot):
        """Test worker cleanup."""
        window = MainWindow()
        qtbot.addWidget(window)

        window.thread = MagicMock()
        window.worker = MagicMock()

        window.cleanup_worker()
        assert window.thread is None
        assert window.worker is None
