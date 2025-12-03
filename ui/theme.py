"""
PiPhone-X Theme Configuration
Beautiful dark theme with neon accents
"""

from dataclasses import dataclass


@dataclass
class Colors:
    """Color palette for PiPhone-X"""
    # Base colors
    background: str = "#0a0a0f"
    surface: str = "#141420"
    surface_light: str = "#1e1e2e"
    
    # Text colors
    text_primary: str = "#e8e8f0"
    text_secondary: str = "#8888a0"
    text_muted: str = "#555566"
    
    # Accent colors
    accent_primary: str = "#00d4aa"      # Cyan/Teal
    accent_secondary: str = "#7c3aed"    # Purple
    accent_warning: str = "#f59e0b"      # Amber
    accent_danger: str = "#ef4444"       # Red
    accent_success: str = "#22c55e"      # Green
    
    # Call-specific colors
    call_active: str = "#22c55e"
    call_end: str = "#ef4444"
    call_incoming: str = "#00d4aa"
    
    # Status bar
    status_bg: str = "#0a0a0f"
    status_text: str = "#8888a0"
    
    # Keypad
    key_bg: str = "#1e1e2e"
    key_hover: str = "#2a2a3e"
    key_text: str = "#e8e8f0"
    key_special: str = "#00d4aa"
    
    # Tab bar
    tab_bg: str = "#0a0a0f"
    tab_active: str = "#00d4aa"
    tab_inactive: str = "#555566"


class Theme:
    """Theme configuration for PiPhone-X UI"""
    
    # Display dimensions (portrait mode for phone)
    WIDTH = 320
    HEIGHT = 480
    
    # Fonts
    FONT_FAMILY = "Helvetica"
    FONT_MONO = "Courier"
    
    FONT_TITLE = (FONT_FAMILY, 18, "bold")
    FONT_LARGE = (FONT_FAMILY, 16, "bold")
    FONT_MEDIUM = (FONT_FAMILY, 14)
    FONT_SMALL = (FONT_FAMILY, 12)
    FONT_TINY = (FONT_FAMILY, 10)
    
    FONT_KEYPAD = (FONT_FAMILY, 24, "bold")
    FONT_DISPLAY = (FONT_MONO, 28, "bold")
    FONT_DISPLAY_SMALL = (FONT_MONO, 20)
    
    # Spacing
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 16
    
    # Component sizes
    STATUS_BAR_HEIGHT = 24
    TAB_BAR_HEIGHT = 50
    BUTTON_HEIGHT = 48
    BUTTON_RADIUS = 8
    
    # Touch sizes (minimum 44x44 for touch)
    TOUCH_SIZE = 44
    KEY_SIZE = 60
    
    # Colors instance
    colors = Colors()
    
    @classmethod
    def get_style_config(cls) -> dict:
        """Get ttk style configuration"""
        return {
            'TFrame': {
                'background': cls.colors.background
            },
            'TLabel': {
                'background': cls.colors.background,
                'foreground': cls.colors.text_primary,
                'font': cls.FONT_MEDIUM
            },
            'TButton': {
                'background': cls.colors.surface_light,
                'foreground': cls.colors.text_primary,
                'font': cls.FONT_MEDIUM,
                'borderwidth': 0
            }
        }

