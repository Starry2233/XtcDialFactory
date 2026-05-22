"""Template marketplace dialog for browsing, importing, and exporting project templates."""

import json
import os
import shutil
import zipfile
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QFileDialog, QMessageBox, QDialogButtonBox, QWidget,
    QTextEdit,
)


TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates")
)


class TemplateMarketDialog(QDialog):
    """Dialog to browse local templates, import/export .xtc-template files, and apply templates."""

    def __init__(self, current_project=None, parent=None):
        super().__init__(parent)
        self.current_project = current_project
        self.selected_template = None
        self.setWindowTitle("模板市场")
        self.setMinimumSize(640, 480)
        self._setup_ui()
        self._refresh_template_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Template list with details panel side by side
        content_layout = QHBoxLayout()

        # Left: template list
        list_group = QGroupBox("本地模板")
        list_layout = QVBoxLayout(list_group)

        self.template_list = QListWidget()
        self.template_list.setSpacing(2)
        self.template_list.setStyleSheet("""
            QListWidget { background: #2b2b2b; border: 1px solid #3a3a3a; font-size: 13px; outline: none; }
            QListWidget::item { padding: 10px 12px; border-radius: 4px; margin: 2px 4px; }
            QListWidget::item:hover { background: #3a3a3a; }
            QListWidget::item:selected { background: #264f78; }
        """)
        self.template_list.currentItemChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.template_list)

        content_layout.addWidget(list_group, 1)

        # Right: template details
        detail_group = QGroupBox("模板详情")
        detail_layout = QVBoxLayout(detail_group)

        self.detail_name = QLabel("<b>名称:</b> ")
        self.detail_name.setWordWrap(True)
        detail_layout.addWidget(self.detail_name)

        self.detail_type = QLabel("<b>类型:</b> ")
        detail_layout.addWidget(self.detail_type)

        self.detail_version = QLabel("<b>版本:</b> ")
        detail_layout.addWidget(self.detail_version)

        self.detail_author = QLabel("<b>作者:</b> ")
        detail_layout.addWidget(self.detail_author)

        self.detail_description = QTextEdit()
        self.detail_description.setReadOnly(True)
        self.detail_description.setMaximumHeight(120)
        self.detail_description.setStyleSheet("background: #1e1e1e; border: 1px solid #3a3a3a; color: #ccc; padding: 6px;")
        detail_layout.addWidget(QLabel("<b>描述:</b>"))
        detail_layout.addWidget(self.detail_description)

        detail_layout.addStretch()
        content_layout.addWidget(detail_group, 1)

        layout.addLayout(content_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        self.import_btn = QPushButton("导入...")
        self.import_btn.setToolTip("从 .xtc-template 文件导入模板")
        self.import_btn.clicked.connect(self._import_template)
        button_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton("导出...")
        self.export_btn.setToolTip("将当前项目导出为 .xtc-template 文件")
        self.export_btn.clicked.connect(self._export_template)
        if self.current_project is None:
            self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()

        self.apply_btn = QPushButton("应用到当前项目")
        self.apply_btn.setToolTip("基于选中模板创建新项目")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_template)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

        # Standard dialog buttons (Close)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_template_list(self):
        """Scan templates directory and populate the list widget."""
        self.template_list.clear()
        self._template_metadata = {}

        if not os.path.isdir(TEMPLATES_DIR):
            return

        for entry in sorted(os.listdir(TEMPLATES_DIR)):
            template_dir = os.path.join(TEMPLATES_DIR, entry)
            if not os.path.isdir(template_dir):
                continue
            if entry.startswith("."):
                continue

            meta_path = os.path.join(template_dir, "template.json")
            config_path = os.path.join(template_dir, "config.json")

            meta = None
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

            if meta is None:
                # Fallback: try config.json based detection
                project_type = "unknown"
                if os.path.isfile(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                        if "elementList" in cfg:
                            project_type = "compose_dial"
                        else:
                            project_type = "cl_dial"
                    except (json.JSONDecodeError, IOError):
                        pass
                elif os.path.isdir(os.path.join(template_dir, "src")):
                    project_type = "cl_dial"

                meta = {
                    "name": entry,
                    "type": project_type,
                    "description": "",
                    "version": "1.0",
                    "author": "",
                }

            display_name = meta.get("name", entry)
            project_type = meta.get("type", "unknown")
            description = meta.get("description", "")

            type_label = {
                "cl_dial": ".cl 传统表盘",
                "pl_plugin": ".pl 组件插件",
                "compose_dial": "组合表盘",
            }.get(project_type, project_type)

            item_text = f"{display_name}  ({type_label})"
            if description:
                item_text += f"\n{description[:60]}{'...' if len(description) > 60 else ''}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, template_dir)
            item.setToolTip(f"{display_name} v{meta.get('version', '1.0')} by {meta.get('author', 'unknown')}")
            self.template_list.addItem(item)

            self._template_metadata[template_dir] = meta

    def _on_selection_changed(self, current, previous):
        """Update detail panel when template selection changes."""
        if current is None:
            self.detail_name.setText("<b>名称:</b> ")
            self.detail_type.setText("<b>类型:</b> ")
            self.detail_version.setText("<b>版本:</b> ")
            self.detail_author.setText("<b>作者:</b> ")
            self.detail_description.clear()
            self.apply_btn.setEnabled(False)
            return

        template_dir = current.data(Qt.UserRole)
        meta = self._template_metadata.get(template_dir, {})

        self.detail_name.setText(f"<b>名称:</b> {meta.get('name', '')}")
        project_type = meta.get("type", "unknown")
        type_label = {
            "cl_dial": ".cl 传统表盘",
            "pl_plugin": ".pl 组件插件",
            "compose_dial": "组合表盘",
        }.get(project_type, project_type)
        self.detail_type.setText(f"<b>类型:</b> {type_label}")
        self.detail_version.setText(f"<b>版本:</b> {meta.get('version', '1.0')}")
        self.detail_author.setText(f"<b>作者:</b> {meta.get('author', '')}")
        self.detail_description.setPlainText(meta.get("description", ""))
        self.apply_btn.setEnabled(True)

    def _import_template(self):
        """Import a .xtc-template zip file and extract it into templates directory."""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入模板", "", "XTC 模板包 (*.xtc-template);;ZIP 文件 (*.zip);;所有文件 (*)"
        )
        if not path:
            return

        try:
            with zipfile.ZipFile(path, "r") as zf:
                # Validate: must contain template.json
                file_list = zf.namelist()
                if "template.json" not in file_list:
                    QMessageBox.warning(self, "导入失败",
                        "选中的文件不是有效的 .xtc-template 包：缺少 template.json")
                    return

                # Read template.json to get the template name
                meta_raw = zf.read("template.json")
                meta = json.loads(meta_raw)
                template_name = meta.get("name", os.path.splitext(os.path.basename(path))[0])

                # Determine target directory (avoid overwriting)
                target_dir = os.path.join(TEMPLATES_DIR, template_name)
                if os.path.exists(target_dir):
                    base_name = template_name
                    counter = 1
                    while os.path.exists(target_dir):
                        target_dir = os.path.join(TEMPLATES_DIR, f"{base_name}_{counter}")
                        counter += 1

                # Extract
                os.makedirs(target_dir, exist_ok=True)
                for member in file_list:
                    # Strip any leading directory components for safety
                    target_path = os.path.join(target_dir, member)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    zf.extract(member, target_dir)

            self._refresh_template_list()
            QMessageBox.information(self, "导入成功",
                f"模板 \"{meta.get('name', template_name)}\" 已导入到模板目录。")

        except (zipfile.BadZipFile, json.JSONDecodeError, IOError) as e:
            QMessageBox.critical(self, "导入失败", f"无法导入模板:\n{e}")

    def _export_template(self):
        """Pack current project into a .xtc-template zip file."""
        if self.current_project is None:
            QMessageBox.information(self, "提示", "请先打开一个项目，然后再导出模板。")
            return

        project_dir = self.current_project.root_dir
        if not project_dir or not os.path.isdir(project_dir):
            QMessageBox.warning(self, "导出失败", "当前项目目录不存在，无法导出。")
            return

        default_name = self.current_project.name or "untitled"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出模板", f"{default_name}.xtc-template",
            "XTC 模板包 (*.xtc-template);;所有文件 (*)"
        )
        if not save_path:
            return

        # Build template metadata
        project_type_value = self.current_project.project_type.value
        meta = {
            "name": self.current_project.name,
            "type": project_type_value,
            "description": f"从项目 \"{self.current_project.name}\" 导出的模板",
            "version": self.current_project.version_name,
            "author": self.current_project.author or "",
        }

        try:
            with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Write template.json at the root
                zf.writestr("template.json", json.dumps(meta, indent=2, ensure_ascii=False))

                # Collect project files to include
                include_extensions = {".json", ".xml", ".java", ".gradle", ".properties", ".txt", ".png", ".jpg", ".jpeg"}
                exclude_dirs = {"build", ".gradle", "__pycache__", ".git"}

                for root, dirs, files in os.walk(project_dir):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        relpath = os.path.relpath(filepath, project_dir)
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in include_extensions or filename == "AndroidManifest.xml":
                            zf.write(filepath, relpath)

            QMessageBox.information(self, "导出成功",
                f"模板已导出到:\n{save_path}")

        except (IOError, OSError) as e:
            QMessageBox.critical(self, "导出失败", f"无法导出模板:\n{e}")

    def _apply_template(self):
        """Copy selected template contents into a new project directory and accept dialog."""
        current = self.template_list.currentItem()
        if current is None:
            QMessageBox.information(self, "提示", "请先选择一个模板。")
            return

        template_dir = current.data(Qt.UserRole)
        meta = self._template_metadata.get(template_dir, {})

        # Ask user where to create the new project
        dest_parent = QFileDialog.getExistingDirectory(
            self, "选择目标目录以创建新项目",
            os.path.dirname(TEMPLATES_DIR)
        )
        if not dest_parent:
            return

        dir_name = meta.get("name", os.path.basename(template_dir))
        dest_dir = os.path.join(dest_parent, dir_name)
        if os.path.exists(dest_dir):
            QMessageBox.warning(self, "创建失败",
                f"目录已存在:\n{dest_dir}\n\n请选择其他位置或删除现有目录。")
            return

        try:
            shutil.copytree(template_dir, dest_dir, ignore=shutil.ignore_patterns("__pycache__"))
            self.selected_template = dest_dir
            self.accept()
        except (IOError, OSError) as e:
            QMessageBox.critical(self, "创建失败", f"无法创建项目目录:\n{e}")
