#!/usr/bin/env python3
"""
Audio Bridge for SIM7600X
Routes audio between Pi audio devices and the SIM7600X modem

Requirements:
    sudo apt install python3-pyaudio pulseaudio
    
Usage:
    python3 audio_bridge.py
    
This script bridges:
    - Pi microphone -> Modem (so caller can hear you)
    - Modem -> Pi speakers (so you can hear caller)
"""

import pyaudio
import threading
import time
import subprocess
import sys

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 8000  # Phone audio is typically 8kHz

class AudioBridge:
    def __init__(self):
        self.running = False
        self.pa = None
        self.mic_stream = None
        self.speaker_stream = None
        self.modem_in = None
        self.modem_out = None
        
        # Device indices (will be detected)
        self.mic_device = None
        self.speaker_device = None
        self.modem_device = None
    
    def list_devices(self):
        """List all audio devices"""
        self.pa = pyaudio.PyAudio()
        
        print("\n=== Audio Devices ===")
        print("-" * 60)
        
        modem_candidates = []
        mic_candidates = []
        speaker_candidates = []
        
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            name = info['name']
            inputs = info['maxInputChannels']
            outputs = info['maxOutputChannels']
            
            print(f"{i}: {name}")
            print(f"   Inputs: {inputs}, Outputs: {outputs}")
            
            # Detect modem (usually has "SIM" or "Qualcomm" in name)
            name_lower = name.lower()
            if 'sim' in name_lower or 'qualcomm' in name_lower or 'modem' in name_lower:
                modem_candidates.append(i)
                print(f"   ^ Possible MODEM device")
            
            # USB mic
            if inputs > 0 and ('usb' in name_lower or 'mic' in name_lower):
                mic_candidates.append(i)
                print(f"   ^ Possible MICROPHONE")
            
            # Pi audio output
            if outputs > 0 and ('bcm' in name_lower or 'headphone' in name_lower or 
                               'analog' in name_lower or 'default' in name_lower):
                speaker_candidates.append(i)
                print(f"   ^ Possible SPEAKER output")
        
        print("-" * 60)
        
        # Auto-select devices
        if mic_candidates:
            self.mic_device = mic_candidates[0]
            print(f"Selected MIC: Device {self.mic_device}")
        
        if speaker_candidates:
            self.speaker_device = speaker_candidates[0]
            print(f"Selected SPEAKER: Device {self.speaker_device}")
        
        if modem_candidates:
            self.modem_device = modem_candidates[0]
            print(f"Selected MODEM: Device {self.modem_device}")
        else:
            print("\n⚠ No modem audio device found!")
            print("The SIM7600X may not be in USB audio mode.")
            print("Try: AT+CPCMREG=1 in the AT Console")
        
        return modem_candidates, mic_candidates, speaker_candidates
    
    def start(self, mic_idx=None, speaker_idx=None, modem_idx=None):
        """Start audio bridging"""
        if mic_idx is not None:
            self.mic_device = mic_idx
        if speaker_idx is not None:
            self.speaker_device = speaker_idx
        if modem_idx is not None:
            self.modem_device = modem_idx
        
        if self.mic_device is None or self.speaker_device is None:
            print("Error: Microphone and speaker devices must be specified")
            return False
        
        if self.pa is None:
            self.pa = pyaudio.PyAudio()
        
        self.running = True
        
        # Start mic -> modem thread (your voice to caller)
        if self.modem_device is not None:
            self.mic_thread = threading.Thread(target=self._mic_to_modem)
            self.mic_thread.daemon = True
            self.mic_thread.start()
            
            # Start modem -> speaker thread (caller's voice to you)
            self.speaker_thread = threading.Thread(target=self._modem_to_speaker)
            self.speaker_thread.daemon = True
            self.speaker_thread.start()
            
            print("Audio bridge started (Pi <-> Modem)")
        else:
            # No modem device - just do loopback test
            print("No modem device - running mic loopback test")
            self.loopback_thread = threading.Thread(target=self._mic_loopback)
            self.loopback_thread.daemon = True
            self.loopback_thread.start()
        
        return True
    
    def start_mic_only(self, mic_idx=None, modem_idx=None):
        """
        Start mic-only bridging for hybrid setup:
        - Pi USB mic -> Modem (so caller hears you)
        - Use HAT's 3.5mm jack for speaker (to hear caller)
        """
        if mic_idx is not None:
            self.mic_device = mic_idx
        if modem_idx is not None:
            self.modem_device = modem_idx
        
        if self.mic_device is None:
            print("Error: Microphone device not found")
            return False
        
        if self.modem_device is None:
            print("Error: Modem audio device not found")
            print("Enable USB audio: AT+CPCMREG=1")
            return False
        
        if self.pa is None:
            self.pa = pyaudio.PyAudio()
        
        self.running = True
        
        # Only start mic -> modem thread
        self.mic_thread = threading.Thread(target=self._mic_to_modem)
        self.mic_thread.daemon = True
        self.mic_thread.start()
        
        print("=" * 50)
        print("HYBRID MODE ACTIVE")
        print("=" * 50)
        print(f"  Your voice: Pi USB Mic ({self.mic_device}) -> Modem")
        print(f"  Caller's voice: Use headphones on HAT's 3.5mm jack")
        print("=" * 50)
        
        return True
    
    def stop(self):
        """Stop audio bridging"""
        self.running = False
        time.sleep(0.5)
        
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
        if self.speaker_stream:
            self.speaker_stream.stop_stream()
            self.speaker_stream.close()
        if self.modem_in:
            self.modem_in.stop_stream()
            self.modem_in.close()
        if self.modem_out:
            self.modem_out.stop_stream()
            self.modem_out.close()
        
        if self.pa:
            self.pa.terminate()
        
        print("Audio bridge stopped")
    
    def _mic_to_modem(self):
        """Route microphone audio to modem"""
        try:
            self.mic_stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.mic_device,
                frames_per_buffer=CHUNK
            )
            
            self.modem_out = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=self.modem_device,
                frames_per_buffer=CHUNK
            )
            
            print(f"Mic ({self.mic_device}) -> Modem ({self.modem_device}) started")
            
            while self.running:
                data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                self.modem_out.write(data)
                
        except Exception as e:
            print(f"Mic->Modem error: {e}")
    
    def _modem_to_speaker(self):
        """Route modem audio to speakers"""
        try:
            self.modem_in = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.modem_device,
                frames_per_buffer=CHUNK
            )
            
            self.speaker_stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=self.speaker_device,
                frames_per_buffer=CHUNK
            )
            
            print(f"Modem ({self.modem_device}) -> Speaker ({self.speaker_device}) started")
            
            while self.running:
                data = self.modem_in.read(CHUNK, exception_on_overflow=False)
                self.speaker_stream.write(data)
                
        except Exception as e:
            print(f"Modem->Speaker error: {e}")
    
    def _mic_loopback(self):
        """Test mic by playing back to speaker"""
        try:
            self.mic_stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.mic_device,
                frames_per_buffer=CHUNK
            )
            
            self.speaker_stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=self.speaker_device,
                frames_per_buffer=CHUNK
            )
            
            print(f"Loopback: Mic ({self.mic_device}) -> Speaker ({self.speaker_device})")
            print("Speak into mic - you should hear yourself...")
            
            while self.running:
                data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                self.speaker_stream.write(data)
                
        except Exception as e:
            print(f"Loopback error: {e}")


def main():
    print("=" * 60)
    print("SIM7600X Audio Bridge")
    print("=" * 60)
    
    bridge = AudioBridge()
    
    # List devices
    modem, mic, speaker = bridge.list_devices()
    
    print("\nOptions:")
    print("  1. Full bridge (Pi mic <-> Modem <-> Pi speaker)")
    print("  2. Mic only (Pi USB mic -> Modem, use HAT for speaker)")
    print("  3. Test microphone (loopback to Pi speaker)")
    print("  4. Quit")
    
    try:
        choice = input("\nChoice [1-4]: ").strip()
        
        if choice == "1":
            if not modem:
                print("\nNo modem audio device found.")
                print("Make sure USB audio is enabled on the modem:")
                print("  AT+CPCMREG=1")
                return
            bridge.start()
            print("\nPress Ctrl+C to stop...")
            while True:
                time.sleep(1)
        
        elif choice == "2":
            # Mic only mode - for hybrid setup
            if not modem:
                print("\nNo modem audio device found.")
                print("Make sure USB audio is enabled on the modem:")
                print("  AT+CPCMREG=1")
                return
            bridge.start_mic_only()
            print("\nPress Ctrl+C to stop...")
            while True:
                time.sleep(1)
                
        elif choice == "3":
            bridge.start()  # Will do loopback if no modem
            print("\nPress Ctrl+C to stop...")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        bridge.stop()


if __name__ == "__main__":
    main()

