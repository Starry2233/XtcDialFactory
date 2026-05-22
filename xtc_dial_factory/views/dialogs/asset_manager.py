"""Dialog for managing extra asset files (images, etc.) in compose dial projects."""

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialogButtonBox, QFileDialog, QMessageBox
)


class AssetManagerDialog(QDialog):
    """Manage extra files to deploy alongside a compose dial (backgrounds, etc.)."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(f"资源管理 - {project.name}")
        self.setMinimumSize(700, 400)
        self._setup_ui()
        self._load_assets()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "管理部署到设备时附带的额外资源文件（如背景图片、GIF 等）。\n"
            "本地路径相对于项目目录，远程路径为设备上的绝对路径。"
        ))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["本地文件", "设备路径", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加文件...")
        add_btn.clicked.connect(self._add_file)
        btn_layout.addWidget(add_btn)
        remove_btn = QPushButton("删除行")
        remove_btn.clicked.connect(self._remove_row)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_file(self):
        """Open file picker, add a row with the selected file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择资源文件", self.project.root_dir,
            "图片 (*.png *.jpg *.jpeg *.gif *.bmp);;所有文件 (*)"
        )
        if not file_path:
            return

        local_rel = os.path.relpath(file_path, self.project.root_dir)
        # Suggest a remote path based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        dial_dir = self.project.get_dial_dir()
        remote_suffix = f"compose/{os.path.basename(file_path)}"
        if self.project.project_type.value == "compose_dial":
            remote_path = f"/sdcard/xtc/dial/{remote_suffix}"
        else:
            remote_path = os.path.join(dial_dir, os.path.basename(file_path))

        self._add_row(local_rel, remote_path, "")

    def _add_row(self, local="", remote="", note=""):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(local))
        self.table.setItem(row, 1, QTableWidgetItem(remote))
        self.table.setItem(row, 2, QTableWidgetItem(note))

    def _remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _load_assets(self):
        for asset in self.project.assets:
            self._add_row(asset.local, asset.remote)

    def _collect_assets(self) -> list:
        """Read asset data from the table rows."""
        from ...models.project import AssetFile
        results = []
        for i in range(self.table.rowCount()):
            local = self.table.item(i, 0).text().strip() if self.table.item(i, 0) else ""
            remote = self.table.item(i, 1).text().strip() if self.table.item(i, 1) else ""
            if not local and not remote:
                continue
            results.append(AssetFile(local=local, remote=remote))
        return results

    def _on_accept(self):
        assets = self._collect_assets()
        # Validate: local files should exist
        for asset in assets:
            full_path = os.path.join(self.project.root_dir, asset.local)
            if asset.local and not os.path.isfile(full_path):
                reply = QMessageBox.question(
                    self, "文件不存在",
                    f"本地文件不存在:\n{full_path}\n\n仍要添加吗？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        self.project.assets = assets
        self.accept()
