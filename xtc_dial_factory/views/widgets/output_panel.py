"""Build/deploy output panel with colored, auto-scrolling text display."""

from PySide6.QtCore import Qt, QMetaObject, Q_ARG
from PySide6.QtWidgets import (
    QDockWidget, QPlainTextEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtGui import QTextCursor, QColor, QFont


# Color scheme matching VS Code dark theme
_COLORS = {
    "info":    QColor("#cccccc"),
    "warning": QColor("#e5c07b"),
    "error":   QColor("#f44747"),
    "success": QColor("#89d185"),
    "header":  QColor("#61afef"),
}


class OutputPanel(QDockWidget):
    """Dock widget displaying colored build/deploy output in real-time."""

    def __init__(self, parent=None):
        super().__init__("输出", parent)
        self.setObjectName("output_panel")

        self._widget = QWidget()
        self.setWidget(self._widget)

        layout = QVBoxLayout(self._widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header.setStyleSheet("background: #1e1e1e; border-bottom: 1px solid #333;")

        title = QLabel("编译 / 部署输出")
        title.setStyleSheet("color: #999; font-size: 12px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.setStyleSheet("""
            QPushButton { background:#333; color:#ccc; border:1px solid #555; padding:2px 8px; font-size:11px; }
            QPushButton:hover { background:#444; }
        """)
        self._clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(self._clear_btn)

        layout.addWidget(header)

        # Text area
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(10_000)
        self._text.setFont(QFont("Consolas", 10))
        self._text.setStyleSheet("""
            QPlainTextEdit {
                background: #1e1e1e; color: #cccccc;
                border: none; padding: 4px 8px;
                selection-background-color: #264f78;
            }
        """)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self._text)

        self.setMinimumHeight(120)

    # ---- public API ---------------------------------------------------------

    def append(self, text: str, type: str = "info"):
        """Append a line of colored text.  Thread-safe (invokes via meta-call)."""
        color = _COLORS.get(type, _COLORS["info"])
        QMetaObject.invokeMethod(
            self._text, "appendHtml",
            Qt.QueuedConnection,
            Q_ARG(str, f'<pre style="color:{color.name()};margin:0;font-family:Consolas;font-size:10pt;">'
                       f'{_escape(text)}</pre>')
        )

    def append_lines(self, lines: list[tuple[str, str]]):
        """Append multiple (text, type) pairs at once."""
        html_parts = []
        for text, type_ in lines:
            color = _COLORS.get(type_, _COLORS["info"])
            html_parts.append(
                f'<pre style="color:{color.name()};margin:0;font-family:Consolas;font-size:10pt;">'
                f'{_escape(text)}</pre>'
            )
        QMetaObject.invokeMethod(
            self._text, "appendHtml",
            Qt.QueuedConnection,
            Q_ARG(str, "".join(html_parts))
        )

    def clear(self):
        """Clear all output."""
        self._text.clear()

    def set_running(self, running: bool):
        """Update appearance while a task is in progress."""
        if running:
            self._text.setStyleSheet("""
                QPlainTextEdit {
                    background: #1e1e1e; color: #cccccc;
                    border: none; padding: 4px 8px;
                    selection-background-color: #264f78;
                    border-left: 3px solid #89d185;
                }
            """)
        else:
            self._text.setStyleSheet("""
                QPlainTextEdit {
                    background: #1e1e1e; color: #cccccc;
                    border: none; padding: 4px 8px;
                    selection-background-color: #264f78;
                }
            """)

    def _on_task_start(self, title: str):
        """Call at the beginning of a build/deploy task."""
        self.set_running(True)
        self.append(f"━━━ {title} ━━━", "header")

    def _on_task_done(self, success: bool, message: str):
        """Call when a task finishes."""
        self.set_running(False)
        self.append(f"→ {message}", "success" if success else "error")
        self.append("", "info")  # blank line spacer


def _escape(text: str) -> str:
    """Minimal HTML escaping for plain text."""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
