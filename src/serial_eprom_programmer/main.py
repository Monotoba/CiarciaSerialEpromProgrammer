"""Entry point for Serial EPROM Programmer application."""

import sys

from PySide6.QtWidgets import QApplication

from serial_eprom_programmer.config import AppSettings
from serial_eprom_programmer.gui.main_window import MainWindow
from serial_eprom_programmer.gui.theme_manager import ThemeManager


def main() -> int:
    """Launch the application.

    Returns:
        Application exit code
    """
    app = QApplication(sys.argv)

    # Load and apply saved theme
    settings = AppSettings()
    theme = settings.get_theme()
    ThemeManager.apply_theme(app, theme)  # type: ignore

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
