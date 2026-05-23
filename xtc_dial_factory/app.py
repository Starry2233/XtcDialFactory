"""Application setup and configuration."""

import os
import sys
import json
from pathlib import Path
from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import QApplication

from . import __app_name__, __version__, __org_name__
from .themes import apply_theme
from .error_reporter import install_crash_handler
from PySide6.QtGui import QIcon


class AppSettings:
    """Application settings wrapper using QSettings."""

    def __init__(self):
        self._settings = QSettings(__org_name__, __app_name__)

    @property
    def sdk_path(self) -> str:
        return self._settings.value("sdk_path",
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Android\Sdk"))

    @sdk_path.setter
    def sdk_path(self, value: str):
        self._settings.setValue("sdk_path", value)

    @property
    def keystore_path(self) -> str:
        return self._settings.value("keystore_path", "E:/android.keystore")

    @keystore_path.setter
    def keystore_path(self, value: str):
        self._settings.setValue("keystore_path", value)

    @property
    def keystore_password(self) -> str:
        return self._settings.value("keystore_password", "")

    @keystore_password.setter
    def keystore_password(self, value: str):
        self._settings.setValue("keystore_password", value)

    @property
    def keystore_alias(self) -> str:
        return self._settings.value("keystore_alias", "")

    @keystore_alias.setter
    def keystore_alias(self, value: str):
        self._settings.setValue("keystore_alias", value)

    @property
    def recent_projects(self) -> list:
        raw = self._settings.value("recent_projects", "[]")
        if isinstance(raw, str):
            return json.loads(raw)
        return raw or []

    @recent_projects.setter
    def recent_projects(self, value: list):
        self._settings.setValue("recent_projects", json.dumps(value))

    @property
    def device_id(self) -> str:
        return self._settings.value("device_id", "")

    @device_id.setter
    def device_id(self, value: str):
        self._settings.setValue("device_id", value)

    @property
    def language(self) -> str:
        return self._settings.value("language", "zh_CN")

    @language.setter
    def language(self, value: str):
        self._settings.setValue("language", value)

    @property
    def build_tools_version(self) -> str:
        return self._settings.value("build_tools_version", "37.0.0")

    @build_tools_version.setter
    def build_tools_version(self, value: str):
        self._settings.setValue("build_tools_version", value)

    @property
    def theme(self) -> str:
        return self._settings.value("theme", "dark")

    @theme.setter
    def theme(self, value: str):
        self._settings.setValue("theme", value)

    @property
    def java_home(self) -> str:
        return self._settings.value("java_home", "")

    @java_home.setter
    def java_home(self, value: str):
        self._settings.setValue("java_home", value)

    def add_recent_project(self, path: str):
        projects = self.recent_projects
        if path in projects:
            projects.remove(path)
        projects.insert(0, path)
        self.recent_projects = projects[:10]  # Keep max 10


def create_app(argv=None) -> QApplication:
    """Create and configure the QApplication."""
    if argv is None:
        argv = sys.argv

    app = QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(__org_name__)

    # Use Fusion style — respects stylesheets fully, unlike Windows native
    app.setStyle("Fusion")

    # Load saved theme and apply
    settings = AppSettings()
    apply_theme(settings.theme)

    # Set app icon
    icon_dir = Path(__file__).parent.parent / "resources" / "icons"
    if icon_dir.exists():
        icon_files = list(icon_dir.glob("*.ico")) + list(icon_dir.glob("*.png"))
        if icon_files:
            app.setWindowIcon(QIcon(str(icon_files[0])))

    # Install crash handler after QApplication is created
    install_crash_handler()

    return app
