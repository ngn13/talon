import os
import sys
import ctypes
import shutil
import logging
from components.resource_utils import get_resource_path

logger = logging.getLogger(__name__)

def set_wallpaper(image_path: str) -> None:
    try:
        success = ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
        if success:
            logger.info("Wallpaper set successfully")
        else:
            logger.error("SystemParametersInfoW returned failure")
    except OSError as e:
        logger.exception("OS error setting wallpaper: %s", e)
    except Exception as e:
        logger.exception("Unexpected error setting wallpaper: %s", e)

def main() -> None:
    logger.info("apply_background started")
    source_image = get_resource_path("DesktopBackground.png")
    if not os.path.exists(source_image):
        logger.error("DesktopBackground.png not found at %s", source_image)
        return
    pictures = os.path.join(os.path.expanduser("~"), "Pictures")
    os.makedirs(pictures, exist_ok=True)
    dest = os.path.join(pictures, "DesktopBackground.png")
    try:
        shutil.copy2(source_image, dest)
        logger.info("Copied %s → %s", source_image, dest)
    except (OSError, IOError) as e:
        logger.exception("Failed to copy background: %s", e)
        return
    set_wallpaper(dest)

if __name__ == "__main__":
    main()