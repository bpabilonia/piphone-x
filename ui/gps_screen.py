"""
PiPhone-X GPS Tracking Screen
Real-time GPS position and navigation display
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import Optional, List, Tuple
from .theme import Theme, Colors
from .components import TouchButton, ProgressRing


class GPSScreen(tk.Frame):
    """
    GPS tracking and position display screen
    """
    
    def __init__(self, parent, modem, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        self.colors = colors
        self.modem = modem
        self.gps_active = False
        self.tracking = False
        self.track_points: List[Tuple[float, float]] = []
        
        self._create_ui()
        
        # Start update loop
        self._update_loop()
    
    def _create_ui(self):
        """Build the GPS interface - compact for 320x480 (406px available)"""
        # Header - compact
        header = tk.Frame(self, bg=self.colors.surface, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="GPS Navigation",
            font=Theme.FONT_MEDIUM,
            bg=self.colors.surface,
            fg=self.colors.text_primary
        ).pack(side=tk.LEFT, padx=10, pady=8)
        
        # GPS power toggle
        self.power_btn = TouchButton(
            header,
            text="GPS OFF",
            command=self._toggle_gps,
            width=70,
            height=28,
            bg=self.colors.accent_danger,
            fg=self.colors.text_primary,
            font=Theme.FONT_TINY
        )
        self.power_btn.pack(side=tk.RIGHT, padx=8, pady=6)
        
        # Main content
        content = tk.Frame(self, bg=self.colors.background)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Top section - Compass and status
        top_frame = tk.Frame(content, bg=self.colors.background)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Compass widget (smaller)
        self._create_compass(top_frame)
        
        # Status info on right
        status_frame = tk.Frame(top_frame, bg=self.colors.background)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Fix status
        self.fix_indicator = tk.Label(
            status_frame,
            text="● No Fix",
            font=Theme.FONT_SMALL,
            bg=self.colors.background,
            fg=self.colors.accent_danger
        )
        self.fix_indicator.pack(anchor=tk.W)
        
        # Satellites
        self.sat_label = tk.Label(
            status_frame,
            text="Satellites: --",
            font=Theme.FONT_TINY,
            bg=self.colors.background,
            fg=self.colors.text_secondary
        )
        self.sat_label.pack(anchor=tk.W, pady=2)
        
        # Accuracy
        self.accuracy_label = tk.Label(
            status_frame,
            text="Accuracy: --",
            font=Theme.FONT_TINY,
            bg=self.colors.background,
            fg=self.colors.text_secondary
        )
        self.accuracy_label.pack(anchor=tk.W)
        
        # Coordinate display - compact
        coord_frame = tk.Frame(content, bg=self.colors.surface)
        coord_frame.pack(fill=tk.X, pady=5)
        
        # Latitude
        lat_frame = tk.Frame(coord_frame, bg=self.colors.surface)
        lat_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            lat_frame,
            text="LAT",
            font=Theme.FONT_TINY,
            bg=self.colors.surface,
            fg=self.colors.text_muted
        ).pack(side=tk.LEFT)
        
        self.lat_label = tk.Label(
            lat_frame,
            text="---.------°",
            font=(Theme.FONT_MONO, 14),
            bg=self.colors.surface,
            fg=self.colors.accent_primary
        )
        self.lat_label.pack(side=tk.LEFT, padx=10)
        
        # Longitude
        lon_frame = tk.Frame(coord_frame, bg=self.colors.surface)
        lon_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        tk.Label(
            lon_frame,
            text="LON",
            font=Theme.FONT_TINY,
            bg=self.colors.surface,
            fg=self.colors.text_muted
        ).pack(side=tk.LEFT)
        
        self.lon_label = tk.Label(
            lon_frame,
            text="---.------°",
            font=(Theme.FONT_MONO, 14),
            bg=self.colors.surface,
            fg=self.colors.accent_primary
        )
        self.lon_label.pack(side=tk.LEFT, padx=10)
        
        # Speed and altitude row - compact
        metrics_frame = tk.Frame(content, bg=self.colors.background)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Speed
        speed_frame = tk.Frame(metrics_frame, bg=self.colors.surface_light, width=95, height=50)
        speed_frame.pack(side=tk.LEFT, padx=3)
        speed_frame.pack_propagate(False)
        
        tk.Label(
            speed_frame,
            text="SPEED",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface_light,
            fg=self.colors.text_muted
        ).pack(pady=(5, 0))
        
        self.speed_label = tk.Label(
            speed_frame,
            text="-- km/h",
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary
        )
        self.speed_label.pack()
        
        # Altitude
        alt_frame = tk.Frame(metrics_frame, bg=self.colors.surface_light, width=95, height=50)
        alt_frame.pack(side=tk.LEFT, padx=3)
        alt_frame.pack_propagate(False)
        
        tk.Label(
            alt_frame,
            text="ALTITUDE",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface_light,
            fg=self.colors.text_muted
        ).pack(pady=(5, 0))
        
        self.alt_label = tk.Label(
            alt_frame,
            text="-- m",
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary
        )
        self.alt_label.pack()
        
        # Course/heading
        course_frame = tk.Frame(metrics_frame, bg=self.colors.surface_light, width=95, height=50)
        course_frame.pack(side=tk.LEFT, padx=3)
        course_frame.pack_propagate(False)
        
        tk.Label(
            course_frame,
            text="HEADING",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface_light,
            fg=self.colors.text_muted
        ).pack(pady=(5, 0))
        
        self.course_label = tk.Label(
            course_frame,
            text="--°",
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary
        )
        self.course_label.pack()
        
        # Bottom buttons - compact
        btn_frame = tk.Frame(content, bg=self.colors.background)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Track recording button
        self.track_btn = TouchButton(
            btn_frame,
            text="Track",
            command=self._toggle_tracking,
            width=90,
            height=36,
            bg=self.colors.accent_secondary,
            font=Theme.FONT_SMALL
        )
        self.track_btn.pack(side=tk.LEFT, padx=3)
        
        # Copy coordinates button
        TouchButton(
            btn_frame,
            text="Copy",
            command=self._copy_location,
            width=90,
            height=36,
            font=Theme.FONT_SMALL
        ).pack(side=tk.LEFT, padx=3)
        
        # Refresh button
        TouchButton(
            btn_frame,
            text="Refresh",
            command=self._refresh_gps,
            width=90,
            height=36,
            font=Theme.FONT_SMALL
        ).pack(side=tk.LEFT, padx=3)
    
    def _create_compass(self, parent):
        """Create compass widget"""
        self.compass = Canvas(
            parent,
            width=80,
            height=80,
            bg=self.colors.background,
            highlightthickness=0
        )
        self.compass.pack(side=tk.LEFT, padx=5)
        
        self._draw_compass(0)
    
    def _draw_compass(self, heading: float):
        """Draw compass with given heading"""
        self.compass.delete("all")
        
        cx, cy = 40, 40
        r = 32
        
        # Outer circle
        self.compass.create_oval(
            cx-r, cy-r, cx+r, cy+r,
            outline=self.colors.surface_light,
            width=2
        )
        
        # Cardinal directions
        directions = [("N", 0), ("E", 90), ("S", 180), ("W", 270)]
        for label, angle in directions:
            rad = math.radians(angle - heading - 90)
            x = cx + (r - 12) * math.cos(rad)
            y = cy + (r - 12) * math.sin(rad)
            
            color = self.colors.accent_danger if label == "N" else self.colors.text_muted
            self.compass.create_text(x, y, text=label, fill=color, font=Theme.FONT_SMALL)
        
        # Needle
        needle_len = 25
        rad = math.radians(-90)  # Points up (north)
        
        # North (red) side
        self.compass.create_polygon(
            cx, cy - needle_len,
            cx - 6, cy,
            cx + 6, cy,
            fill=self.colors.accent_danger
        )
        
        # South (white) side
        self.compass.create_polygon(
            cx, cy + needle_len,
            cx - 6, cy,
            cx + 6, cy,
            fill=self.colors.text_primary
        )
        
        # Center dot
        self.compass.create_oval(cx-4, cy-4, cx+4, cy+4, fill=self.colors.surface_light)
    
    def _toggle_gps(self):
        """Toggle GPS power"""
        if self.gps_active:
            if self.modem:
                self.modem.gps_power_off()
            self.gps_active = False
            self.power_btn.set_text("GPS OFF")
            self.power_btn.set_colors(bg=self.colors.accent_danger)
            self._clear_display()
        else:
            if self.modem:
                self.modem.gps_power_on()
            self.gps_active = True
            self.power_btn.set_text("GPS ON")
            self.power_btn.set_colors(bg=self.colors.accent_success)
    
    def _toggle_tracking(self):
        """Toggle GPS tracking/recording"""
        if self.tracking:
            self.tracking = False
            self.track_btn.set_text("Start Tracking")
            self.track_btn.set_colors(bg=self.colors.accent_secondary)
            
            # Show track summary
            if self.track_points:
                points = len(self.track_points)
                self.fix_indicator.config(text=f"Track saved: {points} points")
        else:
            self.tracking = True
            self.track_points = []
            self.track_btn.set_text("Stop Tracking")
            self.track_btn.set_colors(bg=self.colors.accent_warning)
    
    def _copy_location(self):
        """Copy current coordinates to clipboard"""
        if self.modem:
            gps = self.modem.gps_data
            if gps.fix_status:
                coords = f"{gps.latitude:.6f}, {gps.longitude:.6f}"
                self.clipboard_clear()
                self.clipboard_append(coords)
                
                # Visual feedback
                self.fix_indicator.config(text="Copied!", fg=self.colors.accent_success)
                self.after(2000, self._update_fix_status)
    
    def _refresh_gps(self):
        """Force GPS refresh"""
        if self.modem and self.gps_active:
            self.modem.get_gps_position()
            self._update_display()
    
    def _update_loop(self):
        """Periodic GPS update loop"""
        if self.gps_active and self.modem:
            self.modem.get_gps_position()
            self._update_display()
            
            # Record track point if tracking
            if self.tracking and self.modem.gps_data.fix_status:
                gps = self.modem.gps_data
                self.track_points.append((gps.latitude, gps.longitude))
        
        # Schedule next update (every 2 seconds)
        self.after(2000, self._update_loop)
    
    def _update_display(self):
        """Update all GPS display elements"""
        if not self.modem:
            return
        
        gps = self.modem.gps_data
        
        # Update fix status
        self._update_fix_status()
        
        if gps.fix_status:
            # Coordinates
            lat_dir = "N" if gps.latitude >= 0 else "S"
            lon_dir = "E" if gps.longitude >= 0 else "W"
            
            self.lat_label.config(text=f"{abs(gps.latitude):.6f}° {lat_dir}")
            self.lon_label.config(text=f"{abs(gps.longitude):.6f}° {lon_dir}")
            
            # Speed (convert knots to km/h if needed)
            speed_kmh = gps.speed * 1.852 if gps.speed < 100 else gps.speed
            self.speed_label.config(text=f"{speed_kmh:.1f} km/h")
            
            # Altitude
            self.alt_label.config(text=f"{gps.altitude:.0f} m")
            
            # Course/heading
            self.course_label.config(text=f"{gps.course:.0f}°")
            self._draw_compass(gps.course)
            
            # Satellites
            self.sat_label.config(text=f"Satellites: {gps.satellites}")
        else:
            self._clear_display()
    
    def _update_fix_status(self):
        """Update the fix status indicator"""
        if not self.modem:
            return
        
        gps = self.modem.gps_data
        
        if gps.fix_status:
            self.fix_indicator.config(text="● GPS Fix", fg=self.colors.accent_success)
        else:
            self.fix_indicator.config(text="● Searching...", fg=self.colors.accent_warning)
    
    def _clear_display(self):
        """Clear all GPS display values"""
        self.lat_label.config(text="---.------°")
        self.lon_label.config(text="---.------°")
        self.speed_label.config(text="-- km/h")
        self.alt_label.config(text="-- m")
        self.course_label.config(text="--°")
        self.sat_label.config(text="Satellites: --")
        self.fix_indicator.config(text="● No Fix", fg=self.colors.accent_danger)
        self._draw_compass(0)
    
    def get_track_points(self) -> List[Tuple[float, float]]:
        """Get recorded track points"""
        return self.track_points.copy()

