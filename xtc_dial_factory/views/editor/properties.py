"""Property editor panel for watch face elements."""

import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QLabel, QGroupBox, QPushButton,
    QScrollArea, QPlainTextEdit
)

from ...models.project import ThemeAssemblyElement


class PropertyEditor(QWidget):
    """Right-side panel for editing element properties."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_element: ThemeAssemblyElement | None = None
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title
        self.title_label = QLabel("属性")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        self.no_selection_label = QLabel("\n没有选中的组件\n\n在画布上点击组件以编辑属性")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #888;")
        layout.addWidget(self.no_selection_label)

        # Scrollable property form
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.hide()

        self.form_widget = QWidget()
        self.form = QFormLayout(self.form_widget)

        # Basic properties
        basic_group = QGroupBox("基本属性")
        basic_form = QFormLayout(basic_group)

        self.component_edit = QLineEdit()
        self.component_edit.textChanged.connect(self._on_changed)
        basic_form.addRow("组件名称:", self.component_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["1: 普通组件", "7: 背景组件", "11: 文本组件"])
        self.type_combo.currentIndexChanged.connect(self._on_changed)
        basic_form.addRow("类型:", self.type_combo)

        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 999999)
        self.id_spin.valueChanged.connect(self._on_changed)
        basic_form.addRow("组件ID:", self.id_spin)

        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 9999)
        self.version_spin.valueChanged.connect(self._on_changed)
        basic_form.addRow("版本号:", self.version_spin)

        self.form.addRow(basic_group)

        # Position and size
        pos_group = QGroupBox("位置和大小")
        pos_form = QFormLayout(pos_group)

        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 360)
        self.x_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("X:", self.x_spin)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 360)
        self.y_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("Y:", self.y_spin)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 360)
        self.width_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("宽度:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 360)
        self.height_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("高度:", self.height_spin)

        self.dpx_spin = QDoubleSpinBox()
        self.dpx_spin.setRange(0, 360)
        self.dpx_spin.setDecimals(1)
        self.dpx_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("dpX:", self.dpx_spin)

        self.dpy_spin = QDoubleSpinBox()
        self.dpy_spin.setRange(0, 360)
        self.dpy_spin.setDecimals(1)
        self.dpy_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("dpY:", self.dpy_spin)

        self.dpw_spin = QDoubleSpinBox()
        self.dpw_spin.setRange(0, 360)
        self.dpw_spin.setDecimals(1)
        self.dpw_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("dpWidth:", self.dpw_spin)

        self.dph_spin = QDoubleSpinBox()
        self.dph_spin.setRange(0, 360)
        self.dph_spin.setDecimals(1)
        self.dph_spin.valueChanged.connect(self._on_changed)
        pos_form.addRow("dpHeight:", self.dph_spin)

        self.form.addRow(pos_group)

        # Extra JSON
        extra_group = QGroupBox("扩展配置 (extra JSON)")
        extra_layout = QVBoxLayout(extra_group)

        self.extra_edit = QPlainTextEdit()
        self.extra_edit.setMaximumHeight(120)
        self.extra_edit.textChanged.connect(self._on_changed)
        extra_layout.addWidget(self.extra_edit)

        format_btn = QPushButton("格式化 JSON")
        format_btn.clicked.connect(self._format_extra)
        extra_layout.addWidget(format_btn)

        self.form.addRow(extra_group)

        self.scroll.setWidget(self.form_widget)
        layout.addWidget(self.scroll)
        layout.addStretch()

    def load_element(self, element: ThemeAssemblyElement | None):
        """Load element properties into the editor."""
        if element is None:
            self.clear()
            return

        self.current_element = element
        self._updating = True

        self.no_selection_label.hide()
        self.scroll.show()
        self.title_label.setText(f"属性: {element.component or '(未命名)'}")

        # Populate fields
        self.component_edit.setText(element.component)
        self.type_combo.setCurrentIndex(max(0, self._type_to_index(element.type)))
        self.id_spin.setValue(element.componentId or 0)
        self.version_spin.setValue(element.versionCode)
        self.x_spin.setValue(element.x)
        self.y_spin.setValue(element.y)
        self.width_spin.setValue(element.width)
        self.height_spin.setValue(element.height)
        self.dpx_spin.setValue(element.dpX)
        self.dpy_spin.setValue(element.dpY)
        self.dpw_spin.setValue(element.dpWidth)
        self.dph_spin.setValue(element.dpHeight)

        # Format extra JSON
        try:
            extra_obj = json.loads(element.extra)
            self.extra_edit.setPlainText(json.dumps(extra_obj, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, TypeError):
            self.extra_edit.setPlainText(element.extra)

        self._updating = False

    def clear(self):
        """Clear the editor."""
        self.current_element = None
        self.no_selection_label.show()
        self.scroll.hide()
        self.title_label.setText("属性")

    def _on_changed(self):
        """Update the element when any property changes."""
        if self._updating or not self.current_element:
            return
        self.current_element.component = self.component_edit.text()
        self.current_element.componentId = self.id_spin.value() or None
        self.current_element.type = self._index_to_type(self.type_combo.currentIndex())
        self.current_element.versionCode = self.version_spin.value()
        self.current_element.x = self.x_spin.value()
        self.current_element.y = self.y_spin.value()
        self.current_element.width = self.width_spin.value()
        self.current_element.height = self.height_spin.value()
        self.current_element.dpX = self.dpx_spin.value()
        self.current_element.dpY = self.dpy_spin.value()
        self.current_element.dpWidth = self.dpw_spin.value()
        self.current_element.dpHeight = self.dph_spin.value()

        # Update extra JSON
        extra_text = self.extra_edit.toPlainText()
        try:
            json.loads(extra_text)  # Validate
            self.current_element.extra = extra_text
        except json.JSONDecodeError:
            pass  # Keep old value if invalid JSON

        self.title_label.setText(f"属性: {self.current_element.component or '(未命名)'}")

    def _format_extra(self):
        """Pretty-format the extra JSON."""
        try:
            obj = json.loads(self.extra_edit.toPlainText())
            self.extra_edit.setPlainText(json.dumps(obj, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            pass

    @staticmethod
    def _type_to_index(t: int) -> int:
        return {1: 0, 7: 1, 11: 2}.get(t, 0)

    @staticmethod
    def _index_to_type(i: int) -> int:
        return [1, 7, 11][i] if 0 <= i <= 2 else 1
