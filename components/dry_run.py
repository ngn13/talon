import logging
import requests
import hashlib
import shutil
import os
import subprocess as _sp
import winreg as _wr
import urllib.request

from talon_safety_check import run_safety_checks
from components.browser_install import WINGET_MAP, CHOCO_MAP
from components.resource_utils import get_resource_path
from components.debloat_windows import SCRIPT_SPECS, run_debloat
from components.windows_check import is_windows_11

logger = logging.getLogger(__name__)

class _DummyKey:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def SetValueEx(self, *args, **kwargs):
        pass

"""
Simulate the full Talon installation without making any real changes.
- Runs real safety checks (with ping stubbed)
- Verifies Windows version
- Downloads & hash-checks all PS scripts (real network)
- Checks browser installer availability
- Checks wallpaper file exists
- Simulates the debloat pipeline (registry, scripts, PowerShell, reboot) with no-ops for all destructive operations
- Returns (errors, report)
"""
def dry_run(selected_browser: str):
    errors = []
    logger.info("=== Dry‑Run: Starting prerequisite checks ===")
    orig_run = _sp.run
    def fake_run_for_safety(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd:
            op = cmd[0].lower()
            if op in ("ping", "taskkill", "powershell", "start", "shutdown"):
                logger.info("Dry‑run: would run subprocess: %r", cmd)
                return _sp.CompletedProcess(cmd, 0)
        return orig_run(cmd, *args, **kwargs)
    _sp.run = fake_run_for_safety
    try:
        run_safety_checks()
    except SystemExit as e:
        errors.append(f"Safety check would exit (code {e.code})")
    except Exception as e:
        errors.append(f"Safety check error: {e}")
    finally:
        _sp.run = orig_run
    if not is_windows_11():
        errors.append("Not on Windows 11.")
    for key, spec in SCRIPT_SPECS.items():
        url, expected_hash = spec["url"], spec["hash"]
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                errors.append(f"{key}: HTTP {resp.status_code}")
            else:
                actual_hash = hashlib.sha256(resp.content).hexdigest()
                if actual_hash.lower() != expected_hash.lower():
                    errors.append(
                        f"{key}: hash mismatch (expected {expected_hash}, got {actual_hash})"
                    )
        except Exception as e:
            errors.append(f"{key}: download error: {e}")
    if not shutil.which("winget") and not shutil.which("choco"):
        errors.append("Neither winget nor choco detected for browser install.")
    else:
        if selected_browser not in WINGET_MAP:
            errors.append(f"No winget mapping for browser '{selected_browser}'")
        if selected_browser not in CHOCO_MAP:
            logger.info("No choco mapping for '%s'; winget only", selected_browser)
    wallpaper = get_resource_path("DesktopBackground.png")
    if not os.path.exists(wallpaper):
        errors.append(f"Missing wallpaper file: {wallpaper}")
    logger.info("=== Dry‑Run: Simulating debloat pipeline ===")
    _sp_orig      = _sp.run
    _wr_orig      = _wr.CreateKeyEx
    urlr_orig     = urllib.request.urlretrieve
    _wr.CreateKeyEx = lambda *args, **kwargs: _DummyKey()
    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd:
            op = cmd[0].lower()
            if op in ("ping", "taskkill", "powershell", "start", "shutdown"):
                logger.info("Dry‑run: would run subprocess: %r", cmd)
                return _sp.CompletedProcess(cmd, 0)
        return _sp_orig(cmd, *args, **kwargs)
    _sp.run = fake_run
    urllib.request.urlretrieve = lambda url, dest, reporthook=None: dest
    try:
        run_debloat()
        logger.info("Dry‑run: run_debloat() would complete cleanly")
    except SystemExit as e:
        errors.append(f"run_debloat() would exit (code {e.code})")
    except Exception as e:
        errors.append(f"run_debloat() error: {e}")
    finally:
        _sp.run                  = _sp_orig
        _wr.CreateKeyEx          = _wr_orig
        urllib.request.urlretrieve = urlr_orig
    if errors:
        report = "Dry‑run found issues:\n" + "\n".join(f" • {e}" for e in errors)
    else:
        report = "Dry‑run completed with no issues detected."
    logger.info("=== Dry‑Run: End ===")
    return errors, report