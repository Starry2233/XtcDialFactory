"""Dialog for configuring inter-plugin communication in compose dials."""

from PySide6.QtCore import Qt
from ...models.project import PluginCommunication
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox
)


class CommunicationDialog(QDialog):
    """Configure which components send messages to which."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(f"组件通信配置 - {project.name}")
        self.setMinimumSize(700, 400)
        self._setup_ui()
        self._load_communications()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("配置组合表盘各组件之间的消息通信 (sendMessage / registerCallback):"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["源组件", "目标组件", "Action", "数据模板", "启用"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加行")
        add_btn.clicked.connect(self._add_row)
        btn_layout.addWidget(add_btn)
        remove_btn = QPushButton("删除行")
        remove_btn.clicked.connect(self._remove_row)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _element_names(self):
        """Return component names from the project's element list."""
        if self.project.compose_dial:
            return [e.component for e in self.project.compose_dial.elementList if e.component]
        return []

    def _populate_combo(self, combo: QComboBox, exclude: str = ""):
        """Populate a combo box with element names, optionally excluding one."""
        combo.clear()
        names = self._element_names()
        for name in names:
            if name != exclude:
                combo.addItem(name)

    def _add_row(self, source="", target="", action="", data_template="{}", enabled=True):
        row = self.table.rowCount()
        self.table.insertRow(row)

        names = self._element_names()

        # Source combo
        src_combo = QComboBox()
        for n in names:
            src_combo.addItem(n)
        if source and source in names:
            src_combo.setCurrentText(source)
        elif names:
            src_combo.setCurrentIndex(0)
        self.table.setCellWidget(row, 0, src_combo)

        # Target combo
        tgt_combo = QComboBox()
        for n in names:
            tgt_combo.addItem(n)
        if target and target in names:
            tgt_combo.setCurrentText(target)
        elif len(names) > 1:
            tgt_combo.setCurrentIndex(1)
        self.table.setCellWidget(row, 1, tgt_combo)

        # Action text
        self.table.setItem(row, 2, QTableWidgetItem(action))

        # Data template text
        self.table.setItem(row, 3, QTableWidgetItem(data_template))

        # Enabled checkbox
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        self.table.setItem(row, 4, item)

    def _remove_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _load_communications(self):
        for comm in self.project.communications:
            self._add_row(
                source=comm.source_component,
                target=comm.target_component,
                action=comm.action,
                data_template=comm.data_template,
                enabled=comm.enabled,
            )

    def _collect_communications(self) -> list:
        """Read communication data from the table rows."""
        results = []
        for i in range(self.table.rowCount()):
            src_widget = self.table.cellWidget(i, 0)
            tgt_widget = self.table.cellWidget(i, 1)
            if not src_widget or not tgt_widget:
                continue
            source = src_widget.currentText().strip()
            target = tgt_widget.currentText().strip()
            if not source or not target:
                continue
            action = self.table.item(i, 2).text().strip() if self.table.item(i, 2) else ""
            data_tpl = self.table.item(i, 3).text().strip() if self.table.item(i, 3) else "{}"
            enabled_item = self.table.item(i, 4)
            enabled = enabled_item.checkState() == Qt.Checked if enabled_item else True
            results.append(PluginCommunication(
                source_component=source,
                target_component=target,
                action=action,
                data_template=data_tpl,
                enabled=enabled,
            ))
        return results

    def _on_accept(self):
        comms = self._collect_communications()
        # Validate source != target
        for comm in comms:
            if comm.source_component == comm.target_component:
                QMessageBox.warning(self, "验证失败",
                    f"源组件和目标组件不能相同: {comm.source_component}")
                return
        self.project.communications = comms
        self.accept()
