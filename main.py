"""
SideDock — Always-On-Top Clock Overlay for Windows

Displays the current time as a transparent, non-interactive overlay.
The window is click-through (WS_EX_TRANSPARENT) so it never interferes
with anything underneath. Controlled entirely via the system tray icon.
"""

import tkinter as tk
import time
import ctypes
import sys
import os

from settings import SettingsDialog, load_config, save_config
from tray import TrayManager

# ── Win32 constants for click-through window ──
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080   # Hides from Alt-Tab / taskbar
WS_EX_NOACTIVATE = 0x08000000   # Never steals focus

user32 = ctypes.windll.user32
GetWindowLong = user32.GetWindowLongW
SetWindowLong = user32.SetWindowLongW


# ── Transparency color key ──
# This exact color becomes fully transparent on Windows.
TRANSPARENT_COLOR = "#010101"


class SideDock:
    """Main application — transparent always-on-top clock overlay."""

    def __init__(self):
        self.config = load_config()
        self.settings_window = None

        # ── Root window setup ──
        self.root = tk.Tk()
        self.root.title("SideDock")
        self.root.overrideredirect(True)          # Borderless
        self.root.attributes("-topmost", True)     # Always on top
        self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.configure(bg=TRANSPARENT_COLOR)

        # ── Clock label ──
        self.clock_label = tk.Label(
            self.root,
            text="",
            bg=TRANSPARENT_COLOR,
            font=("Segoe UI Light", self.config["font_size"]),
            fg=self._effective_color(),
            anchor="center",
        )
        self.clock_label.pack(expand=True, fill="both")

        # ── Position ──
        self._apply_position()

        # ── Make click-through (after window is mapped) ──
        self.root.update_idletasks()
        self.root.after(50, self._make_click_through)

        # ── System tray ──
        self.tray = TrayManager(
            on_options=self._open_options,
            on_quit=self._quit,
        )
        self.tray.start()

        # ── Start clock ──
        self._tick()

    def _make_click_through(self):
        """Set Win32 extended styles so the window is fully non-interactive."""
        hwnd = int(self.root.winfo_id())

        # Walk up to the real top-level HWND (tkinter wraps in a frame)
        hwnd = user32.GetParent(hwnd) or hwnd

        style = GetWindowLong(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        SetWindowLong(hwnd, GWL_EXSTYLE, style)

        # Re-assert topmost after style change
        self.root.attributes("-topmost", True)

    def _apply_position(self):
        """Position the window. Defaults to top-right if no saved position."""
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        # Estimate label size based on font
        estimated_w = self.config["font_size"] * 5
        estimated_h = int(self.config["font_size"] * 1.6)

        px = self.config.get("pos_x")
        py = self.config.get("pos_y")

        if px is None or py is None:
            # Default: top-right corner with some margin
            px = sw - estimated_w - 32
            py = 32

        self.root.geometry(f"{estimated_w}x{estimated_h}+{px}+{py}")

    def _effective_color(self):
        """
        Compute the displayed text color by blending the chosen color
        toward TRANSPARENT_COLOR based on opacity.

        Since tkinter on Windows doesn't support per-pixel alpha on text,
        we simulate transparency by interpolating the RGB values toward
        the transparent key color.
        """
        opacity = self.config["opacity"]
        hex_color = self.config["color"]

        # Parse hex
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        # Parse transparent key
        tr = int(TRANSPARENT_COLOR[1:3], 16)
        tg = int(TRANSPARENT_COLOR[3:5], 16)
        tb = int(TRANSPARENT_COLOR[5:7], 16)

        # Lerp toward transparent color
        er = int(tr + (r - tr) * opacity)
        eg = int(tg + (g - tg) * opacity)
        eb = int(tb + (b - tb) * opacity)

        # Ensure we never land exactly on the transparent key color
        result = f"#{er:02x}{eg:02x}{eb:02x}"
        if result == TRANSPARENT_COLOR:
            return "#020202"
        return result

    def _tick(self):
        """Update the clock every 500ms."""
        now = time.strftime(self.config.get("time_format", "%H:%M:%S"))
        self.clock_label.config(text=now)
        self.root.after(500, self._tick)

    # ── Tray callbacks (called from tray thread → must schedule on main thread) ──

    def _open_options(self):
        """Open the settings dialog (thread-safe via root.after)."""
        self.root.after(0, self._show_settings)

    def _show_settings(self):
        """Create and display the settings window."""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        self.settings_window = SettingsDialog(
            self.root, self.config.copy(), self._on_settings_changed
        )

    def _on_settings_changed(self, new_config):
        """Apply new settings from the options dialog in real-time."""
        self.config = new_config

        # Update font
        self.clock_label.config(
            font=("Segoe UI Light", self.config["font_size"]),
            fg=self._effective_color(),
        )

        # Reposition / resize
        self._apply_position()

        # Re-assert click-through (style can get reset on geometry changes)
        self.root.after(50, self._make_click_through)

    def _quit(self):
        """Clean shutdown from tray → Close."""
        self.root.after(0, self._shutdown)

    def _shutdown(self):
        self.tray.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SideDock()
    app.run()
