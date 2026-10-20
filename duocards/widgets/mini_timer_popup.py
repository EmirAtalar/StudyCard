"""
Study Card - Masaüstü Yüzen Mini Zamanlayıcı & Kronometre Widget'ı (MiniTimerPopup).
Masaüstünün herhangi bir yerine sürüklenebilen, her zaman en üstte (Always on Top)
kalan, yeşil neon parlaklığında kompakt mini kronometre/zamanlayıcı pop-up'ı.
"""

import math
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QColor, QCursor, QMouseEvent
from duocards.timer_engine import timer_engine
from duocards.settings import settings
from duocards.kwin_helper import position_kwin_bottom_right, is_wayland
from duocards.i18n import t
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton


class MiniTimerPopup(QWidget):
    """
    Masaüstünde yüzen kompakt, fütüristik neon yeşil sayaç penceresi.
    """
    closed = pyqtSignal()
    request_open_main = pyqtSignal()

    _instance: Optional["MiniTimerPopup"] = None

    def __init__(self, parent=None):
        if MiniTimerPopup._instance is not None:
            try:
                MiniTimerPopup._instance.close()
            except Exception:
                pass

        super().__init__(parent)
        MiniTimerPopup._instance = self

        self.lang = settings.get("ui_language", "en")
        self.setWindowTitle(ui_text('Study Card Mini Timer', self.lang))
        self.setObjectName("miniTimerPopup")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        self._drag_pos = QPoint()
        self._pulse_phase = 0.0
        self._setup_ui()
        self._position_on_screen()

        # Motor sinyallerine bağlan
        timer_engine.tick.connect(self.update_display)
        timer_engine.mode_changed.connect(self._on_mode_changed)

        # Anlık akıcı ekran güncelleme zamanlayıcısı (33ms - 30 FPS akıcı centisecond)
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(33)
        self._ui_timer.timeout.connect(self.update_display)
        self._ui_timer.start()

        # Neon Çerçeve Parlama Animasyonu (Yazı değil, dikdörtgen parlar)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)
        self._pulse_timer.timeout.connect(self._animate_neon_pulse)
        self._pulse_timer.start()

        self.update_display()

    @property
    def lbl_mode(self):
        return self.btn_mode_toggle

    def _setup_ui(self):
        self.setFixedSize(325, 114)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(4, 4, 4, 4)

        # Cam Efektli & Neon Çerçeveli Konteynır (Dikdörtgen parlar)
        self.container = QFrame()
        self.container.setObjectName("miniContainer")
        self.container.setStyleSheet("""
            QFrame#miniContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #090e17, stop:0.6 #0f172a, stop:1 #131d31);
                border: 1.5px solid rgba(16, 185, 129, 0.6);
                border-radius: 16px;
            }
        """)

        # Soft Neon Yeşil Dikdörtgen Parlama Efekti
        self.container_glow = QGraphicsDropShadowEffect(self.container)
        self.container_glow.setColor(QColor(0, 255, 136, 160))
        self.container_glow.setBlurRadius(20)
        self.container_glow.setOffset(0, 0)
        self.container.setGraphicsEffect(self.container_glow)

        main_box = QVBoxLayout(self.container)
        main_box.setContentsMargins(12, 8, 12, 8)
        main_box.setSpacing(4)

        # 1. Üst Bar: Mod Rozeti + Yanıp Sönen Lamba + Büyüt / Kapat Butonları
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        mode_key = "mode_stopwatch" if timer_engine.mode == "stopwatch" else "mode_countdown"
        self.btn_mode_toggle = QPushButton(t(mode_key, self.lang))
        self.btn_mode_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.2);
                color: #34d399;
                font-size: 9px;
                font-weight: 800;
                border-radius: 5px;
                padding: 2px 6px;
                border: 1px solid rgba(16, 185, 129, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.35);
            }
        """)
        self.btn_mode_toggle.clicked.connect(self._toggle_mode)

        self.lamp = QLabel()
        self.lamp.setFixedSize(7, 7)
        self.lamp.setStyleSheet("background-color: #00ff88; border-radius: 3px; border: 1px solid #ffffff;")

        top_bar.addWidget(self.btn_mode_toggle)
        top_bar.addWidget(self.lamp)
        top_bar.addStretch()

        # Kapat butonu
        btn_close = QPushButton("X")
        btn_close.setFixedSize(18, 18)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 11px;
                font-weight: 800;
                border-radius: 9px;
            }
            QPushButton:hover {
                color: #ef4444;
                background-color: rgba(239, 68, 68, 0.2);
            }
        """)
        btn_close.clicked.connect(self.close)

        top_bar.addWidget(btn_close)
        main_box.addLayout(top_bar)

        # 2. Orta Alan: Saat Göstergesi (Saat parlamaz, keskin ve net kalır)
        self.lbl_time = QLabel("00:00:00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 21px;
                font-weight: 900;
                letter-spacing: 1px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                background: transparent;
                border: none;
            }
        """)

        main_box.addWidget(self.lbl_time)

        # 3. Alt Bar: Kontrol Butonları (Başlat/Durdur, Sıfırla, Kaydet)
        controls_bar = QHBoxLayout()
        controls_bar.setSpacing(8)

        self.btn_play = QPushButton(t('btn_start', self.lang))
        self.btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_play.setFixedHeight(26)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 11px;
                font-weight: 800;
                border-radius: 6px;
                padding: 0 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_play.clicked.connect(self._toggle_running)

        self.btn_reset = QPushButton(t("btn_reset", self.lang))
        self.btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset.setFixedHeight(26)
        self.btn_reset.setToolTip(t("btn_reset", self.lang))
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 700;
                border-radius: 6px;
                padding: 0 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.16);
                color: #ffffff;
            }
        """)
        self.btn_reset.clicked.connect(self._reset_current)

        self.btn_save = QPushButton(t("btn_save", self.lang))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setFixedHeight(26)
        self.btn_save.setToolTip(t("btn_save_to_goal", self.lang))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #34d399;
                font-size: 11px;
                font-weight: 800;
                border-radius: 6px;
                padding: 0 8px;
                border: 1px solid rgba(16, 185, 129, 0.35);
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
            }
        """)
        self.btn_save.clicked.connect(self._save_session)

        controls_bar.addStretch()
        controls_bar.addWidget(self.btn_play)
        controls_bar.addWidget(self.btn_reset)
        controls_bar.addWidget(self.btn_save)
        controls_bar.addStretch()

        main_box.addLayout(controls_bar)
        root_layout.addWidget(self.container)

        # Sürükleme için event filtreleri
        self.container.installEventFilter(self)
        self.lbl_time.installEventFilter(self)

    def _toggle_mode(self):
        new_mode = "timer" if timer_engine.mode == "stopwatch" else "stopwatch"
        timer_engine.set_mode(new_mode)

    def _on_mode_changed(self, mode: str):
        if mode == "stopwatch":
            self.btn_mode_toggle.setText(t("mode_stopwatch", self.lang))
            self.btn_save.setVisible(True)
        else:
            self.btn_mode_toggle.setText(t("mode_countdown", self.lang))
            self.btn_save.setVisible(False)
        self.update_display()

    def _toggle_running(self):
        if timer_engine.mode == "stopwatch":
            timer_engine.toggle_stopwatch()
        else:
            timer_engine.toggle_timer()
        self.update_display()

    def _reset_current(self):
        if timer_engine.mode == "stopwatch":
            timer_engine.reset_stopwatch()
        else:
            timer_engine.reset_timer()
        self.update_display()

    def _save_session(self):
        if timer_engine.mode == "stopwatch":
            timer_engine.save_stopwatch_session("Mini Widget Oturumu")
        self.update_display()

    def _animate_neon_pulse(self):
        """Yeşil neon çerçeveyi (dikdörtgeni) dalgalı biçimde parlatıp söndürür. Saat yazısı parlamaz."""
        is_running = timer_engine.is_stopwatch_running if timer_engine.mode == "stopwatch" else timer_engine.is_timer_running
        if is_running:
            self._pulse_phase += 0.08
            sine = (math.sin(self._pulse_phase) + 1.0) / 2.0
            alpha = int(90 + sine * 150)
            blur = int(14 + sine * 16)
            self.container_glow.setColor(QColor(0, 255, 136, alpha))
            self.container_glow.setBlurRadius(blur)
        else:
            self.container_glow.setColor(QColor(0, 255, 136, 120))
            self.container_glow.setBlurRadius(16)

    def update_display(self):
        """TimerEngine saatini ekrana yansıtır."""
        pause_txt = t("btn_pause", self.lang)
        start_txt = t("btn_start", self.lang)

        if timer_engine.mode == "stopwatch":
            elapsed = timer_engine.get_stopwatch_elapsed()
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            cs = int((elapsed * 100) % 100)
            self.lbl_time.setText(f"{h:02d}:{m:02d}:{s:02d}:{cs:02d}")

            is_running = timer_engine.is_stopwatch_running
            self.btn_play.setText(pause_txt if is_running else start_txt)
            self.btn_play.setStyleSheet(
                "background-color: #f59e0b; color: #ffffff; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 0 12px; border: none;"
                if is_running else
                "background-color: #10b981; color: #ffffff; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 0 12px; border: none;"
            )
            self.lamp.setStyleSheet(
                "background-color: #00ff88; border-radius: 3px; border: 1px solid #ffffff;"
                if is_running else
                "background-color: #64748b; border-radius: 3px; border: 1px solid #475569;"
            )
        else:
            rem = timer_engine.get_timer_remaining()
            h = int(rem // 3600)
            m = int((rem % 3600) // 60)
            s = int(rem % 60)
            if h > 0:
                self.lbl_time.setText(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                self.lbl_time.setText(f"{m:02d}:{s:02d}")

            is_running = timer_engine.is_timer_running
            self.btn_play.setText(pause_txt if is_running else start_txt)
            self.btn_play.setStyleSheet(
                "background-color: #f59e0b; color: #ffffff; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 0 12px; border: none;"
                if is_running else
                "background-color: #10b981; color: #ffffff; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 0 12px; border: none;"
            )
            self.lamp.setStyleSheet(
                "background-color: #00ff88; border-radius: 3px; border: 1px solid #ffffff;"
                if is_running else
                "background-color: #64748b; border-radius: 3px; border: 1px solid #475569;"
            )

    # ---------------- FARE İLE SÜRÜKLEME ----------------

    def eventFilter(self, watched, event):
        if watched in (self.container, self.lbl_time):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                handle = self.windowHandle()
                if handle and handle.startSystemMove():
                    return True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            elif event.type() == QEvent.Type.MouseMove and event.buttons() == Qt.MouseButton.LeftButton:
                if hasattr(self, "_drag_pos") and not self._drag_pos.isNull():
                    self.move(event.globalPosition().toPoint() - self._drag_pos)
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            if handle and handle.startSystemMove():
                event.accept()
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if hasattr(self, "_drag_pos") and not self._drag_pos.isNull():
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def _position_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            x = avail.right() - self.width() - 20
            y = avail.bottom() - self.height() - 20
            self.move(x, y)

    def update_language(self, lang: str):
        self.lang = lang
        self.setWindowTitle(ui_text('Study Card Mini Timer', lang))
        mode_key = "mode_stopwatch" if timer_engine.mode == "stopwatch" else "mode_countdown"
        self.btn_mode_toggle.setText(t(mode_key, lang))
        self.btn_reset.setText(t("btn_reset", lang))
        self.btn_reset.setToolTip(t("btn_reset", lang))
        self.btn_save.setText(t("btn_save", lang))
        self.btn_save.setToolTip(t("btn_save_to_goal", lang))
        self.update_display()
        localize_tree(self,lang)

    def closeEvent(self, event):
        if hasattr(self, "_pulse_timer") and self._pulse_timer.isActive():
            self._pulse_timer.stop()
        if hasattr(self, "_ui_timer") and self._ui_timer.isActive():
            self._ui_timer.stop()
        try:
            timer_engine.tick.disconnect(self.update_display)
        except Exception:
            pass
        try:
            timer_engine.mode_changed.disconnect(self._on_mode_changed)
        except Exception:
            pass
        if MiniTimerPopup._instance == self:
            MiniTimerPopup._instance = None
        self.closed.emit()
        super().closeEvent(event)


def show_mini_timer_popup() -> MiniTimerPopup:
    """Masaüstünde yüzen mini kronometre pop-up'ını açar veya öne getirir."""
    lang = settings.get("ui_language", "en")
    if MiniTimerPopup._instance is not None:
        try:
            MiniTimerPopup._instance.update_language(lang)
            MiniTimerPopup._instance.showNormal()
            MiniTimerPopup._instance.raise_()
            MiniTimerPopup._instance.activateWindow()
            return MiniTimerPopup._instance
        except Exception:
            MiniTimerPopup._instance = None

    popup = MiniTimerPopup()
    popup.update_language(lang)
    popup.show()
    popup.raise_()
    return popup
