#!/usr/bin/env python3
"""
PiPhone-X - Raspberry Pi Phone
Main Application Entry Point

A phone application for Raspberry Pi 3+ with Waveshare SIM7600X 4G HAT
Supports phone calls, SMS messaging, and GPS navigation

Display: 480x320 touchscreen
"""

import tkinter as tk
from tkinter import messagebox
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.theme import Theme, Colors
from ui.components import StatusBar, TabBar
from ui.phone_screen import PhoneScreen
from ui.sms_screen import SMSScreen
from ui.gps_screen import GPSScreen
from ui.diagnostics_screen import DiagnosticsScreen

# Import SIM7600X module
from sim7600x import SIM7600X, SIM7600XSimulator


class PiPhoneApp:
    """
    Main PiPhone-X Application
    
    Touch-optimized phone interface for Raspberry Pi with SIM7600X HAT
    """
    
    def __init__(self, simulation_mode: bool = False, port: str = None):
        """
        Initialize the PiPhone application
        
        Args:
            simulation_mode: If True, use simulated modem for testing
            port: Serial port for SIM7600X HAT (None for auto-detect)
        """
        self.simulation_mode = simulation_mode
        self.serial_port = port
        self.colors = Theme.colors
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("PiPhone-X")
        self.root.geometry(f"{Theme.WIDTH}x{Theme.HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.colors.background)
        
        # Configure for fullscreen on Raspberry Pi
        if not simulation_mode:
            try:
                self.root.attributes('-fullscreen', True)
            except:
                pass  # Fullscreen not supported
        
        # Hide cursor for touch interface
        # self.root.config(cursor="none")
        
        # Initialize modem
        self.modem = None
        self._init_modem()
        
        # Build UI
        self._create_ui()
        
        # Start status updates
        self._start_status_updates()
    
    def _init_modem(self):
        """Initialize the SIM7600X modem connection"""
        if self.simulation_mode:
            print("Running in simulation mode")
            self.modem = SIM7600XSimulator()
            self.modem.connect()
            return
        
        # If user specified a port, try that first
        if self.serial_port:
            try:
                print(f"Trying user-specified port: {self.serial_port}")
                self.modem = SIM7600X(port=self.serial_port)
                if self.modem.connect():
                    print(f"Connected to modem on {self.serial_port}")
                    return
                else:
                    print(f"Failed to connect on {self.serial_port}")
            except Exception as e:
                print(f"Failed on {self.serial_port}: {e}")
        
        # Auto-detect: try common serial ports for the HAT
        ports = [
            "/dev/ttyUSB2",  # Most common for SIM7600X HAT
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
            "/dev/ttyAMA0",
            "/dev/serial0"
        ]
        
        for port in ports:
            try:
                print(f"Trying port: {port}")
                self.modem = SIM7600X(port=port)
                if self.modem.connect():
                    print(f"Connected to modem on {port}")
                    return
            except Exception as e:
                print(f"Failed on {port}: {e}")
                continue
        
        # No modem found - fall back to simulation mode
        print("No modem found, running in simulation mode")
        self.modem = SIM7600XSimulator()
        self.modem.connect()
        self.simulation_mode = True
    
    def _create_ui(self):
        """Build the main user interface"""
        # Status bar at top - pack first
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.TOP)
        
        # Create content frame (but pack after tab bar)
        self.content_frame = tk.Frame(
            self.root,
            bg=self.colors.background
        )
        
        # Create screens BEFORE tab bar (screens dict must exist for callbacks)
        self.screens = {}
        self.screens['phone'] = PhoneScreen(self.content_frame, self.modem)
        self.screens['sms'] = SMSScreen(self.content_frame, self.modem)
        self.screens['gps'] = GPSScreen(self.content_frame, self.modem)
        self.screens['diag'] = DiagnosticsScreen(self.content_frame, self.modem)
        
        # Tab bar at bottom - pack BEFORE content so it reserves space
        tabs = [
            ("📞", "Phone", lambda: self._show_screen('phone')),
            ("💬", "SMS", lambda: self._show_screen('sms')),
            ("📍", "GPS", lambda: self._show_screen('gps')),
            ("⚙", "Diag", lambda: self._show_screen('diag'))
        ]
        
        self.tab_bar = TabBar(self.root, tabs)
        self.tab_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Now pack content frame to fill remaining space
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Show phone screen by default
        self._show_screen('phone')
        
        # Simulation mode indicator
        if self.simulation_mode:
            sim_label = tk.Label(
                self.status_bar,
                text="SIM",
                font=Theme.FONT_TINY,
                bg=self.colors.status_bg,
                fg=self.colors.accent_warning
            )
            sim_label.pack(side=tk.RIGHT, padx=5)
    
    def _show_screen(self, screen_name: str):
        """Switch to a different screen"""
        # Hide all screens
        for name, screen in self.screens.items():
            screen.pack_forget()
        
        # Show requested screen
        if screen_name in self.screens:
            self.screens[screen_name].pack(fill=tk.BOTH, expand=True)
    
    def _start_status_updates(self):
        """Start periodic status bar updates"""
        self._update_status()
    
    def _update_status(self):
        """Update status bar information"""
        # Update time
        current_time = time.strftime("%H:%M")
        self.status_bar.update_time(current_time)
        
        # Update from modem
        if self.modem and self.modem.connected:
            # Signal strength
            signal = self.modem.get_signal_strength()
            self.status_bar.update_signal(signal)
            
            # Operator
            info = self.modem.get_network_info()
            self.status_bar.update_operator(info.get('operator', ''))
            
            # GPS status
            gps = self.modem.gps_data
            self.status_bar.update_gps(
                active=hasattr(self.screens.get('gps'), 'gps_active') and 
                       self.screens['gps'].gps_active,
                has_fix=gps.fix_status if gps else False
            )
        
        # Schedule next update (every 5 seconds)
        self.root.after(5000, self._update_status)
    
    def run(self):
        """Start the application main loop"""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Bind escape key for fullscreen exit
        self.root.bind("<Escape>", lambda e: self._on_close())
        
        print("PiPhone-X starting...")
        print(f"Display: {Theme.WIDTH}x{Theme.HEIGHT}")
        print(f"Simulation mode: {self.simulation_mode}")
        
        # Start main loop
        self.root.mainloop()
    
    def _on_close(self):
        """Handle application close"""
        if self.modem:
            self.modem.disconnect()
        self.root.destroy()


def main():
    """Application entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PiPhone-X - Raspberry Pi Phone")
    parser.add_argument(
        "--sim", "--simulation",
        action="store_true",
        help="Run in simulation mode without hardware"
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Serial port for SIM7600X HAT (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = PiPhoneApp(simulation_mode=args.sim, port=args.port)
    app.run()


if __name__ == "__main__":
    main()

