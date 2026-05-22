"""Config editor dialog for dial config.json."""

import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel,
    QDialogButtonBox, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from ...models.project import DialConfig, NetComposeDial, ThemeAssemblyElement, ProjectType


class ConfigEditor(QDialog):
    """Visual editor for config.json (DialConfig / NetComposeDial)."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(f"配置编辑器 - {project.name}")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Basic config tab
        basic_tab = QWidget()
        basic_form = QFormLayout(basic_tab)

        self.source_name_edit = QLineEdit()
        basic_form.addRow("sourceName:", self.source_name_edit)

        self.dial_name_edit = QLineEdit()
        basic_form.addRow("dialName:", self.dial_name_edit)

        self.clock_type_combo = QComboBox()
        self.clock_type_combo.addItems([
            "1: 传统CL表盘", "6: 自定义照片", "7: 主题包", "9: 组合表盘"
        ])
        basic_form.addRow("clockType:", self.clock_type_combo)

        self.use_state_combo = QComboBox()
        self.use_state_combo.addItems(["1: 使用中", "2: 可用", "4: 未使用"])
        basic_form.addRow("useState:", self.use_state_combo)

        self.dial_dir_edit = QLineEdit()
        basic_form.addRow("dialDir:", self.dial_dir_edit)

        self.version_code_spin = QSpinBox()
        self.version_code_spin.setRange(1, 9999)
        basic_form.addRow("versionCode:", self.version_code_spin)

        self.version_name_edit = QLineEdit()
        basic_form.addRow("versionName:", self.version_name_edit)

        tabs.addTab(basic_tab, "基本配置")

        # Compose dial tab
        compose_tab = QWidget()
        compose_layout = QVBoxLayout(compose_tab)

        compose_info = QLabel("组合表盘元素列表")
        compose_layout.addWidget(compose_info)

        self.element_table = QTableWidget()
        self.element_table.setColumnCount(7)
        self.element_table.setHorizontalHeaderLabels(
            ["组件", "类型", "X", "Y", "宽度", "高度", "版本"])
        self.element_table.horizontalHeader().setStretchLastSection(True)
        self.element_table.setEditTriggers(QTableWidget.DoubleClicked)
        compose_layout.addWidget(self.element_table)

        btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("添加行")
        add_row_btn.clicked.connect(self._add_element_row)
        btn_layout.addWidget(add_row_btn)
        remove_row_btn = QPushButton("删除行")
        remove_row_btn.clicked.connect(self._remove_element_row)
        btn_layout.addWidget(remove_row_btn)
        compose_layout.addLayout(btn_layout)

        tabs.addTab(compose_tab, "组合表盘元素")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_config(self):
        if self.project.project_type == ProjectType.COMPOSE_DIAL and self.project.compose_dial:
            cd = self.project.compose_dial
            self.source_name_edit.setText(str(cd.id))
            self.dial_name_edit.setText(cd.name)
            self.clock_type_combo.setCurrentIndex(3)
            self.dial_dir_edit.setText(f"/sdcard/xtc/dial/compose/custom_dial/{cd.id}/")
            self._load_elements(cd.elementList)
        else:
            self.source_name_edit.setText(self.project.source_name)
            self.dial_name_edit.setText(self.project.name)
            self.dial_dir_edit.setText(f"/sdcard/xtc/dial/{self.project.source_name}/")

        self.version_code_spin.setValue(self.project.version_code)
        self.version_name_edit.setText(self.project.version_name)

    def _load_elements(self, elements: list):
        self.element_table.setRowCount(len(elements))
        for i, e in enumerate(elements):
            self.element_table.setItem(i, 0, QTableWidgetItem(e.component))
            self.element_table.setItem(i, 1, QTableWidgetItem(str(e.type)))
            self.element_table.setItem(i, 2, QTableWidgetItem(str(e.x)))
            self.element_table.setItem(i, 3, QTableWidgetItem(str(e.y)))
            self.element_table.setItem(i, 4, QTableWidgetItem(str(e.width)))
            self.element_table.setItem(i, 5, QTableWidgetItem(str(e.height)))
            self.element_table.setItem(i, 6, QTableWidgetItem(str(e.versionCode)))

    def _add_element_row(self):
        row = self.element_table.rowCount()
        self.element_table.insertRow(row)

    def _remove_element_row(self):
        row = self.element_table.currentRow()
        if row >= 0:
            self.element_table.removeRow(row)

    def _get_elements_from_table(self) -> list:
        elements = []
        for i in range(self.element_table.rowCount()):
            item = self.element_table.item(i, 0)
            if item and item.text().strip():
                elements.append(ThemeAssemblyElement(
                    component=item.text(),
                    type=int(self.element_table.item(i, 1).text() or "1"),
                    x=int(self.element_table.item(i, 2).text() or "0"),
                    y=int(self.element_table.item(i, 3).text() or "0"),
                    width=int(self.element_table.item(i, 4).text() or "100"),
                    height=int(self.element_table.item(i, 5).text() or "100"),
                    versionCode=int(self.element_table.item(i, 6).text() or "1"),
                ))
        return elements

    def _on_accept(self):
        self.project.version_code = self.version_code_spin.value()
        self.project.version_name = self.version_name_edit.text()

        if self.project.project_type == ProjectType.COMPOSE_DIAL:
            if not self.project.compose_dial:
                self.project.compose_dial = NetComposeDial()
            cd = self.project.compose_dial
            try:
                cd.id = int(self.source_name_edit.text())
            except ValueError:
                cd.id = hash(self.source_name_edit.text()) % 900000 + 100000
            cd.name = self.dial_name_edit.text()
            cd.elementList = self._get_elements_from_table()

        self.accept()
