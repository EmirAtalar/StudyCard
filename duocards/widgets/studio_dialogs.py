"""Studycard's own modal windows and shared studio controls."""
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtWidgets import (QDialog, QFrame, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QButtonGroup, QScrollArea, QSpinBox, QFormLayout, QApplication)
from duocards.ui_localization import QLabel, QPushButton, QLineEdit, QComboBox, ui_text
from duocards.icons import get_icon, PERSONAL_ICONS, PERSONAL_ICON_LABELS
from duocards.settings import settings
from duocards.styles import transform_preferences

STUDIO_STYLES = '''
QWidget { color: #e2e8f0; background: transparent; border: none; }
QFrame#studioShell { background: #111827; border: 1px solid #243550; border-radius: 16px; }
QFrame[studioPanel="true"] { background: #121824; border: 1px solid #243550; border-radius: 14px; }
QLabel[role="eyebrow"] { color: #10b981; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
QLabel[role="heading"] { color: #f8fafc; font-size: 25px; font-weight: 800; }
QLabel[role="muted"] { color: #94a3b8; font-size: 12px; }
QLabel[role="error"] { color: #fb7185; font-size: 12px; }
QPushButton { background: #162032; border: 1px solid #243550; border-radius: 9px; padding: 8px 14px; min-height: 22px; font-weight: 600; }
QPushButton:hover { background: #1e293b; border-color: #10b981; }
QPushButton[variant="primary"] { background: #10b981; color: #ffffff; border-color: #10b981; }
QPushButton[variant="primary"]:hover { background: #059669; }
QPushButton[variant="danger"] { background: #431c2c; color: #fb7185; border-color: #75324b; }
QPushButton[variant="quiet"] { background: transparent; border-color: transparent; color: #94a3b8; }
QPushButton:checked { background: #153b36; border-color: #10b981; color: #6ee7b7; }
QPushButton:disabled { color: #64748b; background: #111827; border-color: #1e293b; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #0c121e; border: 1px solid #243550; border-radius: 9px; padding: 9px 12px; min-height: 22px; color: #f1f5f9; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #10b981; }
QComboBox QAbstractItemView { background: #111827; color: #e2e8f0; selection-background-color: #153b36; border: 1px solid #243550; padding: 5px; }
QCheckBox { color: #e2e8f0; spacing: 9px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #334155; border-radius: 5px; background: #0c121e; }
QCheckBox::indicator:checked { background: #10b981; border-color: #10b981; }
QTableWidget { background: #0c121e; alternate-background-color: #121824; border: 1px solid #243550; border-radius: 9px; gridline-color: #1e293b; selection-background-color: #153b36; }
QTableWidget::item { padding: 8px; }
QHeaderView::section { background: #162032; color: #cbd5e1; border: none; padding: 9px; font-weight: 600; }
QTableCornerButton::section { background: #162032; border: none; }
QProgressBar { background: #162032; border: none; border-radius: 4px; min-height: 6px; }
QProgressBar::chunk { background: #10b981; border-radius: 4px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: #334155; min-height: 25px; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: transparent; }
QMenu { background: #111827; color: #e2e8f0; border: 1px solid #243550; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 5px; }
QMenu::item:selected { background: #153b36; color: #6ee7b7; }
'''


def apply_studio_style(widget, style=STUDIO_STYLES):
    widget._preference_original_style = style
    widget._preference_applied_style = transform_preferences(style)
    widget.setStyleSheet(widget._preference_applied_style)


def label(text, lang, role=None, translate=True):
    result = QLabel(ui_text(text, lang) if translate else text)
    result.setWordWrap(True)
    result.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        result.setProperty('role', role)
    return result


def button(text, lang, action, icon=None, variant=None, translate=True):
    result = QPushButton(ui_text(text, lang) if translate else text)
    result.setCursor(Qt.CursorShape.PointingHandCursor)
    if variant:
        result.setProperty('variant', variant)
    if icon:
        result.setIcon(get_icon(icon, 18, settings.get('accent_color', '#10b981')))
    result.clicked.connect(lambda checked=False: action())
    return result


class StudioDialog(QDialog):
    def __init__(self, title, subtitle='', parent=None, icon='maker', width=600):
        super().__init__(parent)
        self.lang = settings.get('ui_language', 'en')
        self.setWindowTitle(ui_text(title, self.lang))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        apply_studio_style(self)
        self._drag = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        shell = QFrame(); shell.setObjectName('studioShell')
        outer.addWidget(shell)
        body = QVBoxLayout(shell); body.setContentsMargins(24, 22, 24, 20); body.setSpacing(18)
        self.header = QWidget()
        self.header.installEventFilter(self)
        header = QHBoxLayout(self.header); header.setContentsMargins(0, 0, 0, 0)
        emblem = QLabel(); emblem.setPixmap(get_icon(icon, 30).pixmap(30, 30)); header.addWidget(emblem)
        title_box = QVBoxLayout()
        title_box.addWidget(label(title, self.lang, 'heading'))
        if subtitle:
            title_box.addWidget(label(subtitle, self.lang, 'muted'))
        header.addLayout(title_box, 1)
        close = button('×', self.lang, self.reject, variant='quiet'); close.setFixedSize(34, 34); close.setToolTip(ui_text('Close', self.lang)); header.addWidget(close)
        body.addWidget(self.header)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.content = QWidget(); self.form = QVBoxLayout(self.content); self.form.setContentsMargins(0, 0, 4, 0); self.form.setSpacing(15)
        self.scroll.setWidget(self.content); body.addWidget(self.scroll, 1)
        self.error = label('', self.lang, 'error'); self.error.hide(); body.addWidget(self.error)
        self.footer = QHBoxLayout(); self.footer.setSpacing(10)
        self.footer.addStretch()
        self.cancel_button = button('Cancel', self.lang, self.reject)
        self.submit_button = button('Save', self.lang, self.accept, variant='primary')
        self.submit_button.setDefault(True)
        self.footer.addWidget(self.cancel_button); self.footer.addWidget(self.submit_button)
        body.addLayout(self.footer)
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else None
        self.resize(min(width, geometry.width()-40) if geometry else width, min(650, geometry.height()-60) if geometry else 650)

    def field(self, text, control):
        self.form.addWidget(label(text, self.lang))
        self.form.addWidget(control)
        return control

    def fail(self, message):
        self.error.setText(ui_text(message, self.lang)); self.error.show()

    def eventFilter(self, watched, event):
        if watched is self.header:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag = event.globalPosition().toPoint()-self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint()-self._drag); return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag = None
        return super().eventFilter(watched, event)


class IconPicker(QWidget):
    def __init__(self, selected='table_grid', parent=None, columns=6):
        super().__init__(parent)
        self.group = QButtonGroup(self); self.group.setExclusive(True)
        self.buttons = {}
        grid = QGridLayout(self); grid.setContentsMargins(0, 0, 0, 0); grid.setSpacing(8)
        self._expanded=False
        for index, key in enumerate(PERSONAL_ICONS):
            choice = QPushButton(); choice.setCheckable(True); choice.setIcon(get_icon(key, 25)); choice.setIconSize(QSize(25, 25)); choice.setFixedSize(52, 46)
            choice.setToolTip(ui_text('Icon: {name}', name=ui_text(PERSONAL_ICON_LABELS[key]))); choice.setAccessibleName(choice.toolTip())
            self.group.addButton(choice); self.buttons[key] = choice; grid.addWidget(choice, index//columns, index%columns)
            choice.setVisible(index<12)
        self.expand_button=button('Show all {count} icons',settings.get('ui_language','en'),self.toggle_expanded)
        self.expand_button.setText(ui_text('Show all {count} icons',count=len(PERSONAL_ICONS)))
        self._grid=grid;self._columns=columns
        grid.addWidget(self.expand_button,2 if columns==6 else 3,0,1,columns)
        self.set_value(selected)

    def value(self):
        return next((key for key, choice in self.buttons.items() if choice.isChecked()), 'table_grid')

    def set_value(self, selected):
        self.buttons.get(selected, self.buttons['table_grid']).setChecked(True)
        if selected in PERSONAL_ICONS and PERSONAL_ICONS.index(selected)>=12 and not self._expanded:
            self.toggle_expanded()

    def toggle_expanded(self):
        self._expanded=not self._expanded
        for index,choice in enumerate(self.buttons.values()):choice.setVisible(index<12 or self._expanded)
        self._grid.removeWidget(self.expand_button)
        rows=(len(PERSONAL_ICONS)+self._columns-1)//self._columns if self._expanded else (12+self._columns-1)//self._columns
        self._grid.addWidget(self.expand_button,rows,0,1,self._columns)
        self.expand_button.setText(ui_text('Show fewer icons') if self._expanded else ui_text('Show all {count} icons',count=len(PERSONAL_ICONS)))

    def update_language(self,lang):
        for key,choice in self.buttons.items():
            choice.setToolTip(ui_text('Icon: {name}',lang,name=ui_text(PERSONAL_ICON_LABELS[key],lang)))
            choice.setAccessibleName(choice.toolTip())
        self.expand_button.setText(ui_text('Show fewer icons',lang) if self._expanded else ui_text('Show all {count} icons',lang,count=len(PERSONAL_ICONS)))


class TextDialog(StudioDialog):
    def __init__(self, title, field_title, value='', parent=None):
        super().__init__(title, 'Make it yours.', parent, width=470)
        self.input = self.field(field_title, QLineEdit(value)); self.input.setMaxLength(120)
        self.resize(self.width(), 330)
        self.input.setFocus(); self.input.selectAll()

    def accept(self):
        if not self.input.text().strip():
            self.fail('Please enter a name.'); self.input.setFocus(); return
        super().accept()

    @classmethod
    def get_text(cls, parent, title, field_title, value=''):
        dialog = cls(title, field_title, value, parent)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        value = dialog.input.text().strip()
        dialog.deleteLater()
        return value, accepted


class ConfirmDialog(StudioDialog):
    def __init__(self, title, message, parent=None, action_text='Delete'):
        super().__init__(title, '', parent, width=480)
        self.form.addWidget(label(message, self.lang))
        self.submit_button.setText(ui_text(action_text, self.lang)); self.submit_button.setProperty('variant', 'danger')
        self.submit_button.setDefault(False); self.cancel_button.setDefault(True)
        self.resize(self.width(), 300)

    @classmethod
    def ask(cls, parent, title, message, action_text='Delete'):
        dialog = cls(title, message, parent, action_text)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        dialog.deleteLater()
        return accepted


class TableDetailsDialog(StudioDialog):
    def __init__(self, parent=None, document=None):
        super().__init__('Table identity' if document else 'New table', 'Choose a name, an icon and a starting point for your extension.', parent, 'table_grid', 700)
        self.name = self.field('Table name', QLineEdit(document['name'] if document else ''))
        self.name.setPlaceholderText(ui_text('e.g. My irregular verbs', self.lang)); self.name.setMaxLength(120)
        self.description = self.field('Description', QLineEdit(document.get('description', '') if document else ''))
        self.description.setMaxLength(300)
        self.icons = self.field('Choose an icon', IconPicker(document.get('icon', 'table_grid') if document else 'table_grid'))
        self.template = QComboBox()
        for name, key in [('Blank table','blank'),('Irregular verbs template','verbs'),('Phrases and examples','phrases')]: self.template.addItem(ui_text(name, self.lang), key)
        self.columns = QSpinBox(); self.columns.setRange(1, 32); self.columns.setValue(2)
        self.rows = QSpinBox(); self.rows.setRange(1, 100); self.rows.setValue(8)
        self.speakers = None
        if document is None:
            self.field('Template', self.template)
            dimensions = QFormLayout(); dimensions.addRow(label('Starting rows', self.lang), self.rows); dimensions.addRow(label('Starting columns', self.lang), self.columns); self.form.addLayout(dimensions)
            self.template.currentIndexChanged.connect(lambda: self.columns.setEnabled(self.template.currentData() == 'blank'))
            self.form.addWidget(label('Your table appears in Extensions as soon as you create it.', self.lang, 'muted'))
            self.submit_button.setText(ui_text('Create extension', self.lang))
        self.name.setFocus()

    def accept(self):
        if not self.name.text().strip():
            self.fail('Please enter a name.'); self.name.setFocus(); return
        super().accept()

    def metadata(self):
        return dict(name=self.name.text().strip(), description=self.description.text().strip(), icon=self.icons.value())
