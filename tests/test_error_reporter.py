"""Tests for crash/error reporting system."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from xtc_dial_factory.error_reporter import (
    install_crash_handler, get_crash_logs, read_crash_log,
    clear_crash_logs, get_crash_log_dir,
)


class TestInstallCrashHandler:
    def test_installs_excepthook(self):
        old_hook = sys.excepthook
        try:
            with patch("xtc_dial_factory.error_reporter._ensure_log_dir"):
                install_crash_handler()
                assert sys.excepthook is not old_hook
        finally:
            sys.excepthook = old_hook

    def test_passes_keyboard_interrupt(self):
        old_hook = MagicMock()
        sys.excepthook = old_hook
        try:
            with patch("xtc_dial_factory.error_reporter._ensure_log_dir"):
                install_crash_handler()
                sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
                old_hook.assert_called_once()
        finally:
            sys.excepthook = old_hook

    def test_passes_system_exit(self):
        old_hook = MagicMock()
        sys.excepthook = old_hook
        try:
            with patch("xtc_dial_factory.error_reporter._ensure_log_dir"):
                install_crash_handler()
                sys.excepthook(SystemExit, SystemExit(0), None)
                old_hook.assert_called_once()
        finally:
            sys.excepthook = old_hook


class TestCrashLogs:
    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        log_dir = tmp_path / "crash_logs"
        log_dir.mkdir()
        (log_dir / "crash_20250101_120000.log").write_text(
            "=== Crash Report ===\nTest error 1\n", encoding="utf-8"
        )
        (log_dir / "crash_20250102_120000.log").write_text(
            "=== Crash Report ===\nTest error 2\n", encoding="utf-8"
        )
        (log_dir / "not_a_crash.log").write_text("irrelevant", encoding="utf-8")
        return str(log_dir)

    def test_get_crash_logs(self, temp_log_dir):
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", temp_log_dir):
            logs = get_crash_logs()
            assert len(logs) == 2
            assert logs[0] == "crash_20250102_120000.log"
            assert logs[1] == "crash_20250101_120000.log"

    def test_read_crash_log(self, temp_log_dir):
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", temp_log_dir):
            content = read_crash_log("crash_20250101_120000.log")
            assert "Test error 1" in content

    def test_read_nonexistent_log(self, temp_log_dir):
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", temp_log_dir):
            content = read_crash_log("nonexistent.log")
            assert content == ""

    def test_clear_crash_logs(self, temp_log_dir):
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", temp_log_dir):
            clear_crash_logs()
            remaining = os.listdir(temp_log_dir)
            assert all("crash_" not in f for f in remaining)

    def test_get_crash_log_dir(self, temp_log_dir):
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", temp_log_dir):
            d = get_crash_log_dir()
            assert d == temp_log_dir
            assert os.path.isdir(d)

    def test_get_crash_log_dir_creates(self, tmp_path):
        nonexistent = str(tmp_path / "new_crash_logs")
        assert not os.path.exists(nonexistent)
        with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", nonexistent):
            d = get_crash_log_dir()
            assert os.path.isdir(d)

    def test_crash_handler_writes_log(self, tmp_path):
        old_hook = sys.excepthook
        try:
            log_dir = str(tmp_path / "crash_logs")
            with patch("xtc_dial_factory.error_reporter.CRASH_LOG_DIR", log_dir):
                with patch("xtc_dial_factory.error_reporter._show_error_dialog"):
                    install_crash_handler()
                    try:
                        raise ValueError("test crash")
                    except ValueError:
                        exc_type, exc_value, exc_tb = sys.exc_info()
                        sys.excepthook(exc_type, exc_value, exc_tb)

            # Verify outside patch context — CRASH_LOG_DIR is restored but
            # the directory and file persist on disk
            assert os.path.isdir(log_dir)
            files = [f for f in os.listdir(log_dir)
                     if f.startswith("crash_") and f.endswith(".log")]
            assert len(files) == 1
            log_path = os.path.join(log_dir, files[0])
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "ValueError" in content
            assert "test crash" in content
        finally:
            sys.excepthook = old_hook
