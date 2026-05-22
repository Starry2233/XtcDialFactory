"""Crash/error handling system for XTC Dial Factory."""

import os
import sys
import datetime
import traceback
import platform


CRASH_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crash_logs")


def _ensure_log_dir():
    """Create crash_logs directory if it doesn't exist."""
    os.makedirs(CRASH_LOG_DIR, exist_ok=True)


def _get_system_info() -> str:
    """Collect system information for crash dumps."""
    lines = [
        "--- System Information ---",
        f"OS: {platform.system()} {platform.release()} ({platform.version()})",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"Python: {sys.version}",
        f"Platform: {sys.platform}",
    ]
    return "\n".join(lines)


def install_crash_handler():
    """Install a custom sys.excepthook to log crashes and show user dialog.

    Must be called after QApplication is created so that QMessageBox can be
    displayed. Does not intercept KeyboardInterrupt or SystemExit.
    """
    _ensure_log_dir()
    old_hook = sys.excepthook

    def crash_handler(exc_type, exc_value, exc_tb):
        if exc_type in (KeyboardInterrupt, SystemExit):
            old_hook(exc_type, exc_value, exc_tb)
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(CRASH_LOG_DIR, f"crash_{filename_ts}.log")

        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        crash_dump = (
            f"=== XTC Dial Factory Crash Report ===\n"
            f"Timestamp: {timestamp}\n"
            f"Exception: {exc_type.__name__}\n"
            f"Message: {exc_value}\n\n"
            f"{_get_system_info()}\n\n"
            f"--- Traceback ---\n"
            f"{tb_text}\n"
        )

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(crash_dump)
        except OSError:
            pass

        _show_error_dialog(exc_type, exc_value, tb_text, log_path)

        old_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = crash_handler


def _show_error_dialog(exc_type, exc_value, tb_text, log_path):
    """Display an error dialog with crash details."""
    try:
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtGui import QTextCursor

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("XTC Dial Factory - 意外错误")
        msg_box.setText(
            f"程序遇到意外错误:\n\n{exc_type.__name__}: {exc_value}"
        )
        msg_box.setInformativeText(
            f"详细错误信息已保存到:\n{log_path}"
        )
        msg_box.setDetailedText(tb_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet("""
            QMessageBox { background: #2b2b2b; color: #cccccc; }
            QLabel { color: #cccccc; }
            QTextEdit { background: #1e1e1e; color: #d4d4d4;
                        font-family: Consolas, monospace; }
            QPushButton { background: #0e639c; color: white;
                          border: none; padding: 6px 16px;
                          border-radius: 4px; min-width: 80px; }
            QPushButton:hover { background: #1177bb; }
        """)
        msg_box.exec()
    except Exception:
        pass


def get_crash_logs() -> list:
    """Return list of crash log filenames sorted newest first."""
    _ensure_log_dir()
    try:
        files = [f for f in os.listdir(CRASH_LOG_DIR)
                 if f.startswith("crash_") and f.endswith(".log")]
        files.sort(reverse=True)
        return files
    except OSError:
        return []


def read_crash_log(filename: str) -> str:
    """Return the content of a specific crash log file."""
    path = os.path.join(CRASH_LOG_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def clear_crash_logs():
    """Delete all crash log files."""
    for filename in get_crash_logs():
        try:
            os.remove(os.path.join(CRASH_LOG_DIR, filename))
        except OSError:
            pass


def get_crash_log_dir() -> str:
    """Return the absolute path to the crash logs directory."""
    _ensure_log_dir()
    return CRASH_LOG_DIR
