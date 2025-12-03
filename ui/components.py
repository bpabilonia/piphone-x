"""
PiPhone-X Custom UI Components
Touch-optimized widgets for 480x320 display
"""

import tkinter as tk
from tkinter import Canvas
from typing import Callable, Optional, List, Tuple
from .theme import Theme, Colors


class TouchButton(Canvas):
    """
    Touch-friendly button with rounded corners and hover effects
    """
    
    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        width: int = 100,
        height: int = 48,
        bg: str = None,
        fg: str = None,
        hover_bg: str = None,
        font: tuple = None,
        icon: str = None,
        radius: int = 8,
        **kwargs
    ):
        colors = Theme.colors
        self.bg_color = bg or colors.surface_light
        self.fg_color = fg or colors.text_primary
        self.hover_color = hover_bg or colors.key_hover
        self.radius = radius
        self.text = text
        self.icon = icon
        self.font = font or Theme.FONT_MEDIUM
        self.command = command
        self.pressed = False
        
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=colors.background,
            highlightthickness=0,
            **kwargs
        )
        
        self._draw()
        
        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _draw(self, hover: bool = False, pressed: bool = False):
        """Draw the button with current state"""
        self.delete("all")
        
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        r = self.radius
        
        # Choose color based on state
        if pressed:
            fill = self.hover_color
        elif hover:
            fill = self.hover_color
        else:
            fill = self.bg_color
        
        # Draw rounded rectangle
        self._rounded_rect(2, 2, w-2, h-2, r, fill)
        
        # Draw text/icon
        if self.icon:
            self.create_text(
                w//2, h//2 - 8,
                text=self.icon,
                fill=self.fg_color,
                font=(Theme.FONT_FAMILY, 20)
            )
            if self.text:
                self.create_text(
                    w//2, h//2 + 12,
                    text=self.text,
                    fill=self.fg_color,
                    font=Theme.FONT_TINY
                )
        else:
            self.create_text(
                w//2, h//2,
                text=self.text,
                fill=self.fg_color,
                font=self.font
            )
    
    def _rounded_rect(self, x1, y1, x2, y2, r, fill):
        """Draw a rounded rectangle"""
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
            x1+r, y1
        ]
        self.create_polygon(points, fill=fill, smooth=True)
    
    def _on_enter(self, event):
        self._draw(hover=True)
    
    def _on_leave(self, event):
        self.pressed = False
        self._draw()
    
    def _on_press(self, event):
        self.pressed = True
        self._draw(pressed=True)
    
    def _on_release(self, event):
        if self.pressed and self.command:
            self.command()
        self.pressed = False
        self._draw()
    
    def set_text(self, text: str):
        """Update button text"""
        self.text = text
        self._draw()
    
    def set_colors(self, bg: str = None, fg: str = None):
        """Update button colors"""
        if bg:
            self.bg_color = bg
        if fg:
            self.fg_color = fg
        self._draw()


class CircleButton(Canvas):
    """
    Circular button for call controls
    """
    
    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        size: int = 60,
        bg: str = None,
        fg: str = None,
        font: tuple = None,
        **kwargs
    ):
        colors = Theme.colors
        self.bg_color = bg or colors.accent_primary
        self.fg_color = fg or colors.background
        self.font = font or Theme.FONT_LARGE
        self.command = command
        self.text = text
        self.size = size
        
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=colors.background,
            highlightthickness=0,
            **kwargs
        )
        
        self._draw()
        
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _draw(self, pressed: bool = False):
        self.delete("all")
        s = self.size
        pad = 2
        
        color = self.bg_color if not pressed else self.fg_color
        text_color = self.fg_color if not pressed else self.bg_color
        
        # Draw circle
        self.create_oval(pad, pad, s-pad, s-pad, fill=color, outline="")
        
        # Draw text
        self.create_text(s//2, s//2, text=self.text, fill=text_color, font=self.font)
    
    def _on_press(self, event):
        self._draw(pressed=True)
    
    def _on_release(self, event):
        self._draw()
        if self.command:
            self.command()


class StatusBar(tk.Frame):
    """
    Top status bar showing time, signal, battery
    """
    
    def __init__(self, parent, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.status_bg, height=Theme.STATUS_BAR_HEIGHT, **kwargs)
        
        self.colors = colors
        
        # Time display
        self.time_label = tk.Label(
            self,
            text="12:00",
            font=Theme.FONT_SMALL,
            bg=colors.status_bg,
            fg=colors.text_primary
        )
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        # Operator name
        self.operator_label = tk.Label(
            self,
            text="",
            font=Theme.FONT_TINY,
            bg=colors.status_bg,
            fg=colors.text_secondary
        )
        self.operator_label.pack(side=tk.LEFT, padx=5)
        
        # Right side - signal, battery
        self.battery_label = tk.Label(
            self,
            text="🔋",
            font=Theme.FONT_SMALL,
            bg=colors.status_bg,
            fg=colors.text_primary
        )
        self.battery_label.pack(side=tk.RIGHT, padx=10)
        
        self.signal_label = tk.Label(
            self,
            text="📶",
            font=Theme.FONT_SMALL,
            bg=colors.status_bg,
            fg=colors.text_primary
        )
        self.signal_label.pack(side=tk.RIGHT, padx=5)
        
        # GPS indicator
        self.gps_label = tk.Label(
            self,
            text="",
            font=Theme.FONT_TINY,
            bg=colors.status_bg,
            fg=colors.accent_primary
        )
        self.gps_label.pack(side=tk.RIGHT, padx=5)
    
    def update_time(self, time_str: str):
        self.time_label.config(text=time_str)
    
    def update_signal(self, strength: int):
        """Update signal strength (0-100)"""
        if strength > 75:
            text = "📶"
        elif strength > 50:
            text = "📶"
        elif strength > 25:
            text = "📶"
        elif strength > 0:
            text = "📶"
        else:
            text = "✕"
        self.signal_label.config(text=f"{text} {strength}%")
    
    def update_operator(self, name: str):
        self.operator_label.config(text=name)
    
    def update_gps(self, active: bool, has_fix: bool = False):
        if active and has_fix:
            self.gps_label.config(text="GPS ●", fg=self.colors.accent_success)
        elif active:
            self.gps_label.config(text="GPS ○", fg=self.colors.accent_warning)
        else:
            self.gps_label.config(text="")


class TabBar(tk.Frame):
    """
    Bottom navigation tab bar
    """
    
    def __init__(
        self,
        parent,
        tabs: List[Tuple[str, str, Callable]],  # (icon, label, callback)
        **kwargs
    ):
        colors = Theme.colors
        super().__init__(parent, bg=colors.tab_bg, height=Theme.TAB_BAR_HEIGHT, **kwargs)
        
        self.colors = colors
        self.tabs = []
        self.active_index = 0
        
        # Calculate tab width
        tab_width = Theme.WIDTH // len(tabs)
        
        for i, (icon, label, callback) in enumerate(tabs):
            tab = tk.Frame(self, bg=colors.tab_bg, width=tab_width, height=Theme.TAB_BAR_HEIGHT)
            tab.pack(side=tk.LEFT, fill=tk.Y)
            tab.pack_propagate(False)
            
            icon_label = tk.Label(
                tab,
                text=icon,
                font=(Theme.FONT_FAMILY, 18),
                bg=colors.tab_bg,
                fg=colors.tab_inactive
            )
            icon_label.pack(pady=(4, 0))
            
            text_label = tk.Label(
                tab,
                text=label,
                font=Theme.FONT_TINY,
                bg=colors.tab_bg,
                fg=colors.tab_inactive
            )
            text_label.pack()
            
            # Store references
            tab_data = {
                'frame': tab,
                'icon': icon_label,
                'text': text_label,
                'callback': callback
            }
            self.tabs.append(tab_data)
            
            # Bind click events
            tab.bind("<Button-1>", lambda e, idx=i: self._select_tab(idx))
            icon_label.bind("<Button-1>", lambda e, idx=i: self._select_tab(idx))
            text_label.bind("<Button-1>", lambda e, idx=i: self._select_tab(idx))
        
        # Select first tab
        self._select_tab(0)
    
    def _select_tab(self, index: int):
        """Select a tab by index"""
        # Deselect previous
        if self.active_index < len(self.tabs):
            prev = self.tabs[self.active_index]
            prev['icon'].config(fg=self.colors.tab_inactive)
            prev['text'].config(fg=self.colors.tab_inactive)
        
        # Select new
        self.active_index = index
        current = self.tabs[index]
        current['icon'].config(fg=self.colors.tab_active)
        current['text'].config(fg=self.colors.tab_active)
        
        # Call callback
        if current['callback']:
            current['callback']()
    
    def set_active(self, index: int):
        """Programmatically set active tab"""
        self._select_tab(index)


class NumPad(tk.Frame):
    """
    Numeric keypad for phone dialing
    """
    
    def __init__(
        self,
        parent,
        on_key: Callable[[str], None],
        on_backspace: Callable[[], None] = None,
        on_call: Callable[[], None] = None,
        on_hangup: Callable[[], None] = None,
        show_call_buttons: bool = True,
        **kwargs
    ):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        self.colors = colors
        self.on_key = on_key
        self.on_backspace = on_backspace
        self.on_call = on_call
        self.on_hangup = on_hangup
        
        # Key layout with sub-labels
        keys = [
            ('1', ''),
            ('2', 'ABC'),
            ('3', 'DEF'),
            ('4', 'GHI'),
            ('5', 'JKL'),
            ('6', 'MNO'),
            ('7', 'PQRS'),
            ('8', 'TUV'),
            ('9', 'WXYZ'),
            ('*', ''),
            ('0', '+'),
            ('#', ''),
        ]
        
        # Create grid - sized for 320x480 portrait display (406px available)
        key_size = 58
        for i, (key, sub) in enumerate(keys):
            row = i // 3
            col = i % 3
            
            btn_frame = tk.Frame(self, bg=colors.background)
            btn_frame.grid(row=row, column=col, padx=3, pady=2)
            
            btn = TouchButton(
                btn_frame,
                text=key,
                command=lambda k=key: self._on_key_press(k),
                width=key_size,
                height=key_size,
                font=(Theme.FONT_FAMILY, 20, "bold"),
                radius=key_size//2
            )
            btn.pack()
            
            # Add sub-label (positioned inside the button area)
            if sub:
                sub_label = tk.Label(
                    btn_frame,
                    text=sub,
                    font=(Theme.FONT_FAMILY, 7),
                    bg=colors.background,
                    fg=colors.text_muted
                )
                sub_label.place(relx=0.5, rely=0.75, anchor=tk.CENTER)
        
        # Call/Hangup buttons
        if show_call_buttons:
            call_row = tk.Frame(self, bg=colors.background)
            call_row.grid(row=4, column=0, columnspan=3, pady=5)
            
            # Call button (green)
            self.call_btn = CircleButton(
                call_row,
                text="📞",
                command=self.on_call,
                size=55,
                bg=colors.call_active
            )
            self.call_btn.pack(side=tk.LEFT, padx=12)
            
            # Hangup button (red)
            self.hangup_btn = CircleButton(
                call_row,
                text="✕",
                command=self.on_hangup,
                size=55,
                bg=colors.call_end
            )
            self.hangup_btn.pack(side=tk.LEFT, padx=12)
            
            # Backspace button
            if self.on_backspace:
                self.back_btn = TouchButton(
                    call_row,
                    text="⌫",
                    command=self.on_backspace,
                    width=55,
                    height=55,
                    font=(Theme.FONT_FAMILY, 18),
                    radius=27
                )
                self.back_btn.pack(side=tk.LEFT, padx=12)
    
    def _on_key_press(self, key: str):
        if self.on_key:
            self.on_key(key)


class MessageBubble(tk.Frame):
    """
    Chat message bubble for SMS display - compact for 320px width
    """
    
    def __init__(
        self,
        parent,
        message: str,
        timestamp: str,
        is_sent: bool = False,
        **kwargs
    ):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        # Choose alignment and colors - compact for 320px width
        if is_sent:
            bg_color = colors.accent_primary
            fg_color = colors.background
            anchor = tk.E
            padx = (40, 5)
        else:
            bg_color = colors.surface_light
            fg_color = colors.text_primary
            anchor = tk.W
            padx = (5, 40)
        
        # Bubble frame
        bubble = tk.Frame(self, bg=bg_color)
        bubble.pack(anchor=anchor, padx=padx, pady=2)
        
        # Message text
        msg_label = tk.Label(
            bubble,
            text=message,
            font=Theme.FONT_TINY,
            bg=bg_color,
            fg=fg_color,
            wraplength=200,
            justify=tk.LEFT
        )
        msg_label.pack(padx=8, pady=4)
        
        # Timestamp - compact
        time_label = tk.Label(
            bubble,
            text=timestamp,
            font=(Theme.FONT_FAMILY, 7),
            bg=bg_color,
            fg=fg_color if is_sent else colors.text_muted
        )
        time_label.pack(padx=8, pady=(0, 3), anchor=tk.E)


class ScrollableFrame(tk.Frame):
    """
    Scrollable container frame for long content
    """
    
    def __init__(self, parent, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self,
            bg=colors.background,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar (hidden by default on touch)
        self.scrollbar = tk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        # self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Inner frame for content
        self.inner = tk.Frame(self.canvas, bg=colors.background)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.inner,
            anchor=tk.NW
        )
        
        # Bind resize
        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Touch scrolling
        self.canvas.bind("<Button-1>", self._on_touch_start)
        self.canvas.bind("<B1-Motion>", self._on_touch_move)
        
        self._touch_y = 0
    
    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_touch_start(self, event):
        self._touch_y = event.y
    
    def _on_touch_move(self, event):
        delta = self._touch_y - event.y
        self.canvas.yview_scroll(int(delta/20), "units")
        self._touch_y = event.y
    
    def scroll_to_bottom(self):
        """Scroll to bottom of content"""
        self.canvas.yview_moveto(1.0)


class ProgressRing(Canvas):
    """
    Circular progress indicator
    """
    
    def __init__(
        self,
        parent,
        size: int = 40,
        thickness: int = 4,
        bg_color: str = None,
        fg_color: str = None,
        **kwargs
    ):
        colors = Theme.colors
        self.size = size
        self.thickness = thickness
        self.bg_ring = bg_color or colors.surface_light
        self.fg_ring = fg_color or colors.accent_primary
        self.progress = 0
        
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=colors.background,
            highlightthickness=0,
            **kwargs
        )
        
        self._draw()
    
    def _draw(self):
        self.delete("all")
        pad = self.thickness // 2 + 2
        
        # Background ring
        self.create_arc(
            pad, pad, self.size-pad, self.size-pad,
            start=90, extent=-360,
            outline=self.bg_ring,
            width=self.thickness,
            style=tk.ARC
        )
        
        # Progress ring
        extent = -360 * (self.progress / 100)
        self.create_arc(
            pad, pad, self.size-pad, self.size-pad,
            start=90, extent=extent,
            outline=self.fg_ring,
            width=self.thickness,
            style=tk.ARC
        )
    
    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress = max(0, min(100, value))
        self._draw()

