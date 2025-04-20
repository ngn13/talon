""" Import necessary modules for the program to work """
import sys
import ctypes
import os
import tempfile
import subprocess
import requests
import shutil
import logging
import hashlib
import winreg
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop

logger = logging.getLogger(__name__)

class ScriptError(Exception):
    pass

def log(message: str):
    """Log to file and stdout."""
    logging.info(message)
    print(message)

def is_admin() -> bool:
    """Returns True if running with elevation."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)

class _AskContinueHandler(QObject):
    askSignal = pyqtSignal(str, str)
    askResult = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.askSignal.connect(self._on_ask)

    @pyqtSlot(str, str)
    def _on_ask(self, title: str, message: str):
        choice = QMessageBox.question(
            None, title, message,
            QMessageBox.Yes | QMessageBox.No
        )
        self.askResult.emit(choice == QMessageBox.Yes)

_ask_handler = _AskContinueHandler()

def _ask_continue(title: str, message: str) -> bool:
    loop = QEventLoop()
    result = {"choice": False}

    def _on_result(choice: bool):
        result["choice"] = choice
        loop.quit()

    _ask_handler.askResult.connect(_on_result)
    _ask_handler.askSignal.emit(title, message)
    loop.exec_()
    _ask_handler.askResult.disconnect(_on_result)
    return result["choice"]

def apply_registry_changes():
    log("Applying registry changes...")
    registry_modifications = [
        # Align taskbar to the left
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
         "TaskbarAl", winreg.REG_DWORD, 0),

        # Dark mode for apps
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
         "AppsUseLightTheme", winreg.REG_DWORD, 0),

        # Dark mode for system UI
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
         "SystemUsesLightTheme", winreg.REG_DWORD, 0),

        # Disable Game DVR UI popup
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
         "AppCaptureEnabled", winreg.REG_DWORD, 0),

        # Disable Game DVR policy (reduces FPS drops)
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\PolicyManager\default\ApplicationManagement\AllowGameDVR",
         "Value", winreg.REG_DWORD, 0),

        # Remove menu delay
        (winreg.HKEY_CURRENT_USER,
         r"Control Panel\Desktop",
         "MenuShowDelay", winreg.REG_SZ, "0"),

        # Disable window animations
        (winreg.HKEY_CURRENT_USER,
         r"Control Panel\Desktop\WindowMetrics",
         "MinAnimate", winreg.REG_DWORD, 0),

        # Reduce tooltip hover time
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
         "ExtendedUIHoverTime", winreg.REG_DWORD, 1),

        # Always show file extensions
        (winreg.HKEY_CURRENT_USER,
         r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
         "HideFileExt", winreg.REG_DWORD, 0),
    ]
    for root, path, name, val_type, val in registry_modifications:
        try:
            with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, val_type, val)
                log(f"Applied {name} to {path}")
        except Exception as e:
            log(f"Failed to modify {name} in {path}: {e}")
    log("Restarting Explorer to apply registry tweaks...")
    subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["start", "explorer.exe"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log("Explorer restarted.")

SCRIPT_SPECS = {
    "edge_vanisher": {
        "url": "https://code.ravendevteam.org/talon/edge_vanisher.ps1",
        "hash": "fa3935e37a7116d9e51696de7f72f5067ae46987eacfcfe7c25c1ed6350355ba",
        "filename": "edge_vanisher.ps1"
    },
    "uninstall_oo": {
        "url": "https://code.ravendevteam.org/talon/uninstall_oo.ps1",
        "hash": "b5cd6e63ab023c7fe8d28674e4433aff98c820d0d6d180a10ae7b5549a7b2640",
        "filename": "uninstall_oo.ps1"
    },
    "update_policy_changer": {
        "url": "https://code.ravendevteam.org/talon/update_policy_changer.ps1",
        "hash": "a6bfc189422a1e393a1f849b9f24b9880298e0fba1f66f1f53b577e61472f2df",
        "filename": "UpdatePolicyChanger.ps1"
    },
}

def _download_and_verify(spec_key):
    spec = SCRIPT_SPECS[spec_key]
    url, expected_hash, filename = spec["url"], spec["hash"], spec["filename"]
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, filename)

    log(f"Downloading {filename} from {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log(f"Download error for {filename}: {e}")
        if not _ask_continue(
            "Download Failed",
            f"Could not download {filename}:\n{e}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
        return None

    content = resp.content
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash.lower() != expected_hash.lower():
        log(f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
        if not _ask_continue(
            "Script Verification Failed",
            f"Hash mismatch for {filename}:\nExpected {expected_hash}\nGot      {actual_hash}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
    try:
        with open(script_path, "wb") as f:
            f.write(content)
        log(f"Saved {filename} to {script_path}")
    except Exception as e:
        log(f"Failed to write {filename}: {e}")
        if not _ask_continue(
            "File Write Error",
            f"Could not save {filename}:\n{e}\n\nContinue installation anyway?"
        ):
            sys.exit(1)

    return script_path

def run_edge_vanisher():
    log("Starting Edge Vanisher")
    script = _download_and_verify("edge_vanisher")
    if not script:
        return run_oouninstall()

    cmd = f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script}'; exit"
    log(f"Executing PowerShell: {cmd}")
    proc = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        log(f"Edge Vanisher failed: {proc.stderr or proc.stdout}")
        if not _ask_continue(
            "Edge Vanisher Error",
            f"Edge Vanisher script returned error:\n{proc.stderr or proc.stdout}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
    else:
        log("Edge Vanisher completed successfully")
    return run_oouninstall()

def run_oouninstall():
    log("Starting Office Online Uninstall")
    script = _download_and_verify("uninstall_oo")
    if not script:
        return run_tweaks()

    cmd = f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script}'"
    log(f"Executing PowerShell: {cmd}")
    proc = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        log(f"OO Uninstall failed: {proc.stderr or proc.stdout}")
        if not _ask_continue(
            "Office Online Uninstall Error",
            f"OO uninstall script returned error:\n{proc.stderr or proc.stdout}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
    else:
        log("OO Uninstall completed successfully")
    return run_tweaks()

def run_tweaks():
    log("Running CTT WinUtil tweaks")
    try:
        if hasattr(sys, "_MEIPASS"):
            json_path = os.path.join(sys._MEIPASS, "barebones.json")
        else:
            json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "barebones.json"))
        log(f"Using config: {json_path}")

        temp_dir = tempfile.gettempdir()
        log_file = os.path.join(temp_dir, "cttwinutil.log")

        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"$ErrorActionPreference='SilentlyContinue'; iex \"& {{ $(irm christitus.com/win) }} -Config '{json_path}' -Run\" *>&1 | Tee-Object -FilePath '{log_file}'"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                log(f"CTT: {line.strip()}")
                if "Tweaks are Finished" in line:
                    break

        proc.wait()
        if proc.returncode != 0:
            log(f"CTT WinUtil exited with {proc.returncode}")
            if not _ask_continue(
                "CTT WinUtil Error",
                f"CTT WinUtil returned code {proc.returncode}. Check logs?\n\nContinue installation anyway?"
            ):
                sys.exit(1)
    except Exception as e:
        log(f"Error running CTT WinUtil: {e}")
        if not _ask_continue(
            "CTT WinUtil Exception",
            f"Exception during tweaks:\n{e}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
    return run_winconfig()

def run_winconfig():
    log("Running Raphi’s Win11Debloat")
    try:
        url = "https://win11debloat.raphi.re/"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, "Win11Debloat.ps1")
        log(f"Downloading Raphi script from {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(script_path, "wb") as f:
            f.write(resp.content)
        cmd = (
            f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script_path}' "
            "-Silent -RemoveApps -RemoveGamingApps -DisableTelemetry "
            "-DisableBing -DisableSuggestions -DisableLockscreenTips -RevertContextMenu "
            "-TaskbarAlignLeft -HideSearchTb -DisableWidgets -DisableCopilot -ExplorerToThisPC "
            "-ClearStartAllUsers -DisableDVR -DisableStartRecommended -ExplorerToThisPC "
            "-DisableMouseAcceleration"
        )
        log(f"Executing PowerShell: {cmd}")
        proc = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if proc.returncode != 0:
            log(f"Win11Debloat failed: {proc.stderr or proc.stdout}")
            if not _ask_continue(
                "Win11Debloat Error",
                f"Raphi’s script returned error:\n{proc.stderr or proc.stdout}\n\nContinue installation anyway?"
            ):
                sys.exit(1)
    except Exception as e:
        log(f"Error running Win11Debloat: {e}")
        if not _ask_continue(
            "Win11Debloat Exception",
            f"Exception during Win11Debloat:\n{e}\n\nContinue installation anyway?"
        ):
            sys.exit(1)
    return run_updatepolicychanger()

def run_updatepolicychanger():
    log("Running UpdatePolicyChanger")
    script = _download_and_verify("update_policy_changer")
    if not script:
        return finalize_installation()

    cmd = f"Set-ExecutionPolicy Bypass -Scope Process -Force; & '{script}'; exit"
    log(f"Executing PowerShell: {cmd}")
    proc = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    if proc.returncode != 0:
        log(f"UpdatePolicyChanger failed: {proc.stderr or proc.stdout}")
        if not _ask_continue(
            "UpdatePolicyChanger Error",
            f"Script returned error:\n{proc.stderr or proc.stdout}\n\nContinue installation anyway?"
        ):
            sys.exit(1)

    return finalize_installation()

def finalize_installation():
    log("Installation complete. Restarting system…")
    try:
        subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
    except Exception as e:
        log(f"Restart failed: {e}")
        if not _ask_continue(
            "Restart Failed",
            f"Could not restart automatically:\n{e}\n\nYou will need to restart manually."
        ):
            sys.exit(1)

def run_debloat():
    apply_registry_changes()
    run_edge_vanisher()
    run_oouninstall()
    run_tweaks()
    run_winconfig()
    run_updatepolicychanger()
    finalize_installation()