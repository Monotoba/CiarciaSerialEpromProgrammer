"""
Serial EPROM Programmer — A PySide6 GUI for classic 27xx EPROMs.

Public API exports.
"""

from serial_eprom_programmer.devices import EPROM_TYPES, EpromType
from serial_eprom_programmer.programmer import SerialEpromProgrammer
from serial_eprom_programmer.utils import hex_dump

__version__ = "1.0.0"
__all__ = [
    "EpromType",
    "EPROM_TYPES",
    "SerialEpromProgrammer",
    "hex_dump",
]
