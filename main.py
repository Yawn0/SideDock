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
import psutil

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

        # ── Track network stats ──
        self.last_net_bytes = 0
        self.last_net_time = time.time()
        try:
            self.last_net_bytes = psutil.net_io_counters().bytes_recv
        except Exception:
            pass

        # ── Root window setup ──
        self.root = tk.Tk()
        self.root.title("SideDock")
        self.root.overrideredirect(True)          # Borderless
        self.root.attributes("-topmost", True)     # Always on top
        self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.configure(bg=TRANSPARENT_COLOR)

        # ── Main container frame ──
        self.container_frame = tk.Frame(self.root, bg=TRANSPARENT_COLOR)
        self.container_frame.pack(expand=True, fill="both")

        # ── Stats frame ──
        self.stats_frame = tk.Frame(self.container_frame, bg=TRANSPARENT_COLOR)
        
        effective_color = self._effective_color()
        stats_font = ("Segoe UI", max(9, int(self.config["font_size"] * 0.25)))
        
        self.cpu_label = tk.Label(
            self.stats_frame,
            text="CPU: 0%",
            bg=TRANSPARENT_COLOR,
            font=stats_font,
            fg=effective_color,
            anchor="w",
        )
        self.cpu_label.pack(fill="x", expand=True)

        self.ram_label = tk.Label(
            self.stats_frame,
            text="RAM: 0%",
            bg=TRANSPARENT_COLOR,
            font=stats_font,
            fg=effective_color,
            anchor="w",
        )
        self.ram_label.pack(fill="x", expand=True)

        self.net_label = tk.Label(
            self.stats_frame,
            text="DL: 0.0 MB/s",
            bg=TRANSPARENT_COLOR,
            font=stats_font,
            fg=effective_color,
            anchor="w",
        )
        self.net_label.pack(fill="x", expand=True)

        # ── Divider line ──
        self.divider = tk.Frame(
            self.container_frame,
            width=2,
            bg=effective_color,
        )

        # ── Clock label ──
        self.clock_label = tk.Label(
            self.container_frame,
            text="",
            bg=TRANSPARENT_COLOR,
            font=("Segoe UI Light", self.config["font_size"]),
            fg=effective_color,
            anchor="e",
        )

        # ── Layout arrangement ──
        self._arrange_layout()

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

    def _arrange_layout(self):
        """Pack or unpack stats elements according to configuration."""
        self.stats_frame.pack_forget()
        self.divider.pack_forget()
        self.clock_label.pack_forget()

        if self.config.get("show_stats", True):
            self.stats_frame.pack(side="left", fill="y", padx=(12, 0), pady=4)
            self.divider.pack(side="left", fill="y", padx=16, pady=8)
            self.clock_label.pack(side="right", expand=True, fill="both", padx=(0, 12))
            self.clock_label.config(anchor="e")
        else:
            self.clock_label.pack(side="right", expand=True, fill="both", padx=(0, 12))
            self.clock_label.config(anchor="e")

    def _apply_position(self):
        """Position the window. Defaults to top-right if no saved position."""
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        # Always use a stable width and height to keep the clock right-aligned and prevent shifts
        font_size = self.config["font_size"]
        estimated_w = int(font_size * 7.8) + 60
        estimated_h = max(60, int(font_size * 1.6))

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
        """Update the clock and stats every 500ms."""
        # Update clock
        now = time.strftime(self.config.get("time_format", "%H:%M:%S"))
        self.clock_label.config(text=now)

        # Update stats if enabled
        if self.config.get("show_stats", True):
            try:
                # CPU usage
                cpu_pct = psutil.cpu_percent(interval=None)
                self.cpu_label.config(text=f"CPU: {int(cpu_pct)}%")

                # RAM usage
                ram = psutil.virtual_memory()
                self.ram_label.config(text=f"RAM: {int(ram.percent)}%")

                # Download speed calculation
                current_time = time.time()
                net_io = psutil.net_io_counters()
                current_bytes = net_io.bytes_recv

                elapsed_time = current_time - self.last_net_time
                if elapsed_time > 0:
                    bytes_diff = current_bytes - self.last_net_bytes
                    mb_s = (bytes_diff / (1024 * 1024)) / elapsed_time
                    if mb_s < 0:
                        mb_s = 0.0
                    self.net_label.config(text=f"DL: {mb_s:.1f} MB/s")

                self.last_net_bytes = current_bytes
                self.last_net_time = current_time
            except Exception:
                pass

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

        effective_color = self._effective_color()
        stats_font = ("Segoe UI", max(9, int(self.config["font_size"] * 0.25)))

        # Update clock font/color
        self.clock_label.config(
            font=("Segoe UI Light", self.config["font_size"]),
            fg=effective_color,
        )

        # Update stats font/color
        self.cpu_label.config(font=stats_font, fg=effective_color)
        self.ram_label.config(font=stats_font, fg=effective_color)
        self.net_label.config(font=stats_font, fg=effective_color)

        # Update divider color
        self.divider.config(bg=effective_color)

        # Update layout packing (show/hide stats)
        self._arrange_layout()

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
