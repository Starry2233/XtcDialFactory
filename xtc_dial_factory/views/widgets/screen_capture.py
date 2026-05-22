"""Device screen capture dialog.

Captures and displays a live screenshot from an ADB-connected device.
All ADB communication uses QProcess so the UI remains responsive.
"""

from PySide6.QtCore import Qt, QTimer, QProcess, Signal
from PySide6.QtGui import QPixmap, QImage, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCheckBox, QMessageBox, QFileDialog, QProgressBar, QWidget,
    QSizePolicy
)


class ScreenCaptureDialog(QDialog):
    """Dialog that captures device screenshots via ADB and displays them."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设备屏幕截图")
        self.setMinimumSize(480, 640)
        self.resize(540, 720)

        # State
        self._current_pixmap: QPixmap | None = None
        self._capture_process: QProcess | None = None
        self._device_info_process: QProcess | None = None
        self._waiting_for_device = False
        self._capture_count = 0

        self._setup_ui()
        self._query_device_info()

    # ---- UI Setup -----------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Device info label
        self.device_label = QLabel("正在查询设备信息...")
        self.device_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.device_label)

        # Screenshot display area
        self.screenshot_label = QLabel("点击「刷新截图」获取设备屏幕")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #444; "
            "border-radius: 6px; color: #666;"
        )
        self.screenshot_label.setMinimumSize(360, 360)
        self.screenshot_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.screenshot_label.setScaledContents(False)
        layout.addWidget(self.screenshot_label, stretch=1)

        # Progress bar for loading indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("刷新截图")
        self.refresh_btn.setMinimumHeight(36)
        self.refresh_btn.clicked.connect(self._start_capture)
        btn_layout.addWidget(self.refresh_btn)

        self.save_btn = QPushButton("保存...")
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_screenshot)
        btn_layout.addWidget(self.save_btn)

        # Auto-refresh checkbox
        self.auto_refresh_cb = QCheckBox("自动刷新 (3 秒)")
        self.auto_refresh_cb.setStyleSheet("font-size: 12px;")
        self.auto_refresh_cb.toggled.connect(self._on_auto_refresh_toggled)
        btn_layout.addWidget(self.auto_refresh_cb)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Auto-refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(3000)
        self._refresh_timer.timeout.connect(self._start_capture)

    # ---- Device Info --------------------------------------------------------

    def _query_device_info(self):
        """Fetch the device model name via adb shell getprop."""
        self.device_label.setText("正在查询设备信息...")
        proc = QProcess(self)
        self._device_info_process = proc
        proc.finished.connect(self._on_device_info_finished)
        proc.start("adb", ["shell", "getprop", "ro.product.model"])

    def _on_device_info_finished(self, exit_code: int):
        proc = self._device_info_process
        self._device_info_process = None
        if exit_code != 0 or not proc:
            stderr = bytes(proc.readAllStandardError()).decode("utf-8", errors="replace").strip() if proc else ""
            if "no devices/emulators found" in stderr.lower() or "error" in stderr.lower():
                self.device_label.setText("未检测到设备 — 请连接设备并确认 adb 可用")
                self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            else:
                self.device_label.setText(f"设备信息查询失败: {stderr or '未知错误'}")
                self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            return

        model = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace").strip()
        if model:
            self.device_label.setText(f"设备: {model}")
            self.device_label.setStyleSheet("color: #98c379; font-size: 12px;")
        else:
            self.device_label.setText("设备: 未知型号")
            self.device_label.setStyleSheet("color: #888; font-size: 12px;")

    # ---- Screenshot Capture via QProcess ------------------------------------

    def _start_capture(self):
        """Start an async screen capture via adb exec-out screencap -p."""
        if self._capture_process is not None:
            return  # already running

        self._show_loading(True)
        self.refresh_btn.setEnabled(False)

        proc = QProcess(self)
        self._capture_process = proc
        proc.finished.connect(self._on_capture_finished)
        proc.start("adb", ["exec-out", "screencap", "-p"])

    def _on_capture_finished(self, exit_code: int):
        proc = self._capture_process
        self._capture_process = None
        self._show_loading(False)
        self.refresh_btn.setEnabled(True)

        if exit_code != 0:
            stderr = bytes(proc.readAllStandardError()).decode("utf-8", errors="replace").strip()
            if "no devices/emulators found" in stderr.lower() or "error" in stderr.lower():
                self.device_label.setText("未检测到设备 — 请连接设备并确认 adb 可用")
                self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            elif "device unauthorized" in stderr.lower():
                self.device_label.setText("设备未授权 — 请在手机上确认 USB 调试授权")
                self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            else:
                self.device_label.setText(f"截图失败: {stderr or f'退出码 {exit_code}'}")
                self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            return

        raw_bytes = bytes(proc.readAllStandardOutput())
        if not raw_bytes:
            self.device_label.setText("截图失败: 未收到数据")
            self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            return

        image = QImage.fromData(raw_bytes)
        if image.isNull():
            self.device_label.setText("截图失败: 无法解析图像数据")
            self.device_label.setStyleSheet("color: #e06c75; font-size: 12px;")
            return

        pixmap = QPixmap.fromImage(image)
        self._current_pixmap = pixmap
        self.save_btn.setEnabled(True)
        self._display_pixmap(pixmap)

        self._capture_count += 1
        self.device_label.setText(
            f"{self.device_label.text().split(' |')[0]} | {pixmap.width()}x{pixmap.height()}"
            f" | 已截 {self._capture_count} 次"
        )
        # Keep existing style (don't override the color from device info)

    def _display_pixmap(self, pixmap: QPixmap):
        """Scale and display pixmap in the label, preserving aspect ratio."""
        label_size = self.screenshot_label.size()
        scaled = pixmap.scaled(
            label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.screenshot_label.setPixmap(scaled)

    # ---- Save ---------------------------------------------------------------

    def _save_screenshot(self):
        """Prompt for a save path and write the current screenshot to disk."""
        if self._current_pixmap is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存截图",
            "screenshot.png",
            "PNG 图像 (*.png);;JPEG 图像 (*.jpg *.jpeg);;所有文件 (*)",
        )
        if not path:
            return

        ok = self._current_pixmap.save(path)
        if ok:
            QMessageBox.information(self, "保存成功", f"截图已保存到:\n{path}")
        else:
            QMessageBox.critical(self, "保存失败", f"无法保存截图到:\n{path}")

    # ---- Auto-Refresh -------------------------------------------------------

    def _on_auto_refresh_toggled(self, checked: bool):
        if checked:
            self._refresh_timer.start()
            # Trigger an immediate capture when enabling
            if self._capture_process is None:
                self._start_capture()
        else:
            self._refresh_timer.stop()

    # ---- Loading Indicator --------------------------------------------------

    def _show_loading(self, active: bool):
        self.progress_bar.setVisible(active)
        if active:
            self.screenshot_label.setText("正在截取设备屏幕...")

    # ---- Overrides ----------------------------------------------------------

    def resizeEvent(self, event):
        """Re-scale the pixmap when the dialog is resized."""
        super().resizeEvent(event)
        if self._current_pixmap is not None:
            self._display_pixmap(self._current_pixmap)

    def closeEvent(self, event):
        """Clean up running processes when closing."""
        self._refresh_timer.stop()
        if self._capture_process is not None:
            self._capture_process.kill()
            self._capture_process.waitForFinished(1000)
            self._capture_process = None
        if self._device_info_process is not None:
            self._device_info_process.kill()
            self._device_info_process.waitForFinished(1000)
            self._device_info_process = None
        super().closeEvent(event)
