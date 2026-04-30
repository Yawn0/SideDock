"""
SideDock — Settings Dialog
Options window with transparency, color, and font size controls.
Changes apply in real-time and persist to config.json.
"""

import tkinter as tk
from tkinter import colorchooser
import json
import os

import sys
from startup import is_startup_enabled, set_startup

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")


def load_config():
    """Load settings from config.json, returning defaults if missing."""
    defaults = {
        "opacity": 0.5,
        "color": "#FFFFFF",
        "font_size": 48,
        "pos_x": None,
        "pos_y": None,
        "time_format": "%H:%M:%S",
    }
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            defaults.update(data)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return defaults


def save_config(config):
    """Persist settings to config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


class SettingsDialog(tk.Toplevel):
    """Options dialog — transparency slider, color picker, font size selector."""

    def __init__(self, parent, config, on_change_callback):
        super().__init__(parent)
        self.config = config
        self.on_change = on_change_callback

        self.title("SideDock Options")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg="#1e1e2e")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Prevent multiple instances
        self.grab_set()

        self._build_ui()
        self._center_on_screen()

    def _center_on_screen(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sx = self.winfo_screenwidth()
        sy = self.winfo_screenheight()
        x = (sx - w) // 2
        y = (sy - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}
        label_style = {"bg": "#1e1e2e", "fg": "#cdd6f4", "font": ("Segoe UI", 11)}
        heading_style = {"bg": "#1e1e2e", "fg": "#89b4fa", "font": ("Segoe UI", 13, "bold")}

        # --- Title ---
        tk.Label(self, text="⚙  SideDock Options", **heading_style).pack(
            pady=(16, 8), padx=16, anchor="w"
        )

        separator = tk.Frame(self, height=1, bg="#45475a")
        separator.pack(fill="x", padx=16, pady=(0, 8))

        # --- Transparency ---
        tk.Label(self, text="Text Opacity", **label_style).pack(anchor="w", **pad)

        self.opacity_var = tk.DoubleVar(value=self.config["opacity"])
        opacity_frame = tk.Frame(self, bg="#1e1e2e")
        opacity_frame.pack(fill="x", padx=16)

        self.opacity_label = tk.Label(
            opacity_frame,
            text=f"{int(self.config['opacity'] * 100)}%",
            bg="#1e1e2e",
            fg="#a6adc8",
            font=("Segoe UI", 10),
            width=5,
        )
        self.opacity_label.pack(side="right")

        self.opacity_slider = tk.Scale(
            opacity_frame,
            from_=0.05,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.opacity_var,
            command=self._on_opacity_change,
            bg="#1e1e2e",
            fg="#cdd6f4",
            troughcolor="#313244",
            highlightthickness=0,
            showvalue=False,
            length=250,
            activebackground="#89b4fa",
            sliderrelief="flat",
        )
        self.opacity_slider.pack(side="left", fill="x", expand=True)

        # --- Color ---
        tk.Label(self, text="Text Color", **label_style).pack(anchor="w", **pad)

        color_frame = tk.Frame(self, bg="#1e1e2e")
        color_frame.pack(fill="x", padx=16)

        self.color_preview = tk.Frame(
            color_frame, width=32, height=32, bg=self.config["color"], relief="solid", bd=1
        )
        self.color_preview.pack(side="left")
        self.color_preview.pack_propagate(False)

        self.color_hex_label = tk.Label(
            color_frame,
            text=self.config["color"],
            bg="#1e1e2e",
            fg="#a6adc8",
            font=("Consolas", 10),
        )
        self.color_hex_label.pack(side="left", padx=(8, 0))

        color_btn = tk.Button(
            color_frame,
            text="Choose Color",
            command=self._pick_color,
            bg="#45475a",
            fg="#cdd6f4",
            activebackground="#585b70",
            activeforeground="#cdd6f4",
            relief="flat",
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=12,
            pady=4,
        )
        color_btn.pack(side="right")

        # --- Font Size ---
        tk.Label(self, text="Font Size", **label_style).pack(anchor="w", **pad)

        size_frame = tk.Frame(self, bg="#1e1e2e")
        size_frame.pack(fill="x", padx=16)

        self.size_label = tk.Label(
            size_frame,
            text=f"{self.config['font_size']}pt",
            bg="#1e1e2e",
            fg="#a6adc8",
            font=("Segoe UI", 10),
            width=5,
        )
        self.size_label.pack(side="right")

        self.size_var = tk.IntVar(value=self.config["font_size"])
        self.size_slider = tk.Scale(
            size_frame,
            from_=16,
            to=200,
            orient="horizontal",
            variable=self.size_var,
            command=self._on_size_change,
            bg="#1e1e2e",
            fg="#cdd6f4",
            troughcolor="#313244",
            highlightthickness=0,
            showvalue=False,
            length=250,
            activebackground="#89b4fa",
            sliderrelief="flat",
        )
        self.size_slider.pack(side="left", fill="x", expand=True)

        # --- Position ---
        tk.Label(self, text="Position", **label_style).pack(anchor="w", **pad)

        pos_frame = tk.Frame(self, bg="#1e1e2e")
        pos_frame.pack(fill="x", padx=16)

        spinbox_style = {
            "bg": "#313244",
            "fg": "#cdd6f4",
            "buttonbackground": "#45475a",
            "insertbackground": "#cdd6f4",
            "highlightthickness": 0,
            "relief": "flat",
            "font": ("Consolas", 10),
            "width": 6,
        }

        tk.Label(pos_frame, text="X:", bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 10)).pack(
            side="left"
        )

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        default_x = self.config.get("pos_x") or (screen_w - 300)
        default_y = self.config.get("pos_y") or 32

        self.pos_x_var = tk.IntVar(value=default_x)
        pos_x_spin = tk.Spinbox(
            pos_frame,
            from_=0,
            to=screen_w,
            textvariable=self.pos_x_var,
            command=self._on_pos_change,
            **spinbox_style,
        )
        pos_x_spin.pack(side="left", padx=(4, 12))
        pos_x_spin.bind("<Return>", lambda e: self._on_pos_change())

        tk.Label(pos_frame, text="Y:", bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 10)).pack(
            side="left"
        )

        self.pos_y_var = tk.IntVar(value=default_y)
        pos_y_spin = tk.Spinbox(
            pos_frame,
            from_=0,
            to=screen_h,
            textvariable=self.pos_y_var,
            command=self._on_pos_change,
            **spinbox_style,
        )
        pos_y_spin.pack(side="left", padx=(4, 0))
        pos_y_spin.bind("<Return>", lambda e: self._on_pos_change())

        # --- Start with Windows ---
        separator2 = tk.Frame(self, height=1, bg="#45475a")
        separator2.pack(fill="x", padx=16, pady=(12, 4))

        startup_frame = tk.Frame(self, bg="#1e1e2e")
        startup_frame.pack(fill="x", padx=16, pady=(4, 0))

        self.startup_var = tk.BooleanVar(value=is_startup_enabled())
        startup_cb = tk.Checkbutton(
            startup_frame,
            text="Start with Windows",
            variable=self.startup_var,
            command=self._on_startup_toggle,
            bg="#1e1e2e",
            fg="#cdd6f4",
            selectcolor="#313244",
            activebackground="#1e1e2e",
            activeforeground="#cdd6f4",
            font=("Segoe UI", 11),
            cursor="hand2",
            highlightthickness=0,
            bd=0,
        )
        startup_cb.pack(side="left")

        # --- Bottom padding ---
        tk.Frame(self, height=16, bg="#1e1e2e").pack()

    def _on_opacity_change(self, val):
        opacity = float(val)
        self.config["opacity"] = opacity
        self.opacity_label.config(text=f"{int(opacity * 100)}%")
        self._apply()

    def _pick_color(self):
        result = colorchooser.askcolor(
            color=self.config["color"], title="Pick Text Color", parent=self
        )
        if result and result[1]:
            hex_color = result[1]
            self.config["color"] = hex_color
            self.color_preview.config(bg=hex_color)
            self.color_hex_label.config(text=hex_color)
            self._apply()

    def _on_size_change(self, val):
        size = int(val)
        self.config["font_size"] = size
        self.size_label.config(text=f"{size}pt")
        self._apply()

    def _on_pos_change(self):
        self.config["pos_x"] = self.pos_x_var.get()
        self.config["pos_y"] = self.pos_y_var.get()
        self._apply()

    def _on_startup_toggle(self):
        set_startup(self.startup_var.get())

    def _apply(self):
        """Push changes to the main app and save to disk."""
        save_config(self.config)
        if self.on_change:
            self.on_change(self.config)

    def _on_close(self):
        self.grab_release()
        self.destroy()
