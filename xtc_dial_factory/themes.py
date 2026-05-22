"""Theme system — dark and light mode stylesheets."""

from PySide6.QtWidgets import QApplication


def dark_stylesheet() -> str:
    """Return the dark theme stylesheet."""
    return """
    QWidget {
        background-color: #2b2b2b;
        color: #cccccc;
    }

    QLabel { color: #cccccc; }

    QGroupBox {
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 16px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #cccccc;
    }

    QPushButton {
        background-color: #0e639c;
        color: white;
        border: none;
        padding: 5px 14px;
        border-radius: 4px;
        min-width: 70px;
    }
    QPushButton:hover { background-color: #1177bb; }
    QPushButton:pressed { background-color: #094771; }
    QPushButton:disabled { background-color: #3c3c3c; color: #666; }

    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
        background-color: #1e1e1e;
        color: #d4d4d4;
        border: 1px solid #3c3c3c;
        border-radius: 3px;
        padding: 3px 6px;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #0e639c;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: #252526;
        color: #cccccc;
        selection-background-color: #094771;
        border: 1px solid #3c3c3c;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #3c3c3c;
        border: none;
        width: 16px;
    }

    QListWidget, QTreeView {
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        outline: none;
    }
    QListWidget::item:selected, QTreeView::item:selected {
        background-color: #264f78;
    }
    QListWidget::item:hover, QTreeView::item:hover {
        background-color: #2a2d2e;
    }

    QTableWidget, QTableView {
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        gridline-color: #3c3c3c;
    }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #264f78;
    }
    QHeaderView::section {
        background-color: #333;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        padding: 4px;
    }

    QTabWidget::pane {
        border: 1px solid #3c3c3c;
        background-color: #2b2b2b;
    }
    QTabBar::tab {
        background-color: #2b2b2b;
        color: #cccccc;
        border: 1px solid #3c3c3c;
        border-bottom: none;
        padding: 6px 14px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background-color: #1e1e1e; border-bottom: 1px solid #1e1e1e; }
    QTabBar::tab:hover:!selected { background-color: #333; }

    QScrollBar:vertical { background: #2b2b2b; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: #555; min-height: 30px; border-radius: 4px; }
    QScrollBar::handle:vertical:hover { background: #777; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal { background: #2b2b2b; height: 10px; }
    QScrollBar::handle:horizontal { background: #555; min-width: 30px; border-radius: 4px; }
    QScrollBar::handle:horizontal:hover { background: #777; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    QMenuBar { background-color: #333; color: #cccccc; border-bottom: 1px solid #3c3c3c; }
    QMenuBar::item:selected { background-color: #094771; }
    QMenu { background-color: #2b2b2b; color: #cccccc; border: 1px solid #3c3c3c; }
    QMenu::item:selected { background-color: #094771; }
    QMenu::separator { height: 1px; background: #3c3c3c; margin: 4px 8px; }

    QToolBar { background-color: #333; border-bottom: 1px solid #3c3c3c; spacing: 4px; padding: 2px; }
    QToolBar QToolButton {
        background-color: transparent; color: #cccccc;
        border: none; padding: 4px 8px; border-radius: 3px;
    }
    QToolBar QToolButton:hover { background-color: #3c3c3c; }
    QToolBar QToolButton:pressed { background-color: #094771; }

    QStatusBar { background-color: #007acc; color: white; }
    QDockWidget { color: #cccccc; }
    QDockWidget::title { background-color: #333; padding: 6px; border-bottom: 1px solid #3c3c3c; }

    QDialogButtonBox, QDialogButtonBox QWidget { background-color: #2b2b2b; }
    QDialogButtonBox QPushButton { min-width: 80px; }

    QMessageBox { background-color: #2b2b2b; color: #cccccc; }
    QMessageBox QLabel { color: #cccccc; }
    QMessageBox QPushButton { min-width: 80px; }

    QRadioButton, QCheckBox { color: #cccccc; spacing: 6px; }
    QRadioButton::indicator:checked, QCheckBox::indicator:checked {
        background-color: #0e639c; border: 1px solid #0e639c;
        border-radius: 3px; width: 14px; height: 14px;
    }
    QRadioButton::indicator:unchecked, QCheckBox::indicator:unchecked {
        background-color: #1e1e1e; border: 1px solid #555;
        border-radius: 3px; width: 14px; height: 14px;
    }

    QToolTip { background-color: #333; color: #cccccc; border: 1px solid #555; padding: 4px; }
    QProgressBar { background-color: #1e1e1e; border: 1px solid #3c3c3c; border-radius: 3px; text-align: center; color: #cccccc; }
    QProgressBar::chunk { background-color: #0e639c; border-radius: 2px; }
    QTableWidget QLineEdit { background-color: #1e1e1e; color: #d4d4d4; border: none; }
    """


def light_stylesheet() -> str:
    """Return the light theme stylesheet."""
    return """
    QWidget {
        background-color: #f5f5f5;
        color: #1e1e1e;
    }

    QLabel { color: #1e1e1e; }

    QGroupBox {
        border: 1px solid #d0d0d0;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 16px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #1e1e1e;
    }

    QPushButton {
        background-color: #e0e0e0;
        color: #1e1e1e;
        border: 1px solid #c0c0c0;
        padding: 5px 14px;
        border-radius: 4px;
        min-width: 70px;
    }
    QPushButton:hover { background-color: #d0d0d0; }
    QPushButton:pressed { background-color: #b0b0b0; }
    QPushButton:disabled { background-color: #f0f0f0; color: #aaa; }

    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        color: #1e1e1e;
        border: 1px solid #c0c0c0;
        border-radius: 3px;
        padding: 3px 6px;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #0078d4;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #1e1e1e;
        selection-background-color: #0078d4;
        selection-color: white;
        border: 1px solid #c0c0c0;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #e8e8e8;
        border: none;
        width: 16px;
    }

    QListWidget, QTreeView {
        background-color: #ffffff;
        color: #1e1e1e;
        border: 1px solid #d0d0d0;
        outline: none;
    }
    QListWidget::item:selected, QTreeView::item:selected {
        background-color: #cce5ff;
        color: #1e1e1e;
    }
    QListWidget::item:hover, QTreeView::item:hover {
        background-color: #e8f0fe;
    }

    QTableWidget, QTableView {
        background-color: #ffffff;
        color: #1e1e1e;
        border: 1px solid #d0d0d0;
        gridline-color: #e0e0e0;
    }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #cce5ff;
    }
    QHeaderView::section {
        background-color: #e8e8e8;
        color: #1e1e1e;
        border: 1px solid #d0d0d0;
        padding: 4px;
    }

    QTabWidget::pane {
        border: 1px solid #d0d0d0;
        background-color: #f5f5f5;
    }
    QTabBar::tab {
        background-color: #e8e8e8;
        color: #1e1e1e;
        border: 1px solid #d0d0d0;
        border-bottom: none;
        padding: 6px 14px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background-color: #f5f5f5; border-bottom: 1px solid #f5f5f5; }
    QTabBar::tab:hover:!selected { background-color: #ddd; }

    QScrollBar:vertical { background: #f0f0f0; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: #c0c0c0; min-height: 30px; border-radius: 4px; }
    QScrollBar::handle:vertical:hover { background: #a0a0a0; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal { background: #f0f0f0; height: 10px; }
    QScrollBar::handle:horizontal { background: #c0c0c0; min-width: 30px; border-radius: 4px; }
    QScrollBar::handle:horizontal:hover { background: #a0a0a0; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    QMenuBar { background-color: #e8e8e8; color: #1e1e1e; border-bottom: 1px solid #d0d0d0; }
    QMenuBar::item:selected { background-color: #cce5ff; }
    QMenu { background-color: #ffffff; color: #1e1e1e; border: 1px solid #d0d0d0; }
    QMenu::item:selected { background-color: #cce5ff; }
    QMenu::separator { height: 1px; background: #e0e0e0; margin: 4px 8px; }

    QToolBar { background-color: #e8e8e8; border-bottom: 1px solid #d0d0d0; spacing: 4px; padding: 2px; }
    QToolBar QToolButton {
        background-color: transparent; color: #1e1e1e;
        border: none; padding: 4px 8px; border-radius: 3px;
    }
    QToolBar QToolButton:hover { background-color: #d0d0d0; }
    QToolBar QToolButton:pressed { background-color: #b0b0b0; }

    QStatusBar { background-color: #007acc; color: white; }
    QDockWidget { color: #1e1e1e; }
    QDockWidget::title { background-color: #e8e8e8; padding: 6px; border-bottom: 1px solid #d0d0d0; }

    QDialogButtonBox, QDialogButtonBox QWidget { background-color: #f5f5f5; }
    QDialogButtonBox QPushButton { min-width: 80px; }

    QMessageBox { background-color: #f5f5f5; color: #1e1e1e; }
    QMessageBox QLabel { color: #1e1e1e; }
    QMessageBox QPushButton { min-width: 80px; }

    QRadioButton, QCheckBox { color: #1e1e1e; spacing: 6px; }
    QRadioButton::indicator:checked, QCheckBox::indicator:checked {
        background-color: #0078d4; border: 1px solid #0078d4;
        border-radius: 3px; width: 14px; height: 14px;
    }
    QRadioButton::indicator:unchecked, QCheckBox::indicator:unchecked {
        background-color: #ffffff; border: 1px solid #999;
        border-radius: 3px; width: 14px; height: 14px;
    }

    QToolTip { background-color: #fffde7; color: #1e1e1e; border: 1px solid #ccc; padding: 4px; }
    QProgressBar { background-color: #ffffff; border: 1px solid #d0d0d0; border-radius: 3px; text-align: center; color: #1e1e1e; }
    QProgressBar::chunk { background-color: #0078d4; border-radius: 2px; }
    QTableWidget QLineEdit { background-color: #ffffff; color: #1e1e1e; border: none; }
    """


def apply_theme(theme: str):
    """Apply the given theme ('dark' or 'light') to the QApplication."""
    app = QApplication.instance()
    if not app:
        return
    if theme == "light":
        app.setStyleSheet(light_stylesheet())
    else:
        app.setStyleSheet(dark_stylesheet())
