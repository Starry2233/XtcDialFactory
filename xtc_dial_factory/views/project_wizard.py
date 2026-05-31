"""New project creation wizard."""

import os
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton, QFileDialog,
    QMessageBox, QRadioButton, QButtonGroup, QGroupBox, QCheckBox
)
from PySide6.QtGui import QPixmap, QIcon

from ..models.project import (Project, ProjectType, NetComposeDial, ThemeAssemblyElement,
                               DialConfig, ThemePackConfig, IconPackConfig)


class ProjectTypePage(QWizardPage):
    """Page 1: Select project type."""

    def __init__(self):
        super().__init__()
        self.setTitle("选择项目类型")
        self.setSubTitle("选择要创建的表盘或组件项目类型")

        layout = QVBoxLayout(self)

        self.type_group = QButtonGroup(self)

        # CL Dial
        self.rb_cl = QRadioButton(".cl 传统表盘")
        self.rb_cl.setToolTip("自定义表盘，通过 Java 代码渲染整个表盘界面")
        layout.addWidget(self.rb_cl)
        self.type_group.addButton(self.rb_cl, 0)

        # PL Plugin
        self.rb_pl = QRadioButton(".pl 组件插件")
        self.rb_pl.setToolTip("组合表盘的元素插件，如时间、日期、电池、自定义组件")
        layout.addWidget(self.rb_pl)
        self.type_group.addButton(self.rb_pl, 1)

        # Compose Dial
        self.rb_compose = QRadioButton("组合表盘 (DIY)")
        self.rb_compose.setToolTip("通过 JSON 配置组合多个 .pl 插件形成一个完整表盘")
        layout.addWidget(self.rb_compose)
        self.type_group.addButton(self.rb_compose, 2)

        # Theme Package
        self.rb_theme = QRadioButton("主题包")
        self.rb_theme.setToolTip("包含表盘 + 图标包 + 可选附加组件（背景、充电动画、AOD等）")
        layout.addWidget(self.rb_theme)
        self.type_group.addButton(self.rb_theme, 3)

        # Icon Package
        self.rb_icon = QRadioButton("图标包")
        self.rb_icon.setToolTip("自定义应用图标样式（大小、颜色、遮罩）")
        layout.addWidget(self.rb_icon)
        self.type_group.addButton(self.rb_icon, 4)

        self.rb_cl.setChecked(True)
        layout.addStretch()

    def project_type(self) -> ProjectType:
        id = self.type_group.checkedId()
        return [ProjectType.CL_DIAL, ProjectType.PL_PLUGIN,
                ProjectType.COMPOSE_DIAL, ProjectType.THEME_PACKAGE,
                ProjectType.ICON_PACKAGE][id]


class ProjectInfoPage(QWizardPage):
    """Page 2: Project name, package, author, etc."""

    def __init__(self):
        super().__init__()
        self.setTitle("项目信息")
        self.setSubTitle("设置项目名称和基本信息")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: MyWatchFace")
        layout.addRow("项目名称:", self.name_edit)
        self.registerField("projectName*", self.name_edit)

        self.package_edit = QLineEdit()
        self.package_edit.setPlaceholderText("com.xtc.mywatchface")
        layout.addRow("包名:", self.package_edit)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("作者名")
        layout.addRow("作者:", self.author_edit)

        self.version_code_spin = QSpinBox()
        self.version_code_spin.setRange(1, 9999)
        self.version_code_spin.setValue(1)
        layout.addRow("版本号:", self.version_code_spin)

        self.version_name_edit = QLineEdit("1.0.0")
        layout.addRow("版本名称:", self.version_name_edit)

        # Plugin type for .pl projects (determines DIY editor category)
        self.plugin_type_combo = QComboBox()
        self.plugin_type_combo.addItem("普通组件 (type=1)", 1)
        self.plugin_type_combo.addItem("背景组件 (type=7)", 7)
        self.plugin_type_combo.addItem("文本组件 (type=11)", 11)
        self.plugin_type_combo.setToolTip(
            "DIY 表盘编辑器中的组件分类：\n"
            "  普通组件 — 时间、日期、电池、步数、天气等\n"
            "  背景组件 — 全屏背景（GIF/图片）\n"
            "  文本组件 — 自定义文本显示"
        )
        layout.addRow("组件类型:", self.plugin_type_combo)

        self.name_edit.textChanged.connect(self._update_package)
        self.name_edit.textChanged.connect(self.completeChanged)
        self.name_edit.textChanged.connect(self._on_type_changed)
        self.plugin_type_combo.currentIndexChanged.connect(self.completeChanged)

    def _on_type_changed(self, name: str):
        # Show/hide plugin type combo based on project type
        # (the wizard type page hasn't been committed yet at creation time,
        #  so we check at runtime via parent().type_page)
        pass

    def _update_package(self, name: str):
        if name and not self.package_edit.isModified():
            self.package_edit.setText(f"com.xtc.{name.lower()}")

    def isComplete(self):
        return bool(self.name_edit.text().strip())


class ProjectLocationPage(QWizardPage):
    """Page 3: Project location."""

    def __init__(self):
        super().__init__()
        self.setTitle("项目位置")
        self.setSubTitle("选择项目保存目录")

        layout = QHBoxLayout(self)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(os.path.expanduser("~/XtcDialProjects"))
        layout.addWidget(self.path_edit)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if path:
            self.path_edit.setText(path)

    def project_path(self) -> str:
        base = self.path_edit.text().strip() or os.path.expanduser("~/XtcDialProjects")
        name = self.field("projectName")
        return os.path.join(base, name)


class ComposeConfigPage(QWizardPage):
    """Page 4 (optional): Compose dial initial configuration."""

    def __init__(self):
        super().__init__()
        self.setTitle("组合表盘配置")
        self.setSubTitle("添加初始组件元素")

        layout = QVBoxLayout(self)

        # Template selection
        template_group = QGroupBox("快速模板")
        t_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("空白组合表盘", "empty")
        self.template_combo.addItem("基础表盘 (时间 + 日期)", "basic")
        self.template_combo.addItem("完整表盘 (时间 + 日期 + 电池 + 步数)", "full")
        t_layout.addWidget(self.template_combo)
        layout.addWidget(template_group)

        # Preview info
        info = QLabel("组合表盘通过 JSON 配置驱动，无需编译 Java 代码。\n"
                       "之后可以在可视化编辑器中添加/调整组件。")
        info.setStyleSheet("padding: 8px;")
        layout.addWidget(info)
        layout.addStretch()

    def get_elements(self) -> list:
        template = self.template_combo.currentData()
        if template == "basic":
            return [
                ThemeAssemblyElement(component="time_no_6", componentId=916, type=1,
                    x=56, y=3, width=180, height=86, versionCode=10),
                ThemeAssemblyElement(component="date_3", componentId=20, type=1,
                    x=38, y=82, width=112, height=29, versionCode=15),
            ]
        elif template == "full":
            return [
                ThemeAssemblyElement(component="time_no_6", componentId=916, type=1,
                    x=56, y=3, width=180, height=86, versionCode=10),
                ThemeAssemblyElement(component="date_3", componentId=20, type=1,
                    x=38, y=82, width=112, height=29, versionCode=15),
                ThemeAssemblyElement(component="battery_5", componentId=19, type=1,
                    x=169, y=91, width=44, height=24, versionCode=15),
            ]
        return []


class ThemePackConfigPage(QWizardPage):
    """Page for theme package configuration."""

    def __init__(self):
        super().__init__()
        self.setTitle("主题包配置")
        self.setSubTitle("配置主题包包含的内容")

        layout = QVBoxLayout(self)

        # Dial source selection
        dial_group = QGroupBox("表盘设置")
        dial_layout = QFormLayout(dial_group)
        self.dial_source_edit = QLineEdit()
        self.dial_source_edit.setPlaceholderText("现有 dial 的 sourceName（可选）")
        dial_layout.addRow("表盘 sourceName:", self.dial_source_edit)
        layout.addWidget(dial_group)

        # Theme extras
        extras_group = QGroupBox("附加组件（可选）")
        extras_layout = QVBoxLayout(extras_group)

        self.include_icon_pack = QCheckBox("包含图标包")
        self.include_icon_pack.setChecked(True)
        extras_layout.addWidget(self.include_icon_pack)

        self.include_bg = QCheckBox("包含背景配置")
        extras_layout.addWidget(self.include_bg)

        self.include_charge = QCheckBox("包含充电动画")
        extras_layout.addWidget(self.include_charge)

        self.include_aod = QCheckBox("包含 AOD 息屏显示")
        extras_layout.addWidget(self.include_aod)

        self.include_turn = QCheckBox("包含唤醒动画")
        extras_layout.addWidget(self.include_turn)

        layout.addWidget(extras_group)
        layout.addStretch()


class IconPackConfigPage(QWizardPage):
    """Page for icon package configuration."""

    def __init__(self):
        super().__init__()
        self.setTitle("图标包配置")
        self.setSubTitle("设置图标样式参数")

        layout = QFormLayout(self)

        self.icon_name_edit = QLineEdit()
        self.icon_name_edit.setPlaceholderText("我的图标包")
        layout.addRow("图标包名称:", self.icon_name_edit)

        self.icon_dp_spin = QSpinBox()
        self.icon_dp_spin.setRange(24, 128)
        self.icon_dp_spin.setValue(48)
        self.icon_dp_spin.setSuffix(" dp")
        layout.addRow("图标大小:", self.icon_dp_spin)

        self.name_color_edit = QLineEdit("#FFFFFF")
        layout.addRow("应用名颜色:", self.name_color_edit)

        self.convert_type_combo = QComboBox()
        self.convert_type_combo.addItem("无转换", 0)
        self.convert_type_combo.addItem("遮罩模式", 1)
        self.convert_type_combo.addItem("缩放模式", 2)
        layout.addRow("图标转换类型:", self.convert_type_combo)

        info = QLabel("图标资源 PNG 文件可以在创建项目后添加到 assets 目录中。")
        info.setWordWrap(True)
        layout.addRow(info)


class ProjectWizard(QWizard):
    """Wizard for creating new XTC projects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumSize(600, 500)

        self.created_project: Project | None = None

        # Pages (always added; visibility controlled via nextId)
        self.type_page = ProjectTypePage()
        self.info_page = ProjectInfoPage()
        self.loc_page = ProjectLocationPage()
        self.compose_page = ComposeConfigPage()
        self.theme_page = ThemePackConfigPage()
        self.icon_page = IconPackConfigPage()

        self.addPage(self.type_page)
        self.addPage(self.info_page)
        self.addPage(self.loc_page)
        self.addPage(self.compose_page)
        self.addPage(self.theme_page)
        self.addPage(self.icon_page)

    def nextId(self) -> int:
        """Control page flow based on project type."""
        current_id = self.currentId()
        if current_id == 0:  # ProjectTypePage -> InfoPage (always)
            return 1
        elif current_id == 1:  # InfoPage -> LocationPage (always)
            return 2
        elif current_id == 2:  # LocationPage -> conditional config page
            ptype = self.type_page.project_type()
            if ptype == ProjectType.COMPOSE_DIAL:
                return 3
            elif ptype == ProjectType.THEME_PACKAGE:
                return 4
            elif ptype == ProjectType.ICON_PACKAGE:
                return 5
            else:  # CL_DIAL or PL_PLUGIN — done
                return -1
        elif current_id in (3, 4, 5):
            return -1  # last page
        return super().nextId()

        # Each page needs autoFillBackground so stylesheet background-color takes effect
        for page_id in self.pageIds():
            p = self.page(page_id)
            p.setAutoFillBackground(True)

        self.setStartId(0)

    def accept(self):
        """Create project when wizard is accepted."""
        try:
            project = self._create_project()
            if project:
                self.created_project = project
                super().accept()
        except Exception as e:
            QMessageBox.critical(self, "创建失败", f"项目创建失败:\n{str(e)}")

    def _create_project(self) -> Project | None:
        type_page = self.page(0)
        info_page = self.page(1)
        loc_page = self.page(2)
        compose_page = self.page(3)
        theme_page = self.page(4)
        icon_page = self.page(5)

        ptype = type_page.project_type()
        name = info_page.name_edit.text().strip()
        package = info_page.package_edit.text().strip() or f"com.xtc.{name.lower()}"
        author = info_page.author_edit.text().strip()

        project = Project(name, ptype, package, author)
        project.version_code = info_page.version_code_spin.value()
        project.version_name = info_page.version_name_edit.text().strip()

        project.root_dir = loc_page.project_path()

        # Create project directory
        os.makedirs(project.root_dir, exist_ok=True)

        if ptype == ProjectType.COMPOSE_DIAL:
            self._create_compose_dial(project, compose_page)
        elif ptype == ProjectType.CL_DIAL:
            self._create_cl_dial(project)
        elif ptype == ProjectType.PL_PLUGIN:
            project.plugin_type = info_page.plugin_type_combo.currentData()
            self._create_pl_plugin(project)
        elif ptype == ProjectType.THEME_PACKAGE:
            self._create_theme_package(project, theme_page)
        elif ptype == ProjectType.ICON_PACKAGE:
            self._create_icon_package(project, icon_page)

        # Write project file
        project_file = os.path.join(project.root_dir, ".xtcproject")
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)

        return project

    def _create_compose_dial(self, project: Project, compose_page: ComposeConfigPage):
        """Initialize compose dial project."""
        dial_id = hash(project.name) % 900000 + 100000  # Generate ID like device
        elements = compose_page.get_elements()

        compose_dial = NetComposeDial(
            id=dial_id,
            name=project.name,
            elementList=elements
        )
        project.compose_dial = compose_dial

        # Write config.json
        config_path = os.path.join(project.root_dir, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(compose_dial.to_json())

        # Create custom_dial directory structure
        dial_dir = f"/sdcard/xtc/dial/compose/custom_dial/{dial_id}/"
        os.makedirs(os.path.join(project.root_dir, "target"), exist_ok=True)

        # Write deployment info
        deploy_info = {
            "device_path": dial_dir,
            "config_file": "config.json"
        }
        with open(os.path.join(project.root_dir, "deploy.json"), "w") as f:
            json.dump(deploy_info, f, indent=2)

    def _create_cl_dial(self, project: Project):
        """Initialize .cl traditional dial project."""
        pkg_dir = os.path.join(project.root_dir, "src", "main", "java",
                               *project.package_name.split("."))
        os.makedirs(pkg_dir, exist_ok=True)

        # Write DialViewImpl.java
        dial_java = f'''package {project.package_name};

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.view.View;
import com.xtc.common.BaseDial;

public class DialViewImpl {{
    public static BaseDial getDialView(Context context, String sourceName) {{
        return new ClockDial(context);
    }}

    static class ClockDial extends BaseDial {{
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private String timeText = "12:00";

        public ClockDial(Context context) {{
            super(context);
            paint.setColor(Color.WHITE);
            paint.setTextSize(48);
            paint.setTypeface(Typeface.DEFAULT_BOLD);
            paint.setTextAlign(Paint.Align.CENTER);
        }}

        @Override
        protected void onDraw(Canvas canvas) {{
            super.onDraw(canvas);
            int cx = getWidth() / 2;
            int cy = getHeight() / 2;
            canvas.drawColor(Color.parseColor("#22000000"));
            canvas.drawText(timeText, cx, cy + 16, paint);
        }}

        @Override
        public void updateTime() {{
            java.text.SimpleDateFormat sdf =
                new java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault());
            this.timeText = sdf.format(new java.util.Date());
            invalidate();
        }}

        @Override
        public void setShow(boolean show) {{
            setVisibility(show ? VISIBLE : GONE);
        }}

        @Override
        public String[] getMethodString() {{
            return new String[]{{"updateTime", "setShow"}};
        }}
    }}
}}
'''
        with open(os.path.join(pkg_dir, "DialViewImpl.java"), "w", encoding="utf-8") as f:
            f.write(dial_java)

        # Write AndroidManifest.xml
        manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="''' + project.package_name + '''">
    <application android:label="''' + project.name + '''" />
</manifest>
'''
        with open(os.path.join(project.root_dir, "AndroidManifest.xml"), "w", encoding="utf-8") as f:
            f.write(manifest)

        # Write config.json
        config = {
            "sourceName": project.source_name,
            "dialName": project.name,
            "clockType": 1,
            "useState": 1,
            "dialDir": f"/sdcard/xtc/dial/{project.source_name}/",
            "versionCode": project.version_code,
            "keyVersion": 1
        }
        with open(os.path.join(project.root_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # Write build.gradle
        self._write_gradle(project)

        # Write deploy info
        deploy_info = {
            "device_cl_path": f"/sdcard/xtc/dial/{project.source_name}/{project.source_name}.cl",
            "device_config_path": f"/sdcard/xtc/dial/{project.source_name}/config.json",
            "source_name": project.source_name,
            "clockType": 1
        }
        with open(os.path.join(project.root_dir, "deploy.json"), "w") as f:
            json.dump(deploy_info, f, indent=2)

    def _create_pl_plugin(self, project: Project):
        """Initialize .pl plugin project."""
        pkg_dir = os.path.join(project.root_dir, "src", "main", "java",
                               *project.package_name.split("."))
        os.makedirs(pkg_dir, exist_ok=True)

        # Write Plugin.java
        plugin_java = f'''package {project.package_name};

import android.content.Context;
import android.graphics.Color;
import android.view.View;
import android.widget.TextView;
import com.xtc.diydial.iplugin.IPlugin;
import com.xtc.diydial.iplugin.IMessageCallback;

public class Plugin implements IPlugin {{
    private TextView view;
    private IMessageCallback callback;

    @Override
    public String getSourceName() {{
        return "{project.source_name}";
    }}

    @Override
    public View getView(String extra) {{
        if (view == null) {{
            view = new TextView(null);
        }}
        view.setText("{project.name}");
        view.setTextColor(Color.WHITE);
        view.setTextSize(18);
        view.setBackgroundColor(Color.parseColor("#33000000"));
        return view;
    }}

    @Override
    public void initPlugin(Context context, String apkPath) {{
        if (context != null && view == null) {{
            view = new TextView(context);
        }}
    }}

    @Override
    public void registerCallback(IMessageCallback callback) {{
        this.callback = callback;
    }}

    @Override
    public Object sendMessage(int action, Object data) {{
        if (callback != null) {{
            callback.callback(0, data);
        }}
        return null;
    }}

    @Override
    public void sendMessage(int action, Object data, IMessageCallback callback) {{
    }}
}}
'''
        with open(os.path.join(pkg_dir, "Plugin.java"), "w", encoding="utf-8") as f:
            f.write(plugin_java)

        # Write AndroidManifest.xml
        manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="''' + project.package_name + '''">
    <application android:label="''' + project.name + '''" />
</manifest>
'''
        with open(os.path.join(project.root_dir, "AndroidManifest.xml"), "w", encoding="utf-8") as f:
            f.write(manifest)

        # Write config.json with metadata for DIY editor catalog
        config = {
            "sourceName": project.source_name,
            "name": project.name,
            "type": project.plugin_type,
            "versionCode": project.version_code
        }
        with open(os.path.join(project.root_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # Write build.gradle
        self._write_gradle(project)

        # Write deploy info
        deploy_info = {
            "device_pl_path": f"/sdcard/xtc/dial/compose/element/{project.source_name}/{project.version_code}/{project.source_name}.pl",
            "device_config_path": f"/sdcard/xtc/dial/compose/element/{project.source_name}/{project.version_code}/config.json",
            "source_name": project.source_name,
            "version_code": project.version_code
        }
        with open(os.path.join(project.root_dir, "deploy.json"), "w") as f:
            json.dump(deploy_info, f, indent=2)

    def _create_theme_package(self, project: Project, theme_page: ThemePackConfigPage):
        """Initialize theme package project."""
        sn = project.source_name

        theme_config = ThemePackConfig(
            sourceName=sn,
            name=project.name,
            nameCompat=project.name,
            themePackDir=f"/sdcard/xtc/themepackage/{sn}/",
            versionCode=project.version_code,
            keyVersion=1,
        )

        # Dial source (optional reference)
        dial_source = theme_page.dial_source_edit.text().strip()
        if dial_source:
            dial_cfg = DialConfig(
                sourceName=dial_source,
                clockType=ClockType.TRADITIONAL_CL.value,
                useState=1,
                dialDir=f"/sdcard/xtc/dial/{dial_source}/",
                versionCode=1,
            )
            theme_config.dialConfig = dial_cfg.to_json()

        # Optional icon pack
        if theme_page.include_icon_pack.isChecked():
            icon_config = IconPackConfig(
                iconName=f"{project.name} 图标",
                sourceName=sn,
                iconDp=48.0,
                nameColor="#FFFFFF",
                themePath=f"/sdcard/xtc/themepackage/{sn}/icon/",
            )
            theme_config.mIconConfig = icon_config.to_json()

        project.theme_pack_config = theme_config

        # Create directories
        os.makedirs(os.path.join(project.root_dir, "dial"), exist_ok=True)
        os.makedirs(os.path.join(project.root_dir, "icon"), exist_ok=True)
        os.makedirs(os.path.join(project.root_dir, "preview"), exist_ok=True)

        # Write themepack.json
        with open(project.get_config_path(), "w", encoding="utf-8") as f:
            f.write(theme_config.to_json())

        # Write deploy info
        deploy_info = {
            "device_path": theme_config.themePackDir,
            "source_name": sn,
        }
        with open(os.path.join(project.root_dir, "deploy.json"), "w") as f:
            json.dump(deploy_info, f, indent=2)

    def _create_icon_package(self, project: Project, icon_page: IconPackConfigPage):
        """Initialize icon package project."""
        sn = project.source_name

        icon_config = IconPackConfig(
            iconName=icon_page.icon_name_edit.text().strip() or f"{project.name}",
            sourceName=sn,
            iconDp=float(icon_page.icon_dp_spin.value()),
            nameColor=icon_page.name_color_edit.text().strip() or "#FFFFFF",
            convertType=icon_page.convert_type_combo.currentData(),
            themePath=f"/sdcard/xtc/themepackage/{sn}/icon/",
        )
        project.icon_pack_config = icon_config

        # Create directories
        os.makedirs(os.path.join(project.root_dir, "icon"), exist_ok=True)
        os.makedirs(os.path.join(project.root_dir, "preview"), exist_ok=True)

        # Write icon_config.json
        with open(project.get_config_path(), "w", encoding="utf-8") as f:
            f.write(icon_config.to_json())

    def _write_gradle(self, project: Project):
        """Write a build script reference."""
        build_script = '''@echo off
REM XTC Dial Factory Build Script
REM This script compiles Java -> DEX -> APK -> Signed APK
REM
REM Prerequisites:
REM   - Android SDK with build-tools 37.0.0
REM   - JDK 8+
REM   - Android Keystore
REM
REM Usage:
REM   build.bat [cl|pl]

setlocal enabledelayedexpansion

set SDK=%USERPROFILE%\\AppData\\Local\\Android\\Sdk
set BT=%SDK%\\build-tools\\37.0.0
set ANDROID_JAR=%SDK%\\platforms\\android-34\\android.jar
set KEYSTORE=E:\\android.keystore
set KEYPASS=
set ALIAS=
set STUBS=%~dp0..\\resources\\stubs

if "%1"=="cl" goto build_cl
if "%1"=="pl" goto build_pl
echo Usage: %0 [cl^|pl]
exit /b 1

:build_cl
set OUT=%CD%\\build\\cl
for /r src\\main\\java %%f in (*.java) do set SRC_FILES=!SRC_FILES! "%%f"
if "!SRC_FILES!"=="" echo No source files found & exit /b 1

mkdir "%OUT%\\classes" 2>nul
javac -source 8 -target 8 -bootclasspath "%ANDROID_JAR%" -cp "%STUBS%" -d "%OUT%\\classes" !SRC_FILES!
if errorlevel 1 exit /b 1

set CLS_FILES=
for /r "%OUT%\\classes" %%f in (*.class) do set CLS_FILES=!CLS_FILES! "%%f"
"%BT%\\d8.bat" --lib "%ANDROID_JAR%" --release --output "%OUT%" !CLS_FILES!
if errorlevel 1 exit /b 1

copy "AndroidManifest.xml" "%OUT%\\" >nul
pushd "%OUT%"
"%BT%\\aapt" package -f -M AndroidManifest.xml -I "%ANDROID_JAR%" -F xtcwatch.apk
"%BT%\\aapt" add xtcwatch.apk classes.dex
"%BT%\\apksigner.bat" sign --ks "%KEYSTORE%" --ks-key-alias "%ALIAS%" --ks-pass "pass:%KEYPASS%" xtcwatch.apk
popd

mkdir "%~dp0output" 2>nul
copy "%OUT%\\xtcwatch.apk" "%~dp0output\\%~n0.cl" /y >nul
echo Build complete: %~dp0output\\%~n0.cl
exit /b 0

:build_pl
set OUT=%CD%\\build\\pl
for /r src\\main\\java %%f in (*.java) do set SRC_FILES=!SRC_FILES! "%%f"
if "!SRC_FILES!"=="" echo No source files found & exit /b 1

mkdir "%OUT%\\classes" 2>nul
javac -source 8 -target 8 -bootclasspath "%ANDROID_JAR%" -cp "%STUBS%" -d "%OUT%\\classes" !SRC_FILES!
if errorlevel 1 exit /b 1

set CLS_FILES=
for /r "%OUT%\\classes" %%f in (*.class) do set CLS_FILES=!CLS_FILES! "%%f"
"%BT%\\d8.bat" --lib "%ANDROID_JAR%" --release --output "%OUT%" !CLS_FILES!
if errorlevel 1 exit /b 1

copy "AndroidManifest.xml" "%OUT%\\" >nul
pushd "%OUT%"
"%BT%\\aapt" package -f -M AndroidManifest.xml -I "%ANDROID_JAR%" -F myplugin.apk
"%BT%\\aapt" add myplugin.apk classes.dex
"%BT%\\apksigner.bat" sign --ks "%KEYSTORE%" --ks-key-alias "%ALIAS%" --ks-pass "pass:%KEYPASS%" myplugin.apk
popd

mkdir "%~dp0output" 2>nul
copy "%OUT%\\myplugin.apk" "%~dp0output\\%~n0.pl" /y >nul
echo Build complete: %~dp0output\\%~n0.pl
exit /b 0
'''
        with open(os.path.join(project.root_dir, "build.bat"), "w", encoding="utf-8") as f:
            f.write(build_script)
