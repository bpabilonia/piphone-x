# PiPhone-X

A complete phone application for Raspberry Pi 3+ with Waveshare SIM7600X 4G HAT, featuring phone calls, SMS messaging, GPS navigation, and hardware diagnostics.

![PiPhone-X](https://img.shields.io/badge/Platform-Raspberry%20Pi%203%2B-red)
![Display](https://img.shields.io/badge/Display-480x320-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)

## Features

### 📞 Phone Calls
- Touch-friendly numeric keypad
- Dial, answer, and hang up calls
- Incoming call notifications
- Call duration timer
- DTMF tone support during calls
- Mute and speaker controls

### 💬 SMS Messaging
- Send and receive text messages
- Conversation view with message bubbles
- Message list with previews
- Compose new messages
- Delete messages

### 📍 GPS Navigation
- Real-time position tracking
- Latitude/Longitude display
- Speed, altitude, and heading
- Compass visualization
- GPS track recording
- Copy coordinates to clipboard

### ⚙️ Diagnostics
- Hardware self-test
- Module information display
- AT command console
- Network status monitoring
- Signal strength visualization

## Hardware Requirements

- **Raspberry Pi 3B+** or newer (32-bit OS)
- **Waveshare SIM7600X 4G HAT** (SIM7600G-H, SIM7600E-H, etc.)
- **480x320 touchscreen display** (SPI or HDMI)
- **SIM card** with voice/data plan
- **Antenna** (4G LTE + GPS)
- **Power supply** (5V 3A recommended)

## Wiring

The SIM7600X HAT connects directly to the Raspberry Pi GPIO header:

| HAT Pin | Pi Pin | Function |
|---------|--------|----------|
| 5V | Pin 2, 4 | Power |
| GND | Pin 6, 9 | Ground |
| TXD | Pin 10 (GPIO 15) | Serial RX |
| RXD | Pin 8 (GPIO 14) | Serial TX |
| PWR | Pin 7 (GPIO 4) | Power Key |

## Installation

### 1. Enable Serial Interface

```bash
sudo raspi-config
# Navigate to: Interface Options > Serial Port
# - Login shell over serial: No
# - Serial port hardware enabled: Yes
sudo reboot
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Tkinter
sudo apt install -y python3 python3-pip python3-tk

# Install project dependencies
cd piphone-x
pip3 install -r requirements.txt
```

### 3. Configure USB Serial

The SIM7600X HAT creates multiple serial ports when connected:
- `/dev/ttyUSB0` - Diagnostic port
- `/dev/ttyUSB1` - GPS NMEA port
- `/dev/ttyUSB2` - AT command port (primary)
- `/dev/ttyUSB3` - Audio port

Add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

### 4. Test the Connection

```bash
# Check if the modem is detected
ls /dev/ttyUSB*

# Test AT commands
python3 -c "from sim7600x import SIM7600X; m = SIM7600X(); print('Connected:', m.connect())"
```

## Usage

### Run the Application

```bash
# Normal mode (auto-detect modem)
python3 main.py

# Simulation mode (no hardware required)
python3 main.py --sim

# Specify serial port
python3 main.py --port /dev/ttyUSB2
```

### Auto-start on Boot

Create a systemd service:

```bash
sudo nano /etc/systemd/system/piphone.service
```

Add the following:

```ini
[Unit]
Description=PiPhone-X Application
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/piphone-x
ExecStart=/usr/bin/python3 /home/pi/piphone-x/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl enable piphone.service
sudo systemctl start piphone.service
```

## Project Structure

```
piphone-x/
├── main.py              # Application entry point
├── sim7600x.py          # SIM7600X HAT communication module
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── ui/
    ├── __init__.py     # UI package
    ├── theme.py        # Colors and styling
    ├── components.py   # Reusable UI widgets
    ├── phone_screen.py # Phone/dialer interface
    ├── sms_screen.py   # SMS messaging interface
    ├── gps_screen.py   # GPS tracking interface
    └── diagnostics_screen.py # Testing panel
```

## AT Command Reference

Common AT commands for the SIM7600X:

| Command | Description |
|---------|-------------|
| `AT` | Test connection |
| `AT+CSQ` | Signal strength |
| `AT+CREG?` | Network registration |
| `AT+COPS?` | Operator info |
| `ATD<number>;` | Dial number |
| `ATA` | Answer call |
| `ATH` | Hang up |
| `AT+CMGF=1` | SMS text mode |
| `AT+CMGS="<number>"` | Send SMS |
| `AT+CMGL="ALL"` | List all SMS |
| `AT+CGPS=1,1` | Enable GPS |
| `AT+CGPSINFO` | Get GPS position |

## Troubleshooting

### No modem detected

1. Check USB connection
2. Verify HAT power (PWR LED should be on)
3. Press power button on HAT for 3 seconds
4. Check `dmesg | grep ttyUSB`

### No network registration

1. Verify SIM card is inserted correctly
2. Check antenna connection
3. Ensure SIM has active service
4. Run `AT+CREG?` - response should show `,1` or `,5`

### No GPS fix

1. Ensure GPS antenna has clear sky view
2. Wait 1-2 minutes for cold start
3. Check `AT+CGPS?` returns `1`
4. Indoor GPS may not work well

### Display issues

1. Verify display configuration in `/boot/config.txt`
2. Set correct resolution: `hdmi_cvt=480 320 60`
3. For SPI displays, install appropriate drivers

## API Usage

Use the SIM7600X module programmatically:

```python
from sim7600x import SIM7600X

# Connect to modem
modem = SIM7600X(port="/dev/ttyUSB2")
modem.connect()

# Make a call
modem.dial("+15551234567")

# Send SMS
modem.send_sms("+15551234567", "Hello from PiPhone!")

# Get GPS position
modem.gps_power_on()
gps = modem.get_gps_position()
print(f"Location: {gps.latitude}, {gps.longitude}")

# Get signal strength
signal = modem.get_signal_strength()
print(f"Signal: {signal}%")

# Disconnect
modem.disconnect()
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Waveshare for the excellent SIM7600X HAT documentation
- The Raspberry Pi community

