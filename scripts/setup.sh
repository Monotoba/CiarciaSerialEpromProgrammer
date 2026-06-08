#!/bin/bash
set -e

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "=== Serial EPROM Programmer Setup ==="
echo "Python version: $PYTHON_VERSION"

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
    echo "ERROR: Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

VENV_DIR=".venv"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing uv..."
pip install uv 2>/dev/null || echo "Note: uv installation failed, will use pip"

echo "Installing project and dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -e ".[dev]"
else
    pip install -e ".[dev]"
fi

if [[ ! -d ".git" ]]; then
    echo "Initializing git repository..."
    git init
    git config user.email "rmorgan62@gmail.com" 2>/dev/null || true
    git config user.name "Test User" 2>/dev/null || true
    git add .
    git commit -m "Initial commit: project scaffolding and setup" 2>/dev/null || echo "Git commit skipped"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the application, execute:"
echo "  bash scripts/run.sh"
echo ""
echo "To run tests, execute:"
echo "  bash scripts/test.sh"
echo ""
