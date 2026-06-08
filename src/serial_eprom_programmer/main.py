"""Entry point for Serial EPROM Programmer application."""

import sys

from PySide6.QtWidgets import QApplication

from serial_eprom_programmer.gui.main_window import MainWindow


def main() -> int:
    """Launch the application.

    Returns:
        Application exit code
    """
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
