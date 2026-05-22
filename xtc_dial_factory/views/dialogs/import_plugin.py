"""Dialog for importing .pl plugin files as compose components."""

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel,
    QDialogButtonBox, QFileDialog, QMessageBox,
)

from ...build.pl_parser import PlParser


class ImportPluginDialog(QDialog):
    """Dialog to import a .pl plugin file and configure it as a compose component."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入 .pl 组件")
        self.setMinimumSize(480, 360)
        self._pl_path = ""
        self._parsed_info = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("选择 .pl 文件")
        file_layout = QVBoxLayout(file_group)
        file_row = QVBoxLayout()
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #888;")
        self.file_path_label.setWordWrap(True)
        file_row.addWidget(self.file_path_label)
        self.select_btn = QPushButton("浏览...")
        self.select_btn.clicked.connect(self._select_file)
        file_row.addWidget(self.select_btn)
        file_layout.addLayout(file_row)
        layout.addWidget(file_group)

        # Parsed info display
        info_group = QGroupBox("插件信息")
        info_form = QFormLayout(info_group)

        self.source_name_label = QLabel("-")
        info_form.addRow("源名称:", self.source_name_label)

        self.package_name_label = QLabel("-")
        info_form.addRow("包名:", self.package_name_label)

        self.version_label = QLabel("-")
        info_form.addRow("版本:", self.version_label)

        layout.addWidget(info_group)

        # Configuration
        config_group = QGroupBox("组件配置")
        config_form = QFormLayout(config_group)

        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("在面板中显示的名称")
        config_form.addRow("显示名称:", self.display_name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem("1: 普通组件", 1)
        self.type_combo.addItem("7: 背景组件", 7)
        self.type_combo.addItem("11: 文本组件", 11)
        config_form.addRow("组件类型:", self.type_combo)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 360)
        self.width_spin.setValue(100)
        config_form.addRow("默认宽度:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 360)
        self.height_spin.setValue(100)
        config_form.addRow("默认高度:", self.height_spin)

        layout.addWidget(config_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_accept_enabled()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 .pl 插件文件", "", "插件文件 (*.pl);;所有文件 (*)"
        )
        if not path:
            return

        try:
            parser = PlParser(path)
            info = parser.parse()
        except Exception as e:
            QMessageBox.critical(self, "解析失败", f"无法解析 .pl 文件:\n{e}")
            return

        if not info.get("package_name"):
            QMessageBox.warning(self, "解析结果", "未能从 AndroidManifest.xml 中提取包名，请确认文件格式正确。")

        self._pl_path = path
        self._parsed_info = info

        filename = os.path.splitext(os.path.basename(path))[0]
        self.file_path_label.setText(path)
        self.file_path_label.setStyleSheet("color: #fff;")
        self.source_name_label.setText(filename)
        self.package_name_label.setText(info.get("package_name", "(未知)"))
        self.version_label.setText(str(info.get("version_code", 1)))
        self.display_name_edit.setText(filename)
        self.display_name_edit.setFocus()
        self._update_accept_enabled()

    def _update_accept_enabled(self):
        ok_btn = self.buttonBox() if hasattr(self, "buttonBox") else None
        if ok_btn:
            ok_btn.setEnabled(bool(self._pl_path))

    def buttonBox(self):
        for child in self.findChildren(QDialogButtonBox):
            return child
        return None

    def _on_accept(self):
        if not self._pl_path:
            QMessageBox.information(self, "提示", "请先选择一个 .pl 文件")
            return
        if not self.display_name_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入显示名称")
            return
        self.accept()

    @property
    def component_info(self) -> dict:
        filename = os.path.splitext(os.path.basename(self._pl_path))[0]
        return {
            "pl_path": self._pl_path,
            "source_name": filename,
            "package_name": self._parsed_info.get("package_name", ""),
            "version_code": self._parsed_info.get("version_code", 1),
            "display_name": self.display_name_edit.text().strip(),
            "type": self.type_combo.currentData(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
        }
