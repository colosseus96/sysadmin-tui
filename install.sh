#!/bin/bash
# Install script for dockertui dependencies

set -e

echo "======================================"
echo "  dockertui - Dependency Installer"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3 first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  RHEL/CentOS:   sudo yum install python3 python3-pip"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    exit 1
fi

echo "[✓] Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "[WARN] pip is not installed. Attempting to install..."
    
    # Try different methods based on OS
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python-pip
    else
        echo "[ERROR] Could not automatically install pip."
        echo "Please install pip manually for your distribution."
        exit 1
    fi
fi

# Determine which pip command to use
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null && command -v pip &> /dev/null; then
    PIP_CMD="pip"
fi

echo "[✓] pip found: $($PIP_CMD --version)"
echo ""

# Check if running in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[INFO] Not running in a virtual environment."
    echo "It's recommended to use a virtual environment, but we'll continue with system packages."
    echo ""
    read -p "Continue with system-wide installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

echo "Installing dependencies from requirements.txt..."
echo ""

# Install requirements
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
else
    echo "[WARN] requirements.txt not found, installing default packages..."
    $PIP_CMD install rich psutil
fi

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "You can now run dockertui with:"
echo "  python3 dockertui.py"
echo ""
echo "Optional: Make it executable and move to PATH:"
echo "  chmod +x dockertui.py"
echo "  sudo mv dockertui.py /usr/local/bin/dockertui"
echo ""
