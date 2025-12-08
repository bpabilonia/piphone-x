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
echo "[1/6] Updating system packages..."
sudo apt update

# Install system dependencies (including libraries needed for Pillow if building from source)
echo "[2/6] Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    python3-rpi.gpio \
    python3-serial \
    python3-pyaudio \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    portaudio19-dev

# Install Python packages (minimal - most are installed via apt)
echo "[3/6] Installing Python packages..."
pip3 install --user schedule

# Add user to dialout group for serial access
echo "[4/6] Configuring serial permissions..."
if ! groups | grep -q dialout; then
    sudo usermod -a -G dialout $USER
    echo "Added $USER to dialout group"
    echo "Please log out and back in for changes to take effect"
fi

# Add user to audio group for audio access
echo "[5/6] Configuring audio permissions..."
if ! groups | grep -q audio; then
    sudo usermod -a -G audio $USER
    echo "Added $USER to audio group"
fi

# Enable serial interface
echo "[6/6] Checking serial configuration..."
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
echo "IMPORTANT: Log out and back in for group changes to take effect!"
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

