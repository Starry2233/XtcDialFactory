"""Code editor widget with syntax highlighting."""

import os
from PySide6.QtCore import Qt, QRect, QRegularExpression
from PySide6.QtGui import (
    QPainter, QColor, QFont, QTextFormat, QSyntaxHighlighter,
    QTextCharFormat, QFontMetricsF, QKeySequence, QShortcut
)
from PySide6.QtWidgets import (
    QPlainTextEdit, QTextEdit, QWidget, QVBoxLayout, QTabWidget, QMessageBox
)


def _make_format(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    if italic:
        f.setFontItalic(True)
    return f


def _multi_line_comment(highlighter: QSyntaxHighlighter, start: str, end: str, fmt: QTextCharFormat):
    """Helper for multi-line comment rules."""
    highlighter.setCurrentBlockState(0)
    # Must be called from within the highlighter's highlightBlock


class JavaHighlighter(QSyntaxHighlighter):
    """Java syntax highlighter."""

    KEYWORDS = [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "final", "finally", "float", "for",
        "goto", "if", "implements", "import", "instanceof", "int",
        "interface", "long", "native", "new", "package", "private",
        "protected", "public", "return", "short", "static", "strictfp",
        "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while", "true", "false", "null",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # Keywords
        kw_fmt = _make_format("#c678dd", bold=True)
        for word in self.KEYWORDS:
            self._rules.append((
                QRegularExpression(f"\\b{word}\\b"),
                kw_fmt
            ))

        # Annotations
        self._rules.append((
            QRegularExpression(r"@\w+"),
            _make_format("#e5c07b")
        ))

        # Strings
        self._rules.append((
            QRegularExpression(r'"(?:[^"\\]|\\.)*"'),
            _make_format("#98c379")
        ))

        # Characters
        self._rules.append((
            QRegularExpression(r"'(?:[^'\\]|\\.)'"),
            _make_format("#98c379")
        ))

        # Numbers
        self._rules.append((
            QRegularExpression(r"\b\d+\.?\d*(?:[fFLl]|(?=[^\w]))"),
            _make_format("#d19a66")
        ))

        # Single-line comments
        self._rules.append((
            QRegularExpression(r"//[^\n]*"),
            _make_format("#7f848e", italic=True)
        ))

        # Multi-line comment format
        self._comment_start = QRegularExpression(r"/\*")
        self._comment_end = QRegularExpression(r"\*/")
        self._multiline_fmt = _make_format("#7f848e", italic=True)

    def highlightBlock(self, text: str):
        # Apply single-line rules
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        # Multi-line comments
        self.setCurrentBlockState(0)
        start_idx = 0
        if self.previousBlockState() != 1:
            m = self._comment_start.match(text)
            if m.hasMatch():
                start_idx = m.capturedStart()
            else:
                return
        else:
            start_idx = 0

        m = self._comment_end.match(text, start_idx + 2)
        if m.hasMatch():
            end_idx = m.capturedStart() + m.capturedLength()
            length = end_idx - start_idx
            self.setFormat(start_idx, length, self._multiline_fmt)
            self.setCurrentBlockState(0)
        else:
            self.setFormat(start_idx, len(text) - start_idx, self._multiline_fmt)
            self.setCurrentBlockState(1)


class XmlHighlighter(QSyntaxHighlighter):
    """XML syntax highlighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # Tags
        self._rules.append((
            QRegularExpression(r"</?\w[^>]*>"),
            _make_format("#61afef")
        ))

        # Attributes
        self._rules.append((
            QRegularExpression(r"\b\w+(?=\s*=)"),
            _make_format("#e5c07b")
        ))

        # Attribute values (raw string can't end with backslash, but " is fine)
        self._rules.append((
            QRegularExpression(r'"[^"]*"'),
            _make_format("#98c379")
        ))

        # Comments
        self._rules.append((
            QRegularExpression(r"<!--[^>]*-->"),
            _make_format("#7f848e", italic=True)
        ))

        self._comment_start = QRegularExpression(r"<!--")
        self._comment_end = QRegularExpression(r"-->")
        self._multiline_fmt = _make_format("#7f848e", italic=True)

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        # Multi-line comments
        self.setCurrentBlockState(0)
        start_idx = 0
        if self.previousBlockState() != 1:
            m = self._comment_start.match(text)
            if m.hasMatch():
                start_idx = m.capturedStart()
            else:
                return
        else:
            start_idx = 0

        m = self._comment_end.match(text, start_idx + 4)
        if m.hasMatch():
            end_idx = m.capturedStart() + m.capturedLength()
            self.setFormat(start_idx, end_idx - start_idx, self._multiline_fmt)
        else:
            self.setFormat(start_idx, len(text) - start_idx, self._multiline_fmt)
            self.setCurrentBlockState(1)


class JsonHighlighter(QSyntaxHighlighter):
    """JSON syntax highlighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = [
            (QRegularExpression(r'"[^"]*"\s*:'), _make_format("#e5c07b")),  # Keys
            (QRegularExpression(r'"[^"]*"'), _make_format("#98c379")),       # String values
            (QRegularExpression(r"\b(?:true|false|null)\b"), _make_format("#56b6c2")),  # Literals
            (QRegularExpression(r"\b-?\d+\.?\d*(?:[eE][+-]?\d+)?\b"), _make_format("#d19a66")),  # Numbers
        ]
        self._multiline_fmt = _make_format("#7f848e", italic=True)

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class LineNumberArea(QWidget):
    """Gutter widget for line numbers."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QRect(0, 0, self._editor.line_number_width(), 0).size()

    def paintEvent(self, event):
        self._editor._paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    """Code editor with line numbers and syntax highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 4px;
            }
        """)

        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_width()
        self._highlight_current_line()

    def line_number_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 8 + 10 * digits

    def _update_line_number_width(self, _new_block_count=None):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(),
                                          self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def _paint_line_numbers(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self._line_number_area.width() - 8,
                                 self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2a2d2e"))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra_selections.append(sel)
        self.setExtraSelections(extra_selections)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))


def create_highlighter(file_path: str, editor: QPlainTextEdit) -> QSyntaxHighlighter | None:
    """Create the appropriate highlighter for a file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        ".java": JavaHighlighter,
        ".xml": XmlHighlighter,
        ".json": JsonHighlighter,
        ".cfg": JsonHighlighter,
        ".properties": JavaHighlighter,
        ".gradle": JavaHighlighter,
        ".kt": JavaHighlighter,
    }
    cls = mapping.get(ext)
    if cls:
        hl = cls(editor)
        hl.setDocument(editor.document())  # Explicitly set document (required in PySide6)
        return hl
    return None


class FileEditorTab(QWidget):
    """A single file open in an editor tab."""

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._modified = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = CodeEditor()
        layout.addWidget(self.editor)

        # Load content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.setPlainText(content)
        except (IOError, UnicodeDecodeError):
            self.editor.setPlainText(f"// Error: cannot read {file_path}")
            self.editor.setReadOnly(True)

        # Syntax highlighting
        self.highlighter = create_highlighter(file_path, self.editor)

        # Track modifications
        self.editor.textChanged.connect(self._on_text_changed)

        # Save shortcut
        sc = QShortcut(QKeySequence("Ctrl+S"), self)
        sc.activated.connect(self.save)

    def _on_text_changed(self):
        if not self._modified:
            self._modified = True

    @property
    def is_modified(self) -> bool:
        return self._modified

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self._modified = False
            return True
        except IOError as e:
            QMessageBox.critical(self, "保存失败", f"无法保存 {self.file_path}:\n{e}")
            return False
