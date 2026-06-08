"""Theme management for dark/light/system modes."""

from typing import Literal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor


ThemeMode = Literal["dark", "light", "system"]


class ThemeManager:
    """Manage application themes."""

    @staticmethod
    def get_dark_stylesheet() -> str:
        """Get dark theme stylesheet."""
        return """
        QWidget {
            color: #e0e0e0;
            background-color: #1e1e1e;
        }
        QMainWindow {
            background-color: #1e1e1e;
        }
        QGroupBox {
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 5px;
            margin-top: 0.5em;
            padding-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #383838;
        }
        QPushButton:pressed {
            background-color: #1a1a1a;
        }
        QComboBox {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QLineEdit {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
        }
        QPlainTextEdit {
            background-color: #252525;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 4px;
        }
        QProgressBar {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #0078d4;
        }
        QLabel {
            color: #e0e0e0;
        }
        QDialog {
            background-color: #1e1e1e;
        }
        QScrollArea {
            background-color: #1e1e1e;
        }
        QTabWidget::pane {
            border: 1px solid #404040;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #e0e0e0;
            padding: 5px;
            border: 1px solid #404040;
        }
        QTabBar::tab:selected {
            background-color: #383838;
        }
        QMessageBox {
            background-color: #1e1e1e;
        }
        QMessageBox QLabel {
            color: #e0e0e0;
        }
        """

    @staticmethod
    def get_light_stylesheet() -> str:
        """Get light theme stylesheet (returns empty, uses system)."""
        # Light theme uses system defaults, so return empty string
        return ""

    @staticmethod
    def get_system_theme() -> ThemeMode:
        """Detect system theme preference."""
        # Get palette from current application style
        app = QApplication.instance()
        if app:
            palette = app.palette()
            # Check if system is in dark mode by examining base color lightness
            base_color = palette.base().color()
            if base_color.lightness() < 128:
                return "dark"
        return "light"

    @staticmethod
    def apply_theme(app: QApplication, theme: ThemeMode) -> None:
        """Apply theme to application."""
        if theme == "system":
            theme = ThemeManager.get_system_theme()

        if theme == "dark":
            stylesheet = ThemeManager.get_dark_stylesheet()
            app.setStyle("Fusion")
            app.setStyleSheet(stylesheet)
        else:
            # Light mode: reset to system style
            app.setStyle("Fusion")
            app.setStyleSheet("")

    @staticmethod
    def validate_theme(theme: str) -> bool:
        """Check if theme name is valid."""
        return theme in ("dark", "light", "system")
