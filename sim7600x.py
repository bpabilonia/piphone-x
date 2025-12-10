"""
SIM7600X 4G HAT Communication Module
Handles phone calls, SMS, and GPS functionality via AT commands

For Waveshare SIM7600X 4G HAT on Raspberry Pi 3+
"""

import time
import threading
import queue
import re
from typing import Optional, Callable, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import serial, gracefully handle if not available
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Hardware modem support disabled.")


class CallState(Enum):
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    INCOMING = "incoming"
    ACTIVE = "active"
    HELD = "held"


@dataclass
class GPSData:
    """GPS position data"""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    speed: float = 0.0
    course: float = 0.0
    timestamp: str = ""
    satellites: int = 0
    fix_status: bool = False
    hdop: float = 0.0  # Horizontal dilution of precision (accuracy indicator)
    fix_type: int = 0  # 0=no fix, 1=GPS, 2=DGPS, 3=PPS, etc.
    
    def to_dict(self) -> dict:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'speed': self.speed,
            'course': self.course,
            'timestamp': self.timestamp,
            'satellites': self.satellites,
            'fix_status': self.fix_status,
            'hdop': self.hdop,
            'fix_type': self.fix_type
        }
    
    @property
    def accuracy_meters(self) -> float:
        """Approximate horizontal accuracy in meters (HDOP * ~5m base accuracy)"""
        if self.hdop > 0:
            return self.hdop * 5.0
        return 0.0


@dataclass
class SMSMessage:
    """SMS message data"""
    index: int
    status: str
    sender: str
    timestamp: str
    content: str


class SIM7600X:
    """
    SIM7600X 4G HAT Controller
    
    Provides interface for:
    - Phone calls (dial, answer, hangup)
    - SMS (send, receive, list)
    - GPS (position, speed, tracking)
    - Network status and signal strength
    """
    
    def __init__(self, port: str = "/dev/ttyUSB2", baudrate: int = 115200):
        """
        Initialize SIM7600X connection
        
        Args:
            port: Serial port for AT commands (usually /dev/ttyUSB2 for HAT)
            baudrate: Communication speed (default 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        
        # State tracking
        self.call_state = CallState.IDLE
        self.current_call_number = ""
        self.gps_data = GPSData()
        self.signal_strength = 0
        self.network_registered = False
        self.operator_name = ""
        
        # Callbacks for events
        self.on_incoming_call: Optional[Callable[[str], None]] = None
        self.on_call_ended: Optional[Callable[[], None]] = None
        self.on_sms_received: Optional[Callable[[SMSMessage], None]] = None
        self.on_gps_update: Optional[Callable[[GPSData], None]] = None
        
        # Background monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        self._response_queue = queue.Queue()
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """Establish connection to SIM7600X module"""
        if not SERIAL_AVAILABLE:
            print("Serial module not available. Use SIM7600XSimulator instead.")
            self.connected = False
            return False
        
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1
            )
            time.sleep(0.5)
            
            # Test connection with AT command
            response = self._send_at_command("AT")
            if "OK" in response:
                self.connected = True
                self._initialize_module()
                self._start_monitor()
                return True
            return False
            
        except serial.SerialException as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close connection to module"""
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
    
    def _initialize_module(self):
        """Configure module for operation"""
        print("Initializing SIM7600X module...")
        
        # Disable echo
        self._send_at_command("ATE0")
        
        # Set SMS text mode
        self._send_at_command("AT+CMGF=1")
        
        # Enable SMS notifications
        self._send_at_command("AT+CNMI=2,1,0,0,0")
        
        # Set character set to GSM
        self._send_at_command('AT+CSCS="GSM"')
        
        # Enable caller ID
        self._send_at_command("AT+CLIP=1")
        
        # Configure audio for calls
        self._setup_audio()
        
        # Configure network for SpeedTalk/T-Mobile
        # Set to 3G mode (more reliable for voice/SMS on MVNOs)
        print("Setting network mode to 3G (WCDMA)...")
        self._send_at_command("AT+CNMP=14")
        
        # Set APN for SpeedTalk (mobilenet)
        print("Configuring APN: mobilenet")
        self._send_at_command('AT+CGDCONT=1,"IP","mobilenet"')
        
        # Force network registration
        print("Registering on network...")
        self._send_at_command("AT+COPS=0", timeout=30)
        
        # Wait a moment for registration
        time.sleep(5)
        
        # Get initial network status
        self._update_network_status()
        
        if self.network_registered:
            print(f"Successfully registered on: {self.operator_name}")
        else:
            print("Warning: Not registered on network yet. May take a few moments.")
    
    def _setup_audio(self):
        """Configure audio for voice calls"""
        print("Configuring audio...")
        
        # Set audio device to headset/external (1=headset, 3=speaker phone)
        # Try headset first for 3.5mm jack
        self._send_at_command("AT+CSDVC=1")
        
        # Set speaker volume (0-5, 5=max)
        self._send_at_command("AT+CLVL=5")
        
        # Set microphone gain (channel, gain 0-15)
        self._send_at_command("AT+CMIC=0,10")
        
        # Enable sidetone (hear yourself) - helps confirm mic is working
        self._send_at_command("AT+SIDET=0,1000")
        
        # Unmute microphone
        self._send_at_command("AT+CMUT=0")
        
        # Enable USB audio mode (if supported)
        # This routes audio over USB for Pi audio devices
        response = self._send_at_command("AT+CPCMREG?")
        if "ERROR" not in response:
            # Enable PCM audio interface
            self._send_at_command("AT+CPCMREG=1")
        
        print("Audio configured")
    
    def set_audio_device(self, device: str) -> bool:
        """
        Set audio output device
        device: 'headset', 'speaker', 'usb'
        """
        devices = {
            'headset': 1,   # 3.5mm headset jack on HAT
            'speaker': 3,   # External speaker
            'handset': 0,   # Default handset
        }
        
        if device not in devices:
            return False
        
        response = self._send_at_command(f"AT+CSDVC={devices[device]}")
        return "OK" in response
    
    def set_volume(self, level: int) -> bool:
        """Set speaker volume (0-5)"""
        level = max(0, min(5, level))
        response = self._send_at_command(f"AT+CLVL={level}")
        return "OK" in response
    
    def set_mic_gain(self, gain: int) -> bool:
        """Set microphone gain (0-15)"""
        gain = max(0, min(15, gain))
        response = self._send_at_command(f"AT+CMIC=0,{gain}")
        return "OK" in response
    
    def mute_mic(self, mute: bool = True) -> bool:
        """Mute or unmute microphone"""
        response = self._send_at_command(f"AT+CMUT={1 if mute else 0}")
        return "OK" in response
    
    def _send_at_command(self, command: str, timeout: float = 2.0) -> str:
        """
        Send AT command and wait for response
        
        Args:
            command: AT command string
            timeout: Response timeout in seconds
            
        Returns:
            Response string from module
        """
        if not self.serial or not self.serial.is_open:
            return "ERROR: Not connected"
        
        with self._lock:
            try:
                # Clear any pending data
                self.serial.reset_input_buffer()
                
                # Send command
                cmd = f"{command}\r\n"
                self.serial.write(cmd.encode())
                
                # Wait for response
                response = ""
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if self.serial.in_waiting:
                        data = self.serial.read(self.serial.in_waiting)
                        response += data.decode('utf-8', errors='ignore')
                        
                        # Check for command completion
                        if "OK" in response or "ERROR" in response or ">" in response:
                            break
                    time.sleep(0.05)
                
                return response.strip()
                
            except Exception as e:
                return f"ERROR: {e}"
    
    def _start_monitor(self):
        """Start background thread for monitoring incoming events"""
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background loop for monitoring unsolicited responses"""
        while not self._stop_monitor.is_set():
            try:
                if self.serial and self.serial.in_waiting:
                    with self._lock:
                        data = self.serial.read(self.serial.in_waiting)
                        text = data.decode('utf-8', errors='ignore')
                        self._process_unsolicited(text)
            except Exception:
                pass
            time.sleep(0.1)
    
    def _process_unsolicited(self, data: str):
        """Process unsolicited responses from module"""
        lines = data.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Incoming call notification
            if "+CLIP:" in line:
                match = re.search(r'\+CLIP:\s*"([^"]*)"', line)
                if match:
                    number = match.group(1)
                    self.call_state = CallState.INCOMING
                    self.current_call_number = number
                    if self.on_incoming_call:
                        self.on_incoming_call(number)
            
            # Call ended
            elif "NO CARRIER" in line or "BUSY" in line:
                self.call_state = CallState.IDLE
                self.current_call_number = ""
                if self.on_call_ended:
                    self.on_call_ended()
            
            # New SMS notification
            elif "+CMTI:" in line:
                match = re.search(r'\+CMTI:\s*"[^"]*",(\d+)', line)
                if match:
                    index = int(match.group(1))
                    sms = self.read_sms(index)
                    if sms and self.on_sms_received:
                        self.on_sms_received(sms)
    
    # ==================== PHONE FUNCTIONS ====================
    
    def dial(self, number: str) -> bool:
        """
        Dial a phone number
        
        Args:
            number: Phone number to dial
            
        Returns:
            True if dialing started successfully
        """
        # Clean number
        number = re.sub(r'[^\d+*#]', '', number)
        
        response = self._send_at_command(f"ATD{number};", timeout=10)
        
        if "OK" in response or "CONNECT" in response:
            self.call_state = CallState.DIALING
            self.current_call_number = number
            return True
        return False
    
    def answer(self) -> bool:
        """Answer incoming call"""
        response = self._send_at_command("ATA", timeout=5)
        if "OK" in response or "CONNECT" in response:
            self.call_state = CallState.ACTIVE
            return True
        return False
    
    def hangup(self) -> bool:
        """End current call"""
        response = self._send_at_command("ATH", timeout=5)
        if "OK" in response:
            self.call_state = CallState.IDLE
            self.current_call_number = ""
            return True
        return False
    
    def send_dtmf(self, tone: str) -> bool:
        """Send DTMF tone during call"""
        response = self._send_at_command(f"AT+VTS={tone}")
        return "OK" in response
    
    def get_call_status(self) -> Tuple[CallState, str]:
        """Get current call state and number"""
        return (self.call_state, self.current_call_number)
    
    # ==================== SMS FUNCTIONS ====================
    
    def send_sms(self, number: str, message: str) -> bool:
        """
        Send SMS message
        
        Args:
            number: Recipient phone number
            message: Message text
            
        Returns:
            True if sent successfully
        """
        # Clean number
        number = re.sub(r'[^\d+]', '', number)
        
        # Set text mode
        self._send_at_command("AT+CMGF=1")
        
        # Start SMS send
        response = self._send_at_command(f'AT+CMGS="{number}"', timeout=5)
        
        if ">" in response:
            # Send message content with Ctrl+Z to finish
            self.serial.write(message.encode())
            self.serial.write(bytes([26]))  # Ctrl+Z
            
            # Wait for send confirmation
            time.sleep(3)
            response = ""
            start = time.time()
            while time.time() - start < 10:
                if self.serial.in_waiting:
                    response += self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    if "+CMGS:" in response or "ERROR" in response:
                        break
                time.sleep(0.1)
            
            return "+CMGS:" in response
        
        return False
    
    def read_sms(self, index: int) -> Optional[SMSMessage]:
        """
        Read SMS by index
        
        Args:
            index: Message storage index
            
        Returns:
            SMSMessage object or None
        """
        response = self._send_at_command(f"AT+CMGR={index}", timeout=3)
        
        # Parse response
        match = re.search(
            r'\+CMGR:\s*"([^"]*)","([^"]*)","[^"]*","([^"]*)".*?\r\n(.+)',
            response, re.DOTALL
        )
        
        if match:
            return SMSMessage(
                index=index,
                status=match.group(1),
                sender=match.group(2),
                timestamp=match.group(3),
                content=match.group(4).strip().replace('\r\n', '\n')
            )
        return None
    
    def list_sms(self, status: str = "ALL") -> List[SMSMessage]:
        """
        List SMS messages
        
        Args:
            status: Filter by status ("ALL", "REC UNREAD", "REC READ", "STO UNSENT", "STO SENT")
            
        Returns:
            List of SMSMessage objects
        """
        messages = []
        response = self._send_at_command(f'AT+CMGL="{status}"', timeout=10)
        
        # Parse each message
        pattern = r'\+CMGL:\s*(\d+),"([^"]*)","([^"]*)","[^"]*","([^"]*)".*?\r\n([^\+]+)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            messages.append(SMSMessage(
                index=int(match[0]),
                status=match[1],
                sender=match[2],
                timestamp=match[3],
                content=match[4].strip()
            ))
        
        return messages
    
    def delete_sms(self, index: int) -> bool:
        """Delete SMS by index"""
        response = self._send_at_command(f"AT+CMGD={index}")
        return "OK" in response
    
    def delete_all_sms(self) -> bool:
        """Delete all SMS messages"""
        response = self._send_at_command("AT+CMGD=1,4")
        return "OK" in response
    
    # ==================== GPS FUNCTIONS ====================
    
    def gps_power_on(self) -> bool:
        """Enable GPS module"""
        # First check if already on
        status = self._send_at_command("AT+CGPS?", timeout=3)
        if "+CGPS: 1" in status:
            return True
        
        # Turn on GPS with mode 1 (standalone)
        response = self._send_at_command("AT+CGPS=1,1", timeout=5)
        if "OK" in response:
            # Give GPS time to initialize
            time.sleep(2)
            return True
        return False
    
    def gps_power_off(self) -> bool:
        """Disable GPS module"""
        response = self._send_at_command("AT+CGPS=0", timeout=5)
        self.gps_data.fix_status = False
        return "OK" in response
    
    def get_gps_position(self) -> GPSData:
        """
        Get current GPS position
        
        Returns:
            GPSData object with current position
        """
        # Get GPS info
        response = self._send_at_command("AT+CGPSINFO", timeout=5)
        
        # Parse GPS info
        # Format: +CGPSINFO: lat,N/S,lon,E/W,date,UTC time,altitude,speed,course
        # Example: +CGPSINFO: 3749.048467,N,12224.895475,W,100624,175032.0,10.1,0.0,0.0
        match = re.search(
            r'\+CGPSINFO:\s*(\d+\.?\d*),([NS]),(\d+\.?\d*),([EW]),(\d+),(\d+\.?\d*),(\d+\.?\d*),(\d+\.?\d*),(\d+\.?\d*)',
            response
        )
        
        if match:
            # Convert NMEA coordinates to decimal degrees
            lat_nmea = float(match.group(1))
            lat_dir = match.group(2)
            lon_nmea = float(match.group(3))
            lon_dir = match.group(4)
            
            # NMEA format: DDMM.MMMM -> convert to decimal
            lat_deg = int(lat_nmea / 100)
            lat_min = lat_nmea - (lat_deg * 100)
            latitude = lat_deg + (lat_min / 60)
            if lat_dir == 'S':
                latitude = -latitude
            
            lon_deg = int(lon_nmea / 100)
            lon_min = lon_nmea - (lon_deg * 100)
            longitude = lon_deg + (lon_min / 60)
            if lon_dir == 'W':
                longitude = -longitude
            
            self.gps_data = GPSData(
                latitude=latitude,
                longitude=longitude,
                altitude=float(match.group(7)),
                speed=float(match.group(8)),
                course=float(match.group(9)),
                timestamp=f"{match.group(5)} {match.group(6)}",
                fix_status=True
            )
            
            # Get satellite info and HDOP for accuracy
            self._update_gps_satellites()
        else:
            # Check if GPS is on but no fix (response shows empty fields)
            # +CGPSINFO: ,,,,,,,, means GPS on but no fix
            if "+CGPSINFO:" in response:
                self.gps_data.fix_status = False
                self.gps_data.fix_type = 0
                # Still try to get satellite count even without fix
                self._update_gps_satellites()
        
        if self.on_gps_update:
            self.on_gps_update(self.gps_data)
        
        return self.gps_data
    
    def _update_gps_satellites(self):
        """Update satellite count and accuracy info"""
        # Method 1: Try AT+CGPSSTATUS? for fix status
        response = self._send_at_command("AT+CGPSSTATUS?", timeout=3)
        # Response like: +CGPSSTATUS: Location 3D Fix
        if "3D Fix" in response:
            self.gps_data.fix_type = 3
        elif "2D Fix" in response:
            self.gps_data.fix_type = 2
        elif "Location Not Fix" in response or "Location Unknown" in response:
            self.gps_data.fix_type = 0
        
        # Method 2: Get NMEA GGA sentence for satellite count and HDOP
        response = self._send_at_command("AT+CGPSINFOCFG=1,31", timeout=2)  # Enable GGA output
        time.sleep(0.5)
        
        # Read NMEA data
        nmea_response = self._send_at_command("AT+CGPSINFO", timeout=3)
        
        # Try to parse satellite count from GSV or use GPSINF
        sat_response = self._send_at_command("AT+CGPSINF=32", timeout=3)
        
        # Parse NMEA GGA if available
        # $GPGGA,hhmmss.ss,lat,N,lon,W,qual,numSats,hdop,alt,M,height,M,dgpsTime,dgpsId*checksum
        gga_match = re.search(
            r'\$G[PN]GGA,[\d.]*,[\d.]*,[NS],[\d.]*,[EW],\d,(\d+),([\d.]*),',
            nmea_response + sat_response
        )
        
        if gga_match:
            self.gps_data.satellites = int(gga_match.group(1))
            try:
                self.gps_data.hdop = float(gga_match.group(2))
            except:
                self.gps_data.hdop = 0.0
        else:
            # Fallback: try basic satellite query
            sat_match = re.search(r'(\d+)\s*satellites', response.lower())
            if sat_match:
                self.gps_data.satellites = int(sat_match.group(1))
    
    def get_gps_satellites(self) -> int:
        """Get number of visible GPS satellites"""
        self._update_gps_satellites()
        return self.gps_data.satellites
    
    def get_gps_status(self) -> dict:
        """Get detailed GPS status"""
        status = {
            'powered': False,
            'fix': False,
            'fix_type': 0,
            'satellites': 0,
            'hdop': 0.0,
            'accuracy_m': 0.0
        }
        
        # Check if GPS is powered
        response = self._send_at_command("AT+CGPS?", timeout=3)
        if "+CGPS: 1" in response:
            status['powered'] = True
        
        # Get fix status
        response = self._send_at_command("AT+CGPSSTATUS?", timeout=3)
        if "3D Fix" in response:
            status['fix'] = True
            status['fix_type'] = 3
        elif "2D Fix" in response:
            status['fix'] = True
            status['fix_type'] = 2
        
        status['satellites'] = self.gps_data.satellites
        status['hdop'] = self.gps_data.hdop
        status['accuracy_m'] = self.gps_data.accuracy_meters
        
        return status
    
    # ==================== NETWORK FUNCTIONS ====================
    
    def _update_network_status(self):
        """Update network registration and signal info"""
        # Check registration
        response = self._send_at_command("AT+CREG?")
        match = re.search(r'\+CREG:\s*\d+,(\d+)', response)
        if match:
            status = int(match.group(1))
            self.network_registered = status in [1, 5]  # Home or roaming
        
        # Get signal strength
        response = self._send_at_command("AT+CSQ")
        match = re.search(r'\+CSQ:\s*(\d+),', response)
        if match:
            rssi = int(match.group(1))
            # Convert RSSI to percentage (0-31 scale, 99=unknown)
            if rssi != 99:
                self.signal_strength = min(100, int((rssi / 31) * 100))
            else:
                self.signal_strength = 0
        
        # Get operator name
        response = self._send_at_command("AT+COPS?")
        match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]*)"', response)
        if match:
            self.operator_name = match.group(1)
    
    def get_signal_strength(self) -> int:
        """
        Get signal strength percentage
        
        Returns:
            Signal strength 0-100
        """
        self._update_network_status()
        return self.signal_strength
    
    def get_network_info(self) -> Dict:
        """Get network registration info"""
        self._update_network_status()
        return {
            'registered': self.network_registered,
            'operator': self.operator_name,
            'signal': self.signal_strength
        }
    
    # ==================== APN CONFIGURATION ====================
    
    def set_apn(self, apn: str, username: str = "", password: str = "") -> bool:
        """
        Configure APN settings for mobile data
        
        Args:
            apn: Access Point Name (e.g., "Mobilenet")
            username: APN username (leave empty if none)
            password: APN password (leave empty if none)
            
        Returns:
            True if configuration successful
        """
        # Define PDP context with APN
        if username and password:
            cmd = f'AT+CGDCONT=1,"IP","{apn}"'
            self._send_at_command(cmd)
            # Set authentication
            auth_cmd = f'AT+CGAUTH=1,1,"{password}","{username}"'
            response = self._send_at_command(auth_cmd)
        else:
            cmd = f'AT+CGDCONT=1,"IP","{apn}"'
            response = self._send_at_command(cmd)
        
        return "OK" in response
    
    def get_apn(self) -> str:
        """Get current APN configuration"""
        response = self._send_at_command("AT+CGDCONT?")
        match = re.search(r'\+CGDCONT:\s*1,"[^"]*","([^"]*)"', response)
        if match:
            return match.group(1)
        return ""
    
    def activate_pdp(self) -> bool:
        """Activate PDP context (data connection)"""
        response = self._send_at_command("AT+CGACT=1,1", timeout=10)
        return "OK" in response
    
    def deactivate_pdp(self) -> bool:
        """Deactivate PDP context"""
        response = self._send_at_command("AT+CGACT=0,1", timeout=5)
        return "OK" in response
    
    def get_pdp_status(self) -> bool:
        """Check if PDP context is active"""
        response = self._send_at_command("AT+CGACT?")
        return "+CGACT: 1,1" in response
    
    def set_network_mode(self, mode: str = "auto") -> bool:
        """
        Set preferred network mode
        
        Args:
            mode: "auto", "4g", "3g", "2g"
            
        Returns:
            True if successful
        """
        modes = {
            "auto": "2",   # Automatic
            "4g": "38",    # LTE only
            "3g": "14",    # WCDMA only
            "2g": "13"     # GSM only
        }
        if mode not in modes:
            mode = "auto"
        
        response = self._send_at_command(f"AT+CNMP={modes[mode]}")
        return "OK" in response
    
    def force_network_registration(self) -> bool:
        """Force network registration attempt"""
        # Deregister first
        self._send_at_command("AT+COPS=2", timeout=5)
        time.sleep(2)
        # Auto-register
        response = self._send_at_command("AT+COPS=0", timeout=30)
        return "OK" in response
    
    def get_imei(self) -> str:
        """Get device IMEI"""
        response = self._send_at_command("AT+GSN")
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.isdigit() and len(line) == 15:
                return line
        return ""
    
    def get_sim_status(self) -> str:
        """Get SIM card status"""
        response = self._send_at_command("AT+CPIN?")
        if "+CPIN: READY" in response:
            return "READY"
        elif "+CPIN: SIM PIN" in response:
            return "PIN REQUIRED"
        elif "ERROR" in response:
            return "NO SIM"
        return "UNKNOWN"
    
    # ==================== DIAGNOSTIC FUNCTIONS ====================
    
    def send_raw_command(self, command: str, timeout: float = 5.0) -> str:
        """
        Send raw AT command for testing
        
        Args:
            command: Raw AT command
            timeout: Response timeout
            
        Returns:
            Raw response from module
        """
        return self._send_at_command(command, timeout)
    
    def get_module_info(self) -> Dict:
        """Get module identification info"""
        info = {}
        
        # Manufacturer
        response = self._send_at_command("AT+CGMI")
        info['manufacturer'] = response.replace('OK', '').strip()
        
        # Model
        response = self._send_at_command("AT+CGMM")
        info['model'] = response.replace('OK', '').strip()
        
        # Revision
        response = self._send_at_command("AT+CGMR")
        info['revision'] = response.replace('OK', '').strip()
        
        # IMEI
        info['imei'] = self.get_imei()
        
        return info
    
    def run_self_test(self) -> Dict[str, bool]:
        """
        Run diagnostic self-test
        
        Returns:
            Dictionary of test results
        """
        results = {}
        
        # Basic AT test
        response = self._send_at_command("AT")
        results['at_response'] = "OK" in response
        
        # SIM card
        sim_status = self.get_sim_status()
        results['sim_card'] = sim_status == "READY"
        
        # Network
        self._update_network_status()
        results['network'] = self.network_registered
        
        # Signal
        results['signal'] = self.signal_strength > 0
        
        # GPS power
        gps_response = self._send_at_command("AT+CGPS?")
        results['gps_module'] = "OK" in gps_response
        
        return results


# Test mode for running without hardware
class SIM7600XSimulator(SIM7600X):
    """Simulator for testing without actual hardware"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = True
        self.signal_strength = 75
        self.network_registered = True
        self.operator_name = "Test Network"
        self.gps_data = GPSData(
            latitude=37.7749,
            longitude=-122.4194,
            altitude=10.0,
            speed=0.0,
            course=0.0,
            timestamp="2024-01-01 12:00:00",
            satellites=8,
            fix_status=True,
            hdop=1.2,
            fix_type=3
        )
        self._sms_storage: List[SMSMessage] = [
            SMSMessage(1, "REC READ", "+15551234567", "24/01/01,12:00:00", "Hello! This is a test message."),
            SMSMessage(2, "REC UNREAD", "+15559876543", "24/01/01,12:30:00", "Welcome to PiPhone!"),
        ]
        self._sms_counter = 3
    
    def connect(self) -> bool:
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
    
    def _send_at_command(self, command: str, timeout: float = 2.0) -> str:
        return "OK"
    
    def dial(self, number: str) -> bool:
        self.call_state = CallState.DIALING
        self.current_call_number = number
        return True
    
    def answer(self) -> bool:
        self.call_state = CallState.ACTIVE
        return True
    
    def hangup(self) -> bool:
        self.call_state = CallState.IDLE
        self.current_call_number = ""
        return True
    
    def send_sms(self, number: str, message: str) -> bool:
        self._sms_storage.append(SMSMessage(
            self._sms_counter,
            "STO SENT",
            number,
            time.strftime("%y/%m/%d,%H:%M:%S"),
            message
        ))
        self._sms_counter += 1
        return True
    
    def list_sms(self, status: str = "ALL") -> List[SMSMessage]:
        return self._sms_storage
    
    def read_sms(self, index: int) -> Optional[SMSMessage]:
        for sms in self._sms_storage:
            if sms.index == index:
                return sms
        return None
    
    def delete_sms(self, index: int) -> bool:
        self._sms_storage = [s for s in self._sms_storage if s.index != index]
        return True
    
    def gps_power_on(self) -> bool:
        self.gps_data.fix_status = True
        self.gps_data.fix_type = 3
        return True
    
    def gps_power_off(self) -> bool:
        self.gps_data.fix_status = False
        self.gps_data.fix_type = 0
        return True
    
    def get_gps_position(self) -> GPSData:
        # Simulate slight movement
        import random
        if self.gps_data.fix_status:
            self.gps_data.latitude += random.uniform(-0.0001, 0.0001)
            self.gps_data.longitude += random.uniform(-0.0001, 0.0001)
            self.gps_data.speed = random.uniform(0, 5)
            self.gps_data.course = random.uniform(0, 360)
            self.gps_data.satellites = random.randint(6, 12)
            self.gps_data.hdop = random.uniform(0.8, 2.5)
            self.gps_data.fix_type = 3
        self.gps_data.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return self.gps_data
    
    def get_gps_status(self) -> dict:
        return {
            'powered': True,
            'fix': self.gps_data.fix_status,
            'fix_type': self.gps_data.fix_type,
            'satellites': self.gps_data.satellites,
            'hdop': self.gps_data.hdop,
            'accuracy_m': self.gps_data.accuracy_meters
        }
    
    def get_module_info(self) -> Dict:
        return {
            'manufacturer': 'SIMCOM (Simulator)',
            'model': 'SIM7600X',
            'revision': 'LE20B04SIM7600M22',
            'imei': '123456789012345'
        }
    
    def run_self_test(self) -> Dict[str, bool]:
        return {
            'at_response': True,
            'sim_card': True,
            'network': True,
            'signal': True,
            'gps_module': True
        }
    
    def set_apn(self, apn: str, username: str = "", password: str = "") -> bool:
        return True
    
    def get_apn(self) -> str:
        return "mobilenet"
    
    def activate_pdp(self) -> bool:
        return True
    
    def deactivate_pdp(self) -> bool:
        return True
    
    def get_pdp_status(self) -> bool:
        return True
    
    def set_network_mode(self, mode: str = "auto") -> bool:
        return True
    
    def force_network_registration(self) -> bool:
        return True

