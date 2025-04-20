import sys
import ctypes
import logging
import threading
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QEventLoop

from talon_safety_check import run_safety_checks
from components.dry_run import dry_run
from components.browser_select_screen import BrowserSelectScreen
from components.defender_check import DefenderCheck
from components.raven_app_screen import RavenAppScreen
from components.install_screen import InstallScreen
from components import (
    raven_software_install,
    browser_install,
    windows_check,
    apply_background
)
from components.debloat_windows import ScriptError, run_debloat

TALON_VERSION = "1.3.0"

developer_mode = "--developer-mode" in sys.argv
dry_run_flag  = "--dry-run" in sys.argv

LOG_FILE = "talon.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info(
    "\n" + "="*60 +
    f" TALON SESSION START {datetime.now().isoformat()} " +
    "="*60 + "\n"
)

app = None

def get_windows_info():
    try:
        ver = sys.getwindowsversion()
        build = ver.build
        name  = "Windows 11" if build >= 22000 else "Windows 10"
        return {"version": name, "build": build}
    except Exception as e:
        logging.exception("Error detecting Windows version: %s", e)
        return {}

def is_running_as_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logging.exception("Error checking admin rights: %s", e)
        return False

def restart_as_admin():
    try:
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])
        logging.info("Elevating to admin")
        ctypes.windll.shell32.ShellExecuteW(None, "runas",
            sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    except Exception as e:
        logging.exception("Failed elevation: %s", e)
        sys.exit(1)

def show_error_dialog(msg: str):
    QMessageBox.critical(None, "Talon Installer Error", msg)
    if app:
        app.quit()
    else:
        sys.exit(1)

def run_step(worker, on_done):
    done = threading.Event()
    errors = []
    def _w():
        try:
            worker()
        except Exception as e:
            logging.exception("Error in %s: %s", worker.__name__, e)
            errors.append(e)
        finally:
            done.set()
    threading.Thread(target=_w, daemon=True).start()
    timer = QTimer()
    timer.setInterval(50)
    def check():
        if done.is_set():
            timer.stop()
            if errors:
                exc = errors[0]
                if isinstance(exc, ScriptError):
                    choice = QMessageBox.question(
                        None, "Script Error",
                        f"{exc}\n\nContinue installation?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if choice == QMessageBox.Yes:
                        on_done()
                    else:
                        show_error_dialog("Aborted by user.")
                else:
                    show_error_dialog(str(exc))
            else:
                on_done()
    timer.timeout.connect(check)
    timer.start()

def main():
    global app
    logging.info("Starting Talon Installer v%s", TALON_VERSION)
    win = get_windows_info()
    logging.info("Detected %s (build %s)", win.get("version"), win.get("build"))
    app = QApplication(sys.argv)
    if not is_running_as_admin():
        restart_as_admin()
    try:
        dwin = DefenderCheck()
        dwin.defender_disabled_signal.connect(dwin.close)
        loop = QEventLoop()
        dwin.defender_disabled_signal.connect(loop.quit)
        dwin.show()
        loop.exec_()
    except Exception as e:
        logging.exception("Defender check error: %s", e)
    try:
        windows_check.check_system()
    except Exception as e:
        logging.exception("System check error: %s", e)
    selected_browser = None
    try:
        bwin = BrowserSelectScreen()
        loop = QEventLoop()
        selected = {"value": None}
        def on_browser(b):
            selected["value"] = b
            loop.quit()
        bwin.browser_selected.connect(on_browser)
        bwin.show()
        loop.exec_()
        bwin.close()
        selected_browser = selected["value"]
        logging.info("Browser: %s", selected_browser)
    except Exception as e:
        logging.exception("Browser selection error: %s", e)
    install_raven   = None
    try:
        rwin = RavenAppScreen()
        loop2 = QEventLoop()
        choice = {"value": None}
        def on_option(opt):
            choice["value"] = opt
            loop2.quit()
        rwin.option_selected.connect(on_option)
        rwin.show()
        loop2.exec_()
        rwin.close()
        install_raven = choice["value"]
        logging.info("Install Raven: %s", install_raven)
    except Exception as e:
        logging.exception("Raven prompt error: %s", e)
    install_screen = None
    if not developer_mode:
        install_screen = InstallScreen()
        install_screen.show()
    if dry_run_flag:
        errors, report = dry_run(selected_browser)
        dlg = QMessageBox()
        dlg.setWindowTitle("Dry‑Run Report")
        dlg.setText(report + "\n\nProceed with real installation?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if dlg.exec_() != QMessageBox.Yes:
            logging.info("Dry‑run aborted by user")
            app.quit()
            return

    def proceed_to_install():
        start_install()

    QTimer.singleShot(0, lambda: run_step(run_safety_checks, proceed_to_install))

    def on_finalize():
        if install_screen:
            install_screen.set_status("All done. Restarting…")
        app.quit()

    def after_background():
        if install_screen:
            install_screen.set_status("Applying registry tweaks…")
         run_step(run_debloat, on_finalize)

    def after_browser():
        if install_screen:
            install_screen.set_status("Setting desktop background…")
        run_step(apply_background.main, after_background)

    def after_raven():
        if install_screen:
            install_screen.set_status(f"Installing browser: {selected_browser}…")
        run_step(lambda: browser_install.install_browser(selected_browser), after_browser)

    def start_install():
        if install_screen:
            install_screen.set_status("Starting installation…")
        if install_raven:
            if install_screen:
                install_screen.set_status("Installing Raven software…")
            run_step(raven_software_install.main, after_raven)
        else:
            after_raven()

    app.exec_()

if __name__ == "__main__":
    main()