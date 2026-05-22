"""SDK Documentation Viewer dialog for XTC Dial Factory."""

import os
import re
import tempfile
import shutil

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextBrowser,
    QPushButton, QFileDialog, QMessageBox, QWidget, QLabel,
)
from PySide6.QtGui import QFont

from ...docs.sdk_doc_generator import SdkDocGenerator


class SdkDocsViewerDialog(QDialog):
    """Dialog that generates and displays SDK documentation from Java stubs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generator = SdkDocGenerator()
        self._temp_dir: str | None = None
        self._classes: list[dict] = []

        self.setWindowTitle("SDK 文档")
        self.resize(900, 650)
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._generate_and_show()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter: class list (left) + doc viewer (right)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        # --- Left panel: class list ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_header = QLabel("  Classes / Interfaces")
        left_header.setObjectName("leftHeader")
        left_header.setFixedHeight(32)
        left_header.setStyleSheet(
            "background: #2d2d2d; color: #888; font-size: 12px;"
            "border-bottom: 1px solid #3c3c3c;"
            "padding: 0 12px; qproperty-alignment: AlignLeft AlignVCenter;"
        )
        left_layout.addWidget(left_header)

        self.class_list = QListWidget()
        self.class_list.setStyleSheet("""
            QListWidget {
                background: #252526; border: none; outline: none;
                font-size: 13px; color: #cccccc;
            }
            QListWidget::item {
                padding: 6px 12px; border: none;
            }
            QListWidget::item:hover {
                background: #2a2d2e;
            }
            QListWidget::item:selected {
                background: #094771; color: #ffffff;
            }
        """)
        self.class_list.currentItemChanged.connect(self._on_class_selected)
        left_layout.addWidget(self.class_list, 1)

        splitter.addWidget(left_widget)

        # --- Right panel: documentation viewer ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.doc_view = QTextBrowser()
        self.doc_view.setReadOnly(True)
        self.doc_view.setOpenExternalLinks(True)
        self.doc_view.setStyleSheet("""
            QTextBrowser {
                background: #1e1e1e; color: #d4d4d4; border: none;
                font-size: 14px;
            }
        """)
        self.doc_view.setFont(QFont("Segoe UI", 10))
        right_layout.addWidget(self.doc_view, 1)

        # --- Bottom toolbar ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(8)

        toolbar_layout.addStretch()

        self.export_html_btn = QPushButton("导出 HTML...")
        self.export_html_btn.setFixedHeight(28)
        self.export_html_btn.clicked.connect(self._export_html)
        self.export_html_btn.setStyleSheet(self._button_style())
        toolbar_layout.addWidget(self.export_html_btn)

        self.export_md_btn = QPushButton("导出 Markdown...")
        self.export_md_btn.setFixedHeight(28)
        self.export_md_btn.clicked.connect(self._export_markdown)
        self.export_md_btn.setStyleSheet(self._button_style())
        toolbar_layout.addWidget(self.export_md_btn)

        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(self._button_style())
        toolbar_layout.addWidget(close_btn)

        right_layout.addLayout(toolbar_layout)

        splitter.addWidget(right_widget)

        # Splitter proportions: 200px for list, rest for viewer
        splitter.setSizes([200, 700])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    @staticmethod
    def _button_style() -> str:
        return (
            "QPushButton {"
            "  background: #3c3c3c; color: #e0e0e0; border: 1px solid #555;"
            "  border-radius: 4px; padding: 2px 14px; font-size: 12px;"
            "}"
            "QPushButton:hover { background: #505050; }"
            "QPushButton:pressed { background: #2a2a2a; }"
        )

    # ------------------------------------------------------------------
    # Document generation
    # ------------------------------------------------------------------

    def _generate_and_show(self):
        """Generate docs to a temp directory and populate the viewer."""
        # Clean up any previous temp directory
        self._cleanup_temp()

        try:
            classes = self._generator.scan_stubs()
            if not classes:
                QMessageBox.warning(self, "无文档",
                                    "未在 stubs 目录中找到任何 Java 桩文件。")
                return

            self._classes = classes

            # Generate HTML to temp directory
            self._temp_dir = tempfile.mkdtemp(prefix="xtc_sdk_docs_")
            self._generator.generate_html(self._temp_dir)

            # Populate class list
            self.class_list.blockSignals(True)
            self.class_list.clear()

            for cls in sorted(classes, key=lambda c: c["name"]):
                label = f'{"I" if cls["type"] == "interface" else "C"} {cls["name"]}'
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, cls["name"])
                item.setToolTip(f'{cls["package"]}.{cls["name"]}')
                self.class_list.addItem(item)

            self.class_list.blockSignals(False)

            # Select first item
            if self.class_list.count() > 0:
                self.class_list.setCurrentRow(0)

        except Exception as exc:
            QMessageBox.critical(self, "生成失败",
                                 f"生成文档时出错:\n{exc}")

    def _on_class_selected(self, current: QListWidgetItem, previous):
        """Show documentation for the selected class."""
        if not current or not self._temp_dir:
            return

        class_name = current.data(Qt.UserRole)
        if not class_name:
            return

        html_path = os.path.join(self._temp_dir, f"{class_name}.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            # Hide the embedded sidebar via CSS (QTextBrowser already has
            # its own class list on the left). Injecting CSS keeps the
            # full document structure intact so class-based selectors work.
            html = html.replace(
                "</head>",
                "<style>"
                "nav.sidebar{display:none}"
                "main{max-width:none;padding:20px 28px}"
                "</style></head>",
            )
            self.doc_view.setHtml(html)
        else:
            self.doc_view.setHtml(
                "<p style='color:#888;padding:20px;'>"
                "未找到文档页面。</p>"
            )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_html(self):
        """Save generated HTML docs to a user-chosen directory."""
        if not self._classes:
            QMessageBox.information(self, "提示", "没有可导出的文档。")
            return

        target_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录 (HTML)")
        if not target_dir:
            return

        try:
            index_path = self._generator.generate_html(target_dir)
            QMessageBox.information(
                self, "导出成功",
                f"HTML 文档已导出到:\n{target_dir}\n\n"
                f"打开 {os.path.basename(index_path)} 查看。")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败",
                                 f"导出 HTML 时出错:\n{exc}")

    def _export_markdown(self):
        """Save generated Markdown docs to a user-chosen directory."""
        if not self._classes:
            QMessageBox.information(self, "提示", "没有可导出的文档。")
            return

        target_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录 (Markdown)")
        if not target_dir:
            return

        try:
            index_path = self._generator.generate_markdown(target_dir)
            QMessageBox.information(
                self, "导出成功",
                f"Markdown 文档已导出到:\n{target_dir}\n\n"
                f"打开 {os.path.basename(index_path)} 查看。")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败",
                                 f"导出 Markdown 时出错:\n{exc}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_temp(self):
        """Remove the temporary docs directory if it exists."""
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
            self._temp_dir = None

    def closeEvent(self, event):
        self._cleanup_temp()
        super().closeEvent(event)
