"""Shared test fixtures and utilities."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_bin_file():
    """Create a temporary binary file with test data.

    Yields:
        Path to temporary binary file
    """
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        test_data = bytes(range(256))
        f.write(test_data)
        tmp_path = Path(f.name)

    yield tmp_path

    tmp_path.unlink(missing_ok=True)


@pytest.fixture
def mock_serial():
    """Create a mock serial.Serial object.

    Returns:
        MagicMock configured to simulate serial communication
    """
    mock = MagicMock()
    mock.is_open = True
    mock.read = MagicMock(return_value=b"\x00")
    mock.write = MagicMock(return_value=1)
    mock.flush = MagicMock()
    mock.close = MagicMock()
    return mock


@pytest.fixture
def mock_serial_factory(monkeypatch, mock_serial):
    """Factory fixture to patch serial.Serial during tests.

    Args:
        monkeypatch: pytest fixture for patching
        mock_serial: Mock serial object

    Yields:
        Function to call to reset mock state
    """
    def patch_serial():
        monkeypatch.setattr("serial.Serial", lambda *args, **kwargs: mock_serial)

    patch_serial()
    yield mock_serial

    mock_serial.reset_mock()


