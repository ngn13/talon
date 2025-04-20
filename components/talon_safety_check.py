""" Import the necessary modules for the program to work """
import subprocess
import os
import sys
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

class _SafetyPopupHandler(QObject):
    warning = pyqtSignal(str, str)

def _on_warning(title: str, msg: str):
    QMessageBox.warning(None, title, msg)
    sys.exit(1)

_popup_handler = _SafetyPopupHandler()
_popup_handler.warning.connect(_on_warning)

def show_warning_popup(title: str, message: str):
    _popup_handler.warning.emit(title, message)

def run_safety_checks():
    success_count = 0
    for _ in range(3):
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "code.ravendevteam.org"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                success_count += 1
        except Exception:
            pass
    if success_count == 3:
        code_source_network_check = 0
    elif success_count == 0:
        code_source_network_check = 2
    else:
        code_source_network_check = 1
    try:
        result = subprocess.run(
            ["winget", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        is_winget_installed = 1 if result.returncode == 0 else 0
    except Exception:
        is_winget_installed = 0
    subprocess.run(
        ["taskkill", "/F", "/IM", "OneDriveSetup.exe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "OneDrive.exe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if code_source_network_check == 1:
        show_warning_popup(
            "Unstable Internet Connection",
            (
                "Your internet connection is unstable and mostly failed the network check. "
                "Please check your connection before running Talon."
            )
        )
    elif code_source_network_check == 2:
        show_warning_popup(
            "No Internet Connection",
            (
                "You do not have an internet connection. A common reason for this is an incorrect "
                "system time set. Please verify your internet connection and system time before "
                "running Talon."
            )
        )
    if is_winget_installed == 0:
        show_warning_popup(
            "Winget Not Available",
            (
                "Winget, a crucial component for Talon, is not available on your system. "
                "Winget is typically preinstalled on Windows. Please install Winget before "
                "running Talon."
            )
        )