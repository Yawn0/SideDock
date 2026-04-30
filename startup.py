"""
SideDock — Windows Startup Manager
Add/remove SideDock from Windows startup via the registry.
"""

import winreg
import os
import sys

APP_NAME = "SideDock"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path():
    """Return the path to the running executable (works for both .py and .exe)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return sys.executable
    else:
        # Running as script — point to python + script
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'


def is_startup_enabled():
    """Check if SideDock is registered to start with Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable_startup():
    """Add SideDock to Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def disable_startup():
    """Remove SideDock from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return True  # Already not registered
    except OSError:
        return False


def set_startup(enabled):
    """Enable or disable startup based on boolean."""
    if enabled:
        return enable_startup()
    else:
        return disable_startup()
