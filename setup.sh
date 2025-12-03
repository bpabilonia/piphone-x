#!/bin/bash
# PiPhone-X Setup Script
# For Raspberry Pi 3+ with 32-bit OS

set -e

echo "========================================"
echo "  PiPhone-X Installation Script"
echo "========================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: Not running on Raspberry Pi"
    echo "Some features may not work correctly"
    echo ""
fi

# Update system
echo "[1/5] Updating system packages..."
sudo apt update

# Install dependencies
echo "[2/5] Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-pil \
    python3-pil.imagetk

# Install Python packages
echo "[3/5] Installing Python packages..."
pip3 install --user -r requirements.txt

# Add user to dialout group for serial access
echo "[4/5] Configuring serial permissions..."
if ! groups | grep -q dialout; then
    sudo usermod -a -G dialout $USER
    echo "Added $USER to dialout group"
    echo "Please log out and back in for changes to take effect"
fi

# Enable serial interface
echo "[5/5] Checking serial configuration..."
if ! grep -q "enable_uart=1" /boot/config.txt 2>/dev/null; then
    echo ""
    echo "NOTE: You may need to enable the serial interface:"
    echo "  sudo raspi-config"
    echo "  Navigate to: Interface Options > Serial Port"
    echo "  - Login shell over serial: No"
    echo "  - Serial port hardware enabled: Yes"
    echo ""
fi

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To run PiPhone-X:"
echo "  python3 main.py           # Normal mode"
echo "  python3 main.py --sim     # Simulation mode"
echo ""
echo "For auto-start on boot, run:"
echo "  sudo cp piphone.service /etc/systemd/system/"
echo "  sudo systemctl enable piphone"
echo "  sudo systemctl start piphone"
echo ""

