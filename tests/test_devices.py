"""Tests for device type definitions."""

import pytest

from serial_eprom_programmer.devices import EPROM_TYPES, EpromType


class TestEpromType:
    """Test EpromType dataclass."""

    def test_eprom_type_creation(self):
        """Test creating an EpromType."""
        eprom = EpromType("test", 1024)
        assert eprom.name == "test"
        assert eprom.size == 1024

    def test_eprom_type_frozen(self):
        """Test that EpromType is frozen (immutable)."""
        eprom = EpromType("test", 1024)
        with pytest.raises(AttributeError):
            eprom.size = 2048


class TestEpromRegistry:
    """Test EPROM_TYPES registry."""

    def test_registry_has_required_types(self):
        """Test that all required EPROM types are present."""
        required = ["2716", "2732", "2732A", "2764", "27128", "27256", "27512"]
        for chip in required:
            assert chip in EPROM_TYPES, f"Missing EPROM type: {chip}"

    def test_registry_size(self):
        """Test that registry has expected number of entries."""
        assert len(EPROM_TYPES) == 7

    def test_registry_values_are_eprom_types(self):
        """Test that all registry values are EpromType instances."""
        for name, eprom in EPROM_TYPES.items():
            assert isinstance(eprom, EpromType)
            assert eprom.name == name

    def test_eprom_sizes_correct(self):
        """Test that EPROM sizes match specifications."""
        expected_sizes = {
            "2716": 2 * 1024,
            "2732": 4 * 1024,
            "2732A": 4 * 1024,
            "2764": 8 * 1024,
            "27128": 16 * 1024,
            "27256": 32 * 1024,
            "27512": 64 * 1024,
        }
        for chip, expected_size in expected_sizes.items():
            assert EPROM_TYPES[chip].size == expected_size

    def test_eprom_2716_smallest(self):
        """Test that 2716 is smallest EPROM (2KB)."""
        smallest = min(EPROM_TYPES.values(), key=lambda e: e.size)
        assert smallest.name == "2716"
        assert smallest.size == 2048

    def test_eprom_27512_largest(self):
        """Test that 27512 is largest EPROM (64KB)."""
        largest = max(EPROM_TYPES.values(), key=lambda e: e.size)
        assert largest.name == "27512"
        assert largest.size == 65536
