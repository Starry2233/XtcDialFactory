"""Version management dialog for XTC Dial Factory projects."""

import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QPushButton, QPlainTextEdit, QTextBrowser,
    QDialogButtonBox, QGroupBox
)

from ...models.project import Project


class VersionManagerDialog(QDialog):
    """Dialog for managing project version and changelog."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("版本管理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # === Current Version Info ===
        version_group = QGroupBox("版本信息")
        version_form = QFormLayout(version_group)

        self.version_name_edit = QLineEdit(project.version_name)
        version_form.addRow("版本名称:", self.version_name_edit)

        self.version_code_spin = QSpinBox()
        self.version_code_spin.setRange(1, 99999)
        self.version_code_spin.setValue(project.version_code)
        version_form.addRow("版本代码:", self.version_code_spin)

        layout.addWidget(version_group)

        # === Bump Version ===
        bump_group = QGroupBox("升级版本")
        bump_layout = QHBoxLayout(bump_group)

        self.major_btn = QPushButton("主版本 (Major)")
        self.major_btn.clicked.connect(lambda: self._bump("major"))
        bump_layout.addWidget(self.major_btn)

        self.minor_btn = QPushButton("次版本 (Minor)")
        self.minor_btn.clicked.connect(lambda: self._bump("minor"))
        bump_layout.addWidget(self.minor_btn)

        self.patch_btn = QPushButton("修订 (Patch)")
        self.patch_btn.clicked.connect(lambda: self._bump("patch"))
        bump_layout.addWidget(self.patch_btn)

        layout.addWidget(bump_group)

        # === Changelog Input ===
        changelog_group = QGroupBox("更新日志")
        changelog_layout = QVBoxLayout(changelog_group)

        changelog_input_layout = QHBoxLayout()
        self.changelog_edit = QPlainTextEdit()
        self.changelog_edit.setPlaceholderText("输入更新日志条目...")
        self.changelog_edit.setMaximumHeight(80)
        changelog_input_layout.addWidget(self.changelog_edit)

        add_entry_btn = QPushButton("添加到更新日志")
        add_entry_btn.clicked.connect(self._add_changelog_entry)
        changelog_input_layout.addWidget(add_entry_btn)

        changelog_layout.addLayout(changelog_input_layout)

        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setReadOnly(True)
        changelog_layout.addWidget(self.changelog_browser)

        layout.addWidget(changelog_group)

        # === Dialog Buttons ===
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Populate changelog display
        self._refresh_changelog()

    def _bump(self, part: str):
        """Bump version and update UI fields."""
        try:
            parts = self.version_name_edit.text().split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            major, minor, patch = 1, 0, 0

        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            return

        self.version_name_edit.setText(f"{major}.{minor}.{patch}")
        self.version_code_spin.setValue(self.version_code_spin.value() + 1)

    def _add_changelog_entry(self):
        """Prepend a new timestamped changelog entry."""
        text = self.changelog_edit.toPlainText().strip()
        if not text:
            return

        version = self.version_name_edit.text()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        entry = f"[{timestamp}] {version}: {text}"

        self.project.changelog.insert(0, entry)
        self.changelog_edit.clear()
        self._refresh_changelog()

    def _refresh_changelog(self):
        """Re-render changelog history in the read-only browser."""
        self.changelog_browser.clear()
        for entry in self.project.changelog:
            self.changelog_browser.append(entry)

    def _on_accept(self):
        """Write version fields back to the project and close."""
        self.project.version_name = self.version_name_edit.text()
        self.project.version_code = self.version_code_spin.value()
        self.accept()
