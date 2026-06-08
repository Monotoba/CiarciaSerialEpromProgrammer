"""Application configuration and settings."""

from PySide6.QtCore import QSettings


class AppSettings:
    """Manage application settings with persistence."""

    ORGANIZATION = "SerialEpromProgrammer"
    APPLICATION = "serial-eprom-programmer"

    def __init__(self):
        """Initialize settings."""
        self.settings = QSettings(self.ORGANIZATION, self.APPLICATION)

    def get_theme(self) -> str:
        """Get saved theme preference.

        Returns:
            'dark', 'light', or 'system' (default: 'system')
        """
        return str(self.settings.value("theme", "system"))

    def set_theme(self, theme: str) -> None:
        """Save theme preference.

        Args:
            theme: 'dark', 'light', or 'system'
        """
        self.settings.setValue("theme", theme)
        self.settings.sync()

    def get_geometry(self) -> bytes:
        """Get saved window geometry."""
        val = self.settings.value("geometry", b"")
        return bytes(val) if val else b""

    def set_geometry(self, geometry: bytes) -> None:
        """Save window geometry."""
        self.settings.setValue("geometry", geometry)
        self.settings.sync()

    def get_state(self) -> bytes:
        """Get saved window state."""
        val = self.settings.value("state", b"")
        return bytes(val) if val else b""

    def set_state(self, state: bytes) -> None:
        """Save window state."""
        self.settings.setValue("state", state)
        self.settings.sync()

    def get_all(self) -> dict:
        """Get all settings as dictionary."""
        result = {}
        for key in self.settings.allKeys():
            result[key] = self.settings.value(key)
        return result

    def clear(self) -> None:
        """Clear all settings."""
        self.settings.clear()
        self.settings.sync()
