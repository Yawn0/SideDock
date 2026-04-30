"""
SideDock — System Tray
Creates and manages the system tray icon with right-click context menu.
"""

import threading
from PIL import Image, ImageDraw, ImageFont
import pystray


def _create_tray_icon_image():
    """Generate a simple clock icon for the system tray (64x64)."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circle background
    margin = 4
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(30, 30, 46, 255),       # #1e1e2e
        outline=(137, 180, 250, 255),  # #89b4fa
        width=3,
    )

    # Clock hands
    cx, cy = size // 2, size // 2
    # Hour hand (short, pointing ~10 o'clock)
    draw.line([(cx, cy), (cx - 8, cy - 12)], fill=(205, 214, 244, 255), width=3)
    # Minute hand (long, pointing ~2 o'clock)
    draw.line([(cx, cy), (cx + 6, cy - 16)], fill=(205, 214, 244, 255), width=2)
    # Center dot
    draw.ellipse(
        [cx - 3, cy - 3, cx + 3, cy + 3],
        fill=(137, 180, 250, 255),
    )

    return img


class TrayManager:
    """Manages the system tray icon and its context menu."""

    def __init__(self, on_options, on_quit):
        self._on_options = on_options
        self._on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        """Start the tray icon in a background daemon thread."""
        menu = pystray.Menu(
            pystray.MenuItem("Options", self._handle_options),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Close", self._handle_quit),
        )

        self._icon = pystray.Icon(
            name="SideDock",
            icon=_create_tray_icon_image(),
            title="SideDock — Clock Overlay",
            menu=menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop and remove the tray icon."""
        if self._icon:
            self._icon.stop()

    def _handle_options(self, icon, item):
        if self._on_options:
            self._on_options()

    def _handle_quit(self, icon, item):
        if self._on_quit:
            self._on_quit()
