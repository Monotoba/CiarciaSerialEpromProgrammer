"""Tests for Worker thread class."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt

from serial_eprom_programmer.worker import Worker


class TestWorker:
    """Test Worker QObject class."""

    def test_worker_init(self):
        """Test worker initialization."""
        worker = Worker("read", "/dev/ttyUSB0", 9600, 0x0000, b"\xFF" * 100)
        assert worker.action == "read"
        assert worker.port == "/dev/ttyUSB0"
        assert worker.baud == 9600
        assert worker.base == 0x0000

    def test_worker_signals_exist(self):
        """Test that worker has required signals."""
        worker = Worker("read", "/dev/ttyUSB0", 9600, 0x0000, b"")
        assert hasattr(worker, "finished")
        assert hasattr(worker, "failed")
        assert hasattr(worker, "progress")

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_read_action(self, mock_programmer_class):
        """Test worker read action."""
        mock_programmer = MagicMock()
        mock_programmer.read_eprom.return_value = b"\xAA\xBB"
        mock_programmer_class.return_value = mock_programmer

        worker = Worker("read", "/dev/ttyUSB0", 9600, 0x0000, b"\xFF" * 100)
        finished_result = []
        worker.finished.connect(lambda x: finished_result.append(x))

        worker.run()

        assert len(finished_result) == 1
        assert finished_result[0] == b"\xAA\xBB"
        mock_programmer.close.assert_called()

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_blank_action(self, mock_programmer_class):
        """Test worker blank check action."""
        mock_programmer = MagicMock()
        mock_programmer.read_eprom.return_value = b"\xFF\xFF\xAA\xFF"
        mock_programmer_class.return_value = mock_programmer

        worker = Worker("blank", "/dev/ttyUSB0", 9600, 0x0000, b"\xFF" * 4)
        finished_result = []
        worker.finished.connect(lambda x: finished_result.append(x))

        worker.run()

        assert len(finished_result) == 1
        errors = finished_result[0]
        assert len(errors) == 1
        assert errors[0][0] == 0x0002  # Address of non-FF byte

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_program_action(self, mock_programmer_class):
        """Test worker program action."""
        mock_programmer = MagicMock()
        mock_programmer_class.return_value = mock_programmer

        data = b"\xAA\xBB"
        worker = Worker("program", "/dev/ttyUSB0", 9600, 0x0000, data)
        finished_result = []
        worker.finished.connect(lambda x: finished_result.append(x))

        worker.run()

        assert len(finished_result) == 1
        assert finished_result[0] is None
        mock_programmer.program_eprom.assert_called_once()
        mock_programmer.close.assert_called()

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_verify_action(self, mock_programmer_class):
        """Test worker verify action."""
        mock_programmer = MagicMock()
        mock_programmer.read_eprom.return_value = b"\xAA\xBB"
        mock_programmer_class.return_value = mock_programmer

        worker = Worker("verify", "/dev/ttyUSB0", 9600, 0x0000, b"\xAA\xCC")
        finished_result = []
        worker.finished.connect(lambda x: finished_result.append(x))

        worker.run()

        assert len(finished_result) == 1
        errors = finished_result[0]
        assert len(errors) == 1
        assert errors[0][0] == 0x0001  # Address of mismatch
        assert errors[0][1] == 0xCC  # Expected
        assert errors[0][2] == 0xBB  # Got

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_invalid_action(self, mock_programmer_class):
        """Test worker with invalid action."""
        mock_programmer = MagicMock()
        mock_programmer_class.return_value = mock_programmer

        worker = Worker("invalid", "/dev/ttyUSB0", 9600, 0x0000, b"")
        failed_result = []
        worker.failed.connect(lambda x: failed_result.append(x))

        worker.run()

        assert len(failed_result) == 1
        assert "Unknown action" in failed_result[0]
        mock_programmer.close.assert_called()

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_exception_handling(self, mock_programmer_class):
        """Test worker exception handling."""
        mock_programmer_class.side_effect = RuntimeError("Connection failed")

        worker = Worker("read", "/dev/ttyUSB0", 9600, 0x0000, b"")
        failed_result = []
        worker.failed.connect(lambda x: failed_result.append(x))

        worker.run()

        assert len(failed_result) == 1
        assert "Connection failed" in failed_result[0]

    @patch("serial_eprom_programmer.worker.SerialEpromProgrammer")
    def test_worker_progress_callback(self, mock_programmer_class):
        """Test worker progress signal emission."""
        mock_programmer = MagicMock()
        mock_programmer.read_eprom.side_effect = lambda base, size, progress: (
            progress(50) if progress else None,
            b"\x00" * size
        )[-1]
        mock_programmer_class.return_value = mock_programmer

        worker = Worker("read", "/dev/ttyUSB0", 9600, 0x0000, b"\xFF" * 100)
        progress_values = []
        worker.progress.connect(lambda x: progress_values.append(x))

        worker.run()

        assert len(progress_values) > 0
