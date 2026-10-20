"""UI text bindings keep labels, placeholders and combo items in the chosen language.

Only explicitly marked interface text is translated; user vocabulary is untouched.
"""
import json
from pathlib import Path
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

CATALOG = {}
LANGS = ('tr', 'en', 'de', 'es')


class UiText(str):
    def __new__(cls, rendered, kind, key, values):
        obj = super().__new__(cls, rendered)
        obj.binding = (kind, key, values)
        return obj


def ui_text(key, lang=None, **values):
    if lang is None:
        from duocards.settings import settings
        lang = settings.get('ui_language', 'en')
    row = CATALOG.get(key)
    if row is None:
        row = next((v for v in CATALOG.values() if key in v), None)
    rendered = row[LANGS.index(lang) if lang in LANGS else 1] if row else key
    for name, value in values.items():
        rendered = rendered.replace('{' + name + '}', str(value))
    return UiText(rendered, 'ui', key, values)


def render(binding, lang):
    kind, key, values = binding
    if kind == 'ui':
        return ui_text(key, lang, **values)
    from duocards.i18n import t
    return t(key, lang, **values)


class _TextBinding:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text_binding = next((a.binding for a in args if isinstance(a, UiText)), None)
        self._placeholder_binding = None

    def setText(self, value):
        self._text_binding = value.binding if isinstance(value, UiText) else None
        super().setText(value)

    def setToolTip(self, value):
        self._tooltip_binding = value.binding if isinstance(value, UiText) else None
        super().setToolTip(value)

    def setWindowTitle(self, value):
        self._title_binding = value.binding if isinstance(value, UiText) else None
        super().setWindowTitle(value)

    def setPlaceholderText(self, value):
        self._placeholder_binding = value.binding if isinstance(value, UiText) else None
        super().setPlaceholderText(value)


class QLabel(_TextBinding, QtWidgets.QLabel): pass
class QPushButton(_TextBinding, QtWidgets.QPushButton): pass
class QCheckBox(_TextBinding, QtWidgets.QCheckBox): pass
class QLineEdit(_TextBinding, QtWidgets.QLineEdit): pass
class QTextEdit(_TextBinding, QtWidgets.QTextEdit): pass
class QPlainTextEdit(_TextBinding, QtWidgets.QPlainTextEdit): pass


class QComboBox(QtWidgets.QComboBox):
    ROLE = int(Qt.ItemDataRole.UserRole) + 987
    def addItem(self, *args, **kwargs):
        binding = next((a.binding for a in args if isinstance(a, UiText)), None)
        super().addItem(*args, **kwargs)
        if binding:
            self.setItemData(self.count()-1, binding, self.ROLE)

    def setItemText(self, index, value):
        super().setItemText(index, value)
        self.setItemData(index, value.binding if isinstance(value, UiText) else None, self.ROLE)


def localize_tree(root, lang):
    for widget in [root] + root.findChildren(QtWidgets.QWidget):
        binding = getattr(widget, '_text_binding', None)
        if binding:
            widget.setText(render(binding, lang))
        for attribute, setter in (('_tooltip_binding','setToolTip'),('_title_binding','setWindowTitle')):
            binding = getattr(widget,attribute,None)
            if binding: getattr(widget,setter)(render(binding,lang))
        binding = getattr(widget, '_placeholder_binding', None)
        if binding:
            widget.setPlaceholderText(render(binding, lang))
        if isinstance(widget, QComboBox):
            for index in range(widget.count()):
                binding = widget.itemData(index, widget.ROLE)
                if binding:
                    widget.setItemText(index, render(binding, lang))


path = Path(__file__).parent / 'data' / 'ui_catalog.json'
if path.exists():
    CATALOG.update(json.loads(path.read_text(encoding='utf-8')))
