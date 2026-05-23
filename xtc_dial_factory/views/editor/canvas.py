"""Visual editor canvas for composing watch faces."""

import json
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, Slot, QTimer, QTime, QDate
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QTransform, QShortcut,
    QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeySequence
)
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsItemGroup, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QInputDialog
)

from ...models.project import Project, ThemeAssemblyElement, NetComposeDial


class ElementGraphicsItem(QGraphicsRectItem):
    """A selectable/draggable element on the watch face canvas."""

    def __init__(self, element: ThemeAssemblyElement, parent=None):
        super().__init__(0, 0, element.width, element.height, parent)
        self.element = element
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.OpenHandCursor)
        self._is_hovered = False
        self._preview_text = None

        # Position
        self.setPos(element.x, element.y)
        self.setZValue(-1 if element.type in (5, 7) else 0)  # Background at bottom

        self._update_appearance()

    def _update_appearance(self):
        """Update visual appearance based on element type."""
        type_colors = {
            1: QColor(100, 150, 255, 80),    # Normal (blue)
            5: QColor(100, 100, 100, 120),   # Background plugin (gray)
            7: QColor(100, 100, 100, 120),   # Background GIF (gray)
            11: QColor(255, 200, 50, 80),    # Text (yellow)
        }
        color = type_colors.get(self.element.type, QColor(150, 150, 150, 80))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 200), 1))

        # Component name label
        self._label = f"{self.element.component or 'element'} ({self.element.type})"

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)

        # Draw content
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Arial", 8))

        if self._preview_text:
            # Live preview: draw the time/date text larger
            preview_font = QFont("Arial", self._preview_size or 10)
            painter.setFont(preview_font)
            painter.drawText(self.rect(), Qt.AlignCenter, self._preview_text)
        else:
            painter.drawText(self.rect(), Qt.AlignCenter, self._label)

        # Draw selection border
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 200, 255), 2, Qt.DashLine))
            painter.drawRect(self.rect())

        # Draw hover effect
        if self._is_hovered and not self.isSelected():
            painter.setPen(QPen(QColor(0, 200, 255, 100), 1))
            painter.drawRect(self.rect())

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Snap to grid
            new_pos = value
            grid_size = 5
            new_pos.setX(round(new_pos.x() / grid_size) * grid_size)
            new_pos.setY(round(new_pos.y() / grid_size) * grid_size)
            self.element.x = int(new_pos.x())
            self.element.y = int(new_pos.y())
            return new_pos
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.parent_item_selected()
        return super().itemChange(change, value)

    def parent_item_selected(self):
        if self.scene():
            pass  # Signal handled by scene


class WatchFaceScene(QGraphicsScene):
    """Scene representing a 360x360 square watch face."""

    item_selected = Signal(object)  # Emits ThemeAssemblyElement

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.watch_size = 360
        self.setSceneRect(-5, -5, self.watch_size + 10, self.watch_size + 10)

        # Live preview state
        self._live_preview_enabled = False
        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(1000)
        self._preview_timer.timeout.connect(self._tick)

        # Drag indicator
        self._drag_indicator = None

        self._draw_watch_background()
        self._load_elements()

    def _draw_watch_background(self):
        """Draw the watch face boundary and background."""
        # Watch body (square)
        body = QGraphicsRectItem(0, 0, self.watch_size, self.watch_size)
        body.setBrush(QBrush(QColor(15, 15, 15)))
        body.setPen(QPen(QColor(60, 60, 60), 2))
        self.addItem(body)

        # Center crosshair
        cx = cy = self.watch_size / 2
        cross = QGraphicsItemGroup()
        h_line = QGraphicsRectItem(0, cy - 0.5, self.watch_size, 1)
        h_line.setPen(QPen(QColor(40, 40, 40), 1))
        v_line = QGraphicsRectItem(cx - 0.5, 0, 1, self.watch_size)
        v_line.setPen(QPen(QColor(40, 40, 40), 1))
        cross.addToGroup(h_line)
        cross.addToGroup(v_line)
        self.addItem(cross)

        # Safe zone indicator (inner square at 90% margin)
        margin = self.watch_size * 0.05
        safe = QGraphicsRectItem(
            margin, margin,
            self.watch_size * 0.9, self.watch_size * 0.9
        )
        safe.setPen(QPen(QColor(30, 30, 30), 1, Qt.DashLine))
        safe.setBrush(QBrush(Qt.NoBrush))
        self.addItem(safe)

    def _load_elements(self):
        """Load elements from the compose dial into the scene."""
        if not self.project.compose_dial:
            return
        for element in self.project.compose_dial.elementList:
            item = ElementGraphicsItem(element)
            self.addItem(item)

    def add_element(self, element: ThemeAssemblyElement):
        """Add a new element to the scene and project model."""
        if not self.project.compose_dial:
            self.project.compose_dial = NetComposeDial(
                id=hash(self.project.name) % 900000 + 100000,
                name=self.project.name
            )
        # Background elements go first in the list so they render at the
        # bottom on the device (later addView = higher z-order in FrameLayout)
        if element.type in (5, 7):
            self.project.compose_dial.elementList.insert(0, element)
        else:
            self.project.compose_dial.elementList.append(element)
        item = ElementGraphicsItem(element)
        self.addItem(item)

    def remove_selected(self):
        """Remove currently selected element."""
        for item in self.selectedItems():
            if isinstance(item, ElementGraphicsItem):
                if item.element in self.project.compose_dial.elementList:
                    self.project.compose_dial.elementList.remove(item.element)
                self.removeItem(item)

    def get_element_at(self, pos: QPointF) -> ThemeAssemblyElement | None:
        """Get the element at the given scene position."""
        items = self.items(pos)
        for item in items:
            if isinstance(item, ElementGraphicsItem):
                return item.element
        return None

    # Live preview
    def start_live_preview(self):
        self._live_preview_enabled = True
        self._tick()
        self._preview_timer.start()

    def stop_live_preview(self):
        self._live_preview_enabled = False
        self._preview_timer.stop()
        for item in self.items():
            if isinstance(item, ElementGraphicsItem):
                item._preview_text = None
                item.update()

    def _tick(self):
        now = QTime.currentTime()
        today = QDate.currentDate()
        time_str = now.toString("HH:mm")
        date_str = today.toString("MM/dd")

        for item in self.items():
            if not isinstance(item, ElementGraphicsItem):
                continue
            comp = item.element.component or ""
            if "time" in comp.lower():
                item._preview_text = time_str
                item._preview_size = 18 if item.element.width > 100 else 12
                item.update()
            elif "date" in comp.lower():
                item._preview_text = date_str
                item._preview_size = 14 if item.element.width > 100 else 10
                item.update()
            elif item._preview_text is not None:
                item._preview_text = None
                item.update()

    @property
    def is_preview_active(self):
        return self._live_preview_enabled

    # Drag-and-drop support
    def _parse_drag_data(self, text: str) -> dict | None:
        """Parse drag data: JSON format first, fallback to colon format."""
        # Try JSON format first
        if text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
        # Fallback: old colon-separated format
        parts = text.split(":")
        if len(parts) < 3:
            return None
        try:
            return {
                "component": parts[0],
                "type": int(parts[1]),
                "width": int(parts[2]) if len(parts) > 2 else 100,
                "height": int(parts[3]) if len(parts) > 3 else 100,
                "versionCode": int(parts[4]) if len(parts) > 4 else 1,
                "extra": parts[5] if len(parts) > 5 and parts[5] else "{}",
                "thumbnailUrl": parts[6] if len(parts) > 6 else "",
            }
        except (ValueError, IndexError):
            return None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() and self._parse_drag_data(event.mimeData().text()):
            event.acceptProposedAction()
            self._show_drag_indicator(event.scenePos())
            return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self._update_drag_indicator(event.scenePos())
            return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._hide_drag_indicator()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self._hide_drag_indicator()
        if not event.mimeData().hasText():
            event.ignore()
            return

        data = self._parse_drag_data(event.mimeData().text())
        if not data:
            event.ignore()
            return

        element = ThemeAssemblyElement(
            component=data["component"],
            type=data["type"],
            x=int(event.scenePos().x()),
            y=int(event.scenePos().y()),
            width=data["width"],
            height=data["height"],
            versionCode=data["versionCode"],
            extra=data.get("extra", "{}") or "{}",
            thumbnailUrl=data.get("thumbnailUrl", ""),
        )
        self.add_element(element)
        event.acceptProposedAction()

    def _show_drag_indicator(self, pos: QPointF):
        self._hide_drag_indicator()
        self._drag_indicator = QGraphicsRectItem(0, 0, 100, 60)
        self._drag_indicator.setBrush(QBrush(QColor(0, 200, 255, 40)))
        self._drag_indicator.setPen(QPen(QColor(0, 200, 255, 180), 1, Qt.DashLine))
        self._drag_indicator.setPos(pos.x() - 50, pos.y() - 30)
        self._drag_indicator.setZValue(999)
        self.addItem(self._drag_indicator)

    def _update_drag_indicator(self, pos: QPointF):
        if self._drag_indicator:
            self._drag_indicator.setPos(pos.x() - 50, pos.y() - 30)

    def _hide_drag_indicator(self):
        if self._drag_indicator:
            self.removeItem(self._drag_indicator)
            self._drag_indicator = None


class DialEditorCanvas(QWidget):
    """Watch face visual editor widget."""

    item_selected = Signal(object)  # Emits ThemeAssemblyElement

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar - row 1: component add/remove
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("添加组件:"))
        self.component_combo = QComboBox()
        self.component_combo.addItems([
            "自定义组件",
            "时间: time_no_1",
            "时间: time_no_2",
            "时间: time_no_6",
            "日期: date_1",
            "日期: date_3",
            "日期: date_7",
            "电池: battery_2",
            "电池: battery_3",
            "电池: battery_4",
            "电池: battery_5",
            "电池: battery_7",
            "步数: paipai",
            "步数快捷: shortcut_step",
            "星期: week_1",
            "星期: week_2",
            "文本: text_1",
            "自定义文字: self_text",
            "计时指针: timer_pointer_3",
            "背景图片: 背景_植物",
            "背景图片: 背景_蛋仔派对",
        ])
        toolbar.addWidget(self.component_combo)

        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self._on_add_component)
        toolbar.addWidget(self.add_btn)

        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self._on_remove_component)
        toolbar.addWidget(self.remove_btn)

        toolbar.addStretch()

        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(lambda: self._zoom(1.2))
        toolbar.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(lambda: self._zoom(0.8))
        toolbar.addWidget(self.zoom_out_btn)

        self.preview_btn = QPushButton("预览")
        self.preview_btn.setCheckable(True)
        self.preview_btn.clicked.connect(self._on_toggle_preview)
        toolbar.addWidget(self.preview_btn)

        layout.addLayout(toolbar)

        # Toolbar - row 2: Z-order management
        z_toolbar = QHBoxLayout()
        z_toolbar.addWidget(QLabel("层级:"))

        self.to_front_btn = QPushButton("置顶")
        self.to_front_btn.clicked.connect(self._bring_to_front)
        z_toolbar.addWidget(self.to_front_btn)

        self.to_back_btn = QPushButton("置底")
        self.to_back_btn.clicked.connect(self._send_to_back)
        z_toolbar.addWidget(self.to_back_btn)

        self.raise_btn = QPushButton("上移")
        self.raise_btn.clicked.connect(self._raise_element)
        z_toolbar.addWidget(self.raise_btn)

        self.lower_btn = QPushButton("下移")
        self.lower_btn.clicked.connect(self._lower_element)
        z_toolbar.addWidget(self.lower_btn)

        z_toolbar.addStretch()
        layout.addLayout(z_toolbar)

        # Scene and view
        self.scene = WatchFaceScene(self.project)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setAcceptDrops(True)
        self.view.setMinimumSize(400, 400)
        self.view.setMaximumSize(500, 500)
        self.view.scale(1.1, 1.1)

        # Center the view
        layout.addWidget(self.view, 0, Qt.AlignCenter)

        # Connect selection
        self.scene.selectionChanged.connect(self._on_selection_changed)

        # Keyboard shortcuts for Z-order
        self._shortcut_raise = QShortcut(QKeySequence("Ctrl+Shift+Up"), self)
        self._shortcut_raise.activated.connect(self._raise_element)
        self._shortcut_lower = QShortcut(QKeySequence("Ctrl+Shift+Down"), self)
        self._shortcut_lower.activated.connect(self._lower_element)

    def _on_add_component(self):
        """Add component from combo box selection."""
        idx = self.component_combo.currentIndex()
        # (component, type, width, height, versionCode, extra)
        presets = [
            None,  # 0 = custom
            ("time_no_1", 1, 180, 86, 8, None),
            ("time_no_2", 1, 180, 86, 11, None),
            ("time_no_6", 1, 180, 86, 10, None),
            ("date_1", 1, 112, 29, 4, None),
            ("date_3", 1, 112, 29, 15, None),
            ("date_7", 1, 112, 29, 6, None),
            ("battery_2", 1, 44, 24, 3, None),
            ("battery_3", 1, 44, 24, 4, None),
            ("battery_4", 1, 44, 24, 2, None),
            ("battery_5", 1, 44, 24, 15, None),
            ("battery_7", 1, 44, 24, 9, None),
            ("paipai", 1, 88, 88, 26, None),
            ("shortcut_step", 1, 88, 88, 13, None),
            ("week_1", 1, 88, 24, 3, None),
            ("week_2", 1, 88, 24, 3, None),
            ("text_1", 1, 120, 30, 3, None),
            ("self_text", 11, 180, 40, 26,
             '{"configInfo":"{\\"text\\":\\"自定义文字\\",\\"textSize\\":20}","previewStyle":3,"runMode":2}'),
            ("timer_pointer_3", 1, 88, 88, 17, None),
            ("背景_植物", 5, 360, 360, 1,
             '{"previewStyle":1,"runMode":2}',
             "http://watchcdn.okii.com/watch-smartwatch/pic/1666599397174/bg_plant_1.png"),
            ("背景_蛋仔派对", 5, 360, 360, 1,
             '{"previewStyle":0,"runMode":2}',
             "http://watchcdn.okii.com/watch-smartwatch/pic/1686228315621/danzaipaidui9.png"),
        ]
        if idx == 0:
            name, ok = QInputDialog.getText(self, "自定义组件", "组件名称:")
            if ok and name:
                element = ThemeAssemblyElement(
                    component=name, type=1,
                    x=50, y=50, width=100, height=100,
                )
                self.scene.add_element(element)
        elif 0 < idx < len(presets):
            p = presets[idx]
            element = ThemeAssemblyElement(
                component=p[0], type=p[1],
                x=50, y=50, width=p[2], height=p[3], versionCode=p[4],
                extra=p[5] if p[5] else "{}",
                thumbnailUrl=p[6] if len(p) > 6 else "",
            )
            self.scene.add_element(element)

    def _on_remove_component(self):
        self.scene.remove_selected()

    def _on_selection_changed(self):
        try:
            selected = self.scene.selectedItems()
        except RuntimeError:
            return
        if selected and isinstance(selected[0], ElementGraphicsItem):
            self.item_selected.emit(selected[0].element)

    def _zoom(self, factor: float):
        self.view.scale(factor, factor)

    def _on_toggle_preview(self, checked: bool):
        if checked:
            self.scene.start_live_preview()
            self.preview_btn.setText("停止预览")
        else:
            self.scene.stop_live_preview()
            self.preview_btn.setText("预览")

    # Z-order management
    def _bring_to_front(self):
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], ElementGraphicsItem):
            return
        item = selected[0]
        max_z = 0
        for other in self.scene.items():
            if isinstance(other, ElementGraphicsItem) and other is not item:
                max_z = max(max_z, other.zValue())
        item.setZValue(max_z + 1)

    def _send_to_back(self):
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], ElementGraphicsItem):
            return
        item = selected[0]
        min_z = 0
        for other in self.scene.items():
            if isinstance(other, ElementGraphicsItem) and other is not item:
                min_z = min(min_z, other.zValue())
        item.setZValue(min_z - 1)

    def _raise_element(self):
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], ElementGraphicsItem):
            return
        item = selected[0]
        item.setZValue(item.zValue() + 1)

    def _lower_element(self):
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], ElementGraphicsItem):
            return
        item = selected[0]
        item.setZValue(item.zValue() - 1)
