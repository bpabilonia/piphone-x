"""
PiPhone-X Phone/Dialer Screen
Touch-optimized phone interface
"""

import tkinter as tk
from typing import Optional
from .theme import Theme, Colors
from .components import TouchButton, CircleButton, NumPad


class PhoneScreen(tk.Frame):
    """
    Phone dialer and call management screen
    """
    
    def __init__(self, parent, modem, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        self.colors = colors
        self.modem = modem
        self.phone_number = ""
        self.in_call = False
        self.incoming_call = False
        
        self._create_ui()
        
        # Set up modem callbacks
        if modem:
            modem.on_incoming_call = self._on_incoming_call
            modem.on_call_ended = self._on_call_ended
    
    def _create_ui(self):
        """Build the phone interface"""
        # Main container for 320x480 portrait display (406px available)
        self.content = tk.Frame(self, bg=self.colors.background)
        self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Phone number display
        self.display_frame = tk.Frame(self.content, bg=self.colors.background)
        self.display_frame.pack(fill=tk.X, pady=(8, 2))
        
        self.number_display = tk.Label(
            self.display_frame,
            text="",
            font=(Theme.FONT_MONO, 24, "bold"),
            bg=self.colors.background,
            fg=self.colors.text_primary,
            anchor=tk.CENTER
        )
        self.number_display.pack(fill=tk.X)
        
        # Call status label
        self.status_label = tk.Label(
            self.content,
            text="",
            font=Theme.FONT_TINY,
            bg=self.colors.background,
            fg=self.colors.accent_primary
        )
        self.status_label.pack(pady=(0, 2))
        
        # Dialer view
        self._create_dialer_view()
        
        # In-call view (hidden by default)
        self._create_incall_view()
        
        # Show dialer by default
        self._show_dialer()
    
    def _create_dialer_view(self):
        """Create the number pad and dial buttons"""
        self.dialer_frame = tk.Frame(self.content, bg=self.colors.background)
        
        # NumPad
        self.numpad = NumPad(
            self.dialer_frame,
            on_key=self._on_digit,
            on_backspace=self._on_backspace,
            on_call=self._on_dial,
            on_hangup=self._on_hangup,
            show_call_buttons=True
        )
        self.numpad.pack(pady=5)
    
    def _create_incall_view(self):
        """Create the in-call control view"""
        self.incall_frame = tk.Frame(self.content, bg=self.colors.background)
        
        # Caller info
        self.caller_label = tk.Label(
            self.incall_frame,
            text="",
            font=Theme.FONT_TITLE,
            bg=self.colors.background,
            fg=self.colors.text_primary
        )
        self.caller_label.pack(pady=20)
        
        # Call duration
        self.duration_label = tk.Label(
            self.incall_frame,
            text="00:00",
            font=Theme.FONT_DISPLAY_SMALL,
            bg=self.colors.background,
            fg=self.colors.text_secondary
        )
        self.duration_label.pack(pady=10)
        
        # Call controls
        controls_frame = tk.Frame(self.incall_frame, bg=self.colors.background)
        controls_frame.pack(pady=20)
        
        # Mute button
        self.mute_btn = TouchButton(
            controls_frame,
            text="🔇",
            command=self._on_mute,
            width=70,
            height=70,
            font=(Theme.FONT_FAMILY, 24),
            radius=35
        )
        self.mute_btn.grid(row=0, column=0, padx=15)
        
        # Speaker button
        self.speaker_btn = TouchButton(
            controls_frame,
            text="🔊",
            command=self._on_speaker,
            width=70,
            height=70,
            font=(Theme.FONT_FAMILY, 24),
            radius=35
        )
        self.speaker_btn.grid(row=0, column=1, padx=15)
        
        # Keypad button
        self.keypad_btn = TouchButton(
            controls_frame,
            text="⌨",
            command=self._show_dtmf_pad,
            width=70,
            height=70,
            font=(Theme.FONT_FAMILY, 24),
            radius=35
        )
        self.keypad_btn.grid(row=0, column=2, padx=15)
        
        # End call button
        end_frame = tk.Frame(self.incall_frame, bg=self.colors.background)
        end_frame.pack(pady=20)
        
        self.end_call_btn = CircleButton(
            end_frame,
            text="✕",
            command=self._on_hangup,
            size=80,
            bg=self.colors.call_end
        )
        self.end_call_btn.pack()
        
        # Answer button for incoming calls
        self.answer_btn = CircleButton(
            end_frame,
            text="📞",
            command=self._on_answer,
            size=80,
            bg=self.colors.call_active
        )
    
    def _show_dialer(self):
        """Show the dialer view"""
        self.incall_frame.pack_forget()
        self.dialer_frame.pack(fill=tk.BOTH, expand=True)
    
    def _show_incall(self):
        """Show the in-call view"""
        self.dialer_frame.pack_forget()
        self.incall_frame.pack(fill=tk.BOTH, expand=True)
    
    def _show_incoming(self):
        """Show incoming call UI"""
        self._show_incall()
        self.answer_btn.pack(side=tk.LEFT, padx=20)
        self.end_call_btn.pack(side=tk.LEFT, padx=20)
        self.status_label.config(text="Incoming Call", fg=self.colors.call_incoming)
    
    def _on_digit(self, digit: str):
        """Handle digit press"""
        if self.in_call:
            # Send DTMF tone
            if self.modem:
                self.modem.send_dtmf(digit)
        else:
            # Add to phone number
            if len(self.phone_number) < 15:
                self.phone_number += digit
                self._update_display()
    
    def _on_backspace(self):
        """Handle backspace"""
        if not self.in_call and self.phone_number:
            self.phone_number = self.phone_number[:-1]
            self._update_display()
    
    def _update_display(self):
        """Update the phone number display"""
        # Format number for display
        display = self.phone_number
        if len(display) > 10:
            # Format as +X XXX XXX XXXX
            pass  # Keep as-is for international
        elif len(display) == 10:
            display = f"({display[:3]}) {display[3:6]}-{display[6:]}"
        elif len(display) == 7:
            display = f"{display[:3]}-{display[3:]}"
        
        self.number_display.config(text=display)
    
    def _on_dial(self):
        """Initiate phone call"""
        if not self.phone_number:
            return
        
        if self.modem:
            success = self.modem.dial(self.phone_number)
            if success:
                self.in_call = True
                self.caller_label.config(text=self.phone_number)
                self.status_label.config(text="Dialing...", fg=self.colors.accent_primary)
                self._show_incall()
                self._start_call_timer()
            else:
                self.status_label.config(text="Call failed", fg=self.colors.accent_danger)
        else:
            # Demo mode
            self.in_call = True
            self.caller_label.config(text=self.phone_number)
            self.status_label.config(text="Dialing...", fg=self.colors.accent_primary)
            self._show_incall()
            self._start_call_timer()
    
    def _on_answer(self):
        """Answer incoming call"""
        if self.modem:
            success = self.modem.answer()
            if success:
                self.in_call = True
                self.incoming_call = False
                self.status_label.config(text="Connected", fg=self.colors.call_active)
                self.answer_btn.pack_forget()
                self._start_call_timer()
    
    def _on_hangup(self):
        """End current call"""
        if self.modem:
            self.modem.hangup()
        
        self._end_call()
    
    def _on_incoming_call(self, number: str):
        """Handle incoming call notification"""
        self.incoming_call = True
        self.phone_number = number
        self.caller_label.config(text=number or "Unknown")
        self._show_incoming()
    
    def _on_call_ended(self):
        """Handle call ended event"""
        self._end_call()
    
    def _end_call(self):
        """Clean up after call ends"""
        self.in_call = False
        self.incoming_call = False
        self._stop_call_timer()
        self.status_label.config(text="")
        self.duration_label.config(text="00:00")
        self.answer_btn.pack_forget()
        self._show_dialer()
    
    def _on_mute(self):
        """Toggle mute"""
        # Toggle visual state
        pass
    
    def _on_speaker(self):
        """Toggle speaker"""
        # Toggle visual state
        pass
    
    def _show_dtmf_pad(self):
        """Show DTMF keypad during call"""
        pass
    
    # Call timer
    _call_seconds = 0
    _timer_running = False
    
    def _start_call_timer(self):
        """Start the call duration timer"""
        self._call_seconds = 0
        self._timer_running = True
        self._update_call_timer()
    
    def _stop_call_timer(self):
        """Stop the call duration timer"""
        self._timer_running = False
        self._call_seconds = 0
    
    def _update_call_timer(self):
        """Update call duration display"""
        if not self._timer_running:
            return
        
        mins = self._call_seconds // 60
        secs = self._call_seconds % 60
        self.duration_label.config(text=f"{mins:02d}:{secs:02d}")
        
        self._call_seconds += 1
        self.after(1000, self._update_call_timer)
    
    def clear_number(self):
        """Clear the entered phone number"""
        self.phone_number = ""
        self._update_display()

