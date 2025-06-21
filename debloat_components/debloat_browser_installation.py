import os
import sys
import json
import tempfile
import subprocess
from utilities.util_logger import logger
from utilities.util_error_popup import show_error_popup
from utilities.util_powershell_handler import run_powershell_command



def load_choice() -> str:
    temp_dir = os.environ.get('TEMP', tempfile.gettempdir())
    choice_file = os.path.join(temp_dir, 'talon', 'browser_choice.json')
    if not os.path.exists(choice_file):
        raise FileNotFoundError(f"Browser choice file not found: {choice_file}")
    with open(choice_file, 'r') as f:
        data = json.load(f)
    browser = data.get('browser')
    if not browser:
        raise ValueError(f"No 'browser' key in {choice_file}")
    return browser



def ensure_chocolatey():
    try:
        subprocess.run(
            ["choco", "-v"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info("Chocolatey already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Chocolatey not found. Installing now...")
        install_cmd = (
            "Set-ExecutionPolicy Bypass -Scope Process -Force; "
            "[System.Net.ServicePointManager]::SecurityProtocol = "
            "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
            "iex ((New-Object System.Net.WebClient).DownloadString("
            "'https://community.chocolatey.org/install.ps1'))"
        )
        logger.info(f"Running install command: {install_cmd}")
        try:
            run_powershell_command(install_cmd)
            logger.info("✔ Chocolatey installed successfully.")
        except Exception as e:
            logger.error(f"Failed to install Chocolatey: {e}")
            show_error_popup(f"Failed to install Chocolatey:\n{e}", allow_continue=False)
            sys.exit(1)



def _get_choco_exe() -> str:
    env_path = os.environ.get("ChocolateyInstall")
    if env_path:
        choco = os.path.join(env_path, "bin", "choco.exe")
        if os.path.exists(choco):
            return choco
    default_path = os.path.join(
        os.environ.get("ProgramData", r"C:\\ProgramData"),
        "chocolatey",
        "bin",
        "choco.exe",
    )
    return default_path if os.path.exists(default_path) else "choco"



def install_browser(pkg_id: str):
    choco_exe = _get_choco_exe()
    logger.info(f"Installing browser via Chocolatey: {pkg_id}")
    try:
        subprocess.check_call([choco_exe, "install", pkg_id, "-y"])
        logger.info(f"✔ Successfully installed browser: {pkg_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Chocolatey exited with code {e.returncode} for {pkg_id}")
        show_error_popup(
            f"Failed to install browser '{pkg_id}'.\nChocolatey exited with code {e.returncode}.",
            allow_continue=False
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error installing {pkg_id}: {e}")
        show_error_popup(
            f"An unexpected error occurred while installing '{pkg_id}':\n{e}",
            allow_continue=False
        )
        sys.exit(1)



def main():
    try:
        pkg_id = load_choice()
        logger.info(f"Browser selected: {pkg_id}")
    except Exception as e:
        logger.error(f"Error reading browser choice: {e}")
        show_error_popup(f"Internal error reading browser choice:\n{e}", allow_continue=False)
        sys.exit(1)
    ensure_chocolatey()
    install_browser(pkg_id)



if __name__ == "__main__":
    main()
