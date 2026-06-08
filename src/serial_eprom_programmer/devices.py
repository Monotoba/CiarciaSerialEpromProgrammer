"""EPROM type definitions and registry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EpromType:
    """Immutable EPROM type specification."""
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
