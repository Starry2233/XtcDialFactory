"""Settings dialog for SDK, keystore, and build configuration."""

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QFileDialog, QGroupBox, QLabel, QMessageBox,
    QSpinBox, QComboBox
)
from PySide6.QtGui import QIntValidator

from ...app import AppSettings
from ...i18n import I18n
from ...themes import apply_theme


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.original_settings = settings
        self.updated_settings = settings

        layout = QVBoxLayout(self)

        # Language selection
        lang_layout = QFormLayout()
        self.lang_combo = QComboBox()
        supported = I18n.supported_languages()
        current_lang = settings.language
        self._lang_codes = []
        for code, name in supported.items():
            self.lang_combo.addItem(name, code)
            self._lang_codes.append(code)
            if code == current_lang:
                self.lang_combo.setCurrentIndex(self.lang_combo.count() - 1)
        lang_layout.addRow("语言 / Language:", self.lang_combo)
        layout.addLayout(lang_layout)

        # Theme selection
        theme_layout = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("深色 (Dark)", "dark")
        self.theme_combo.addItem("浅色 (Light)", "light")
        current_theme = settings.theme
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        theme_layout.addRow("主题 / Theme:", self.theme_combo)
        layout.addLayout(theme_layout)

        # SDK group
        sdk_group = QGroupBox("Android SDK")
        sdk_form = QFormLayout(sdk_group)

        self.sdk_path_edit = QLineEdit(settings.sdk_path)
        sdk_browse = QPushButton("浏览...")
        sdk_browse.clicked.connect(self._browse_sdk)
        sdk_path_layout = self._row_with_button(self.sdk_path_edit, sdk_browse)
        sdk_form.addRow("SDK 路径:", sdk_path_layout)

        self.build_tools_edit = QLineEdit(settings.build_tools_version)
        sdk_form.addRow("Build Tools 版本:", self.build_tools_edit)

        self.java_home_edit = QLineEdit(settings.java_home)
        java_browse = QPushButton("浏览...")
        java_browse.clicked.connect(self._browse_java)
        java_layout = self._row_with_button(self.java_home_edit, java_browse)
        sdk_form.addRow("JAVA_HOME:", java_layout)

        layout.addWidget(sdk_group)

        # Keystore group
        ks_group = QGroupBox("APK 签名")
        ks_form = QFormLayout(ks_group)

        self.keystore_edit = QLineEdit(settings.keystore_path)
        ks_browse = QPushButton("浏览...")
        ks_browse.clicked.connect(self._browse_keystore)
        ks_layout = self._row_with_button(self.keystore_edit, ks_browse)
        ks_form.addRow("Keystore 路径:", ks_layout)

        self.keystore_alias_edit = QLineEdit(settings.keystore_alias)
        ks_form.addRow("别名:", self.keystore_alias_edit)

        self.keystore_pass_edit = QLineEdit(settings.keystore_password)
        self.keystore_pass_edit.setEchoMode(QLineEdit.Password)
        ks_form.addRow("密码:", self.keystore_pass_edit)

        layout.addWidget(ks_group)

        # Device group
        device_group = QGroupBox("设备")
        device_form = QFormLayout(device_group)

        self.device_id_edit = QLineEdit(settings.device_id)
        self.device_id_edit.setPlaceholderText("留空使用第一个连接的设备")
        device_form.addRow("设备 ID:", self.device_id_edit)

        layout.addWidget(device_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _row_with_button(self, widget, button):
        from PySide6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(button)
        return layout

    def _browse_sdk(self):
        path = QFileDialog.getExistingDirectory(self, "选择 Android SDK 目录")
        if path:
            self.sdk_path_edit.setText(path)

    def _browse_java(self):
        path = QFileDialog.getExistingDirectory(self, "选择 JDK 目录")
        if path:
            self.java_home_edit.setText(path)

    def _browse_keystore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Keystore", "", "Keystore (*.keystore *.jks)")
        if path:
            self.keystore_edit.setText(path)

    def _on_accept(self):
        self.original_settings.sdk_path = self.sdk_path_edit.text()
        self.original_settings.build_tools_version = self.build_tools_edit.text()
        self.original_settings.java_home = self.java_home_edit.text()
        self.original_settings.keystore_path = self.keystore_edit.text()
        self.original_settings.keystore_alias = self.keystore_alias_edit.text()
        self.original_settings.keystore_password = self.keystore_pass_edit.text()
        self.original_settings.device_id = self.device_id_edit.text()
        selected_lang = self.lang_combo.currentData()
        self.original_settings.language = selected_lang
        I18n.instance().set_language(selected_lang)
        selected_theme = self.theme_combo.currentData()
        self.original_settings.theme = selected_theme
        apply_theme(selected_theme)
        self.accept()
