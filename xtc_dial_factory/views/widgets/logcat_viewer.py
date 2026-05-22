"""Logcat viewer widget -- runs adb logcat in a QProcess with filtering."""

import re

from PySide6.QtCore import Qt, QProcess, Signal, Slot
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox,
    QPlainTextEdit, QLabel,
)


# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------

_LOG_LEVEL_COLORS = {
    "F": QColor(255, 80, 80),    # Fatal   -> red
    "E": QColor(255, 80, 80),    # Error   -> red
    "W": QColor(255, 200, 50),   # Warning -> yellow
    "I": QColor(180, 255, 180),  # Info    -> green
    "D": QColor(150, 150, 150),  # Debug   -> gray
    "V": QColor(120, 120, 120),  # Verbose -> dim gray
}

# Regex that matches the timestamp + level in "logcat -v time" output:
#   05-22 12:34:56.789 E/tag( 1234): message
_LOG_PREFIX_RE = re.compile(
    r"^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+"
    r"(?P<level>[FEWIDV])"
    r"/"
)


# ---------------------------------------------------------------------------
# LogHighlighter
# ---------------------------------------------------------------------------

class _LogHighlighter(QSyntaxHighlighter):
    """Per-line highlighter -- colours the whole line by log level."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._formats: dict[str, QTextCharFormat] = {}
        for level, colour in _LOG_LEVEL_COLORS.items():
            fmt = QTextCharFormat()
            fmt.setForeground(colour)
            self._formats[level] = fmt

    def highlightBlock(self, text: str) -> None:
        m = _LOG_PREFIX_RE.match(text)
        if m:
            fmt = self._formats.get(m.group("level"))
            if fmt:
                self.setFormat(0, len(text), fmt)


# ---------------------------------------------------------------------------
# LogcatViewer
# ---------------------------------------------------------------------------

class LogcatViewer(QWidget):
    """Runs ``adb logcat -v time`` in a QProcess and displays log output.

    Features
    --------
    - Non-blocking; uses QProcess so the UI stays responsive.
    - On start, clears the log buffer first (``adb logcat -c``).
    - Configurable substring filter (case-insensitive).
    - Auto-scroll toggle.
    - Colour-coded log levels (red / yellow / green / gray).
    """

    # signals
    processStarted = Signal()
    processStopped = Signal()
    errorOccurred = Signal(str)

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process: QProcess | None = None
        self._buffer: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("日志查看器")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- toolbar row ------------------------------------------------
        toolbar = QHBoxLayout()

        self.start_stop_btn = QPushButton("开始")
        self.start_stop_btn.setFixedWidth(80)
        self.start_stop_btn.clicked.connect(self._toggle)
        toolbar.addWidget(self.start_stop_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.clicked.connect(self._clear_log)
        toolbar.addWidget(self.clear_btn)

        toolbar.addWidget(QLabel("过滤:"))

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("输入过滤关键字（留空显示全部）")
        self.filter_edit.setText("DialTag")
        self.filter_edit.textChanged.connect(self._reapply_filter)
        toolbar.addWidget(self.filter_edit, 1)

        self.auto_scroll_cb = QCheckBox("自动滚动")
        self.auto_scroll_cb.setChecked(True)
        toolbar.addWidget(self.auto_scroll_cb)

        layout.addLayout(toolbar)

        # --- log output -------------------------------------------------
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(10_000)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                selection-background-color: #264f78;
            }
        """)

        self._highlighter = _LogHighlighter(self.log_view.document())

        layout.addWidget(self.log_view, 1)

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True while the logcat process is running."""
        return self._process is not None and self._process.state() == QProcess.ProcessState.Running

    def start(self):
        """Start capturing logcat output (no-op if already running)."""
        if self.is_running():
            return
        self._start_process()

    def stop(self):
        """Stop capturing logcat output (safe when not running)."""
        if not self.is_running():
            return
        self._stop_process()

    # ------------------------------------------------------------------
    # slots
    # ------------------------------------------------------------------

    @Slot()
    def _toggle(self):
        if self.is_running():
            self._stop_process()
        else:
            self._start_process()

    @Slot()
    def _clear_log(self):
        self._buffer.clear()
        self.log_view.clear()

    @Slot()
    def _reapply_filter(self):
        """Re-filter *buffer* against the current filter text."""
        self.log_view.clear()
        pattern = self.filter_edit.text()
        for line in self._buffer:
            if not pattern or pattern.lower() in line.lower():
                self._append_line(line)

    # ------------------------------------------------------------------
    # process lifecycle
    # ------------------------------------------------------------------

    def _start_process(self):
        """Launch the adb logcat sub-processes."""
        if self._process:
            self._process.deleteLater()

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_ready_read)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        # Step 1: clear the log buffer (short-lived process)
        clear_proc = QProcess(self)
        clear_proc.finished.connect(lambda: self._do_start())
        clear_proc.start("adb", ["logcat", "-c"])

    def _do_start(self):
        """Actually launch ``adb logcat -v time`` after clearing the buffer."""
        if self._process is None:
            return
        self._process.start("adb", ["logcat", "-v", "time"])
        self.start_stop_btn.setText("停止")
        self.processStarted.emit()

    def _stop_process(self):
        """Kill the logcat process cleanly."""
        if self._process:
            self._process.kill()
            self._process.waitForFinished(2000)
            self._process.deleteLater()
            self._process = None
        self.start_stop_btn.setText("开始")
        self.processStopped.emit()

    def _on_ready_read(self):
        """Read available output and append to display."""
        if not self._process:
            return
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            self._buffer.append(line)
            # Trim buffer if it exceeds cap
            if len(self._buffer) > 20_000:
                self._buffer = self._buffer[-15_000:]

            pattern = self.filter_edit.text()
            if not pattern or pattern.lower() in line.lower():
                self._append_line(line)

    def _on_finished(self, exit_code: int, exit_status):
        """Handle unexpected process termination."""
        self.start_stop_btn.setText("开始")
        self.processStopped.emit()

    def _on_error(self, error):
        """Handle QProcess errors."""
        msg_map = {
            QProcess.ProcessError.FailedToStart: (
                "adb 未找到或无法启动。请确认 adb 已加入 PATH。"
            ),
            QProcess.ProcessError.Crashed: "adb logcat 进程异常退出。",
            QProcess.ProcessError.Timedout: "adb logcat 超时。",
        }
        msg = msg_map.get(error, "adb 进程发生未知错误。")
        self.errorOccurred.emit(msg)
        self._append_line(f"[错误] {msg}")

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _append_line(self, line: str):
        """Append *line* to the text edit, optionally scrolling to bottom."""
        self.log_view.appendPlainText(line)
        if self.auto_scroll_cb.isChecked():
            self.log_view.moveCursor(QTextCursor.MoveOperation.End)
            self.log_view.ensureCursorVisible()

    # ------------------------------------------------------------------
    # teardown
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._stop_process()
        super().closeEvent(event)
