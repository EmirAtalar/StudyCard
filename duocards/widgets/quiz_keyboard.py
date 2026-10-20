"""Soru ekranlarında odak, yazı girişi ve klavye eylemleri için ortak davranış."""
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QAbstractItemView, QAbstractSpinBox, QPushButton,
)


_TEXT = {
    'check': ['Kontrol Et', 'Check', 'Prüfen', 'Comprobar'],
    'next_button': ['Sonraki Soru', 'Next Question', 'Nächste Frage', 'Siguiente Pregunta'],
    'typing': ['Enter: kontrol et', 'Enter: check', 'Enter: prüfen', 'Enter: comprobar'],
    'choices': ['1–4: cevapla · Yön tuşları / Tab: seç · Enter: onayla',
                '1–4: answer · Arrows / Tab: select · Enter: confirm',
                '1–4: antworten · Pfeile / Tab: wählen · Enter: bestätigen',
                '1–4: responder · Flechas / Tab: elegir · Enter: confirmar'],
    'waiting': ['Cevabı incele · Enter / Boşluk ile devam',
                'Review the answer · Continue with Enter / Space',
                'Antwort lesen · Mit Enter / Leertaste weiter',
                'Revisa la respuesta · Continúa con Enter / Espacio'],
    'next': ['Enter / Boşluk: sonraki soru', 'Enter / Space: next question',
             'Enter / Leertaste: nächste Frage', 'Enter / Espacio: siguiente pregunta'],
    'listen': ['Ctrl+S: dinle', 'Ctrl+S: listen', 'Ctrl+S: anhören', 'Ctrl+S: escuchar'],
    'hint': ['Ctrl+H: ipucu', 'Ctrl+H: hint', 'Ctrl+H: Hinweis', 'Ctrl+H: pista'],
    'restart': ['Ctrl+R: yeni oturum', 'Ctrl+R: new session',
                'Ctrl+R: neue Sitzung', 'Ctrl+R: nueva sesión'],
    'space': ['Boşluk', 'Space', 'Leertaste', 'Espacio'],
    'match': ['Yön tuşları / Tab: seç · Enter / Boşluk: eşleştir',
              'Arrows / Tab: select · Enter / Space: match',
              'Pfeile / Tab: wählen · Enter / Leertaste: zuordnen',
              'Flechas / Tab: elegir · Enter / Espacio: emparejar'],
}


def keyboard_text(key, lang):
    index = ('tr', 'en', 'de', 'es').index(lang) if lang in ('tr', 'en', 'de', 'es') else 1
    return _TEXT[key][index]


def keyboard_help(lang, state, *, hints=False, choices=4):
    keys = [state, 'listen', 'restart'] if state else ['restart']
    if hints:
        keys.insert(-1, 'hint')
    return ' · '.join(keyboard_text(key, lang) for key in keys).replace('1–4',f'1–{choices}')


class _KeyboardRouter(QObject):
    """Her tuşu yalnız onu içeren sayfaya ileten tek uygulama filtresi."""

    def eventFilter(self, obj, event):
        if event.type() not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            return False
        widget = obj
        while isinstance(widget, QWidget):
            keyboard = getattr(widget, '_quiz_keyboard_controller', None)
            if keyboard is not None:
                return keyboard.eventFilter(obj, event)
            widget = widget.parentWidget()
        return False


class QuizKeyboard(QObject):
    """Yalnız görünür sayfanın tuşlarını işler; editör ve filtre tuşlarını korur."""

    def __init__(self, page, *, buttons, listen, next_button=None, typing=None,
                 submit=None, slow=None, hint=None, restart=None, active=None,
                 columns=4, choice_keys=True, enter=None):
        super().__init__(page)
        self.page = page
        self.buttons = buttons
        self.listen = listen
        self.next_button = next_button
        self.typing = typing
        self.submit = submit
        self.slow = slow
        self.hint = hint
        self.restart = restart
        self.active = active or (lambda: True)
        self.columns = columns
        self.choice_keys = choice_keys
        self.custom_enter = enter
        page.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        page._quiz_keyboard_controller = self
        app = QApplication.instance()
        if not hasattr(app, '_quiz_keyboard_router'):
            app._quiz_keyboard_router = _KeyboardRouter(app)
            app.installEventFilter(app._quiz_keyboard_router)

    def available_buttons(self):
        return [button for button in self.buttons() if button.isVisible() and button.isEnabled()]

    def focus_answer(self):
        if not self.page.isVisible() or not self.active():
            return
        if self.next_button and self.next_button.isVisible():
            target = self.next_button if self.next_button.isEnabled() else self.page
        elif self.typing and self.typing.isVisible() and self.typing.isEnabled():
            target = self.typing
        else:
            buttons = self.available_buttons()
            target = buttons[0] if buttons else self.page
        target.setFocus(Qt.FocusReason.OtherFocusReason)

    def _enter(self):
        if self.custom_enter:
            self.custom_enter()
        elif self.next_button and self.next_button.isVisible():
            self.next_button.click()
        elif self.typing and self.typing.isVisible() and self.typing.isEnabled():
            self.submit()
        else:
            buttons = self.available_buttons()
            focused = QApplication.focusWidget()
            if focused in buttons:
                focused.click()
            elif buttons:
                buttons[0].setFocus()

    def _choose(self, index):
        buttons = self.buttons()
        if index < len(buttons) and buttons[index].isVisible() and buttons[index].isEnabled():
            buttons[index].click()

    def _move(self, key):
        buttons = self.buttons()
        focused = QApplication.focusWidget()
        start = buttons.index(focused) if focused in buttons else -1
        step = {Qt.Key.Key_Left: -1, Qt.Key.Key_Right: 1,
                Qt.Key.Key_Up: -self.columns, Qt.Key.Key_Down: self.columns}[key]
        if start == -1:
            self.available_buttons()[0].setFocus()
            return
        # Izgarada aynı yönde ilerleyerek kullanılabilir bir seçenek bul.
        for offset in range(1, len(buttons) + 1):
            candidate = buttons[(start + step * offset) % len(buttons)]
            if candidate.isVisible() and candidate.isEnabled() and candidate is not focused:
                candidate.setFocus()
                return
        self.available_buttons()[0].setFocus()

    def eventFilter(self, obj, event):
        if event.type() not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            return False
        if (not isinstance(obj, QWidget) or not self.page.isVisible() or not self.active()
                or obj.window() is not self.page.window()
                or not (obj is self.page or self.page.isAncestorOf(obj))
                or QApplication.activePopupWidget() or QApplication.activeModalWidget()):
            return False
        key = event.key()
        modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        action = None
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            action = {Qt.Key.Key_S: self.listen, Qt.Key.Key_H: self.hint,
                      Qt.Key.Key_R: self.restart}.get(key)
        elif modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_S:
                action = self.slow
        elif modifiers == Qt.KeyboardModifier.NoModifier:
            control = obj
            while control is not None and control is not self.page:
                if isinstance(control, (QComboBox, QAbstractItemView, QAbstractSpinBox)):
                    return False
                control = control.parentWidget()
            editable = isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit))
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if isinstance(obj, QPushButton):
                    action = obj.click
                elif not editable or obj is self.typing:
                    action = self._enter
            elif not editable:
                if key == Qt.Key.Key_S:
                    action = self.listen
                elif key == Qt.Key.Key_H:
                    action = self.hint
                elif key == Qt.Key.Key_Space and self.next_button and self.next_button.isVisible():
                    action = self._enter
                elif self.choice_keys and Qt.Key.Key_1 <= key <= Qt.Key.Key_4 and self.available_buttons():
                    action = lambda: self._choose(key - Qt.Key.Key_1)
                elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and self.available_buttons():
                    action = lambda: self._move(key)
        if action is None:
            return False
        event.accept()
        if event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
            action()
        return True
