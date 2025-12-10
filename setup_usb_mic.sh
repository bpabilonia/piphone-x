#!/bin/bash
# USB Microphone Setup for Raspberry Pi
# Run with: bash setup_usb_mic.sh

echo "================================"
echo "USB Microphone Setup"
echo "================================"

# Check for USB audio devices
echo ""
echo "Step 1: Checking for USB audio devices..."
echo "-----------------------------------------"
arecord -l

echo ""
echo "Step 2: Checking ALSA cards..."
echo "-----------------------------------------"
cat /proc/asound/cards

echo ""
echo "Step 3: Installing audio tools..."
echo "-----------------------------------------"
sudo apt update
sudo apt install -y alsa-utils pulseaudio pavucontrol

echo ""
echo "Step 4: Setting USB mic as default input..."
echo "-----------------------------------------"

# Find USB audio card number
USB_CARD=$(arecord -l | grep -i usb | head -1 | sed 's/card \([0-9]*\):.*/\1/')

if [ -n "$USB_CARD" ]; then
    echo "Found USB audio on card $USB_CARD"
    
    # Create/update ALSA config
    cat > ~/.asoundrc << EOF
# Default to USB mic for recording
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:0,0"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:$USB_CARD,0"
    }
}

ctl.!default {
    type hw
    card 0
}
EOF
    echo "Created ~/.asoundrc with USB mic as default input"
else
    echo "No USB audio device found!"
    echo "Make sure your USB mic is plugged in."
fi

echo ""
echo "Step 5: Test recording (5 seconds)..."
echo "-----------------------------------------"
echo "Speak into the mic now!"
arecord -d 5 -f cd /tmp/test_mic.wav

echo ""
echo "Step 6: Playing back test..."
echo "-----------------------------------------"
aplay /tmp/test_mic.wav

echo ""
echo "================================"
echo "Setup complete!"
echo ""
echo "To test mic anytime:"
echo "  arecord -d 5 test.wav && aplay test.wav"
echo ""
echo "To adjust mic volume:"
echo "  alsamixer"
echo "  (Press F6 to select USB device, F4 for capture)"
echo "================================"


