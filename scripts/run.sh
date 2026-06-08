#!/bin/bash
set -e

VENV_DIR=".venv"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "ERROR: Virtual environment not found. Run setup.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"
python -m serial_eprom_programmer.main
