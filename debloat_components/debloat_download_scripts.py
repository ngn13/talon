import os
import sys
import tempfile
from utilities.util_logger import logger
from utilities.util_download_handler import download_file
from utilities.util_error_popup import show_error_popup



def main():
    scripts = {
        "edge_vanisher.ps1": "https://code.ravendevteam.org/talon/edge_vanisher.ps1",
        "uninstall_oo.ps1": "https://code.ravendevteam.org/talon/uninstall_oo.ps1",
        "update_policy_changer.ps1": "https://code.ravendevteam.org/talon/update_policy_changer.ps1",
        "update_policy_changer_pro.ps1": "https://code.ravendevteam.org/talon/update_policy_changer_pro.ps1",
    }
    temp_dir = os.environ.get('TEMP', tempfile.gettempdir())
    download_dir = os.path.join(temp_dir, 'talon')
    for name, url in scripts.items():
        logger.info(f"Downloading {url} -> {name}")
        if not download_file(url, dest_name=name):
            sys.exit(1)
        path = os.path.join(download_dir, name)
        if not os.path.exists(path):
            show_error_popup(
                f"Downloaded file not found:\n{path}", allow_continue=False
            )
            sys.exit(1)
        logger.info(f"Successfully downloaded {name}")
    logger.info("All debloat scripts downloaded successfully.")



if __name__ == "__main__":
    main()
