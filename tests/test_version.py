"""Keep the runtime and installed distribution version synchronized."""

from importlib.metadata import version

from serial_eprom_programmer import __version__


def test_runtime_version_matches_distribution():
    assert __version__ == version("serial-eprom-programmer")
