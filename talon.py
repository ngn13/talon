import os
import subprocess
import sys
import threading
import argparse
from screens import load as load_screen
from utilities.util_logger import logger
from utilities.util_error_popup import show_error_popup
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QEvent, QTimer, QMetaObject, Qt, Q_ARG
from utilities.util_admin_check import ensure_admin
import preinstall_components.pre_checks as pre_checks
import debloat_components.debloat_download_scripts as debloat_download_scripts
import debloat_components.debloat_execute_raven_scripts as debloat_execute_raven_scripts
import debloat_components.debloat_execute_external_scripts as debloat_execute_external_scripts
import debloat_components.debloat_browser_installation as debloat_browser_installation
import debloat_components.debloat_registry_tweaks as debloat_registry_tweaks
import debloat_components.debloat_configure_updates as debloat_configure_updates
import debloat_components.debloat_apply_background as debloat_apply_background
from ui_components.ui_base_full import UIBaseFull
from ui_components.ui_header_text import UIHeaderText
from ui_components.ui_title_text import UITitleText



DEBLOAT_STEPS = [
    (
        "download-scripts",
        "Downloading some necessary scripts... (1/8)",
        debloat_download_scripts.main,
    ),
    (
        "execute-raven-scripts",
        "Executing debloating scripts... (2/8)",
        debloat_execute_raven_scripts.main,
    ),
    (
        "browser-installation",
        "Installing your chosen browser... (3/8)",
        debloat_browser_installation.main,
    ),
    (
        "execute-external-scripts",
        "Debloating Windows... (4/8)",
        debloat_execute_external_scripts.main,
    ),
    (
        "registry-tweaks",
        "Making some visual tweaks... (6/8)",
        debloat_registry_tweaks.main,
    ),
    (
        "configure-updates",
        "Configuring Windows Update policies... (7/8)",
        debloat_configure_updates.main,
    ),
    (
        "apply-background",
        "Setting your desktop background... (8/8)",
        debloat_apply_background.main,
    ),
]



def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Talon installer")
    parser.add_argument(
        "--developer-mode",
        action="store_true",
        help="Run without the installing overlay",
    )
    for slug, _, _ in DEBLOAT_STEPS:
        dest = f"skip_{slug.replace('-', '_')}_step"
        parser.add_argument(
            f"--skip-{slug}-step",
            dest=dest,
            action="store_true",
            help=f"Skip the {slug.replace('-', ' ')} step",
        )
    return parser.parse_args(argv)



def run_screen(module_name: str):
    logger.debug(f"Launching screen: {module_name}")
    try:
        mod = load_screen(module_name)
    except ImportError:
        script_file = f"{module_name}.py"
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'screens',
            script_file
        )
        try:
            subprocess.run([sys.executable, script_path], check=True)
        except Exception as e:
            logger.error(f"Failed to launch screen {script_file}: {e}")
            show_error_popup(
                f"Failed to launch screen '{module_name}'.\n{e}",
                allow_continue=False,
            )
            sys.exit(1)
        return
    try:
        mod.main()
    except SystemExit:
        pass
    except Exception as e:
        logger.exception(f"Exception in screen '{module_name}': {e}")
        show_error_popup(
            f"An unexpected error occurred in screen '{module_name}'.\n{e}",
            allow_continue=False,
        )
        sys.exit(1)



def _build_install_ui():
    """Create the installation window and return (app, status_label)."""
    app = QApplication.instance() or QApplication(sys.argv)
    base = UIBaseFull()
    for overlay in base.overlays:
        overlay.setWindowOpacity(0.8)
    overlay = base.primary_overlay
    title_label = UITitleText("Installing Talon...", parent=overlay)
    UIHeaderText(
        "Please don't use your keyboard or mouse. You can watch as Talon works.",
        parent=overlay,
    )
    status_label = UIHeaderText("", parent=overlay, follow_parent_resize=False)

    class StatusResizer(QObject):
        
        def __init__(self, parent, label, bottom_margin):
            super().__init__(parent)
            self.parent = parent
            self.label = label
            self.bottom_margin = bottom_margin
            parent.installEventFilter(self)
            self._update_position()

        def eventFilter(self, obj, event):
            if obj is self.parent and event.type() == QEvent.Resize:
                self._update_position()
            return False

        def _update_position(self):
            w = self.parent.width()
            fm = self.label.fontMetrics()
            h = fm.height()
            y = self.parent.height() - self.bottom_margin - h
            self.label.setGeometry(0, y, w, h)

    StatusResizer(overlay, status_label, bottom_margin=title_label._top_margin)
    base.show()
    status_label.raise_()
    return app, status_label



def _update_status(label: UIHeaderText, message: str):
    if label is None:
        print(message)
    else:
        QMetaObject.invokeMethod(
            label,
            "setText",
            Qt.QueuedConnection,
            Q_ARG(str, message),
        )



def main(argv=None):
    args = parse_args(argv)
    ensure_admin()
    pre_checks.main()
    run_screen('screen_browser_select')
    run_screen('screen_donation_request')
    app = None
    status_label = None
    if not args.developer_mode:
        app, status_label = _build_install_ui()

    def debloat_sequence():
        for slug, message, func in DEBLOAT_STEPS:
            if getattr(args, f"skip_{slug.replace('-', '_')}_step"):
                logger.info(f"Skipping {slug} step")
                continue
            _update_status(status_label, message)
            try:
                func()
            except Exception:
                return
        _update_status(status_label, "Restarting system…")
        subprocess.call(["shutdown", "/r", "/t", "0"])

    if args.developer_mode:
        debloat_sequence()
    else:
        def start_thread():
            threading.Thread(target=debloat_sequence, daemon=True).start()
        QTimer.singleShot(0, start_thread)
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
