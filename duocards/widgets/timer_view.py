"""
Study Card - Zamanlayıcı & Kronometre Ekranı (Timer & Stopwatch View).
1000 Saatlik büyük çalışma hedefini takip eden, uzun saatlerde sapıtmayan
time.monotonic() mimarili kronometre, Pomodoro geri sayım zamanlayıcısı ve
masaüstü yüzen mini widget entegrasyonu.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGridLayout, QScrollArea, QFrame, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QSpinBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QColor
from duocards.timer_engine import timer_engine
from duocards.db import get_recent_timer_sessions, delete_timer_session
from duocards.widgets.mini_timer_popup import show_mini_timer_popup
from duocards.i18n import t
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit


class GoalMetricBox(QFrame):
    """1000 Saatlik hedef paneli için minimalist sayaç kutucuğu."""
    def __init__(self, title: str, value: str, color: str = "#10b981", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            GoalMetricBox {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; text-transform: uppercase; background: transparent;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {color}; background: transparent;")
        layout.addWidget(self.lbl_value)

    def set_values(self, title: str, value: str):
        self.lbl_title.setText(title)
        self.lbl_value.setText(value)


class TargetHoursCustomDialog(QDialog):
    """Modern, çerçevesiz, hızlı çipli ve parıltılı hedef çalışma süresi belirleme penceresi."""
    def __init__(self, current_hours: int = 1000, lang: str = "tr", parent=None):
        super().__init__(parent)
        self.current_hours = current_hours
        self.lang = lang
        self.selected_hours = current_hours
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1.5px solid #10b981;
                border-radius: 16px;
            }
        """)
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(22, 20, 22, 20)
        c_lay.setSpacing(14)

        # Başlık ve Kapatma Butonu
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_text = ui_text('Target Study Duration', self.lang)
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc; background: transparent; border: none;")
        top_row.addWidget(lbl_title, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #ffffff;
            }
        """)
        btn_close.clicked.connect(self.reject)
        top_row.addWidget(btn_close)
        c_lay.addLayout(top_row)

        # Açıklama
        desc_text = (
            ui_text('Set your total target study hours for this language learning journey.', self.lang)
        )
        lbl_desc = QLabel(desc_text)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4; background: transparent; border: none;")
        c_lay.addWidget(lbl_desc)

        # Hızlı Seçim Çipleri (50s, 100s, 250s, 500s, 1000s)
        chips_lbl = QLabel(ui_text('Quick Presets:', self.lang))
        chips_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        c_lay.addWidget(chips_lbl)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        presets = [50, 100, 250, 500, 1000]
        for p in presets:
            btn_chip = QPushButton(ui_text('{p}h', self.lang, **{'p': p}))
            btn_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_chip.setFixedHeight(30)
            btn_chip.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #38bdf8;
                    font-size: 12px;
                    font-weight: 800;
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    border-radius: 8px;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #0284c7;
                    color: #ffffff;
                    border: none;
                }
            """)
            btn_chip.clicked.connect(lambda ch, val=p: self._set_preset(val))
            chips_row.addWidget(btn_chip)
        c_lay.addLayout(chips_row)

        # Giriş Kutusu
        input_box = QHBoxLayout()
        input_box.setSpacing(10)

        self.txt_hours = QLineEdit()
        self.txt_hours.setText(str(self.current_hours))
        self.txt_hours.setFixedHeight(42)
        self.txt_hours.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_hours.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1.5px solid #10b981;
                border-radius: 10px;
                color: #10b981;
                font-size: 18px;
                font-weight: 900;
                padding: 4px 12px;
            }
            QLineEdit:focus {
                border-color: #34d399;
            }
        """)
        self.txt_hours.returnPressed.connect(self._on_save)
        input_box.addWidget(self.txt_hours, 1)

        lbl_unit = QLabel(ui_text('Hours', self.lang))
        lbl_unit.setStyleSheet("color: #cbd5e1; font-weight: 800; font-size: 13px; background: transparent; border: none;")
        input_box.addWidget(lbl_unit)
        c_lay.addLayout(input_box)

        self.lbl_err = QLabel("")
        self.lbl_err.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        c_lay.addWidget(self.lbl_err)

        # Alt Butonlar
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        btn_cancel = QPushButton(ui_text('Cancel', self.lang))
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setFixedSize(90, 36)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #cbd5e1;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #475569;
                color: #ffffff;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton(ui_text('Set Target', self.lang))
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setFixedSize(130, 36)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_save.clicked.connect(self._on_save)
        btn_box.addWidget(btn_save)

        c_lay.addLayout(btn_box)
        main_layout.addWidget(container)

    def _set_preset(self, val: int):
        sfx.play_click()
        self.txt_hours.setText(str(val))
        self.lbl_err.setText("")

    def _on_save(self):
        val = self.txt_hours.text().strip()
        try:
            h = int(val)
            if h > 0:
                self.selected_hours = h
                self.accept()
            else:
                self.lbl_err.setText(ui_text('Target must be greater than 0.', self.lang))
        except ValueError:
            self.lbl_err.setText(ui_text('Please enter a valid number.', self.lang))


class TimerView(QWidget):
    """
    Zamanlayıcı, Kronometre ve 1000 Saat Odak Takibi Ana Ekranı.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "en")
        self._setup_ui()

        # Engine sinyallerini bağla
        timer_engine.tick.connect(self._on_engine_tick)
        timer_engine.session_saved.connect(self._on_session_saved)
        timer_engine.timer_finished.connect(self._on_timer_finished)
        timer_engine.mode_changed.connect(self._on_engine_mode_changed)

        # Canlı anlık ekran güncelleme zamanlayıcısı (33ms - 30 FPS akıcı centisecond)
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(33)
        self._ui_timer.timeout.connect(self._on_engine_tick)
        self._ui_timer.start()

        self._refresh_all()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_all()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 24)
        layout.setSpacing(18)

        # ---------------- 1. ÜST BAŞLIK ALANI & MİNİ WİDGET BUTONU ----------------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)

        self.lbl_title = QLabel(t("timer_title", self.lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("timer_subtitle", self.lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        titles_box.addWidget(self.lbl_title)
        titles_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(titles_box)
        header_row.addStretch()

        # Masaüstü Mini Widget Butonu
        self.btn_open_mini = QPushButton(t('btn_open_mini_widget', self.lang))
        self.btn_open_mini.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_mini.setFixedHeight(38)
        self.btn_open_mini.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #34d399;
                font-size: 12px;
                font-weight: 800;
                border: 1.2px solid rgba(16, 185, 129, 0.4);
                border-radius: 10px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
                border: 1.2px solid #10b981;
            }
        """)
        self.btn_open_mini.clicked.connect(self._open_mini_widget)
        header_row.addWidget(self.btn_open_mini)

        layout.addLayout(header_row)

        # ---------------- 2. 1000 SAAT HEDEF PANELİ (MASTER GOAL) ----------------
        self.goal_card = QFrame()
        self.goal_card.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        goal_layout = QVBoxLayout(self.goal_card)
        goal_layout.setContentsMargins(18, 16, 18, 16)
        goal_layout.setSpacing(14)

        goal_header = QHBoxLayout()
        self.lbl_goal_title = QLabel(t("goal_1000h_title", self.lang))
        self.lbl_goal_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #f8fafc; background: transparent;")
        
        # Yeşil kutucuk: Hedef Seç
        self.btn_select_target = QPushButton(t("set_goal", self.lang))
        self.btn_select_target.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_select_target.setFixedHeight(28)
        self.btn_select_target.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 12px;
                font-weight: 800;
                border-radius: 8px;
                padding: 0 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_select_target.clicked.connect(self._open_target_hours_dialog)

        self.lbl_goal_pct = QLabel(ui_text('0% Complete', self.lang))
        self.lbl_goal_pct.setStyleSheet("font-size: 13px; font-weight: 800; color: #10b981; background: transparent;")
        
        goal_header.addWidget(self.lbl_goal_title)
        goal_header.addSpacing(10)
        goal_header.addWidget(self.btn_select_target)
        goal_header.addStretch()
        goal_header.addWidget(self.lbl_goal_pct)
        goal_layout.addLayout(goal_header)

        # İlerleme Çubuğu (Glow Yeşili)
        self.goal_bar = QProgressBar()
        self.goal_bar.setFixedHeight(14)
        self.goal_bar.setTextVisible(False)
        self.goal_bar.setStyleSheet("""
            QProgressBar {
                background-color: #111827;
                border-radius: 7px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #00ff88);
                border-radius: 7px;
            }
        """)
        goal_layout.addWidget(self.goal_bar)

        # 4 Sayaç Kutusu
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(10)

        self.box_total_done = GoalMetricBox(t("goal_completed", self.lang), "0s 0dk", "#38bdf8")
        self.box_pct = GoalMetricBox(t("goal_pct", self.lang), "%0.0", "#10b981")
        self.box_remaining = GoalMetricBox(t("goal_remaining", self.lang), "1000s 0dk", "#f59e0b")
        self.box_sessions = GoalMetricBox(t("goal_sessions", self.lang), "0 Oturum", "#818cf8")

        metrics_grid.addWidget(self.box_total_done, 0, 0)
        metrics_grid.addWidget(self.box_pct, 0, 1)
        metrics_grid.addWidget(self.box_remaining, 0, 2)
        metrics_grid.addWidget(self.box_sessions, 0, 3)
        goal_layout.addLayout(metrics_grid)

        layout.addWidget(self.goal_card)

        # ---------------- 3. MOD SEÇİM SEKMELERİ (KRONOMETRE / GERİ SAYIM) ----------------
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(10)

        self.btn_tab_sw = QPushButton(t('tab_stopwatch', self.lang))
        self.btn_tab_sw.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_sw.setFixedHeight(38)
        self.btn_tab_sw.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 10px;
                padding: 0 20px;
                border: none;
            }
        """)
        self.btn_tab_sw.clicked.connect(lambda: self._select_mode("stopwatch"))

        self.btn_tab_tm = QPushButton(t('tab_countdown', self.lang))
        self.btn_tab_tm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_tm.setFixedHeight(38)
        self.btn_tab_tm.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 0 20px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton:hover {
                color: #f8fafc;
                background-color: #1e293b;
            }
        """)
        self.btn_tab_tm.clicked.connect(lambda: self._select_mode("timer"))

        tabs_row.addWidget(self.btn_tab_sw)
        tabs_row.addWidget(self.btn_tab_tm)
        tabs_row.addStretch()
        layout.addLayout(tabs_row)

        # ---------------- 4. ANA DİJİTAL SAYAÇ ALANI ----------------
        self.clock_panel = QFrame()
        self.clock_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        clock_layout = QVBoxLayout(self.clock_panel)
        clock_layout.setContentsMargins(24, 20, 24, 20)
        clock_layout.setSpacing(18)
        clock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Geri Sayım İçin Manuel Süre Belirleme (Kullanıcı Kendi Yazar)
        self.custom_timer_frame = QFrame()
        self.custom_timer_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 6px 14px;
            }
        """)
        custom_layout = QHBoxLayout(self.custom_timer_frame)
        custom_layout.setContentsMargins(12, 6, 12, 6)
        custom_layout.setSpacing(10)
        custom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_custom_t = QLabel(t("set_duration_label", self.lang))
        self.lbl_custom_t.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 700; background: transparent; border: none;")
        custom_layout.addWidget(self.lbl_custom_t)

        spin_style = """
            QSpinBox {
                background-color: #0f172a;
                border: 1.5px solid #334155;
                border-radius: 8px;
                color: #00ff88;
                font-size: 13px;
                font-weight: 800;
                padding: 4px 8px;
                min-width: 65px;
                height: 30px;
            }
            QSpinBox:focus {
                border-color: #10b981;
            }
        """

        self.spn_hours = QSpinBox()
        self.spn_hours.setRange(0, 99)
        self.spn_hours.setSuffix(t("spin_hour_suffix", self.lang))
        self.spn_hours.setValue(0)
        self.spn_hours.setStyleSheet(spin_style)

        self.spn_minutes = QSpinBox()
        self.spn_minutes.setRange(0, 59)
        self.spn_minutes.setSuffix(t("spin_min_suffix", self.lang))
        self.spn_minutes.setValue(25)
        self.spn_minutes.setStyleSheet(spin_style)

        self.spn_seconds = QSpinBox()
        self.spn_seconds.setRange(0, 59)
        self.spn_seconds.setSuffix(t("spin_sec_suffix", self.lang))
        self.spn_seconds.setValue(0)
        self.spn_seconds.setStyleSheet(spin_style)

        self.btn_apply_duration = QPushButton(t("set_duration_btn", self.lang))
        self.btn_apply_duration.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_apply_duration.setFixedHeight(30)
        self.btn_apply_duration.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 12px;
                font-weight: 800;
                border-radius: 8px;
                padding: 0 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_apply_duration.clicked.connect(self._on_apply_custom_duration)

        self.spn_hours.editingFinished.connect(self._on_apply_custom_duration)
        self.spn_minutes.editingFinished.connect(self._on_apply_custom_duration)
        self.spn_seconds.editingFinished.connect(self._on_apply_custom_duration)

        custom_layout.addWidget(self.spn_hours)
        custom_layout.addWidget(self.spn_minutes)
        custom_layout.addWidget(self.spn_seconds)
        custom_layout.addWidget(self.btn_apply_duration)

        clock_layout.addWidget(self.custom_timer_frame)

        # Devasa Dijital Ekran (Saat : Dakika : Saniye : Salise)
        self.lbl_clock = QLabel("00:00:00:00")
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_clock.setStyleSheet("""
            QLabel {
                font-size: 64px;
                font-weight: 900;
                color: #00ff88;
                letter-spacing: 3px;
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        clock_layout.addWidget(self.lbl_clock)

        # Aksiyon Butonları
        actions_row = QHBoxLayout()
        actions_row.setSpacing(14)
        actions_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Başlat / Duraklat Butonu
        self.btn_play = QPushButton(t('btn_start', self.lang))
        self.btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_play.setFixedSize(160, 46)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_play.clicked.connect(self._on_play_clicked)

        # 2. Sıfırla Butonu
        self.btn_reset = QPushButton(t('btn_reset', self.lang))
        self.btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset.setFixedSize(120, 46)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 700;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                color: #ffffff;
            }
        """)
        self.btn_reset.clicked.connect(self._on_reset_clicked)

        # 3. Hedefe Ekle & Kaydet Butonu (Sadece Kronometre)
        self.btn_save = QPushButton(t('btn_save_to_goal', self.lang))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setFixedSize(180, 46)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.2);
                color: #34d399;
                font-size: 13px;
                font-weight: 800;
                border-radius: 12px;
                border: 1.5px solid rgba(16, 185, 129, 0.4);
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
                border-color: #10b981;
            }
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)

        # 4. Tur Ekle Butonu
        self.btn_lap = QPushButton(t('btn_add_lap', self.lang))
        self.btn_lap.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_lap.setFixedSize(120, 46)
        self.btn_lap.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                font-size: 13px;
                font-weight: 700;
                border-radius: 12px;
                border: 1.2px solid rgba(56, 189, 248, 0.3);
            }
            QPushButton:hover {
                background-color: #38bdf8;
                color: #ffffff;
            }
        """)
        self.btn_lap.clicked.connect(self._on_lap_clicked)

        actions_row.addWidget(self.btn_play)
        actions_row.addWidget(self.btn_reset)
        actions_row.addWidget(self.btn_save)
        actions_row.addWidget(self.btn_lap)
        clock_layout.addLayout(actions_row)

        layout.addWidget(self.clock_panel)

        # ---------------- 5. TUR (LAP) LİSTESİ ALANI ----------------
        self.laps_panel = QFrame()
        self.laps_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        laps_layout = QVBoxLayout(self.laps_panel)
        laps_layout.setContentsMargins(16, 14, 16, 14)
        laps_layout.setSpacing(10)

        self.lbl_laps_title = QLabel(t("laps_title", self.lang))
        self.lbl_laps_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        laps_layout.addWidget(self.lbl_laps_title)

        self.laps_container = QVBoxLayout()
        self.laps_container.setSpacing(6)
        laps_layout.addLayout(self.laps_container)

        layout.addWidget(self.laps_panel)

        # ---------------- 6. GEÇMİŞ ÇALIŞMA OTURUMLARI ----------------
        self.history_panel = QFrame()
        self.history_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        history_layout = QVBoxLayout(self.history_panel)
        history_layout.setContentsMargins(16, 14, 16, 14)
        history_layout.setSpacing(10)

        self.lbl_history_title = QLabel(t("history_sessions_title", self.lang))
        self.lbl_history_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        history_layout.addWidget(self.lbl_history_title)

        self.history_container = QVBoxLayout()
        self.history_container.setSpacing(6)
        history_layout.addLayout(self.history_container)

        layout.addWidget(self.history_panel)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self._update_tab_styles()

    # ---------------- ETKİLEŞİMLER ----------------

    def _select_mode(self, mode: str):
        timer_engine.set_mode(mode)
        self._update_tab_styles()
        self._on_engine_tick()

    def _on_engine_mode_changed(self, mode: str):
        self._update_tab_styles()
        self._on_engine_tick()

    def _update_tab_styles(self):
        is_sw = (timer_engine.mode == "stopwatch")
        self.btn_tab_sw.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 10px;
                padding: 0 20px;
                border: none;
            }
        """ if is_sw else """
            QPushButton {
                background-color: #162032;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 0 20px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton:hover {
                color: #f8fafc;
                background-color: #1e293b;
            }
        """)

        self.btn_tab_tm.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 10px;
                padding: 0 20px;
                border: none;
            }
        """ if not is_sw else """
            QPushButton {
                background-color: #162032;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 0 20px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton:hover {
                color: #f8fafc;
                background-color: #1e293b;
            }
        """)

        # Kronometre butonları ve geri sayım manuel süre girişi
        self.custom_timer_frame.setVisible(not is_sw)
        self.btn_save.setVisible(is_sw)
        self.btn_lap.setVisible(is_sw)
        self.laps_panel.setVisible(is_sw and len(timer_engine.get_laps()) > 0)

    def _on_apply_custom_duration(self):
        h = self.spn_hours.value()
        m = self.spn_minutes.value()
        s = self.spn_seconds.value()
        total_seconds = h * 3600 + m * 60 + s
        if total_seconds > 0:
            timer_engine.set_timer_duration(total_seconds)
            self._on_engine_tick()

    def _apply_timer_preset(self, seconds: int):
        timer_engine.set_timer_duration(seconds)
        self._on_engine_tick()

    def _on_play_clicked(self):
        if timer_engine.mode == "stopwatch":
            timer_engine.toggle_stopwatch()
        else:
            timer_engine.toggle_timer()
        self._on_engine_tick()

    def _on_reset_clicked(self):
        if timer_engine.mode == "stopwatch":
            timer_engine.reset_stopwatch()
            self._reload_laps()
        else:
            timer_engine.reset_timer()
        self._on_engine_tick()

    def _on_save_clicked(self):
        if timer_engine.mode == "stopwatch":
            s_id = timer_engine.save_stopwatch_session("Odaklanma Oturumu")
            if s_id > 0:
                try:
                    sfx.play_correct()
                except Exception:
                    pass
                self._refresh_all()

    def _on_lap_clicked(self):
        if timer_engine.mode == "stopwatch":
            lap = timer_engine.add_lap()
            if lap:
                self._reload_laps()
                self.laps_panel.setVisible(True)

    def _open_mini_widget(self):
        show_mini_timer_popup()

    def _on_session_saved(self, session_id: int):
        self._refresh_all()

    def _on_timer_finished(self):
        self._refresh_all()

    # ---------------- EKRAN GÜNCELLEMELERİ ----------------

    def _on_engine_tick(self):
        """Her 100ms'de bir saat göstergesini ve buton durumunu yeniler."""
        is_sw = (timer_engine.mode == "stopwatch")

        if is_sw:
            elapsed = timer_engine.get_stopwatch_elapsed()
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            cs = int((elapsed * 100) % 100)
            self.lbl_clock.setText(f"{h:02d}:{m:02d}:{s:02d}:{cs:02d}")

            is_running = timer_engine.is_stopwatch_running
            self.btn_play.setText(t('btn_pause', self.lang) if is_running else t('btn_start', self.lang))
            self.btn_play.setStyleSheet(
                "background-color: #f59e0b; color: #ffffff; font-size: 14px; font-weight: 800; border-radius: 12px; border: none;"
                if is_running else
                "background-color: #10b981; color: #ffffff; font-size: 14px; font-weight: 800; border-radius: 12px; border: none;"
            )
        else:
            rem = timer_engine.get_timer_remaining()
            h = int(rem // 3600)
            m = int((rem % 3600) // 60)
            s = int(rem % 60)
            if h > 0:
                self.lbl_clock.setText(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                self.lbl_clock.setText(f"{m:02d}:{s:02d}")

            is_running = timer_engine.is_timer_running
            self.btn_play.setText(t('btn_pause', self.lang) if is_running else t('btn_start', self.lang))
            self.btn_play.setStyleSheet(
                "background-color: #f59e0b; color: #ffffff; font-size: 14px; font-weight: 800; border-radius: 12px; border: none;"
                if is_running else
                "background-color: #10b981; color: #ffffff; font-size: 14px; font-weight: 800; border-radius: 12px; border: none;"
            )

    def refresh_view(self):
        self._refresh_all()

    def refresh_goal_progress(self):
        self._refresh_all()

    def _refresh_all(self):
        self._on_engine_tick()
        self._reload_1000h_progress()
        self._reload_laps()
        self._reload_history()

    def _open_target_hours_dialog(self):
        sfx.play_click()
        current_hours = timer_engine.get_target_hours()
        dlg = TargetHoursCustomDialog(current_hours=current_hours, lang=self.lang, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            timer_engine.set_target_hours(dlg.selected_hours)
            self._reload_1000h_progress()

    def _reload_1000h_progress(self):
        """Kullanıcının belirlediği hedef ilerleme istatistiklerini hesaplar ve günceller."""
        prog = timer_engine.get_1000h_progress()
        pct = prog["progress_pct"]
        self.goal_bar.setValue(int(pct))
        self.lbl_goal_pct.setText(f"%{pct:.1f} {t('goal_completed_pct', self.lang)}")

        target_h = prog["target_hours"]
        title_text = t("goal_title_template", self.lang, hours=f"{target_h:,}".replace(",", "."))
        self.lbl_goal_title.setText(title_text)

        self.box_total_done.set_values(
            t("goal_completed", self.lang),
            f"{prog['total_h']}s {prog['total_m']}dk"
        )
        self.box_pct.set_values(
            t("goal_pct", self.lang),
            f"%{pct:.2f}"
        )
        self.box_remaining.set_values(
            t("goal_remaining", self.lang),
            f"{prog['rem_h']}s {prog['rem_m']}dk"
        )

        recent = get_recent_timer_sessions(100)
        self.box_sessions.set_values(
            t("goal_sessions", self.lang),
            f"{len(recent)} {t('unit_session', self.lang)}"
        )

    def _reload_laps(self):
        while self.laps_container.count() > 0:
            item = self.laps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        laps = timer_engine.get_laps()
        if not laps:
            self.laps_panel.setVisible(False)
            return

        self.laps_panel.setVisible(True)
        for lap in reversed(laps):
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #111827;
                    border-radius: 8px;
                    padding: 6px 10px;
                }
            """)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(10, 6, 10, 6)

            lbl_lap_no = QLabel(ui_text('Lap #{number}',self.lang,number=lap['lap_no']))
            lbl_lap_no.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700; background: transparent;")

            split_s = int(lap["split"])
            lbl_split = QLabel(f"+{split_s // 60:02d}:{split_s % 60:02d}")
            lbl_split.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")

            tot_s = int(lap["total"])
            lbl_tot = QLabel(f"{tot_s // 3600:02d}:{(tot_s % 3600) // 60:02d}:{tot_s % 60:02d}")
            lbl_tot.setStyleSheet("color: #00ff88; font-size: 12px; font-weight: 800; background: transparent;")

            r_lay.addWidget(lbl_lap_no)
            r_lay.addWidget(lbl_split)
            r_lay.addStretch()
            r_lay.addWidget(lbl_tot)

            self.laps_container.addWidget(row)

    def _reload_history(self):
        while self.history_container.count() > 0:
            item = self.history_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sessions = get_recent_timer_sessions(8)
        if not sessions:
            lbl_empty = QLabel(t("no_sessions_yet", self.lang))
            lbl_empty.setStyleSheet("color: #64748b; font-size: 12px; padding: 8px; background: transparent;")
            self.history_container.addWidget(lbl_empty)
            return

        for s in sessions:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #111827;
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(12, 6, 12, 6)

            lbl_mode = QLabel(t('tab_stopwatch' if s['mode']=='stopwatch' else 'tab_countdown',self.lang))
            lbl_mode.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700; background: transparent;")

            lbl_date = QLabel(str(s["created_at"])[:16])
            lbl_date.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")

            dur_sec = s["duration_seconds"]
            dur_h = dur_sec // 3600
            dur_m = (dur_sec % 3600) // 60
            dur_s = dur_sec % 60
            dur_str = f"{dur_h}s {dur_m}dk {dur_s}sn" if dur_h > 0 else f"{dur_m}dk {dur_s}sn"

            lbl_dur = QLabel(dur_str)
            lbl_dur.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 800; background: transparent;")

            r_lay.addWidget(lbl_mode)
            r_lay.addWidget(lbl_date)
            r_lay.addStretch()
            r_lay.addWidget(lbl_dur)

            self.history_container.addWidget(row)

    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(t("timer_title", lang))
        self.lbl_subtitle.setText(t("timer_subtitle", lang))
        self.btn_open_mini.setText(t('btn_open_mini_widget', lang))
        if hasattr(self, "btn_select_target"):
            self.btn_select_target.setText(t("set_goal", lang))
        self.btn_tab_sw.setText(t('tab_stopwatch', lang))
        self.btn_tab_tm.setText(t('tab_countdown', lang))
        self.btn_reset.setText(t('btn_reset', lang))
        self.btn_save.setText(t('btn_save_to_goal', lang))
        self.btn_lap.setText(t('btn_add_lap', lang))
        self.lbl_laps_title.setText(t("laps_title", lang))
        self.lbl_history_title.setText(t("history_sessions_title", lang))

        if hasattr(self, "lbl_custom_t"):
            self.lbl_custom_t.setText(t("set_duration_label", lang))
        if hasattr(self, "btn_apply_duration"):
            self.btn_apply_duration.setText(t("set_duration_btn", lang))
        if hasattr(self, "spn_hours"):
            self.spn_hours.setSuffix(t("spin_hour_suffix", lang))
            self.spn_minutes.setSuffix(t("spin_min_suffix", lang))
            self.spn_seconds.setSuffix(t("spin_sec_suffix", lang))

        self._refresh_all()
        localize_tree(self,lang)
