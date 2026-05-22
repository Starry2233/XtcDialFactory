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

from ..models.project import Project, ProjectType, NetComposeDial, ThemeAssemblyElement, DialConfig


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

        self.rb_cl.setChecked(True)
        layout.addStretch()

    def project_type(self) -> ProjectType:
        id = self.type_group.checkedId()
        return [ProjectType.CL_DIAL, ProjectType.PL_PLUGIN, ProjectType.COMPOSE_DIAL][id]


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

        self.name_edit.textChanged.connect(self._update_package)
        self.name_edit.textChanged.connect(self.completeChanged)

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


class ProjectWizard(QWizard):
    """Wizard for creating new XTC projects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumSize(600, 500)

        self.created_project: Project | None = None

        # Pages
        self.addPage(ProjectTypePage())
        self.addPage(ProjectInfoPage())
        self.addPage(ProjectLocationPage())
        self.addPage(ComposeConfigPage())

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
            self._create_pl_plugin(project)

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

        # Write config.json
        config = {
            "sourceName": project.source_name,
            "dialName": project.name,
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
