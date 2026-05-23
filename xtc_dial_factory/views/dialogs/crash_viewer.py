"""Crash log viewer dialog for XTC Dial Factory."""

import os
import subprocess

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QPlainTextEdit, QSplitter, QWidget, QMessageBox
)

from ...error_reporter import (
    get_crash_logs, read_crash_log, clear_crash_logs, get_crash_log_dir
)


class CrashViewerDialog(QDialog):
    """Dialog for browsing and viewing crash log files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("错误日志")
        self.setMinimumSize(800, 500)
        self.resize(900, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # === Header ===
        header_layout = QHBoxLayout()
        self.count_label = QLabel("加载中...")
        self.count_label.setStyleSheet("color: #cccccc; padding: 4px 0;")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # === Splitter: list + content ===
        splitter = QSplitter(Qt.Horizontal)

        # Left: crash log list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        list_header = QLabel("崩溃日志列表")
        list_header.setStyleSheet("color: #969696; font-size: 12px; padding: 2px 0;")
        list_layout.addWidget(list_header)

        self.log_list = QListWidget()
        self.log_list.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.log_list)

        splitter.addWidget(list_widget)

        # Right: crash log content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        content_header = QLabel("详细内容")
        content_header.setStyleSheet("color: #969696; font-size: 12px; padding: 2px 0;")
        content_layout.addWidget(content_header)

        self.log_content = QPlainTextEdit()
        self.log_content.setReadOnly(True)
        self.log_content.setStyleSheet("""
            QPlainTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                border: 1px solid #3c3c3c;
                padding: 6px;
            }
        """)
        content_layout.addWidget(self.log_content)

        splitter.addWidget(content_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

        # === Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.open_folder_btn = QPushButton("打开日志文件夹")
        self.open_folder_btn.clicked.connect(self._open_log_folder)
        btn_layout.addWidget(self.open_folder_btn)

        btn_layout.addStretch()

        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.clicked.connect(self._clear_logs)
        btn_layout.addWidget(self.clear_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background: #2b2b2b;
                color: #cccccc;
            }
            QPlainTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, "Courier New", monospace;
            }
            QListWidget {
                background: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                outline: none;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px 6px;
            }
            QListWidget::item:selected {
                background: #264f78;
            }
            QPushButton {
                background: #0e639c;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #1177bb;
            }
            QPushButton:pressed {
                background: #094771;
            }
            QPushButton#clear_btn {
                background: #8a3a3a;
            }
            QPushButton#clear_btn:hover {
                background: #a54545;
            }
        """)

        # Highlight the clear button with a different style
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setStyleSheet("""
            QPushButton#clear_btn {
                background: #8a3a3a;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton#clear_btn:hover {
                background: #a54545;
            }
            QPushButton#clear_btn:pressed {
                background: #6e2e2e;
            }
        """)

        self._refresh_list()

    def _refresh_list(self):
        """Reload the crash log list and update header labels."""
        logs = get_crash_logs()
        self.log_list.clear()

        if not logs:
            self.count_label.setText("暂无崩溃日志")
            self.log_content.clear()
            return

        count = len(logs)
        latest = logs[0]  # Newest first
        # Extract date from filename: crash_YYYYMMDD_HHMMSS.log
        date_str = latest[6:14]
        formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        self.count_label.setText(
            f"共 {count} 条日志 | 最近崩溃: {formatted}"
        )

        for filename in logs:
            self.log_list.addItem(filename)

    @Slot(int)
    def _on_selection_changed(self, row):
        """Display content of the selected crash log."""
        item = self.log_list.item(row)
        if not item:
            return
        content = read_crash_log(item.text())
        self.log_content.setPlainText(content)
        self.log_content.moveCursor(QTextCursor.MoveOperation.Start)

    @Slot()
    def _open_log_folder(self):
        """Open the crash_logs directory in file explorer."""
        log_dir = get_crash_log_dir()
        if os.path.isdir(log_dir):
            try:
                os.startfile(log_dir)
            except (OSError, AttributeError):
                try:
                    subprocess.Popen(["explorer", log_dir])
                except OSError:
                    pass

    @Slot()
    def _clear_logs(self):
        """Delete all crash logs and refresh the list."""

        reply = QMessageBox.question(
            self, "确认清除",
            "确定要删除所有崩溃日志吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        clear_crash_logs()
        self._refresh_list()
        self.log_content.clear()
