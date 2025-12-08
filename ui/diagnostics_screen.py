"""
PiPhone-X Diagnostics & Testing Screen
Hardware testing and AT command interface
"""

import tkinter as tk
from tkinter import scrolledtext
from typing import Optional
from .theme import Theme, Colors
from .components import TouchButton, ScrollableFrame, KeyboardButton


class DiagnosticsScreen(tk.Frame):
    """
    Diagnostics screen for testing hardware and sending raw AT commands
    """
    
    def __init__(self, parent, modem, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        self.colors = colors
        self.modem = modem
        self.test_results = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Build the diagnostics interface - compact for 320x480"""
        # Header - compact
        header = tk.Frame(self, bg=self.colors.surface, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="Diagnostics",
            font=Theme.FONT_MEDIUM,
            bg=self.colors.surface,
            fg=self.colors.text_primary
        ).pack(side=tk.LEFT, padx=10, pady=6)
        
        # Content with tabs
        self.content = tk.Frame(self, bg=self.colors.background)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Tab buttons - compact
        tab_frame = tk.Frame(self.content, bg=self.colors.surface)
        tab_frame.pack(fill=tk.X)
        
        self.tabs = []
        tab_data = [
            ("Test", self._show_self_test),
            ("Info", self._show_module_info),
            ("AT", self._show_at_console),
            ("Network", self._show_network_info)
        ]
        
        for i, (label, cmd) in enumerate(tab_data):
            btn = TouchButton(
                tab_frame,
                text=label,
                command=cmd,
                width=72,
                height=30,
                font=Theme.FONT_TINY
            )
            btn.pack(side=tk.LEFT, padx=2, pady=3)
            self.tabs.append(btn)
        
        # Tab content area
        self.tab_content = tk.Frame(self.content, bg=self.colors.background)
        self.tab_content.pack(fill=tk.BOTH, expand=True)
        
        # Create tab panels
        self._create_self_test_panel()
        self._create_module_info_panel()
        self._create_at_console_panel()
        self._create_network_panel()
        
        # Show first tab
        self._show_self_test()
    
    def _create_self_test_panel(self):
        """Create self-test panel - compact"""
        self.test_panel = tk.Frame(self.tab_content, bg=self.colors.background)
        
        # Test results display
        results_frame = tk.Frame(self.test_panel, bg=self.colors.background)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Test items
        self.test_items = {}
        tests = [
            ("at_response", "AT Response"),
            ("sim_card", "SIM Card"),
            ("network", "Network"),
            ("signal", "Signal"),
            ("gps_module", "GPS Module")
        ]
        
        for key, label in tests:
            item = tk.Frame(results_frame, bg=self.colors.surface)
            item.pack(fill=tk.X, pady=2)
            
            tk.Label(
                item,
                text=label,
                font=Theme.FONT_SMALL,
                bg=self.colors.surface,
                fg=self.colors.text_primary,
                width=15,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=10, pady=8)
            
            status_label = tk.Label(
                item,
                text="Not tested",
                font=Theme.FONT_SMALL,
                bg=self.colors.surface,
                fg=self.colors.text_muted
            )
            status_label.pack(side=tk.RIGHT, padx=10, pady=8)
            
            self.test_items[key] = status_label
        
        # Run tests button
        btn_frame = tk.Frame(self.test_panel, bg=self.colors.background)
        btn_frame.pack(fill=tk.X, pady=5)
        
        TouchButton(
            btn_frame,
            text="Run All Tests",
            command=self._run_self_test,
            width=150,
            height=40,
            bg=self.colors.accent_primary,
            fg=self.colors.background,
            font=Theme.FONT_MEDIUM
        ).pack()
        
        # Summary
        self.test_summary = tk.Label(
            self.test_panel,
            text="",
            font=Theme.FONT_SMALL,
            bg=self.colors.background,
            fg=self.colors.text_secondary
        )
        self.test_summary.pack(pady=5)
    
    def _create_module_info_panel(self):
        """Create module information panel - compact"""
        self.info_panel = tk.Frame(self.tab_content, bg=self.colors.background)
        
        info_frame = tk.Frame(self.info_panel, bg=self.colors.background)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Info items
        self.info_items = {}
        info_fields = [
            ("manufacturer", "Manufacturer"),
            ("model", "Model"),
            ("revision", "Firmware"),
            ("imei", "IMEI"),
            ("sim_status", "SIM Status")
        ]
        
        for key, label in info_fields:
            item = tk.Frame(info_frame, bg=self.colors.surface)
            item.pack(fill=tk.X, pady=2)
            
            tk.Label(
                item,
                text=label,
                font=Theme.FONT_TINY,
                bg=self.colors.surface,
                fg=self.colors.text_muted,
                width=12,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=8, pady=6)
            
            value_label = tk.Label(
                item,
                text="--",
                font=Theme.FONT_SMALL,
                bg=self.colors.surface,
                fg=self.colors.text_primary
            )
            value_label.pack(side=tk.LEFT, padx=5, pady=6)
            
            self.info_items[key] = value_label
        
        # Refresh button
        TouchButton(
            self.info_panel,
            text="Refresh",
            command=self._refresh_module_info,
            width=120,
            height=36,
            font=Theme.FONT_SMALL
        ).pack(pady=8)
    
    def _create_at_console_panel(self):
        """Create AT command console panel - compact"""
        self.console_panel = tk.Frame(self.tab_content, bg=self.colors.background)
        
        # Output area
        self.console_output = scrolledtext.ScrolledText(
            self.console_panel,
            font=(Theme.FONT_MONO, 9),
            bg=self.colors.surface,
            fg=self.colors.accent_primary,
            insertbackground=self.colors.text_primary,
            height=6,
            wrap=tk.WORD
        )
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console_output.config(state=tk.DISABLED)
        
        # Command input area
        input_frame = tk.Frame(self.console_panel, bg=self.colors.surface)
        input_frame.pack(fill=tk.X, padx=5, pady=3)
        
        tk.Label(
            input_frame,
            text="AT>",
            font=(Theme.FONT_MONO, 10),
            bg=self.colors.surface,
            fg=self.colors.accent_primary
        ).pack(side=tk.LEFT, padx=5)
        
        self.cmd_entry = tk.Entry(
            input_frame,
            font=(Theme.FONT_MONO, 10),
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=25
        )
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=6)
        self.cmd_entry.bind("<Return>", lambda e: self._send_at_command())
        
        # Keyboard toggle button
        KeyboardButton(input_frame, self.cmd_entry).pack(side=tk.LEFT, padx=2)
        
        TouchButton(
            input_frame,
            text="Send",
            command=self._send_at_command,
            width=55,
            height=28,
            bg=self.colors.accent_primary,
            fg=self.colors.background,
            font=Theme.FONT_TINY
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Quick commands
        quick_frame = tk.Frame(self.console_panel, bg=self.colors.background)
        quick_frame.pack(fill=tk.X, padx=5, pady=3)
        
        quick_commands = [
            ("AT", "AT"),
            ("CSQ", "AT+CSQ"),
            ("Net", "AT+CREG?"),
            ("GPS+", "AT+CGPS=1,1"),
            ("GPS-", "AT+CGPS=0"),
            ("Clr", None)
        ]
        
        for label, cmd in quick_commands:
            TouchButton(
                quick_frame,
                text=label,
                command=lambda c=cmd: self._quick_command(c),
                width=48,
                height=26,
                font=(Theme.FONT_FAMILY, 8)
            ).pack(side=tk.LEFT, padx=1)
    
    def _create_network_panel(self):
        """Create network information panel - compact"""
        self.network_panel = tk.Frame(self.tab_content, bg=self.colors.background)
        
        info_frame = tk.Frame(self.network_panel, bg=self.colors.background)
        info_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Network items
        self.network_items = {}
        fields = [
            ("registered", "Status"),
            ("operator", "Operator"),
            ("signal", "Signal"),
            ("mode", "Mode")
        ]
        
        for key, label in fields:
            item = tk.Frame(info_frame, bg=self.colors.surface)
            item.pack(fill=tk.X, pady=1)
            
            tk.Label(
                item,
                text=label,
                font=Theme.FONT_TINY,
                bg=self.colors.surface,
                fg=self.colors.text_muted,
                width=8,
                anchor=tk.W
            ).pack(side=tk.LEFT, padx=8, pady=5)
            
            value_label = tk.Label(
                item,
                text="--",
                font=Theme.FONT_TINY,
                bg=self.colors.surface,
                fg=self.colors.text_primary
            )
            value_label.pack(side=tk.RIGHT, padx=8, pady=5)
            
            self.network_items[key] = value_label
        
        # Signal strength bar
        signal_frame = tk.Frame(self.network_panel, bg=self.colors.background)
        signal_frame.pack(fill=tk.X, padx=10, pady=3)
        
        tk.Label(
            signal_frame,
            text="Signal",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.background,
            fg=self.colors.text_secondary
        ).pack(side=tk.LEFT)
        
        self.signal_bar = tk.Canvas(
            signal_frame,
            width=200,
            height=12,
            bg=self.colors.surface,
            highlightthickness=0
        )
        self.signal_bar.pack(side=tk.LEFT, padx=8)
        
        # Network Mode Toggle Section
        mode_section = tk.Frame(self.network_panel, bg=self.colors.surface)
        mode_section.pack(fill=tk.X, padx=5, pady=3)
        
        tk.Label(
            mode_section,
            text="Network Mode",
            font=Theme.FONT_TINY,
            bg=self.colors.surface,
            fg=self.colors.text_primary
        ).pack(pady=(3, 2))
        
        # Mode buttons frame
        mode_btns = tk.Frame(mode_section, bg=self.colors.surface)
        mode_btns.pack(pady=3)
        
        self.mode_buttons = {}
        self.current_mode = "3g"  # Default
        
        modes = [
            ("4G", "lte"),
            ("3G", "3g"),
            ("2G", "2g"),
            ("Auto", "auto")
        ]
        
        for label, mode in modes:
            btn = TouchButton(
                mode_btns,
                text=label,
                command=lambda m=mode: self._set_network_mode(m),
                width=55,
                height=26,
                font=(Theme.FONT_FAMILY, 8),
                bg=self.colors.accent_primary if mode == "3g" else self.colors.surface_light
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.mode_buttons[mode] = btn
        
        # APN Settings Section
        apn_section = tk.Frame(self.network_panel, bg=self.colors.surface)
        apn_section.pack(fill=tk.X, padx=5, pady=3)
        
        tk.Label(
            apn_section,
            text="APN Settings",
            font=Theme.FONT_TINY,
            bg=self.colors.surface,
            fg=self.colors.text_primary
        ).pack(pady=(3, 2))
        
        # APN entry row
        apn_row = tk.Frame(apn_section, bg=self.colors.surface)
        apn_row.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(
            apn_row,
            text="APN:",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface,
            fg=self.colors.text_muted,
            width=5
        ).pack(side=tk.LEFT)
        
        self.apn_entry = tk.Entry(
            apn_row,
            font=(Theme.FONT_FAMILY, 9),
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=18
        )
        self.apn_entry.pack(side=tk.LEFT, padx=3)
        self.apn_entry.insert(0, "mobilenet")  # Default
        
        # Keyboard toggle button
        KeyboardButton(apn_row, self.apn_entry).pack(side=tk.LEFT, padx=1)
        
        TouchButton(
            apn_row,
            text="Apply",
            command=self._apply_apn,
            width=45,
            height=24,
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.accent_primary
        ).pack(side=tk.LEFT, padx=2)
        
        # Optional: Username/Password row (collapsed by default)
        auth_row = tk.Frame(apn_section, bg=self.colors.surface)
        auth_row.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(
            auth_row,
            text="User:",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface,
            fg=self.colors.text_muted,
            width=5
        ).pack(side=tk.LEFT)
        
        self.apn_user_entry = tk.Entry(
            auth_row,
            font=(Theme.FONT_FAMILY, 9),
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=8
        )
        self.apn_user_entry.pack(side=tk.LEFT, padx=2)
        
        KeyboardButton(auth_row, self.apn_user_entry).pack(side=tk.LEFT, padx=1)
        
        tk.Label(
            auth_row,
            text="Pass:",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface,
            fg=self.colors.text_muted,
            width=4
        ).pack(side=tk.LEFT)
        
        self.apn_pass_entry = tk.Entry(
            auth_row,
            font=(Theme.FONT_FAMILY, 9),
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=8,
            show="*"
        )
        self.apn_pass_entry.pack(side=tk.LEFT, padx=2)
        
        KeyboardButton(auth_row, self.apn_pass_entry).pack(side=tk.LEFT, padx=1)
        
        # Current APN display
        self.apn_status = tk.Label(
            apn_section,
            text="Current: mobilenet",
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.surface,
            fg=self.colors.text_muted
        )
        self.apn_status.pack(pady=(2, 4))
        
        # Bottom buttons
        btn_frame = tk.Frame(self.network_panel, bg=self.colors.background)
        btn_frame.pack(fill=tk.X, pady=3)
        
        TouchButton(
            btn_frame,
            text="Refresh",
            command=self._refresh_network,
            width=70,
            height=28,
            font=(Theme.FONT_FAMILY, 8)
        ).pack(side=tk.LEFT, padx=3)
        
        TouchButton(
            btn_frame,
            text="Reset",
            command=self._reset_modem,
            width=70,
            height=28,
            font=(Theme.FONT_FAMILY, 8),
            bg=self.colors.accent_warning
        ).pack(side=tk.LEFT, padx=3)
        
        TouchButton(
            btn_frame,
            text="Register",
            command=self._force_registration,
            width=70,
            height=28,
            font=(Theme.FONT_FAMILY, 8)
        ).pack(side=tk.LEFT, padx=3)
    
    def _hide_all_panels(self):
        """Hide all tab panels"""
        self.test_panel.pack_forget()
        self.info_panel.pack_forget()
        self.console_panel.pack_forget()
        self.network_panel.pack_forget()
    
    def _show_self_test(self):
        """Show self-test panel"""
        self._hide_all_panels()
        self.test_panel.pack(fill=tk.BOTH, expand=True)
        self._highlight_tab(0)
    
    def _show_module_info(self):
        """Show module info panel"""
        self._hide_all_panels()
        self.info_panel.pack(fill=tk.BOTH, expand=True)
        self._highlight_tab(1)
        self._refresh_module_info()
    
    def _show_at_console(self):
        """Show AT console panel"""
        self._hide_all_panels()
        self.console_panel.pack(fill=tk.BOTH, expand=True)
        self._highlight_tab(2)
    
    def _show_network_info(self):
        """Show network panel"""
        self._hide_all_panels()
        self.network_panel.pack(fill=tk.BOTH, expand=True)
        self._highlight_tab(3)
        self._load_current_apn()
        self._refresh_network()
    
    def _highlight_tab(self, index):
        """Highlight active tab"""
        for i, tab in enumerate(self.tabs):
            if i == index:
                tab.set_colors(bg=self.colors.accent_primary, fg=self.colors.background)
            else:
                tab.set_colors(bg=self.colors.surface_light, fg=self.colors.text_primary)
    
    def _run_self_test(self):
        """Run diagnostic self-test"""
        if not self.modem:
            self.test_summary.config(text="No modem connected", fg=self.colors.accent_danger)
            return
        
        # Reset all items
        for label in self.test_items.values():
            label.config(text="Testing...", fg=self.colors.accent_warning)
        self.update()
        
        # Run tests
        results = self.modem.run_self_test()
        
        # Update display
        passed = 0
        for key, result in results.items():
            if key in self.test_items:
                if result:
                    self.test_items[key].config(text="✓ PASS", fg=self.colors.accent_success)
                    passed += 1
                else:
                    self.test_items[key].config(text="✗ FAIL", fg=self.colors.accent_danger)
        
        total = len(results)
        self.test_summary.config(
            text=f"Tests completed: {passed}/{total} passed",
            fg=self.colors.accent_success if passed == total else self.colors.accent_warning
        )
    
    def _refresh_module_info(self):
        """Refresh module information"""
        if not self.modem:
            return
        
        info = self.modem.get_module_info()
        
        for key, value in info.items():
            if key in self.info_items:
                self.info_items[key].config(text=value or "--")
        
        # SIM status
        sim_status = self.modem.get_sim_status()
        self.info_items['sim_status'].config(text=sim_status)
        
        if sim_status == "READY":
            self.info_items['sim_status'].config(fg=self.colors.accent_success)
        else:
            self.info_items['sim_status'].config(fg=self.colors.accent_danger)
    
    def _send_at_command(self):
        """Send AT command from console"""
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        
        # Add to output
        self._console_write(f">>> {cmd}\n", self.colors.text_secondary)
        
        # Send command
        if self.modem:
            response = self.modem.send_raw_command(cmd)
            self._console_write(f"{response}\n\n", self.colors.accent_primary)
        else:
            self._console_write("No modem connected\n\n", self.colors.accent_danger)
        
        self.cmd_entry.delete(0, tk.END)
    
    def _quick_command(self, cmd):
        """Execute quick command"""
        if cmd is None:
            # Clear console
            self.console_output.config(state=tk.NORMAL)
            self.console_output.delete(1.0, tk.END)
            self.console_output.config(state=tk.DISABLED)
        else:
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, cmd)
            self._send_at_command()
    
    def _console_write(self, text, color=None):
        """Write to console output"""
        self.console_output.config(state=tk.NORMAL)
        self.console_output.insert(tk.END, text)
        self.console_output.see(tk.END)
        self.console_output.config(state=tk.DISABLED)
    
    def _refresh_network(self):
        """Refresh network information"""
        if not self.modem:
            return
        
        info = self.modem.get_network_info()
        
        # Registration status
        if info.get('registered'):
            self.network_items['registered'].config(
                text="Registered",
                fg=self.colors.accent_success
            )
        else:
            self.network_items['registered'].config(
                text="Not Registered",
                fg=self.colors.accent_danger
            )
        
        # Operator
        self.network_items['operator'].config(
            text=info.get('operator', '--') or '--'
        )
        
        # Signal
        signal = info.get('signal', 0)
        self.network_items['signal'].config(text=f"{signal}%")
        
        # Current mode display
        mode_names = {
            "auto": "Auto",
            "lte": "4G LTE",
            "3g": "3G WCDMA",
            "2g": "2G GSM"
        }
        self.network_items['mode'].config(
            text=mode_names.get(self.current_mode, "3G WCDMA"),
            fg=self.colors.text_primary
        )
        
        # Update signal bar
        self._draw_signal_bar(signal)
    
    def _draw_signal_bar(self, strength):
        """Draw signal strength bar"""
        self.signal_bar.delete("all")
        
        # Background
        self.signal_bar.create_rectangle(
            0, 0, 200, 12,
            fill=self.colors.surface_light,
            outline=""
        )
        
        # Signal level
        width = int(200 * (strength / 100))
        
        if strength > 70:
            color = self.colors.accent_success
        elif strength > 40:
            color = self.colors.accent_warning
        else:
            color = self.colors.accent_danger
        
        self.signal_bar.create_rectangle(
            0, 0, width, 12,
            fill=color,
            outline=""
        )
    
    def _set_network_mode(self, mode: str):
        """Set network mode (LTE, 3G, 2G, Auto)"""
        if not self.modem:
            return
        
        # Update button colors
        for m, btn in self.mode_buttons.items():
            if m == mode:
                btn.set_colors(bg=self.colors.accent_primary, fg=self.colors.background)
            else:
                btn.set_colors(bg=self.colors.surface_light, fg=self.colors.text_primary)
        
        self.current_mode = mode
        
        # Send AT command based on mode
        mode_commands = {
            "auto": "AT+CNMP=2",    # Automatic
            "lte": "AT+CNMP=38",    # LTE only
            "3g": "AT+CNMP=14",     # WCDMA/3G only
            "2g": "AT+CNMP=13"      # GSM/2G only
        }
        
        mode_names = {
            "auto": "Auto (4G/3G/2G)",
            "lte": "4G LTE Only",
            "3g": "3G WCDMA Only",
            "2g": "2G GSM Only"
        }
        
        # Show status
        self.network_items['mode'].config(
            text=f"Switching to {mode_names.get(mode, mode)}...",
            fg=self.colors.accent_warning
        )
        self.update()
        
        # Send command
        if mode in mode_commands:
            self.modem.send_raw_command(mode_commands[mode])
        
        # Force re-registration
        self.modem.send_raw_command("AT+COPS=0", 10)
        
        # Wait and refresh
        self.after(3000, self._refresh_network)
    
    def _reset_modem(self):
        """Reset/reboot the modem"""
        if not self.modem:
            return
        
        self.network_items['registered'].config(
            text="Resetting...",
            fg=self.colors.accent_warning
        )
        self.update()
        
        # Send reset command
        self.modem.send_raw_command("AT+CFUN=1,1", 5)
        
        # Wait for modem to reboot
        self.after(15000, self._after_reset)
    
    def _after_reset(self):
        """Called after modem reset"""
        if not self.modem:
            return
        
        # Re-apply 3G mode (default)
        self.modem.send_raw_command("AT+CNMP=14")
        self.modem.send_raw_command('AT+CGDCONT=1,"IP","mobilenet"')
        self.modem.send_raw_command("AT+COPS=0", 10)
        
        self.current_mode = "3g"
        for m, btn in self.mode_buttons.items():
            if m == "3g":
                btn.set_colors(bg=self.colors.accent_primary, fg=self.colors.background)
            else:
                btn.set_colors(bg=self.colors.surface_light, fg=self.colors.text_primary)
        
        self.after(5000, self._refresh_network)
    
    def _force_registration(self):
        """Force network re-registration"""
        if not self.modem:
            return
        
        self.network_items['registered'].config(
            text="Registering...",
            fg=self.colors.accent_warning
        )
        self.update()
        
        # Detach and re-attach
        self.modem.send_raw_command("AT+COPS=2", 5)  # Deregister
        self.after(2000, lambda: self.modem.send_raw_command("AT+COPS=0", 30))  # Re-register
        self.after(10000, self._refresh_network)
    
    def _apply_apn(self):
        """Apply APN settings"""
        if not self.modem:
            return
        
        apn = self.apn_entry.get().strip()
        username = self.apn_user_entry.get().strip()
        password = self.apn_pass_entry.get().strip()
        
        if not apn:
            self.apn_status.config(text="Error: APN required", fg=self.colors.accent_danger)
            return
        
        self.apn_status.config(text="Applying...", fg=self.colors.accent_warning)
        self.update()
        
        # Set APN
        if username and password:
            # With authentication
            self.modem.send_raw_command(f'AT+CGDCONT=1,"IP","{apn}"')
            self.modem.send_raw_command(f'AT+CGAUTH=1,1,"{password}","{username}"')
        else:
            # Without authentication
            self.modem.send_raw_command(f'AT+CGDCONT=1,"IP","{apn}"')
        
        # Force re-registration with new APN
        self.modem.send_raw_command("AT+COPS=0", 10)
        
        self.apn_status.config(text=f"Current: {apn}", fg=self.colors.accent_success)
        
        # Refresh after a delay
        self.after(5000, self._refresh_network)
    
    def _load_current_apn(self):
        """Load current APN from modem"""
        if not self.modem:
            return
        
        try:
            apn = self.modem.get_apn()
            if apn:
                self.apn_entry.delete(0, tk.END)
                self.apn_entry.insert(0, apn)
                self.apn_status.config(text=f"Current: {apn}", fg=self.colors.text_muted)
        except:
            pass
    

