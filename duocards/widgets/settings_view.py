"""Study Card ayarları: dil, ses, günlük hedef, widget ve bildirimler."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QSlider, QTimeEdit, QFrame,
    QScrollArea, QLineEdit, QSpinBox, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime, QTimer, QSignalBlocker
from PyQt6.QtGui import QCursor
from duocards.settings import settings
from duocards import autostart
from duocards.sfx import sfx
from duocards.i18n import t
from duocards.languages import get_language_name
from duocards.icons import get_icon
from duocards.widgets.steam_popup import show_steam_notification
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QCheckBox, QLineEdit, QComboBox


class SettingsView(QWidget):
    settings_saved = pyqtSignal()
    language_changed = pyqtSignal(str)
    open_widget_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")
        self._setup_ui()
        self.load_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.search_settings = QLineEdit()
        self.search_settings.setPlaceholderText(ui_text('Search settings…', self.lang))
        self.search_settings.textChanged.connect(self._filter_settings)
        main_layout.addWidget(self.search_settings)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0d121c;
                width: 6px;
                border-radius: 3px;
                margin: 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: #222d42;
                min-height: 28px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #10b981;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setContentsMargins(36, 28, 36, 40)
        self.content_layout.setSpacing(18)

        # Global Soft Panel & Form Elemanları Şablonu
        self.setStyleSheet("""
            /* Ana Kartlar */
            QFrame[panel="card"] {
                background-color: #121824;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 14px;
            }
            QFrame[panel="card"]:hover {
                border-color: rgba(255, 255, 255, 0.08);
            }

            /* Kart Başlık İkon Rozeti */
            QFrame[panel="icon_badge"] {
                background-color: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.16);
                border-radius: 9px;
            }

            /* Satır Ayraçları */
            QFrame[panel="separator"] {
                background-color: rgba(255, 255, 255, 0.035);
                max-height: 1px;
                height: 1px;
                border: none;
            }

            /* Alt Bilgi & Konfigürasyon Kutusu */
            QFrame[panel="subcard"] {
                background-color: #0d121c;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 10px;
            }

            /* Form Elemanları */
            QComboBox {
                background-color: #171f2e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: #f1f5f9;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox:hover {
                background-color: #1c2637;
                border-color: rgba(255, 255, 255, 0.16);
            }
            QComboBox:focus {
                border-color: #10b981;
                background-color: #1a2333;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #131926;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                selection-background-color: rgba(16, 185, 129, 0.18);
                selection-color: #34d399;
                color: #e2e8f0;
                padding: 4px;
                outline: none;
            }

            QLineEdit {
                background-color: #171f2e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 12px;
                color: #f8fafc;
                font-size: 13px;
                selection-background-color: #10b981;
            }
            QLineEdit:hover {
                background-color: #1c2637;
                border-color: rgba(255, 255, 255, 0.15);
            }
            QLineEdit:focus {
                border-color: #10b981;
                background-color: #151d2c;
            }

            QSpinBox, QTimeEdit {
                background-color: #171f2e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 10px;
                color: #f8fafc;
                font-size: 13px;
                font-weight: 600;
            }
            QSpinBox:hover, QTimeEdit:hover {
                background-color: #1c2637;
                border-color: rgba(255, 255, 255, 0.16);
            }
            QSpinBox:focus, QTimeEdit:focus {
                border-color: #10b981;
            }

            QCheckBox {
                color: #f1f5f9;
                font-size: 13px;
                font-weight: 600;
                spacing: 10px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 19px;
                height: 19px;
                border-radius: 5px;
                background-color: #171f2e;
                border: 1px solid rgba(255, 255, 255, 0.14);
            }
            QCheckBox::indicator:hover {
                background-color: #1d273a;
                border-color: #10b981;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #10b981;
            }

            /* QSlider */
            QSlider::groove:horizontal {
                height: 6px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #10b981;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #34d399;
                border-color: #059669;
            }

            /* Buton Çeşitleri */
            QPushButton[btnStyle="secondary"] {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: #cbd5e1;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton[btnStyle="secondary"]:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.16);
            }
            QPushButton[btnStyle="secondary"]:pressed {
                background-color: rgba(255, 255, 255, 0.03);
            }

            QPushButton[btnStyle="accent"] {
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.22);
                color: #34d399;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 16px;
            }
            QPushButton[btnStyle="accent"]:hover {
                background-color: rgba(16, 185, 129, 0.18);
                color: #6ee7b7;
                border-color: rgba(16, 185, 129, 0.35);
            }

            QPushButton[btnStyle="danger"] {
                background-color: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.2);
                color: #f87171;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton[btnStyle="danger"]:hover {
                background-color: rgba(239, 68, 68, 0.16);
                color: #fca5a5;
                border-color: rgba(239, 68, 68, 0.3);
            }

            QPushButton#btnSaveSettings {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 700;
                padding: 10px 28px;
            }
            QPushButton#btnSaveSettings:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
            }
            QPushButton#btnSaveSettings:pressed {
                background: #047857;
            }
        """)

        # ---------------- SAYFA BAŞLIĞI VE AÇIKLAMA ----------------
        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        self.lbl_title = QLabel(t("settings_title", self.lang))
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc; letter-spacing: -0.4px; background: transparent; border: none;")
        self.lbl_subtitle = QLabel(t("settings_subtitle", self.lang))
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 400; background: transparent; border: none;")
        header_box.addWidget(self.lbl_title)
        header_box.addWidget(self.lbl_subtitle)
        self.content_layout.addLayout(header_box)

        # ---------------- BÖLÜM 1: DİL VE BÖLGE SEÇENEKLERİ ----------------
        box_lang, box_lang_lay = self._create_card("globe")
        self.lbl_sec_lang = self._add_card_header(box_lang_lay, "globe", t("sec_lang", self.lang), self._get_sec_desc("lang"))

        # Dil Seçimi Satırı
        self.lbl_ui_lang = QLabel(t("ui_language", self.lang))
        self.cmb_lang = QComboBox()
        for code in ('tr', 'en', 'de', 'es'):
            self.cmb_lang.addItem(get_language_name(code, self.lang), code)
        self.cmb_lang.setMinimumWidth(220)
        self.cmb_lang.setFixedHeight(36)
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)

        self._add_row(box_lang_lay, self.lbl_ui_lang, self._get_hint("lang"), self.cmb_lang)
        self.content_layout.addWidget(box_lang)

        from duocards.widgets.device_backup_panel import DeviceBackupPanel
        self.backup_panel = DeviceBackupPanel(self.lang)
        self.content_layout.addWidget(self.backup_panel)

        # ---------------- BÖLÜM 3: SES VE TELAFFUZ SEÇENEKLERİ ----------------
        box_audio, box_audio_lay = self._create_card("audio")
        self.lbl_sec_audio = self._add_card_header(box_audio_lay, "audio", t("sec_audio", self.lang), self._get_sec_desc("audio"))

        # SFX Aç/Kapat
        self.chk_sfx = QCheckBox()
        self.lbl_sfx_title = QLabel(t("sfx_enable", self.lang))
        self._add_row(box_audio_lay, self.lbl_sfx_title, self._get_hint("sfx"), self.chk_sfx)

        self._add_separator(box_audio_lay)

        # Ses Seviyesi Slider & Test
        self.lbl_vol_title = QLabel(t("sfx_vol", self.lang))
        vol_widget = QWidget()
        vol_lay = QHBoxLayout(vol_widget)
        vol_lay.setContentsMargins(0, 0, 0, 0)
        vol_lay.setSpacing(12)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.slider_vol.setFixedHeight(26)
        self.slider_vol.setMinimumWidth(180)
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_val.setText(f"{v}%"))

        self.lbl_vol_val = QLabel("80%")
        self.lbl_vol_val.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px; min-width: 38px; background: transparent; border: none;")

        self.btn_test_sfx = QPushButton(t("btn_test_sfx", self.lang))
        self.btn_test_sfx.setProperty("btnStyle", "secondary")
        self.btn_test_sfx.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_test_sfx.setFixedHeight(32)
        self.btn_test_sfx.clicked.connect(self._test_sfx)

        vol_lay.addWidget(self.slider_vol, 1)
        vol_lay.addWidget(self.lbl_vol_val)
        vol_lay.addWidget(self.btn_test_sfx)

        self._add_row(box_audio_lay, self.lbl_vol_title, self._get_hint("vol"), vol_widget)

        self._add_separator(box_audio_lay)

        # Otomatik Telaffuz
        self.chk_auto_pronounce = QCheckBox()
        self.chk_auto_pronounce.toggled.connect(self._on_auto_pronounce_toggled)
        self.lbl_auto_pr_title = QLabel(t("auto_pronounce", self.lang))
        self._add_row(box_audio_lay, self.lbl_auto_pr_title, self._get_hint("auto_pr"), self.chk_auto_pronounce)

        self._add_separator(box_audio_lay)

        # Telaffuz Zamanlaması
        self.lbl_pr_timing = QLabel(t("pronounce_timing_label", self.lang))
        self.cmb_pr_timing = QComboBox()
        self.cmb_pr_timing.setFixedHeight(36)
        self.cmb_pr_timing.setMinimumWidth(230)
        self.cmb_pr_timing.addItem(t("pronounce_flip", self.lang), "flip")
        self.cmb_pr_timing.addItem(t("pronounce_appear", self.lang), "appear")
        self.cmb_pr_timing.addItem(t("pronounce_both", self.lang), "both")

        self._add_row(box_audio_lay, self.lbl_pr_timing, self._get_hint("pr_timing"), self.cmb_pr_timing)
        self.content_layout.addWidget(box_audio)

        # ---------------- BÖLÜM 4: ÇALIŞMA VE HEDEFLER ----------------
        box_study, box_study_lay = self._create_card("target")
        self.lbl_sec_study = self._add_card_header(box_study_lay, "target", t("sec_study", self.lang), self._get_sec_desc("study"))

        # Günlük Kart Hedefi
        self.lbl_daily_goal = QLabel(t("daily_goal", self.lang))
        self.spin_daily_goal = QSpinBox()
        self.spin_daily_goal.setRange(5, 100)
        self.spin_daily_goal.setSingleStep(5)
        self.spin_daily_goal.setValue(10)
        self.spin_daily_goal.setFixedWidth(90)
        self.spin_daily_goal.setFixedHeight(36)

        self.lbl_goal_desc = QLabel(t("goal_desc", self.lang))
        self._add_row(box_study_lay, self.lbl_daily_goal, self.lbl_goal_desc, self.spin_daily_goal)

        self._add_separator(box_study_lay)

        # Kart Silme Onayını Sıfırla
        self.lbl_del_reset_title = QLabel(ui_text('Card Deletion Confirmation', self.lang))
        del_controls = QWidget()
        del_controls_lay = QHBoxLayout(del_controls)
        del_controls_lay.setContentsMargins(0, 0, 0, 0)
        del_controls_lay.setSpacing(10)

        self.btn_reset_del_confirm = QPushButton(t("btn_reset_del_confirm", self.lang))
        self.btn_reset_del_confirm.setProperty("btnStyle", "danger")
        self.btn_reset_del_confirm.setFixedHeight(34)
        self.btn_reset_del_confirm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset_del_confirm.clicked.connect(self._reset_delete_confirmation)

        self.lbl_reset_status = QLabel("")
        self.lbl_reset_status.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; background: transparent; border: none;")

        del_controls_lay.addWidget(self.btn_reset_del_confirm)
        del_controls_lay.addWidget(self.lbl_reset_status)
        del_controls_lay.addStretch()

        self._add_row(box_study_lay, self.lbl_del_reset_title, self._get_hint("del_reset"), del_controls)
        self.content_layout.addWidget(box_study)

        # ---------------- BÖLÜM 5: MASAÜSTÜ WIDGET & SİSTEM ----------------
        box_widget, box_widget_lay = self._create_card("desktop")
        self.lbl_sec_widget = self._add_card_header(box_widget_lay, "desktop", t("sec_widget", self.lang), self._get_sec_desc("widget"))

        # Widget Başlatma Satırı
        self.lbl_widget_title = QLabel(ui_text('Desktop Mini Widget', self.lang))
        self.lbl_widget_desc = QLabel(t("desktop_widget_desc", self.lang))
        self.btn_open_widget = QPushButton(t("btn_open_widget", self.lang))
        self.btn_open_widget.setProperty("btnStyle", "accent")
        self.btn_open_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_widget.setFixedHeight(36)
        self.btn_open_widget.clicked.connect(lambda: self.open_widget_requested.emit())

        self._add_row(box_widget_lay, self.lbl_widget_title, self.lbl_widget_desc, self.btn_open_widget)

        self._add_separator(box_widget_lay)

        # Otomatik Başlatma Satırı
        self.chk_autostart = QCheckBox()
        self.lbl_autostart_title = QLabel(t("autostart_enable", self.lang))
        self._add_row(box_widget_lay, self.lbl_autostart_title, self._get_hint("autostart"), self.chk_autostart)

        self._add_separator(box_widget_lay)

        # Global Kısayol Satırı
        self.lbl_shortcut = QLabel(t("shortcut_label", self.lang))
        self.cmb_shortcut = QComboBox()
        self.cmb_shortcut.setFixedHeight(36)
        self.cmb_shortcut.setMinimumWidth(210)
        default_label = ui_text('Ctrl+Alt+S (Default)', self.lang)
        none_label = ui_text('Disabled (None)', self.lang)
        self.cmb_shortcut.addItem(default_label, "Ctrl+Alt+S")
        self.cmb_shortcut.addItem("F9", "F9")
        self.cmb_shortcut.addItem("F10", "F10")
        self.cmb_shortcut.addItem("Ctrl+Shift+S", "Ctrl+Shift+S")
        self.cmb_shortcut.addItem("Alt+S", "Alt+S")
        self.cmb_shortcut.addItem(none_label, "")
        self.cmb_shortcut.currentIndexChanged.connect(self._on_shortcut_changed)

        self._add_row(box_widget_lay, self.lbl_shortcut, self._get_hint("shortcut"), self.cmb_shortcut)
        self.content_layout.addWidget(box_widget)

        # ---------------- BÖLÜM 6: BİLDİRİMLER ----------------
        box_notif, box_notif_lay = self._create_card("bell")
        self.lbl_n_title = self._add_card_header(box_notif_lay, "bell", t("notif_title", self.lang), self._get_sec_desc("notif"))

        # Bildirim Aç/Kapat
        self.chk_notif = QCheckBox()
        self.lbl_notif_enable_title = QLabel(t("notif_enable", self.lang))
        self._add_row(box_notif_lay, self.lbl_notif_enable_title, self._get_hint("notif"), self.chk_notif)

        self._add_separator(box_notif_lay)

        # Bildirim Saati ve Test Butonu
        self.lbl_notif_time = QLabel(t("notif_time", self.lang))
        time_widget = QWidget()
        time_lay = QHBoxLayout(time_widget)
        time_lay.setContentsMargins(0, 0, 0, 0)
        time_lay.setSpacing(10)

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(20, 0))
        self.time_edit.setFixedWidth(100)
        self.time_edit.setFixedHeight(36)

        self.btn_test_notif = QPushButton(t("btn_test_notif", self.lang))
        self.btn_test_notif.setProperty("btnStyle", "secondary")
        self.btn_test_notif.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_test_notif.setFixedHeight(36)
        self.btn_test_notif.clicked.connect(self._test_notification)

        time_lay.addWidget(self.time_edit)
        time_lay.addWidget(self.btn_test_notif)

        self._add_row(box_notif_lay, self.lbl_notif_time, self._get_hint("notif_time"), time_widget)
        self.content_layout.addWidget(box_notif)

        from duocards.widgets.personalization import build_cards
        build_cards(self)

        # ---------------- ALT KAYDET ÇUBUĞU (SOFT DOCK) ----------------
        bottom_box = QFrame()
        bottom_box.setStyleSheet("background: transparent; border: none; margin-top: 10px;")
        bottom_bar = QHBoxLayout(bottom_box)
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(16)

        self.btn_save = QPushButton(t("btn_save_settings", self.lang))
        self.btn_save.setObjectName("btnSaveSettings")
        self.btn_save.setProperty('btnStyle','accent')
        from duocards.styles import transform_preferences
        save_style='''QPushButton { background: #153b36; color: #6ee7b7; border: 1px solid #23765e; border-radius: 10px; padding: 8px 22px; font-size: 13.5px; font-weight: 700; }
            QPushButton:hover { background: #1c5044; border-color: #34d399; color: #a7f3d0; }
            QPushButton:pressed { background: #123329; }
            QPushButton:disabled { background: #152b27; color: #64748b; }'''
        self.btn_save._preference_original_style=save_style
        self.btn_save._preference_applied_style=transform_preferences(save_style)
        self.btn_save.setStyleSheet(self.btn_save._preference_applied_style)
        self.btn_save.setIcon(get_icon('check',18,'#6ee7b7'))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.setFixedHeight(44)
        self.btn_save.setMinimumWidth(220)
        self.btn_save.clicked.connect(self._save_settings)

        self.lbl_save_status = QLabel("")
        self.lbl_save_status.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px; background: transparent; border: none;")

        bottom_bar.addWidget(self.btn_save)
        bottom_bar.addWidget(self.lbl_save_status)
        bottom_bar.addStretch()
        self.content_layout.addWidget(bottom_box)

        self.scroll.setWidget(container)
        main_layout.addWidget(self.scroll)

    # ---------------- UI YARDIMCI METOTLARI (SOFT DİZAYN MOTORU) ----------------

    def _create_card(self, icon_name: str):
        card = QFrame()
        card.setProperty("panel", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)
        return card, card_layout

    def _add_card_header(self, parent_layout: QVBoxLayout, icon_name: str, title: str, subtitle: str):
        header_widget = QWidget()
        header_lay = QHBoxLayout(header_widget)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(14)

        # Rozet
        badge = QFrame()
        badge.setProperty("panel", "icon_badge")
        badge.setFixedSize(38, 38)
        b_lay = QVBoxLayout(badge)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon(icon_name, 20, "#10b981").pixmap(20, 20))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        b_lay.addWidget(icon_lbl)

        # Metinler
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        lbl_h_title = QLabel(title)
        lbl_h_title.setWordWrap(True)
        lbl_h_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc; letter-spacing: -0.2px; background: transparent; border: none;")

        lbl_h_sub = QLabel(subtitle)
        lbl_h_sub.setWordWrap(True)
        lbl_h_sub.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 400; background: transparent; border: none;")

        t_box.addWidget(lbl_h_title)
        t_box.addWidget(lbl_h_sub)

        header_lay.addWidget(badge)
        header_lay.addLayout(t_box, 1)

        parent_layout.addWidget(header_widget)
        self._add_separator(parent_layout)
        return lbl_h_title

    def _add_separator(self, parent_layout: QVBoxLayout):
        sep = QFrame()
        sep.setProperty("panel", "separator")
        sep.setFixedHeight(1)
        parent_layout.addWidget(sep)

    def _add_row(self, parent_layout: QVBoxLayout, title_widget_or_text, desc_widget_or_text, control_widget):
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(2, 4, 2, 4)
        row_lay.setSpacing(20)

        left_box = QVBoxLayout()
        left_box.setSpacing(3)

        if isinstance(title_widget_or_text, QLabel):
            title_lbl = title_widget_or_text
        else:
            title_lbl = QLabel(title_widget_or_text)
        title_lbl.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #e2e8f0; background: transparent; border: none;")
        title_lbl.setWordWrap(True)

        if isinstance(desc_widget_or_text, QLabel):
            desc_lbl = desc_widget_or_text
        else:
            desc_lbl = QLabel(desc_widget_or_text)
        desc_lbl.setStyleSheet("font-size: 12px; color: #64748b; line-height: 1.35; background: transparent; border: none;")
        desc_lbl.setWordWrap(True)

        left_box.addWidget(title_lbl)
        left_box.addWidget(desc_lbl)

        row_lay.addLayout(left_box, 1)
        row_lay.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        parent_layout.addWidget(row)

    def _add_sub_row(self, parent_layout: QVBoxLayout, title_lbl: QLabel, hint_text: str, control_widget):
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 2, 0, 2)
        row_lay.setSpacing(16)

        left_box = QVBoxLayout()
        left_box.setSpacing(2)

        title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #cbd5e1; background: transparent; border: none;")
        hint_lbl = QLabel(hint_text)
        hint_lbl.setStyleSheet("font-size: 11.5px; color: #64748b; background: transparent; border: none;")
        hint_lbl.setWordWrap(True)

        left_box.addWidget(title_lbl)
        left_box.addWidget(hint_lbl)

        row_lay.addLayout(left_box, 1)
        row_lay.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        parent_layout.addWidget(row)

    def _get_sec_desc(self, sec: str) -> str:
        tr = (self.lang == "tr")
        descs = {
            "lang": ui_text('Set interface language and regional localization options.', self.lang),
            "audio": ui_text('Sound effects, volume level, and pronunciation timing options.', self.lang),
            "study": ui_text('Daily card repetition goals and card safety preferences.', self.lang),
            "widget": ui_text('Floating desktop widget, global hotkey, and autostart preferences.', self.lang),
            "notif": ui_text('Desktop reminder notifications to keep your daily study streak.', self.lang)
        }
        return descs.get(sec, "")

    def _get_hint(self, key: str) -> str:
        tr = (self.lang == "tr")
        hints = {
            "lang": ui_text('Changes language across all menus, buttons, and notifications.', self.lang),
            "sfx": ui_text('Plays card flips, correct/wrong answers, and button clicks.', self.lang),
            "vol": ui_text('Master volume for all sound effects and word pronunciations.', self.lang),
            "auto_pr": ui_text('Automatically speaks the word pronunciation aloud.', self.lang),
            "pr_timing": ui_text('Choose when the pronunciation audio should trigger.', self.lang),
            "del_reset": ui_text('Re-enables card deletion confirmation dialog.', self.lang),
            "autostart": ui_text('Study Card starts silently in background on boot.', self.lang),
            "shortcut": ui_text('Global key combination to summon the app window.', self.lang),
            "notif": ui_text('Shows a desktop notification at your scheduled study time.', self.lang),
            "notif_time": ui_text('Choose your preferred daily notification time.', self.lang)
        }
        return hints.get(key, "")

    # ---------------- VERİ YÜKLEME VE SENKRONİZASYON ----------------

    def load_values(self):
        controls = [self.cmb_lang,
                    self.chk_auto_pronounce, self.cmb_pr_timing, self.cmb_shortcut]
        blockers = [QSignalBlocker(control) for control in controls]
        self._loading_values = True
        try:
            from duocards.widgets.personalization import set_value
            for key, (control, kind) in self.extra_controls.items():
                set_value(control, kind, settings.get(key))
            # Dil
            cur_lang = settings.get("ui_language", "tr")
            for i in range(self.cmb_lang.count()):
                if self.cmb_lang.itemData(i) == cur_lang:
                    self.cmb_lang.setCurrentIndex(i)
                    break

            # Bildirim
            self.chk_notif.setChecked(settings.get("daily_notification_enabled", False))
            t_str = settings.get("notification_time", "20:00")
            parts = t_str.split(":")
            if len(parts) == 2:
                self.time_edit.setTime(QTime(int(parts[0]), int(parts[1])))

            # Ses
            self.chk_sfx.setChecked(settings.get("sfx_enabled", True))
            vol = settings.get("sfx_volume", 80)
            self.slider_vol.setValue(vol)
            self.lbl_vol_val.setText(f"{vol}%")
            auto_pr = settings.get("auto_pronounce", False)
            self.chk_auto_pronounce.setChecked(auto_pr)
            self.cmb_pr_timing.setEnabled(auto_pr)
            pr_trig = settings.get("pronounce_trigger", "flip")
            self.cmb_pr_timing.blockSignals(True)
            idx_trig = self.cmb_pr_timing.findData(pr_trig)
            if idx_trig >= 0:
                self.cmb_pr_timing.setCurrentIndex(idx_trig)
            self.cmb_pr_timing.blockSignals(False)
            self.spin_daily_goal.setValue(settings.get("daily_goal", 10))

            # Otomatik Başlatma ve Kısayol
            autostart_on = settings.get("autostart_enabled", False)
            if autostart.is_enabled():
                autostart_on = True
            self.chk_autostart.setChecked(autostart_on)

            current_sc = settings.get("app_shortcut", "Ctrl+Alt+S")
            idx = self.cmb_shortcut.findData(current_sc)
            self.cmb_shortcut.blockSignals(True)
            if idx >= 0:
                self.cmb_shortcut.setCurrentIndex(idx)
            self.cmb_shortcut.blockSignals(False)
            self._sync_desktop_shortcut(current_sc)
        finally:
            self._loading_values = False
            for blocker in blockers:
                blocker.unblock()

    def _on_lang_changed(self):
        new_lang = self.cmb_lang.currentData()
        if new_lang:
            self.lang = new_lang
            settings.set("ui_language", new_lang)
            settings.save()
            self.update_language(new_lang)
            self.language_changed.emit(new_lang)

    def _test_sfx(self):
        settings.set("sfx_volume", self.slider_vol.value())
        sfx.play_correct()

    def _test_notification(self):
        try:
            msg = (
                ui_text("Time to review today's flashcards! Take 5 minutes to keep your streak alive!", self.lang)
            )
            title = ui_text('DAILY STUDY TIME', self.lang)
            show_steam_notification(title, msg)
        except Exception as e:
            title = ui_text('Notification', self.lang)
            QMessageBox.warning(self, title, ui_text('Notification error: {error}',self.lang,error=e))

    def _sync_autostart(self, enabled: bool):
        try:
            autostart.set_enabled(enabled)
        except OSError:
            pass

    def _save_settings(self):
        from duocards.widgets.personalization import get_value
        values = {key: get_value(control, kind) for key, (control, kind) in self.extra_controls.items()}
        lang = self.cmb_lang.currentData() or "tr"
        autostart_val = self.chk_autostart.isChecked()
        shortcut_val = self.cmb_shortcut.currentData() or ""
        values.update(ui_language=lang, daily_notification_enabled=self.chk_notif.isChecked(),
                      notification_time=self.time_edit.time().toString('HH:mm'), sfx_enabled=self.chk_sfx.isChecked(),
                      sfx_volume=self.slider_vol.value(), auto_pronounce=self.chk_auto_pronounce.isChecked(),
                      pronounce_trigger=self.cmb_pr_timing.currentData() or 'flip', daily_goal=self.spin_daily_goal.value(),
                      autostart_enabled=autostart_val, app_shortcut=shortcut_val)
        settings.update(values)
        self._sync_autostart(autostart_val)
        self._sync_desktop_shortcut(shortcut_val)

        self.lbl_save_status.setText(t('saved_success', lang))
        sfx.play_click()
        self.settings_saved.emit()

    def _filter_settings(self, query):
        query = query.casefold().strip()
        if not hasattr(self, 'content_layout'):
            return
        for index in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(index).widget()
            if isinstance(widget, QFrame) and widget.property('panel') == 'card':
                words = ' '.join(label.text() for label in widget.findChildren(QLabel))
                words += ' ' + ' '.join(button.text() for button in widget.findChildren(QPushButton))
                widget.setVisible(not query or query in words.casefold())

    def _on_auto_pronounce_toggled(self, checked: bool):
        self.cmb_pr_timing.setEnabled(checked)
        settings.set("auto_pronounce", checked)

    def _on_shortcut_changed(self):
        val = self.cmb_shortcut.currentData() or ""
        settings.set("app_shortcut", val)
        self._sync_desktop_shortcut(val)
        self.settings_saved.emit()

    def _reset_delete_confirmation(self):
        settings.set("dont_ask_delete_card", False)
        settings.save()
        self.lbl_reset_status.setText(t("del_confirm_reset_success", self.lang))
        QTimer.singleShot(3000, lambda: self.lbl_reset_status.setText(""))

    def _sync_desktop_shortcut(self, shortcut: str):
        pass

    def update_language(self, lang: str):
        self.lang = lang
        with QSignalBlocker(self.cmb_lang):
            for index in range(self.cmb_lang.count()):
                self.cmb_lang.setItemText(index, get_language_name(self.cmb_lang.itemData(index), lang))
        self.backup_panel.update_language(lang)
        self.lbl_title.setText(t("settings_title", lang))
        self.lbl_subtitle.setText(t("settings_subtitle", lang))
        self.lbl_sec_lang.setText(t("sec_lang", lang))
        self.lbl_ui_lang.setText(t("ui_language", lang))
        self.lbl_sec_widget.setText(t("sec_widget", lang))
        self.lbl_widget_title.setText(ui_text('Desktop Mini Widget', lang))
        self.lbl_widget_desc.setText(t("desktop_widget_desc", lang))
        self.btn_open_widget.setText(t("btn_open_widget", lang))
        self.lbl_autostart_title.setText(t("autostart_enable", lang))
        self.lbl_shortcut.setText(t("shortcut_label", lang))
        self.lbl_n_title.setText(t("notif_title", lang))
        self.lbl_notif_enable_title.setText(t("notif_enable", lang))
        self.lbl_notif_time.setText(t("notif_time", lang))
        self.btn_test_notif.setText(t("btn_test_notif", lang))
        self.lbl_sec_audio.setText(t("sec_audio", lang))
        self.lbl_sfx_title.setText(t("sfx_enable", lang))
        self.lbl_vol_title.setText(t("sfx_vol", lang))
        self.btn_test_sfx.setText(t("btn_test_sfx", lang))
        self.lbl_auto_pr_title.setText(t("auto_pronounce", lang))
        self.lbl_pr_timing.setText(t("pronounce_timing_label", lang))
        self.lbl_sec_study.setText(t("sec_study", lang))
        self.lbl_daily_goal.setText(t("daily_goal", lang))
        self.lbl_goal_desc.setText(t("goal_desc", lang))
        self.lbl_del_reset_title.setText(ui_text('Card Deletion Confirmation', lang))
        self.btn_reset_del_confirm.setText(t("btn_reset_del_confirm", lang))
        self.btn_save.setText(t("btn_save_settings", lang))
        localize_tree(self,lang)
