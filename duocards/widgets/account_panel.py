"""Account controls and a non-blocking desktop sync coordinator."""
import threading
from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal, QCoreApplication
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from duocards.sync import SyncClient
from duocards.cloud_account import cloud_ready
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit

TEXT = {
    "tr": ("Hesap ve cihazlar", "Android ve PC’de aynı hesapla giriş yap. Kelimeler, desteler, favoriler ve tekrar durumu otomatik eşitlenir.", "Sunucu adresi", "E-posta", "Şifre (en az 10 karakter)", "Giriş yap", "Hesap oluştur", "Şimdi eşitle", "Çıkış yap", "Hesabına bağlı değil. Kelimelerin bu cihazda saklanıyor.", "Eşitleniyor…", "Eşitleme tamamlandı", "Bekleyen değişiklik", "Çıkış yapıldı; kelimelerin cihazda korundu."),
    "en": ("Account and devices", "Sign in with the same account on Android and PC. Cards, decks, favorites and review progress sync automatically.", "Server URL", "Email", "Password (at least 10 characters)", "Sign in", "Create account", "Sync now", "Sign out", "Signed out. Your cards are stored on this device.", "Syncing…", "Sync complete", "Pending changes", "Signed out; cards remain on this device."),
    "de": ("Konto und Geräte", "Auf Android und PC mit demselben Konto anmelden. Karten, Stapel, Favoriten und Lernfortschritt werden synchronisiert.", "Serveradresse", "E-Mail", "Passwort (mindestens 10 Zeichen)", "Anmelden", "Konto erstellen", "Jetzt synchronisieren", "Abmelden", "Abgemeldet. Karten sind auf diesem Gerät gespeichert.", "Synchronisierung…", "Synchronisierung abgeschlossen", "Ausstehende Änderungen", "Abgemeldet; Karten bleiben auf diesem Gerät."),
    "es": ("Cuenta y dispositivos", "Inicia sesión con la misma cuenta en Android y PC. Las tarjetas, mazos, favoritos y progreso se sincronizan automáticamente.", "URL del servidor", "Correo", "Contraseña (mínimo 10 caracteres)", "Iniciar sesión", "Crear cuenta", "Sincronizar", "Cerrar sesión", "Sin sesión. Las tarjetas están guardadas en este dispositivo.", "Sincronizando…", "Sincronización completa", "Cambios pendientes", "Sesión cerrada; las tarjetas permanecen en este dispositivo."),
}


class SyncCoordinator(QObject):
    status_changed = pyqtSignal(str)
    account_changed = pyqtSignal()
    data_changed = pyqtSignal()
    busy_changed = pyqtSignal(bool)
    _done = pyqtSignal(str, object)

    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client or SyncClient()
        self.busy = False
        self.lang = "tr"
        self.last_status = None
        self.status_value = None
        self.signing_in = False
        self.login_cancel = threading.Event()
        app = QCoreApplication.instance()
        if app:
            app.aboutToQuit.connect(self.cancel_login)
        self._done.connect(self._complete)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync)
        self.timer.start(15000)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self.sync)
        QTimer.singleShot(1000, self.sync)

    def schedule(self):
        self.debounce.start(700)

    def set_language(self, lang):
        self.lang = lang
        self._render_status()

    def _status(self, kind, value=None):
        self.last_status, self.status_value = kind, value
        self._render_status()

    def _render_status(self):
        words = TEXT.get(self.lang, TEXT['en'])
        if self.last_status == 'syncing':
            value = words[10]
        elif self.last_status == 'google':
            value = ui_text('Complete Google sign-in in your browser.', self.lang)
        elif self.last_status == 'logout':
            value = words[13]
        elif self.last_status == 'complete':
            value = f'{words[11]} · {words[12]}: {self.status_value}'
        elif self.last_status == 'error':
            value = ui_text(self.status_value, self.lang)
        else:
            return
        self.status_changed.emit(value)

    def _run(self, kind, action):
        if self.busy:
            return
        self.busy = True
        self.busy_changed.emit(True)
        self._status('google' if self.signing_in else 'syncing')
        def work():
            try:
                result = action()
            except Exception as exc:
                result = exc
            try:
                self._done.emit(kind, result)
            except RuntimeError:
                pass  # Application closed while a network request was in flight.
        threading.Thread(target=work, name="study-card-sync", daemon=True).start()

    def _complete(self, kind, result):
        self.busy = False
        self.signing_in = False
        self.busy_changed.emit(False)
        if isinstance(result, Exception):
            self._status('error', str(result))
            self.account_changed.emit()
            return
        if kind == "login":
            self.account_changed.emit()
            self.sync()
        elif kind == "logout":
            self.account_changed.emit()
            self._status('logout')
        else:
            self._status('complete', result['pending'])
            if result.get("changed"):
                self.data_changed.emit()
            if result["pending"]:
                self.schedule()

    def login(self, url, email, password, register=False):
        self._run("login", lambda: self.client.login(url, email, password, register))

    def login_google(self):
        if self.busy:
            return
        self.signing_in = True
        self.login_cancel = threading.Event()
        self._run('login', lambda: self.client.login_google(cancel=self.login_cancel, lang=self.lang))

    def cancel_login(self):
        self.login_cancel.set()

    def logout(self):
        self._run("logout", self.client.logout)

    def sync(self):
        if self.client.session().get("token"):
            self._run("sync", self.client.sync)


class AccountPanel(QFrame):
    def __init__(self, lang="tr", parent=None):
        super().__init__(parent)
        self.lang = lang
        self.coordinator = None
        self.setProperty("panel", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f1f5f9;")
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.identity = QLabel()
        self.identity.setTextFormat(Qt.TextFormat.PlainText)
        self.identity.setWordWrap(True)
        self.google, self.sync_now, self.sign_out, self.cancel = (QPushButton() for _ in range(4))
        self.availability = QLabel()
        self.availability.setWordWrap(True)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        for widget in (self.title, self.description, self.identity, self.availability):
            layout.addWidget(widget)
        buttons = QHBoxLayout()
        for button in (self.google, self.sync_now, self.sign_out, self.cancel):
            button.setMinimumHeight(40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            primary = button in (self.google, self.sync_now)
            button.setStyleSheet(
                "QPushButton { color: " + ("#052e2b" if primary else "#e2e8f0") +
                "; background: " + ("#10b981" if primary else "#171f2e") +
                "; border: 1px solid #2b374b; border-radius: 8px; padding: 8px 14px; font-weight: 600; }"
                "QPushButton:disabled { color: #94a3b8; background: #222d42; }"
            )
            buttons.addWidget(button)
        layout.addLayout(buttons)
        layout.addWidget(self.status)
        self.google.clicked.connect(lambda: self.coordinator and self.coordinator.login_google())
        self.cancel.clicked.connect(lambda: self.coordinator and self.coordinator.cancel_login())
        self.sync_now.clicked.connect(lambda: self.coordinator and self.coordinator.sync())
        self.sign_out.clicked.connect(lambda: self.coordinator and self.coordinator.logout())
        self.update_language(lang)

    def attach(self, coordinator):
        self.coordinator = coordinator
        coordinator.status_changed.connect(lambda value:self.status.setText(ui_text(value,self.lang)))
        coordinator.set_language(self.lang)
        coordinator.account_changed.connect(self.refresh)
        coordinator.busy_changed.connect(self._busy)
        self.refresh()

    def _busy(self, busy):
        for widget in (self.google, self.sync_now, self.sign_out):
            widget.setEnabled(not busy)
        self.google.setEnabled(not busy and cloud_ready())
        self.cancel.setVisible(bool(busy and self.coordinator and self.coordinator.signing_in))

    def refresh(self):
        session = self.coordinator.client.session() if self.coordinator else {}
        active = bool(session.get("token"))
        self.identity.setText(session.get("email", "") if active else TEXT.get(self.lang, TEXT["en"])[9])
        self.google.setVisible(True)
        self.google.setText(ui_text('Sign in with Google again' if active else 'Sign in with Google', self.lang))
        for widget in (self.sync_now, self.sign_out):
            widget.setVisible(active)
        self.availability.setVisible(not active and not cloud_ready())
        self._busy(self.coordinator.busy if self.coordinator else False)

    def update_language(self, lang):
        self.lang = lang
        words = TEXT.get(lang, TEXT["en"])
        self.title.setText(words[0])
        self.description.setText(ui_text('Sign in with the same Google account on Android and PC. Cards, decks, favorites and review progress sync automatically.', lang))
        self.google.setText(ui_text('Sign in with Google', lang))
        self.cancel.setText(ui_text('Cancel sign-in', lang))
        self.sync_now.setText(words[7])
        self.sign_out.setText(words[8])
        self.availability.setText(ui_text('Google sign-in is not available in this build yet. Your offline cards are safe.', lang))
        if self.coordinator:
            self.coordinator.set_language(lang)
        self.refresh()
        localize_tree(self,lang)
