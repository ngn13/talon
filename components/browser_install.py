import subprocess
import logging
import shutil
from components.debloat_windows import ScriptError

logger = logging.getLogger(__name__)

WINGET_MAP = {
    "Chrome":    "Google.Chrome",
    "Brave":     "Brave.Brave",
    "Firefox":   "Mozilla.Firefox",
    "Librewolf": "Librewolf.Librewolf",
    "Edge":      "Microsoft.Edge"
}

CHOCO_MAP = {
    "Chrome":    "googlechrome",
    "Brave":     "brave",
    "Firefox":   "firefox",
    "Librewolf": "librewolf",
    "Edge":      "microsoft-edge"
}

def install_browser(selected_browser: str):
    if selected_browser not in WINGET_MAP:
        msg = f"Unknown browser selected: {selected_browser}"
        logger.error(msg)
        raise ScriptError(msg)
    win_id = WINGET_MAP[selected_browser]
    logger.info("Installing %s via Winget (%s)", selected_browser, win_id)
    try:
        subprocess.run(
            ["winget", "install", win_id, "--silent",
             "--accept-package-agreements", "--accept-source-agreements"],
            check=True
        )
        logger.info("%s installed successfully via Winget", selected_browser)
        return
    except subprocess.CalledProcessError as e:
        logger.warning("Winget install failed for %s: %s", selected_browser, e)
    if shutil.which("choco") is None:
        msg = f"Chocolatey not found; cannot fallback for {selected_browser}"
        logger.error(msg)
        raise ScriptError(f"Winget failed and Chocolatey unavailable: {selected_browser}")
    if selected_browser not in CHOCO_MAP:
        msg = f"No Chocolatey mapping for {selected_browser}"
        logger.error(msg)
        raise ScriptError(msg)
    choco_id = CHOCO_MAP[selected_browser]
    logger.info("Attempting to install %s via Chocolatey (%s)", selected_browser, choco_id)
    try:
        subprocess.run(
            ["choco", "install", choco_id, "-y"],
            check=True
        )
        logger.info("%s installed successfully via Chocolatey", selected_browser)
    except subprocess.CalledProcessError as e:
        msg = f"Chocolatey install failed for {selected_browser}: {e}"
        logger.error(msg)
        raise ScriptError(msg)