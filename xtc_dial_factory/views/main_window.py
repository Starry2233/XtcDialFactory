"""Main window for XTC Dial Factory."""

import os
import json
from pathlib import Path
from PySide6.QtCore import Qt, Slot, Signal, QObject, QThread, QSettings, QByteArray
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QToolBar, QStatusBar, QDockWidget,
    QTreeView, QListWidget, QListWidgetItem, QTabWidget, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QFileDialog, QMenu, QPushButton
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import QFileSystemModel

from .. import __app_name__, __version__
from ..app import AppSettings
from ..build.builder import ProjectBuilder
from ..build.deploy import Deployer
from ..models.project import Project, ProjectType, DialConfig, NetComposeDial, ThemeAssemblyElement, ClockType
from .project_wizard import ProjectWizard
from .editor.canvas import DialEditorCanvas
from .editor.properties import PropertyEditor
from .dialogs.settings import SettingsDialog
from .dialogs.config_editor import ConfigEditor
from .dialogs.communication_dialog import CommunicationDialog
from .dialogs.asset_manager import AssetManagerDialog
from .dialogs.import_plugin import ImportPluginDialog
from .dialogs.version_manager import VersionManagerDialog
from .dialogs.crash_viewer import CrashViewerDialog
from .dialogs.template_market import TemplateMarketDialog
from .dialogs.sdk_docs_viewer import SdkDocsViewerDialog
from .widgets.screen_capture import ScreenCaptureDialog
from .widgets.logcat_viewer import LogcatViewer
from .widgets.output_panel import OutputPanel
from ..widgets.code_editor import FileEditorTab


PALETTE_COMPONENTS = [
    # ── 时间 ──
    ("时间 (time_no_1)", json.dumps({
        "component": "time_no_1", "type": 1,
        "width": 180, "height": 86, "versionCode": 8
    })),
    ("时间 (time_no_2)", json.dumps({
        "component": "time_no_2", "type": 1,
        "width": 180, "height": 86, "versionCode": 11
    })),
    ("时间 (time_no_6)", json.dumps({
        "component": "time_no_6", "type": 1,
        "width": 180, "height": 86, "versionCode": 10
    })),
    # ── 日期 ──
    ("日期 (date_1)", json.dumps({
        "component": "date_1", "type": 1,
        "width": 112, "height": 29, "versionCode": 4
    })),
    ("日期 (date_3)", json.dumps({
        "component": "date_3", "type": 1,
        "width": 112, "height": 29, "versionCode": 15
    })),
    ("日期 (date_7)", json.dumps({
        "component": "date_7", "type": 1,
        "width": 112, "height": 29, "versionCode": 6
    })),
    # ── 电池 ──
    ("电池 (battery_2)", json.dumps({
        "component": "battery_2", "type": 1,
        "width": 44, "height": 24, "versionCode": 3
    })),
    ("电池 (battery_3)", json.dumps({
        "component": "battery_3", "type": 1,
        "width": 44, "height": 24, "versionCode": 4
    })),
    ("电池 (battery_4)", json.dumps({
        "component": "battery_4", "type": 1,
        "width": 44, "height": 24, "versionCode": 2
    })),
    ("电池 (battery_5)", json.dumps({
        "component": "battery_5", "type": 1,
        "width": 44, "height": 24, "versionCode": 15
    })),
    ("电池 (battery_7)", json.dumps({
        "component": "battery_7", "type": 1,
        "width": 44, "height": 24, "versionCode": 9
    })),
    # ── 步数 ──
    ("步数 (paipai)", json.dumps({
        "component": "paipai", "type": 1,
        "width": 88, "height": 88, "versionCode": 26
    })),
    ("步数快捷 (shortcut_step)", json.dumps({
        "component": "shortcut_step", "type": 1,
        "width": 88, "height": 88, "versionCode": 13
    })),
    # ── 星期 ──
    ("星期 (week_1)", json.dumps({
        "component": "week_1", "type": 1,
        "width": 88, "height": 24, "versionCode": 3
    })),
    ("星期 (week_2)", json.dumps({
        "component": "week_2", "type": 1,
        "width": 88, "height": 24, "versionCode": 3
    })),
    # ── 文本 ──
    ("文本 (text_1)", json.dumps({
        "component": "text_1", "type": 1,
        "width": 120, "height": 30, "versionCode": 3
    })),
    ("自定义文字 (self_text)", json.dumps({
        "component": "self_text", "type": 11,
        "width": 180, "height": 40, "versionCode": 26,
        "extra": '{"configInfo":"{\\"text\\":\\"自定义文字\\",\\"textSize\\":20}","previewStyle":3,"runMode":2}'
    })),
    # ── 计时 ──
    ("计时指针 (timer_pointer_3)", json.dumps({
        "component": "timer_pointer_3", "type": 1,
        "width": 88, "height": 88, "versionCode": 17
    })),
    # ── 背景图片 (type=5 静态图片) ──
    ("背景 (背景_植物)", json.dumps({
        "component": "背景_植物", "type": 5,
        "width": 360, "height": 360, "versionCode": 1,
        "extra": '{"previewStyle":1,"runMode":2}',
        "thumbnailUrl": "http://watchcdn.okii.com/watch-smartwatch/pic/1666599397174/bg_plant_1.png"
    })),
    ("背景 (背景_蛋仔派对)", json.dumps({
        "component": "背景_蛋仔派对", "type": 5,
        "width": 360, "height": 360, "versionCode": 1,
        "extra": '{"previewStyle":0,"runMode":2}',
        "thumbnailUrl": "http://watchcdn.okii.com/watch-smartwatch/pic/1686228315621/danzaipaidui9.png"
    })),
]


class PaletteListWidget(QListWidget):
    """QListWidget producing component:type:width:height:versionCode on drag."""

    def mimeData(self, items):
        mime = super().mimeData(items)
        if items:
            item = items[0]
            raw = item.data(Qt.UserRole)
            if raw:
                try:
                    comp = json.loads(raw) if isinstance(raw, str) else raw
                    mime.setText(json.dumps({
                        "component": comp.get("component", ""),
                        "type": comp.get("type", 1),
                        "width": comp.get("width", 100),
                        "height": comp.get("height", 100),
                        "versionCode": comp.get("versionCode", 1),
                        "extra": comp.get("extra", ""),
                        "thumbnailUrl": comp.get("thumbnailUrl", ""),
                    }))
                except (json.JSONDecodeError, TypeError):
                    pass
        return mime


class TaskWorker(QObject):
    """Runs a task function in a background QThread, streaming output via signals."""

    finished = Signal(bool, str)  # success, message
    output_line = Signal(str, str)  # text, type

    def __init__(self, task_fn):
        super().__init__()
        self._task_fn = task_fn

    def run(self):
        """Execute the task; called from QThread.started."""
        try:
            success, msg = self._task_fn(self._on_output)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

    def _on_output(self, text: str, type: str = "info"):
        self.output_line.emit(text, type)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.current_project: Project | None = None
        self._setup_ui()
        self._create_menus()
        self._create_toolbars()
        self._create_docks()
        self._setup_statusbar()
        self._restore_state()

    def _setup_ui(self):
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # Central widget: tabbed editor
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)

        # Welcome tab
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_label = QLabel(
            "<h1>XTC Dial Factory</h1>"
            "<p>小天才电话手表表盘开发IDE</p>"
            "<hr>"
            "<p><b>开始:</b></p>"
            "<ul>"
            "<li>文件 → 新建项目 (Ctrl+N) — 创建新表盘或插件项目</li>"
            "<li>文件 → 打开项目 (Ctrl+O) — 打开已有项目</li>"
            "<li>工具 → 设置 — 配置 SDK 路径和签名信息</li>"
            "</ul>"
            "<p><b>项目类型:</b></p>"
            "<ul>"
            "<li><b>.cl 传统表盘</b> — 自定义表盘 (Java + XML)</li>"
            "<li><b>.pl 组件插件</b> — 组合表盘的元素插件</li>"
            "<li><b>组合表盘</b> — 多元素组合表盘 (配置驱动)</li>"
            "</ul>"
        )
        welcome_label.setWordWrap(True)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.tab_widget.addTab(self.welcome_widget, "欢迎")

        self.setCentralWidget(self.tab_widget)

    def _create_menus(self):
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu("文件(&F)")

        self.new_action = QAction("新建项目(&N)...", self)
        self.new_action.setShortcut(QKeySequence.New)
        self.new_action.triggered.connect(self._new_project)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction("打开项目(&O)...", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self._open_project)
        self.file_menu.addAction(self.open_action)

        self.file_menu.addSeparator()

        self.save_action = QAction("保存(&S)", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self._save_project)
        self.save_action.setEnabled(False)
        self.file_menu.addAction(self.save_action)

        self.save_as_action = QAction("另存为...", self)
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.save_as_action.triggered.connect(self._save_project_as)
        self.save_as_action.setEnabled(False)
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()

        self.config_action = QAction("编辑配置(&C)...", self)
        self.config_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.config_action.triggered.connect(self._edit_config)
        self.config_action.setEnabled(False)
        self.file_menu.addAction(self.config_action)

        self.import_plugin_action = QAction("导入 .pl 组件(&I)...", self)
        self.import_plugin_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_plugin_action.triggered.connect(self._import_plugin)
        self.import_plugin_action.setEnabled(False)
        self.file_menu.addAction(self.import_plugin_action)

        self.file_menu.addSeparator()

        self.template_market_action = QAction("模板市场(&T)...", self)
        self.template_market_action.triggered.connect(self._open_template_market)
        self.file_menu.addAction(self.template_market_action)

        self.file_menu.addSeparator()

        self._recent_project_actions = []
        for path in self.settings.recent_projects:
            if os.path.isdir(path):
                action = QAction(os.path.basename(path), self)
                action.setData(path)
                action.triggered.connect(lambda checked, p=path: self._load_project(p))
                self.file_menu.addAction(action)
                self._recent_project_actions.append(action)

        self._recent_exit_separator = self.file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        # Build menu
        build_menu = menubar.addMenu("构建(&B)")

        self.build_action = QAction("编译(&B)", self)
        self.build_action.setShortcut(QKeySequence("Ctrl+B"))
        self.build_action.triggered.connect(self._build_project)
        self.build_action.setEnabled(False)
        build_menu.addAction(self.build_action)

        self.deploy_action = QAction("部署到设备(&D)", self)
        self.deploy_action.setShortcut(QKeySequence("Ctrl+D"))
        self.deploy_action.triggered.connect(self._deploy_project)
        self.deploy_action.setEnabled(False)
        build_menu.addAction(self.deploy_action)

        build_menu.addSeparator()

        self.build_and_deploy_action = QAction("编译并部署", self)
        self.build_and_deploy_action.setShortcut(QKeySequence("Ctrl+R"))
        self.build_and_deploy_action.triggered.connect(self._build_and_deploy)
        self.build_and_deploy_action.setEnabled(False)
        build_menu.addAction(self.build_and_deploy_action)

        # Tools menu
        tools_menu = menubar.addMenu("工具(&T)")

        self.communication_action = QAction("组件通信(&M)...", self)
        self.communication_action.triggered.connect(self._edit_communications)
        self.communication_action.setEnabled(False)
        tools_menu.addAction(self.communication_action)

        self.asset_action = QAction("资源管理(&A)...", self)
        self.asset_action.triggered.connect(self._edit_assets)
        self.asset_action.setEnabled(False)
        tools_menu.addAction(self.asset_action)

        self.preview_action = QAction("设置缩略图(&P)...", self)
        self.preview_action.triggered.connect(self._set_preview)
        self.preview_action.setEnabled(False)
        tools_menu.addAction(self.preview_action)

        tools_menu.addSeparator()

        self.screen_capture_action = QAction("设备截图(&S)...", self)
        self.screen_capture_action.setShortcut(QKeySequence("Ctrl+Alt+S"))
        self.screen_capture_action.triggered.connect(self._show_screen_capture)
        tools_menu.addAction(self.screen_capture_action)

        tools_menu.addSeparator()

        self.version_manager_action = QAction("版本管理(&V)...", self)
        self.version_manager_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.version_manager_action.triggered.connect(self._manage_version)
        self.version_manager_action.setEnabled(False)
        tools_menu.addAction(self.version_manager_action)

        tools_menu.addSeparator()

        self.logcat_action = QAction("日志查看器(&L)", self)
        self.logcat_action.setShortcut(QKeySequence("Ctrl+L"))
        self.logcat_action.setCheckable(True)
        self.logcat_action.toggled.connect(self._toggle_logcat)
        tools_menu.addAction(self.logcat_action)

        tools_menu.addSeparator()

        settings_action = QAction("设置(&S)...", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("帮助(&H)")

        self.sdk_docs_action = QAction("SDK 文档(&D)...", self)
        self.sdk_docs_action.triggered.connect(self._show_sdk_docs)
        help_menu.addAction(self.sdk_docs_action)

        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        help_menu.addSeparator()

        self.crash_log_action = QAction("错误日志(&E)...", self)
        self.crash_log_action.triggered.connect(self._show_crash_logs)
        help_menu.addAction(self.crash_log_action)

    def _create_toolbars(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.build_action)
        toolbar.addAction(self.deploy_action)

    def _create_docks(self):
        # Project tree dock
        self.project_dock = QDockWidget("项目文件", self)
        self.project_dock.setObjectName("project_dock")
        self.project_tree = QTreeView()
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setAnimated(True)
        self.project_tree.setIndentation(16)
        self.project_tree.doubleClicked.connect(self._on_project_tree_double_click)
        self.project_dock.setWidget(self.project_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_dock)
        self.project_dock.setVisible(False)  # Hidden until a project is loaded

        # Component palette dock
        self.palette_dock = QDockWidget("组件面板", self)
        self.palette_dock.setObjectName("palette_dock")
        self.palette_list = PaletteListWidget()
        self.palette_list.setDragEnabled(True)
        self.palette_list.setSpacing(2)
        self.palette_list.setStyleSheet("""
            QListWidget { background: #2b2b2b; border: none; font-size: 12px; outline: none; }
            QListWidget::item { padding: 6px 8px; border-radius: 4px; margin: 2px 4px; }
            QListWidget::item:hover { background: #3a3a3a; }
            QListWidget::item:selected { background: #264f78; }
        """)
        self._populate_palette()
        self.palette_list.itemDoubleClicked.connect(self._on_palette_double_click)
        self.palette_dock.setWidget(self.palette_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.palette_dock)

        # Property editor dock
        self.property_dock = QDockWidget("属性", self)
        self.property_dock.setObjectName("property_dock")
        self.property_editor = PropertyEditor()
        self.property_dock.setWidget(self.property_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_dock)

        # Logcat viewer dock (hidden by default)
        self.logcat_dock = QDockWidget("日志", self)
        self.logcat_dock.setObjectName("logcat_dock")
        self.logcat_viewer = LogcatViewer()
        self.logcat_dock.setWidget(self.logcat_viewer)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logcat_dock)
        self.logcat_dock.setVisible(False)

        # Build/deploy output dock
        self.output_panel = OutputPanel(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_panel)
        self.output_panel.setVisible(False)

    def _populate_palette(self):
        """Fill palette with all standard component items."""
        self.palette_list.clear()
        for name, data_json in PALETTE_COMPONENTS:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, data_json)
            try:
                info = json.loads(data_json)
                item.setToolTip(
                    "类型: {} | 尺寸: {}x{} | 版本: {}".format(
                        info.get("type", 1), info.get("width", 100),
                        info.get("height", 100), info.get("versionCode", 1)))
            except json.JSONDecodeError:
                pass
            self.palette_list.addItem(item)

    def _update_palette_for_project(self, project_type):
        """Filter palette items based on project type."""
        self.palette_list.clear()
        if project_type == ProjectType.COMPOSE_DIAL:
            self._populate_palette()
            self._populate_custom_plugins()
        else:
            item = QListWidgetItem("组件面板仅用于组合表盘项目")
            item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled
                          & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
            self.palette_list.addItem(item)

    def _populate_custom_plugins(self):
        """Add imported plugin entries to the palette."""
        if not self.current_project:
            return
        for source_name in self.current_project.custom_plugins:
            data = {
                "component": source_name,
                "type": 1,
                "width": 100,
                "height": 100,
                "versionCode": 1,
            }
            data_json = json.dumps(data)
            item = QListWidgetItem(f"导入: {source_name}")
            item.setData(Qt.UserRole, data_json)
            item.setToolTip(f"导入的插件: {source_name} | 类型: 1 | 尺寸: 100x100")
            self.palette_list.addItem(item)

    @Slot()
    def _on_palette_double_click(self, item):
        """Handle double-click: add component to active canvas."""
        raw = item.data(Qt.UserRole)
        if not raw:
            return
        try:
            comp_data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return

        widget = self.tab_widget.currentWidget()
        if not isinstance(widget, DialEditorCanvas):
            QMessageBox.information(self, "提示",
                "请在组合表盘画布中使用组件面板\n\n"
                "打开方式: 加载或新建一个组合表盘项目")
            return

        element = ThemeAssemblyElement(**comp_data)
        widget.scene.add_element(element)
        self.current_project.mark_dirty()
        self.status_label.setText("已添加组件: {}".format(comp_data.get("component", "")))

    def _setup_statusbar(self):
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label, 1)

    def _restore_state(self):
        if not hasattr(self, '_state_restored'):
            settings = QSettings()
            self.restoreGeometry(settings.value("main_geometry", QByteArray()))
            self.restoreState(settings.value("main_state", QByteArray()))
            self._state_restored = True

    def _set_actions_enabled(self, enabled: bool):
        """Enable/disable project/build actions (used while tasks run)."""
        self.build_action.setEnabled(enabled)
        self.deploy_action.setEnabled(enabled)
        self.build_and_deploy_action.setEnabled(enabled)
        self.save_action.setEnabled(enabled)
        self.config_action.setEnabled(enabled)

    def _run_task_async(self, task_fn, title: str):
        """Run *task_fn* in a background QThread, routing output to the panel."""
        self.output_panel.setVisible(True)
        self.output_panel.raise_()
        self.output_panel._on_task_start(title)
        self._set_actions_enabled(False)
        self.status_label.setText(title)

        self._worker_thread = QThread()
        self._worker = TaskWorker(task_fn)
        self._worker.moveToThread(self._worker_thread)
        self._worker.output_line.connect(self.output_panel.append)
        self._worker.finished.connect(self._on_task_finished)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.start()

    @Slot(bool, str)
    def _on_task_finished(self, success: bool, msg: str):
        """Called when an async build/deploy task completes."""
        self._set_actions_enabled(True)
        self.output_panel._on_task_done(success, msg)
        self.status_label.setText(msg.split("\n")[0] if success else "失败")
        if success:
            self.output_panel.append(f"✓ {msg}", "success")
        else:
            self.output_panel.append(f"✗ {msg}", "error")

    def _rebuild_recent_projects(self):
        for action in self._recent_project_actions:
            self.file_menu.removeAction(action)
        self._recent_project_actions.clear()

        for path in self.settings.recent_projects:
            if os.path.isdir(path):
                action = QAction(os.path.basename(path), self)
                action.setData(path)
                action.triggered.connect(lambda checked, p=path: self._load_project(p))
                self.file_menu.insertAction(self._recent_exit_separator, action)
                self._recent_project_actions.append(action)

    def closeEvent(self, event):
        if self.current_project and self.current_project.is_dirty:
            ret = QMessageBox.question(self, "保存更改",
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                self._save_project()
            elif ret == QMessageBox.Cancel:
                event.ignore()
                return

        settings = QSettings()
        settings.setValue("main_geometry", self.saveGeometry())
        settings.setValue("main_state", self.saveState())
        event.accept()

    # === Slots ===

    @Slot()
    def _new_project(self):
        wizard = ProjectWizard(self)
        if wizard.exec():
            project = wizard.created_project
            if project:
                self._load_project(project.root_dir)

    @Slot()
    def _open_project(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if path:
            self._load_project(path)

    @Slot()
    def _save_project(self):
        # Save active editor tab if it's a modified file
        current = self.tab_widget.currentWidget()
        if hasattr(current, 'is_modified') and current.is_modified:
            current.save()
            self.status_label.setText(f"已保存: {os.path.basename(current.file_path)}")
            return
        # Otherwise save the project
        if self.current_project:
            self._write_project_files(self.current_project)
            self.current_project.mark_clean()
            self.status_label.setText(f"已保存: {self.current_project.name}")

    @Slot()
    def _save_project_as(self):
        if not self.current_project:
            return
        path = QFileDialog.getExistingDirectory(self, "选择保存目录",
            os.path.dirname(self.current_project.root_dir))
        if path:
            self.current_project.root_dir = path
            self._write_project_files(self.current_project)
            self.settings.add_recent_project(path)
            self._rebuild_recent_projects()
            self.status_label.setText(f"已保存到: {path}")

    @Slot()
    def _build_project(self):
        if not self.current_project:
            return
        builder = ProjectBuilder(self.settings)
        self._run_task_async(
            lambda cb: builder.build(self.current_project, on_output=cb),
            "编译");

    @Slot()
    def _deploy_project(self):
        if not self.current_project:
            return
        deployer = Deployer(self.settings)
        self._run_task_async(
            lambda cb: deployer.deploy(self.current_project, on_output=cb),
            "部署");

    @Slot()
    def _build_and_deploy(self):
        if not self.current_project:
            return
        builder = ProjectBuilder(self.settings)
        deployer = Deployer(self.settings)

        def pipeline(on_output):
            if on_output:
                on_output("▶ 编译...")
            ok, msg = builder.build(self.current_project, on_output=on_output)
            if not ok:
                return False, f"编译失败: {msg}"
            if on_output:
                on_output("")
                on_output("▶ 部署...")
            return deployer.deploy(self.current_project, on_output=on_output)

        self._run_task_async(pipeline, "编译并部署")

    @Slot()
    def _edit_config(self):
        if not self.current_project:
            return
        dialog = ConfigEditor(self.current_project, self)
        if dialog.exec():
            self._write_project_files(self.current_project)
            self.status_label.setText(f"配置已更新: {self.current_project.name}")

    @Slot()
    def _edit_communications(self):
        if not self.current_project or not self.current_project.compose_dial:
            return
        count = len(self.current_project.compose_dial.elementList)
        if count < 2:
            QMessageBox.information(self, "提示",
                "组合表盘至少需要 2 个组件才能配置通信。\n"
                f"当前仅有 {count} 个组件。")
            return
        dialog = CommunicationDialog(self.current_project, self)
        if dialog.exec():
            self.current_project.mark_dirty()
            self.status_label.setText(f"通信配置已更新: {self.current_project.name}")

    @Slot()
    def _edit_assets(self):
        if not self.current_project:
            return
        dialog = AssetManagerDialog(self.current_project, self)
        if dialog.exec():
            self._write_project_files(self.current_project)
            self.status_label.setText(f"资源已更新: {self.current_project.name}")

    @Slot()
    def _set_preview(self):
        if not self.current_project:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "选择缩略图", self.current_project.root_dir,
            "图片 (*.png *.jpg *.jpeg);;所有文件 (*)"
        )
        if not path:
            return
        rel = os.path.relpath(path, self.current_project.root_dir)
        self.current_project.preview_image = rel
        self.current_project.mark_dirty()
        self._write_project_files(self.current_project)
        self.status_label.setText(f"缩略图已设置: {rel}")

    @Slot()
    def _import_plugin(self):
        """Import a .pl plugin file as a compose component."""
        if not self.current_project or not self.current_project.project_type == ProjectType.COMPOSE_DIAL:
            return
        dialog = ImportPluginDialog(self)
        if not dialog.exec():
            return
        info = dialog.component_info
        source_name = info["source_name"]

        # Register in project model
        self.current_project.register_imported_plugin(source_name)

        # Add to palette
        data = {
            "component": source_name,
            "type": info["type"],
            "width": info["width"],
            "height": info["height"],
            "versionCode": info["version_code"],
            "package_name": info["package_name"],
        }
        data_json = json.dumps(data)
        display = info["display_name"]
        item = QListWidgetItem(f"导入: {display} ({source_name})")
        item.setData(Qt.UserRole, data_json)
        item.setToolTip(
            "导入的插件: {0} | 类型: {1} | 尺寸: {2}x{3}".format(
                source_name, info["type"], info["width"], info["height"]))
        # Insert after standard components
        self.palette_list.addItem(item)

        # Add to active canvas if available
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, DialEditorCanvas):
            element = ThemeAssemblyElement(
                component=source_name,
                type=info["type"],
                x=50, y=50,
                width=info["width"],
                height=info["height"],
                versionCode=info["version_code"],
            )
            widget.scene.add_element(element)

        self.status_label.setText("已导入插件: {}".format(display))

    @Slot()
    def _open_template_market(self):
        """Open the template marketplace dialog."""
        dialog = TemplateMarketDialog(self.current_project, self)
        if dialog.exec():
            template_dir = dialog.selected_template
            if template_dir:
                self._load_project(template_dir)

    @Slot()
    def _manage_version(self):
        """Open the version manager dialog."""
        if not self.current_project:
            return
        dialog = VersionManagerDialog(self.current_project, self)
        if dialog.exec():
            self.current_project.mark_dirty()
            self._save_project()
            self.status_label.setText(f"版本已更新: {self.current_project.version_name}")

    @Slot()
    def _show_screen_capture(self):
        dialog = ScreenCaptureDialog(self)
        dialog.exec()

    @Slot(bool)
    def _toggle_logcat(self, visible: bool):
        """Show or hide the logcat viewer dock."""
        self.logcat_dock.setVisible(visible)
        if visible:
            self.logcat_viewer.start()
        else:
            self.logcat_viewer.stop()

    @Slot()
    def _show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.updated_settings

    @Slot()
    def _show_about(self):
        QMessageBox.about(self, f"关于 {__app_name__}",
            f"<h3>{__app_name__} v{__version__}</h3>"
            "<p>小天才电话手表表盘开发IDE</p>"
            "<p>基于 PySide6 构建</p>"
            "<hr>"
            "<p>支持 .cl 传统表盘、.pl 组件插件、组合表盘开发</p>")

    @Slot()
    def _show_sdk_docs(self):
        """Open the SDK documentation viewer."""
        dialog = SdkDocsViewerDialog(self)
        dialog.exec()

    @Slot()
    def _show_crash_logs(self):
        """Open the crash log viewer dialog."""
        dialog = CrashViewerDialog(self)
        dialog.exec()

    # === File tree and code editor ===

    def _setup_project_tree(self, root_dir: str):
        """Set up the file tree to show project files."""
        if not hasattr(self, '_fs_model'):
            self._fs_model = QFileSystemModel()
            self._fs_model.setRootPath("")
            self._fs_model.setNameFilters(["*.java", "*.xml", "*.json", "*.cfg",
                                           "*.properties", "*.gradle", "*.txt", "*.md",
                                           "*.png", "*.jpg", "*.gif", "*.cl", "*.pl",
                                           "*.bat", "*.sh", "*.xtcproject"])
            self._fs_model.setNameFilterDisables(False)
            self.project_tree.setModel(self._fs_model)

        self._fs_model.setRootPath(root_dir)
        self.project_tree.setRootIndex(self._fs_model.index(root_dir))

        # Hide known generated/build directories
        for i in range(1, self._fs_model.columnCount()):
            self.project_tree.hideColumn(i)
        self.project_tree.setColumnWidth(0, 280)

        self.project_dock.setWindowTitle(f"项目文件 - {os.path.basename(root_dir)}")
        self.project_dock.setVisible(True)

    def _on_project_tree_double_click(self, index):
        """Open a file in the editor tab when double-clicked."""
        path = self._fs_model.filePath(index)
        if not path:
            return
        if os.path.isfile(path):
            self._open_file_in_editor(path)

    def _open_file_in_editor(self, file_path: str):
        """Open a file in a new editor tab."""
        # Check if already open
        basename = os.path.basename(file_path)
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'file_path') and widget.file_path == file_path:
                self.tab_widget.setCurrentIndex(i)
                return

        # Create editor tab
        editor_tab = FileEditorTab(file_path, self)
        index = self.tab_widget.addTab(editor_tab, basename)
        self.tab_widget.setCurrentIndex(index)

    def _close_tab(self, index: int):
        """Close a tab, checking for unsaved changes."""
        widget = self.tab_widget.widget(index)
        if hasattr(widget, 'is_modified') and widget.is_modified:
            name = self.tab_widget.tabText(index)
            ret = QMessageBox.question(
                self, "未保存",
                f"文件 {name} 已修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:
                return
            if ret == QMessageBox.Save:
                widget.save()
        self.tab_widget.removeTab(index)

    # === Project Loading ===

    def _load_project(self, path: str):
        """Load a project from directory."""
        project_file = os.path.join(path, ".xtcproject")
        if os.path.exists(project_file):
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            project = Project.from_dict(data)
            project.root_dir = path
        else:
            # Try to detect project type
            project = self._detect_project(path)
            if not project:
                QMessageBox.warning(self, "无效项目",
                    f"目录 {path} 不是一个有效的 XTC 项目")
                return

        # Load compose dial elements from config.json
        if project.project_type == ProjectType.COMPOSE_DIAL:
            config_path = project.get_config_path()
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    project.compose_dial = NetComposeDial.from_json(f.read())

        self.current_project = project
        self.settings.add_recent_project(path)
        self._rebuild_recent_projects()

        # Enable relevant actions
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.config_action.setEnabled(True)
        self.build_action.setEnabled(True)
        self.deploy_action.setEnabled(True)
        self.build_and_deploy_action.setEnabled(True)
        self.version_manager_action.setEnabled(True)

        # Import plugin action: only for compose dial projects
        self.import_plugin_action.setEnabled(
            project.project_type == ProjectType.COMPOSE_DIAL)

        # Communication action: only for compose dial with >= 2 elements
        has_elements = bool(
            project.project_type == ProjectType.COMPOSE_DIAL
            and project.compose_dial
            and len(project.compose_dial.elementList) >= 2
        )
        self.communication_action.setEnabled(has_elements)

        # Asset action: only for compose dial projects
        self.asset_action.setEnabled(
            project.project_type == ProjectType.COMPOSE_DIAL
        )
        self.preview_action.setEnabled(
            project.project_type in (ProjectType.CL_DIAL, ProjectType.COMPOSE_DIAL)
        )

        # Update window title
        self.setWindowTitle(f"{project.name} - {__app_name__}")

        # Set up project file tree
        self._setup_project_tree(path)

        # Open project in editor
        self._open_editor(project)
        self._update_palette_for_project(project.project_type)
        self.status_label.setText(f"已加载: {project.name}")

    def _detect_project(self, path: str) -> Project | None:
        """Detect project type from directory contents."""
        config_path = os.path.join(path, "config.json")
        manifest_path = os.path.join(path, "AndroidManifest.xml")

        if not os.path.isdir(path):
            return None

        # Check for compose dial config
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "elementList" in data:
                    project = Project(data.get("name", os.path.basename(path)),
                                      ProjectType.COMPOSE_DIAL)
                    project.compose_dial = NetComposeDial.from_json(json.dumps(data))
                    project.root_dir = path
                    return project
            except (json.JSONDecodeError, KeyError):
                pass

        # Check for .cl / .pl project
        if os.path.exists(manifest_path):
            has_src = os.path.isdir(os.path.join(path, "src"))
            if has_src:
                # Check for DialViewImpl
                src_files = list(Path(path).rglob("DialViewImpl.java"))
                if src_files:
                    project = Project(os.path.basename(path), ProjectType.CL_DIAL)
                    project.root_dir = path
                    return project
                # Check for Plugin.java
                src_files = list(Path(path).rglob("Plugin.java"))
                if src_files:
                    project = Project(os.path.basename(path), ProjectType.PL_PLUGIN)
                    project.root_dir = path
                    return project

        # Generic project
        project = Project(os.path.basename(path), ProjectType.CL_DIAL)
        project.root_dir = path
        return project

    def _open_editor(self, project: Project):
        """Open the appropriate editor for the project type."""
        # Remove welcome tab if present
        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "欢迎":
            self.tab_widget.clear()

        if project.project_type == ProjectType.COMPOSE_DIAL:
            canvas = DialEditorCanvas(project)
            canvas.item_selected.connect(self.property_editor.load_element)
            index = self.tab_widget.addTab(canvas, f"画布: {project.name}")
            self.tab_widget.setCurrentIndex(index)

        else:
            # CL dial / PL plugin: show project overview with source file list
            overview = self._create_project_overview(project)
            type_label = ".cl 传统表盘" if project.project_type == ProjectType.CL_DIAL else ".pl 组件插件"
            index = self.tab_widget.addTab(overview, f"{type_label}: {project.name}")
            self.tab_widget.setCurrentIndex(index)

    def _create_project_overview(self, project: Project) -> QWidget:
        """Create an overview page with key source files listed."""

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        type_label = ".cl 传统表盘" if project.project_type == ProjectType.CL_DIAL else ".pl 组件插件"

        # Header
        header = QLabel(
            f"<h2>{project.name}</h2>"
            f"<p><b>类型:</b> {type_label}</p>"
            f"<p><b>包名:</b> {project.package_name}</p>"
            f"<p><b>位置:</b> {project.root_dir}</p>"
            f"<hr>"
            f"<p><b>快捷键:</b> Ctrl+B 编译 | Ctrl+D 部署 | Ctrl+R 编译并部署</p>"
        )
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Source file list
        src_dir = os.path.join(project.root_dir, "src", "main", "java")
        src_files = []
        if os.path.isdir(src_dir):
            for root, dirs, files in os.walk(src_dir):
                for f in files:
                    if f.endswith(".java"):
                        src_files.append(os.path.join(root, f))

        if src_files:
            files_label = QLabel("<p><b>源文件 (双击打开):</b></p>")
            layout.addWidget(files_label)

            file_list = QListWidget()
            file_list.setMaximumWidth(600)
            file_list.setMaximumHeight(250)
            file_list.setStyleSheet("""
                QListWidget { background: transparent; border: none; }
                QListWidget::item { padding: 4px 8px; border-radius: 3px; }
                QListWidget::item:hover { background: #3a3a3a; }
            """)
            for sf in sorted(src_files):
                rel = os.path.relpath(sf, project.root_dir)
                item = QListWidgetItem(f"  {rel}")
                item.setData(Qt.UserRole, sf)
                file_list.addItem(item)
            file_list.itemDoubleClicked.connect(
                lambda item: self._open_file_in_editor(item.data(Qt.UserRole)))
            layout.addWidget(file_list, 0, Qt.AlignCenter)
        else:
            no_src = QLabel("<p><i>无源文件 — 在 src/main/java/ 目录中添加 .java 文件</i></p>")
            no_src.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_src)

        # Config file links
        for cfg_name in ["AndroidManifest.xml", "config.json"]:
            cfg_path = os.path.join(project.root_dir, cfg_name)
            if os.path.exists(cfg_path):
                link = QPushButton(f"打开 {cfg_name}")
                link.setFlat(True)
                link.setStyleSheet("color: #4da6ff; text-decoration: none; padding: 2px;")
                link.clicked.connect(lambda checked, p=cfg_path: self._open_file_in_editor(p))
                layout.addWidget(link, 0, Qt.AlignCenter)

        # Quick action buttons
        btn_layout = QHBoxLayout()
        for text, slot in [
            ("编译 (Ctrl+B)", self._build_project),
            ("部署 (Ctrl+D)", self._deploy_project),
            ("编译并部署 (Ctrl+R)", self._build_and_deploy),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def _write_project_files(self, project: Project):
        """Write all project files to disk."""
        os.makedirs(project.root_dir, exist_ok=True)

        # Write .xtcproject file
        with open(os.path.join(project.root_dir, ".xtcproject"), "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)

        # Write config files
        if project.project_type == ProjectType.COMPOSE_DIAL and project.compose_dial:
            with open(project.get_config_path(), "w", encoding="utf-8") as f:
                f.write(project.compose_dial.to_json())
        elif project.project_type in (ProjectType.CL_DIAL, ProjectType.PL_PLUGIN):
            config = {
                "sourceName": project.source_name,
                "dialName": project.name,
                "clockType": ClockTypeForProjectType(project.project_type),
                "useState": 1,
                "dialDir": f"/sdcard/xtc/dial/{project.source_name}/" if project.project_type == ProjectType.CL_DIAL else "",
                "versionCode": project.version_code
            }
            with open(project.get_config_path(), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)


def ClockTypeForProjectType(pt: ProjectType) -> int:
    if pt == ProjectType.CL_DIAL:
        return ClockType.TRADITIONAL_CL.value
    elif pt == ProjectType.PL_PLUGIN:
        return 1  # Plugins use type 1 within compose dials
    return 9
