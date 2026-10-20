"""
Study Card - Masaüstü Pop-up Bildirim Widget'ı (Neon Green Floating Notification).
Masaüstünün en sağ alt köşesinde sabit konumda, yanıp sönen neon yeşil efekt ve lamba ile bildirim gösterir.
Wayland (KDE Plasma 6 KWin) ve X11 uyumludur, tek bir sabit konumda belirir ve yukarı kaymaz.
Tıklandığında uygulamayı öne getirir ve çalışma ekranına yönlendirir.
"""

import math
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QPixmap
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.kwin_helper import position_kwin_bottom_right
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton


# Yeşil Saat SVG Vektörü (Renksiz, saf zümrüt/neon yeşili)
_CLOCK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12 6 12 12 16 14"></polyline>
</svg>"""


class SteamNotificationPopup(QWidget):
    """
    Ekranın en sağ alt köşesinde sabit yerde beliren,
    yanıp sönen lamba ve yeşil neon 'Çalışma Zamanı' bildirim penceresi.
    """
    clicked = pyqtSignal()
    _current_instance: Optional["SteamNotificationPopup"] = None

    def __init__(
        self,
        title: str = "",
        message: str = "",
        parent=None,
        duration_ms: int = 7000,
        on_click_callback=None
    ):
        # Eğer aktif bir bildirim varsa eskisini kapatarak tek yerde kalmasını sağla
        if SteamNotificationPopup._current_instance is not None:
            try:
                SteamNotificationPopup._current_instance.close()
            except Exception:
                pass

        super().__init__(parent)
        SteamNotificationPopup._current_instance = self

        self.lang = settings.get("ui_language", "en")
        self.setWindowTitle(ui_text('Study Card Notification', self.lang))
        self.setObjectName("studyCardNotificationPopup")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.on_click_callback = on_click_callback
        self.duration_ms = duration_ms
        self.notif_title = title
        self.notif_message = message
        self._pulse_phase = 0.0

        self._setup_ui()
        self._position_bottom_right()

    def _setup_ui(self):
        # Kompakt ve zarif boyut
        self.setFixedSize(320, 68)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(4, 4, 4, 4)

        # Ana Konteynır (Karanlık zemin ve Neon Yeşil Işıltılı Çerçeve)
        self.container = QFrame()
        self.container.setObjectName("notifContainer")
        self.container.setStyleSheet("""
            QFrame#notifContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #090e17, stop:0.6 #0f172a, stop:1 #131d31);
                border: 1.5px solid rgba(16, 185, 129, 0.55);
                border-radius: 14px;
            }
        """)

        # Soft Neon Dikdörtgen Parlama Efekti
        self.container_glow = QGraphicsDropShadowEffect(self.container)
        self.container_glow.setColor(QColor(0, 255, 136, 180))
        self.container_glow.setBlurRadius(20)
        self.container_glow.setOffset(0, 0)
        self.container.setGraphicsEffect(self.container_glow)

        main_box = QHBoxLayout(self.container)
        main_box.setContentsMargins(12, 10, 12, 10)
        main_box.setSpacing(12)

        # ---------------- SOL: YEŞİL SAAT SİMGESİ ----------------
        self.clock_badge = QLabel()
        self.clock_badge.setFixedSize(38, 38)
        self.clock_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(16, 185, 129, 0.12);
                border: 1.2px solid rgba(16, 185, 129, 0.4);
                border-radius: 19px;
            }
        """)
        pix = QPixmap()
        pix.loadFromData(_CLOCK_SVG.encode("utf-8"))
        self.clock_badge.setPixmap(pix)
        main_box.addWidget(self.clock_badge)

        # ---------------- SAĞ: İÇERİK DÜZENİ ----------------
        content_box = QVBoxLayout()
        content_box.setContentsMargins(0, 0, 0, 0)
        content_box.setSpacing(3)

        # 1. Üst Satır: App Rozeti + Yanıp Sönen Lamba + Kapat Butonu
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        lbl_app = QLabel("STUDY CARD")
        lbl_app.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.2);
            color: #34d399;
            font-size: 8.5px;
            font-weight: 800;
            letter-spacing: 0.5px;
            border-radius: 4px;
            padding: 1px 5px;
            border: none;
        """)

        # Yanıp sönen lamba / LED göstergesi
        self.lamp = QLabel()
        self.lamp.setFixedSize(8, 8)
        self.lamp.setStyleSheet("background-color: #00ff88; border-radius: 4px; border: 1px solid #ffffff;")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(18, 18)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                font-weight: 700;
                font-size: 11px;
                border-radius: 9px;
            }
            QPushButton:hover {
                color: #ef4444;
                background-color: rgba(239, 68, 68, 0.2);
            }
        """)
        btn_close.clicked.connect(self.close)

        top_row.addWidget(lbl_app)
        top_row.addWidget(self.lamp)
        top_row.addStretch()
        top_row.addWidget(btn_close)
        content_box.addLayout(top_row)

        # 2. Ana Satır: Başlık (Yazı parlamaz, keskin ve net kalır)
        display_title = self.notif_title if self.notif_title else (ui_text('Study Time', self.lang))
        self.lbl_title = QLabel(display_title)
        self.lbl_title.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-weight: 900;
                font-size: 14px;
                letter-spacing: 0.3px;
                border: none;
                background: transparent;
            }
        """)
        content_box.addWidget(self.lbl_title)

        if self.notif_message:
            self.lbl_msg = QLabel(self.notif_message)
            self.lbl_msg.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; background: transparent; border: none;")
            self.lbl_msg.setWordWrap(True)
            content_box.addWidget(self.lbl_msg)
            self.setFixedSize(320, 80)

        main_box.addLayout(content_box, 1)
        root_layout.addWidget(self.container)

        # Neon Yanıp Sönme (Pulsing) & Lamba Zamanlayıcısı
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._animate_neon_pulse)
        self._pulse_timer.start(40)

        # Kapanma Zamanlayıcısı
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)
        self.timer.start(self.duration_ms)

    def _animate_neon_pulse(self):
        """Yeşil neon çerçeveyi (dikdörtgeni) ve lambayı dalgalı biçimde parlatıp söndürür (neon efekt). Yazı parlamaz."""
        self._pulse_phase += 0.09
        sine = (math.sin(self._pulse_phase) + 1.0) / 2.0  # 0.0 -> 1.0

        # Dikdörtgenin (container) neon glow parlaklığı ve yayılımı
        alpha = int(90 + sine * 150)
        blur = int(14 + sine * 16)
        self.container_glow.setColor(QColor(0, 255, 136, alpha))
        self.container_glow.setBlurRadius(blur)

        # Lamba (LED) yanıp sönmesi
        lamp_opacity = 0.2 + sine * 0.8
        border_opacity = 0.25 + sine * 0.75
        self.lamp.setStyleSheet(
            f"background-color: rgba(0, 255, 136, {lamp_opacity:.2f}); "
            f"border-radius: 4px; "
            f"border: 1px solid rgba(255, 255, 255, {border_opacity:.2f});"
        )

    def _position_bottom_right(self):
        """Qt pencere konumu - Ekranın en sağ alt köşesinde sabit (16px kenar boşluğu ile)."""
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            x = avail.right() - self.width() - 16
            y = avail.bottom() - self.height() - 16
            self.move(x, y)

    def enterEvent(self, event):
        """Fare üzerine gelince bildirimin otomatik kapanmasını durdur ve parlat."""
        self.timer.stop()
        self.container.setStyleSheet("""
            QFrame#notifContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:0.6 #1e293b, stop:1 #334155);
                border: 1.5px solid #10b981;
                border-radius: 14px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Fare ayrılınca 3.5 saniye sonra kapat."""
        self.container.setStyleSheet("""
            QFrame#notifContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #090e17, stop:0.6 #0f172a, stop:1 #131d31);
                border: 1.5px solid rgba(16, 185, 129, 0.55);
                border-radius: 14px;
            }
        """)
        self.timer.start(3500)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            if self.on_click_callback:
                self.on_click_callback()
            self.close()
            return
        super().mousePressEvent(event)

    def closeEvent(self, event):
        if hasattr(self, "_pulse_timer") and self._pulse_timer.isActive():
            self._pulse_timer.stop()
        if hasattr(self, "_sound_timer") and self._sound_timer.isActive():
            self._sound_timer.stop()
        if SteamNotificationPopup._current_instance == self:
            SteamNotificationPopup._current_instance = None
        super().closeEvent(event)

    def show_popup(self):
        try:
            sfx.play_alert_soft()
        except Exception:
            pass

        # Sürekli soft bir uyarı sesi çal (bildirim kapanana kadar)
        self._sound_timer = QTimer(self)
        self._sound_timer.setInterval(1600)
        self._sound_timer.timeout.connect(lambda: sfx.play_alert_soft())
        self._sound_timer.start()
        self._position_bottom_right()
        self.show()
        self.raise_()

        # KDE Plasma 6 Wayland ortamında KWin üzerinden kesin en sağ-alta yerleştir ve en üstte tut
        QTimer.singleShot(40, lambda: position_kwin_bottom_right(
            self.windowTitle(),
            width=self.width(),
            height=self.height(),
            margin_right=16,
            margin_bottom=16
        ))


def show_steam_notification(title: str = "", message: str = "", on_click=None) -> SteamNotificationPopup:
    """Sağ-alt köşede sabit yerde neon yeşil 'Çalışma Zamanı' bildirimi gösterir."""
    popup = SteamNotificationPopup(title, message, on_click_callback=on_click)
    popup.show_popup()
    return popup
