"""Check a built wheel and launch its GUI without the source checkout."""

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    wheels = list(Path("dist").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("Expected exactly one wheel in dist/")
    with tempfile.TemporaryDirectory() as directory:
        with zipfile.ZipFile(wheels[0]) as archive:
            archive.extractall(directory)
        # Isolated mode excludes PYTHONPATH and the checkout from imports.
        code = """
import sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from PySide6.QtWidgets import QApplication
from serial_eprom_programmer.main import main
from serial_eprom_programmer.gui.main_window import MainWindow
import serial_eprom_programmer
assert Path(serial_eprom_programmer.__file__).is_relative_to(Path(sys.argv[1]))
assert callable(main)
app = QApplication([])
window = MainWindow()
window.show()
app.processEvents()
assert window.isVisible()
assert len(window.buffer) == 2048
window.close()
app.processEvents()
print('Built wheel imports and GUI launch passed')
"""
        subprocess.run(
            [sys.executable, "-I", "-c", code, directory],
            cwd=directory,
            check=True,
            timeout=30,
        )


if __name__ == "__main__":
    main()
