"""
Study Card - Study Session View
Gelişmiş kart çalışma, aralıklı tekrar (SRS), oyunlaştırma animasyonları,
odak sayacı, kombo çarpanı, hafıza ipuçları, ters yön ve aktif hatırlama pratikleri.
"""

import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QComboBox, QStackedWidget, QFrame, QMessageBox,
    QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QCursor
from duocards.db import (
    get_all_decks, get_study_cards, record_study_result, get_distinct_target_languages,
    get_daily_streak, get_today_review_count, add_timer_session, calculate_review_interval
)
from duocards.widgets.card_widget import FlashcardWidget
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.i18n import t
from duocards.languages import detect_card_term_language
from duocards.icons import get_icon
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QComboBox


class StudyView(QWidget):
    request_add_card = pyqtSignal()
    request_edit_card = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_initialized = False
        self.cards_queue = []
        self.repeat_queue = []
        self.session_failed_cards = []   # Oturumda hata yapılanlar (Hataları Tekrar Et için)
        self.current_card_index = 0
        self.session_total_count = 0
        self.known_count = 0
        self.again_count = 0

        self.selected_deck_id = None
        self.selected_target_lang = None
        self.selected_study_mode = "smart"
        self.reverse_mode = False        # Ters Mod (Anlam ➔ Hedef Kelime)
        self.type_in_enabled = False     # Yazarak Pratik Yapma Modu

        self.lang = settings.get("ui_language", "tr")
        self._is_transitioning = False

        self._setup_ui()
        self._setup_shortcuts()
        self._refresh_mode_selector()
        self.refresh_decks_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(12)

        # ---------------- 1. ÜST BAR: SEÇİCİLER & OYUNLAŞTIRMA ROZETLERİ ----------------
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.deck_selector = QComboBox()
        self.deck_selector.setMinimumWidth(200)
        self.deck_selector.currentIndexChanged.connect(self._on_deck_changed)
        top_bar.addWidget(self.deck_selector)

        # Anlam Dili Filtresi
        self.lang_filter_selector = QComboBox()
        self.lang_filter_selector.setMinimumWidth(170)
        self.lang_filter_selector.currentIndexChanged.connect(self._on_lang_filter_changed)
        top_bar.addWidget(self.lang_filter_selector)

        # Çalışma Modu (Akıllı SRS / Hatalar / Favoriler / Tüm Kartlar)
        self.mode_selector = QComboBox()
        self.mode_selector.setMinimumWidth(210)
        self.mode_selector.currentIndexChanged.connect(self._on_study_mode_changed)
        top_bar.addWidget(self.mode_selector)

        top_bar.addStretch()

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setStyleSheet("font-size: 13px; font-weight: 800; color: #94a3b8; background: transparent;")
        top_bar.addWidget(self.lbl_counter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b;
                border-radius: 5px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #38bdf8);
                border-radius: 5px;
            }
        """)
        top_bar.addWidget(self.progress_bar)

        main_layout.addLayout(top_bar)

        # ---------------- 2. ALT HIZLI ARAÇ ÇUBUĞU (EZBER KOLAYLAŞTIRICILAR) ----------------
        quick_tools_bar = QHBoxLayout()
        quick_tools_bar.setSpacing(8)

        # Ters Mod Butonu
        self.btn_toggle_reverse = QPushButton(ui_text('🔄 Dir: Term ➔ Meaning', self.lang))
        self.btn_toggle_reverse.setCheckable(True)
        self.btn_toggle_reverse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_reverse.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border-color: #38bdf8;
            }
            QPushButton:checked {
                background: rgba(56, 189, 248, 0.25);
                color: #7dd3fc;
                border-color: #38bdf8;
                font-weight: 800;
            }
        """)
        self.btn_toggle_reverse.clicked.connect(self._toggle_reverse_mode)
        self.btn_toggle_reverse.setToolTip(ui_text('Shortcut: [R] — Recall the word from its meaning.', self.lang))
        quick_tools_bar.addWidget(self.btn_toggle_reverse)

        # Yazarak Ezberle Modu Butonu
        self.btn_toggle_type_in = QPushButton(ui_text('✍️ Practice Typing (W)', self.lang))
        self.btn_toggle_type_in.setCheckable(True)
        self.btn_toggle_type_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_type_in.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border-color: #10b981;
            }
            QPushButton:checked {
                background: rgba(16, 185, 129, 0.25);
                color: #6ee7b7;
                border-color: #10b981;
                font-weight: 800;
            }
        """)
        self.btn_toggle_type_in.clicked.connect(self._toggle_type_in)
        self.btn_toggle_type_in.setToolTip(ui_text('Shortcut: [W] — Type your answer and press Enter.', self.lang))
        quick_tools_bar.addWidget(self.btn_toggle_type_in)

        # Hızlı Aksiyon Butonları (Telaffuz, Cümle, İpucu, Favori)
        self.btn_quick_audio = QPushButton(ui_text('🔊 Pronunciation (S)', self.lang))
        self.btn_quick_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_audio.setStyleSheet(self._quick_action_style())
        self.btn_quick_audio.clicked.connect(self._play_current_sound)
        quick_tools_bar.addWidget(self.btn_quick_audio)

        self.btn_quick_sentence = QPushButton(ui_text('🔊 Sentence (C)', self.lang))
        self.btn_quick_sentence.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_sentence.setStyleSheet(self._quick_action_style())
        self.btn_quick_sentence.clicked.connect(self._play_sentence_sound)
        quick_tools_bar.addWidget(self.btn_quick_sentence)

        self.btn_quick_fav = QPushButton(ui_text('⭐ Favorite (F)', self.lang))
        self.btn_quick_fav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quick_fav.setStyleSheet(self._quick_action_style("#eab308"))
        self.btn_quick_fav.clicked.connect(self._toggle_card_favorite)
        quick_tools_bar.addWidget(self.btn_quick_fav)

        quick_tools_bar.addStretch()

        main_layout.addLayout(quick_tools_bar)

        # ---------------- 3. ORTA ALAN: STACK (ÇALIŞMA vs. BİTİŞ vs. BOŞ) ----------------
        self.stack = QStackedWidget()

        # Sayfa 0: Kart Çalışma Sayfası
        self.page_study = QWidget()
        study_layout = QVBoxLayout(self.page_study)
        study_layout.setContentsMargins(0, 6, 0, 6)
        study_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.card_widget = FlashcardWidget(is_preview=False)
        self.card_widget.flipped.connect(self._on_card_flipped)
        self.card_widget.favorite_toggled.connect(self._on_card_favorite_toggled)
        self.card_widget.active_recall_tested.connect(self._on_active_recall_tested)
        study_layout.addWidget(self.card_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Alt Aksiyon Butonları Alanı
        self.actions_container = QWidget()
        actions_layout = QHBoxLayout(self.actions_container)
        actions_layout.setContentsMargins(0, 12, 0, 0)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.setSpacing(14)

        # Kart henüz çevrilmemişken gösterilen buton:
        self.btn_flip = QPushButton(t("flip_card", settings.get("ui_language", "tr")))
        self.btn_flip.setObjectName("btnFlip")
        self.btn_flip.setMinimumWidth(260)
        self.btn_flip.setFixedHeight(46)
        self.btn_flip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_flip.setStyleSheet("""
            QPushButton#btnFlip {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                font-size: 15px;
                font-weight: 800;
                border-radius: 14px;
                border: none;
            }
            QPushButton#btnFlip:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
            }
        """)
        self.btn_flip.clicked.connect(self._flip_current_card)
        actions_layout.addWidget(self.btn_flip)

        # Kart çevrildiğinde gösterilen derecelendirme butonları:
        self.rating_widget = QWidget()
        rating_layout = QHBoxLayout(self.rating_widget)
        rating_layout.setContentsMargins(0, 0, 0, 0)
        rating_layout.setSpacing(14)

        self.btn_repeat = QPushButton(t("repeat", settings.get("ui_language", "tr")))
        self.btn_repeat.setObjectName("btnRepeat")
        self.btn_repeat.setMinimumWidth(150)
        self.btn_repeat.setFixedHeight(46)
        self.btn_repeat.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_repeat.setStyleSheet("""
            QPushButton#btnRepeat {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #b91c1c);
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                border-radius: 14px;
                border: none;
            }
            QPushButton#btnRepeat:hover {
                background: #991b1b;
            }
        """)
        self.btn_repeat.clicked.connect(lambda: self._rate_card(1))

        self.btn_hard = QPushButton(t("hard", settings.get("ui_language", "tr")))
        self.btn_hard.setObjectName("btnHard")
        self.btn_hard.setMinimumWidth(140)
        self.btn_hard.setFixedHeight(46)
        self.btn_hard.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_hard.setStyleSheet("""
            QPushButton#btnHard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #b45309);
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                border-radius: 14px;
                border: none;
            }
            QPushButton#btnHard:hover {
                background: #92400e;
            }
        """)
        self.btn_hard.clicked.connect(lambda: self._rate_card(2))

        self.btn_easy = QPushButton(t("easy", settings.get("ui_language", "tr")))
        self.btn_easy.setObjectName("btnEasy")
        self.btn_easy.setMinimumWidth(160)
        self.btn_easy.setFixedHeight(46)
        self.btn_easy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_easy.setStyleSheet("""
            QPushButton#btnEasy {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                border-radius: 14px;
                border: none;
            }
            QPushButton#btnEasy:hover {
                background: #047857;
            }
        """)
        self.btn_easy.clicked.connect(lambda: self._rate_card(3))

        rating_layout.addWidget(self.btn_repeat)
        rating_layout.addWidget(self.btn_hard)
        rating_layout.addWidget(self.btn_easy)

        actions_layout.addWidget(self.rating_widget)
        self.rating_widget.setVisible(False)

        study_layout.addWidget(self.actions_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Alt Kısayol Bilgilendirme Rozeti
        shortcuts_bar = QHBoxLayout()
        shortcuts_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_shortcuts = QLabel(
            ui_text('[Space] Flip • [1] Again • [2] Hard • [3] Easy • [S] Pronunciation • [C] Sentence • [F] Favorite • [R] Reverse • [W] Typing', self.lang)
        )
        self.lbl_shortcuts.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 8px; font-weight: 600; background: transparent;")
        shortcuts_bar.addWidget(self.lbl_shortcuts)
        study_layout.addLayout(shortcuts_bar)

        self.stack.addWidget(self.page_study)

        # Sayfa 1: Oturum Tamamlandı Tebrik Ekranı (Zengin İstatistikler)
        self.page_completed = QWidget()
        comp_layout = QVBoxLayout(self.page_completed)
        comp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_layout.setSpacing(14)

        lbl_party = QLabel()
        lbl_party.setPixmap(get_icon("study", 58).pixmap(58, 58))
        lbl_party.setStyleSheet("background: transparent;")
        lbl_party.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_layout.addWidget(lbl_party)

        self.lbl_congrats = QLabel(t("session_completed", settings.get("ui_language", "tr")))
        self.lbl_congrats.setStyleSheet("font-size: 26px; font-weight: 900; color: #10b981; background: transparent;")
        self.lbl_congrats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_layout.addWidget(self.lbl_congrats)

        # Detaylı İstatistik Kartı
        self.stats_card = QFrame()
        self.stats_card.setMaximumWidth(550)
        self.stats_card.setStyleSheet("""
            QFrame {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        stats_card_lay = QVBoxLayout(self.stats_card)
        stats_card_lay.setSpacing(8)

        self.lbl_session_stats = QLabel("")
        self.lbl_session_stats.setStyleSheet("font-size: 14px; color: #e2e8f0; line-height: 1.5; background: transparent;")
        self.lbl_session_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_card_lay.addWidget(self.lbl_session_stats)

        comp_layout.addWidget(self.stats_card, alignment=Qt.AlignmentFlag.AlignCenter)

        comp_btns = QHBoxLayout()
        comp_btns.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_btns.setSpacing(12)

        self.btn_comp_retry_mistakes = QPushButton(ui_text('⚠️ Review Mistakes Now', self.lang))
        self.btn_comp_retry_mistakes.setFixedHeight(44)
        self.btn_comp_retry_mistakes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_comp_retry_mistakes.setStyleSheet("""
            QPushButton {
                background: #b91c1c;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 12px;
                padding: 0 16px;
                border: none;
            }
            QPushButton:hover {
                background: #991b1b;
            }
        """)
        self.btn_comp_retry_mistakes.clicked.connect(self._retry_session_mistakes)
        self.btn_comp_retry_mistakes.setVisible(False)
        comp_btns.addWidget(self.btn_comp_retry_mistakes)

        self.btn_comp_restart = QPushButton(t("restart_session", settings.get("ui_language", "tr")))
        self.btn_comp_restart.setProperty("class", "btn-secondary")
        self.btn_comp_restart.setFixedHeight(44)
        self.btn_comp_restart.clicked.connect(lambda: self.reload_session(practice_mode=False))
        comp_btns.addWidget(self.btn_comp_restart)

        self.btn_comp_practice = QPushButton(t("practice_mode", settings.get("ui_language", "tr")))
        self.btn_comp_practice.setProperty("class", "btn-secondary")
        self.btn_comp_practice.setFixedHeight(44)
        self.btn_comp_practice.clicked.connect(lambda: self.reload_session(practice_mode=True))
        comp_btns.addWidget(self.btn_comp_practice)

        self.btn_comp_new_card = QPushButton(t("new_card", settings.get("ui_language", "tr")))
        self.btn_comp_new_card.setProperty("class", "btn-primary")
        self.btn_comp_new_card.setFixedHeight(44)
        self.btn_comp_new_card.clicked.connect(lambda: self.request_add_card.emit())
        comp_btns.addWidget(self.btn_comp_new_card)

        comp_layout.addLayout(comp_btns)
        self.stack.addWidget(self.page_completed)

        # Sayfa 2: Çalışılacak Kart Yok Ekranı
        self.page_empty = QWidget()
        empty_layout = QVBoxLayout(self.page_empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(14)

        lbl_empty_icon = QLabel()
        lbl_empty_icon.setPixmap(get_icon("library", 56).pixmap(56, 56))
        lbl_empty_icon.setStyleSheet("background: transparent;")
        lbl_empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(lbl_empty_icon)

        self.lbl_empty_title = QLabel(t("no_reviews_today", settings.get("ui_language", "tr")))
        self.lbl_empty_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; background: transparent;")
        self.lbl_empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.lbl_empty_title)

        self.lbl_empty_desc = QLabel(t("no_reviews_desc", settings.get("ui_language", "tr")))
        self.lbl_empty_desc.setStyleSheet("font-size: 14px; color: #94a3b8; text-align: center; background: transparent;")
        self.lbl_empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.lbl_empty_desc)

        empty_btns = QHBoxLayout()
        empty_btns.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_btns.setSpacing(14)

        self.btn_empty_practice = QPushButton(t("practice_mode", settings.get("ui_language", "tr")))
        self.btn_empty_practice.setProperty("class", "btn-secondary")
        self.btn_empty_practice.setFixedHeight(42)
        self.btn_empty_practice.clicked.connect(lambda: self.reload_session(practice_mode=True))

        self.btn_empty_add = QPushButton(t("new_card", settings.get("ui_language", "tr")))
        self.btn_empty_add.setProperty("class", "btn-primary")
        self.btn_empty_add.setFixedHeight(42)
        self.btn_empty_add.clicked.connect(lambda: self.request_add_card.emit())

        empty_btns.addWidget(self.btn_empty_practice)
        empty_btns.addWidget(self.btn_empty_add)
        empty_layout.addLayout(empty_btns)

        self.stack.addWidget(self.page_empty)

        main_layout.addWidget(self.stack)

    def _quick_action_style(self, highlight_color="#38bdf8"):
        return f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
                color: {highlight_color};
                border-color: {highlight_color};
            }}
        """

    def _setup_shortcuts(self):
        # Boşluk: Çevir
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._flip_current_card)
        # 1 veya Sol Ok: Tekrar Et
        QShortcut(QKeySequence(Qt.Key.Key_1), self, activated=lambda: self._on_rating_shortcut(1))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self._on_rating_shortcut(1))
        # 2: Zor
        QShortcut(QKeySequence(Qt.Key.Key_2), self, activated=lambda: self._on_rating_shortcut(2))
        # 3 veya Sağ Ok: Kolay / Biliyorum
        QShortcut(QKeySequence(Qt.Key.Key_3), self, activated=lambda: self._on_rating_shortcut(3))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self._on_rating_shortcut(3))
        # S: Kelime Telaffuzu Dinle
        QShortcut(QKeySequence(Qt.Key.Key_S), self, activated=self._play_current_sound)
        # C: Örnek Cümleyi Dinle
        QShortcut(QKeySequence(Qt.Key.Key_C), self, activated=self._play_sentence_sound)
        # F: Yıldızla / Favori
        QShortcut(QKeySequence(Qt.Key.Key_F), self, activated=self._toggle_card_favorite)
        # R: Ters Çalışma Yönünü Değiştir
        QShortcut(QKeySequence(Qt.Key.Key_R), self, activated=self._toggle_reverse_mode)
        # W: Yazarak Çalışma Modu
        QShortcut(QKeySequence(Qt.Key.Key_W), self, activated=self._toggle_type_in)
        # E: Düzenle
        QShortcut(QKeySequence(Qt.Key.Key_E), self, activated=self._edit_current_card)

    def _toggle_reverse_mode(self):
        self.reverse_mode = not self.reverse_mode
        self.btn_toggle_reverse.setChecked(self.reverse_mode)
        if self.reverse_mode:
            self.btn_toggle_reverse.setText(ui_text('🔄 Dir: Meaning ➔ Term', self.lang))
        else:
            self.btn_toggle_reverse.setText(ui_text('🔄 Dir: Term ➔ Meaning', self.lang))
        self.card_widget.set_reverse_mode(self.reverse_mode)
        sfx.play_click()

    def _toggle_type_in(self):
        self.type_in_enabled = not self.type_in_enabled
        self.btn_toggle_type_in.setChecked(self.type_in_enabled)
        self.card_widget.set_type_in_enabled(self.type_in_enabled)
        sfx.play_click()

    def _toggle_card_favorite(self):
        self.card_widget.toggle_favorite()

    def _play_sentence_sound(self):
        self.card_widget.play_sentence_audio()

    def _on_card_favorite_toggled(self, card_id: int, is_fav: bool):
        pass

    def _on_active_recall_tested(self, is_correct: bool):
        pass

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_lang_filter_list()
        self._prefetch_audio()

    def _prefetch_audio(self):
        if self.isVisible():
            for upcoming in self.cards_queue[:3]:
                audio_player.prefetch(upcoming.get('term', ''), detect_card_term_language(upcoming))

    def _refresh_mode_selector(self, lang=None):
        """Çalışma modu seçeneklerini günceller."""
        active_lang = lang or getattr(self, "lang", settings.get("ui_language", "tr"))
        current_data = getattr(self, "selected_study_mode", "smart")
        self.mode_selector.blockSignals(True)
        self.mode_selector.clear()

        modes = [
            ("smart", ui_text('🧠 Smart Review (Error Priority)', active_lang)),
            ("mistakes", ui_text('⚠️ Mistakes & Hard Cards', active_lang)),
            ("favorites", ui_text('⭐ Starred & Favorite Cards', active_lang)),
            ("all", ui_text('📚 All Cards (Free Mode)', active_lang))
        ]

        idx_to_select = 0
        for i, (m_key, m_label) in enumerate(modes):
            self.mode_selector.addItem(m_label, m_key)
            if current_data == m_key:
                idx_to_select = i

        self.mode_selector.setCurrentIndex(idx_to_select)
        self.selected_study_mode = self.mode_selector.currentData() or "smart"
        self.mode_selector.blockSignals(False)

    def _on_study_mode_changed(self, index):
        self.selected_study_mode = self.mode_selector.currentData() or "smart"
        self.reload_session()

    def refresh_decks_list(self, lang=None):
        """Deste listesini yeniler."""
        active_lang = lang or getattr(self, "lang", settings.get("ui_language", "tr"))
        current_data = self.deck_selector.currentData()
        self.deck_selector.blockSignals(True)
        self.deck_selector.clear()
        self.deck_selector.addItem(t("deck_selector_all", active_lang), None)

        decks = get_all_decks()
        idx_to_select = 0
        for i, d in enumerate(decks):
            due_label = t("deck_reps", active_lang, count=d.get('due_cards', 0))
            self.deck_selector.addItem(f"{d['name']} ({due_label})", d["id"])
            if current_data == d["id"]:
                idx_to_select = i + 1

        self.deck_selector.setCurrentIndex(idx_to_select)
        self.deck_selector.blockSignals(False)
        self.refresh_lang_filter_list(lang=active_lang)

    def refresh_lang_filter_list(self, lang=None):
        """Kayıtlı farklı hedef dilleri combobox'a yükler."""
        active_lang = lang or getattr(self, "lang", settings.get("ui_language", "tr"))
        current_data = self.lang_filter_selector.currentData()
        self.lang_filter_selector.blockSignals(True)
        self.lang_filter_selector.clear()

        all_label = ui_text('Meaning Language: All', active_lang)
        self.lang_filter_selector.addItem(all_label, None)

        langs = get_distinct_target_languages()
        idx_to_select = 0
        for i, l in enumerate(langs):
            self.lang_filter_selector.addItem(l, l)
            if current_data == l:
                idx_to_select = i + 1

        self.lang_filter_selector.setCurrentIndex(idx_to_select)
        self.selected_target_lang = self.lang_filter_selector.currentData()
        self.lang_filter_selector.blockSignals(False)

    def _on_lang_filter_changed(self, index):
        self.selected_target_lang = self.lang_filter_selector.currentData()
        self.reload_session()

    def _on_deck_changed(self, index):
        self.selected_deck_id = self.deck_selector.currentData()
        self.reload_session()

    def reload_session(self, specific_deck_id=None, practice_mode: bool = False, custom_cards=None, allow_autoplay: bool = True):
        self._session_initialized = True
        if specific_deck_id is not None:
            self.selected_deck_id = specific_deck_id
            for i in range(self.deck_selector.count()):
                if self.deck_selector.itemData(i) == specific_deck_id:
                    self.deck_selector.blockSignals(True)
                    self.deck_selector.setCurrentIndex(i)
                    self.deck_selector.blockSignals(False)
                    break

        if custom_cards is not None:
            cards = custom_cards
        else:
            cards = get_study_cards(
                self.selected_deck_id,
                limit=settings.get('session_size', 50),
                practice_mode=practice_mode,
                target_lang=self.selected_target_lang,
                study_mode=getattr(self, "selected_study_mode", "smart")
            )

        self.cards_queue = list(cards)
        if settings.get('shuffle_cards', True):
            random.shuffle(self.cards_queue)

        self.repeat_queue = []
        self.session_failed_cards = []
        self.current_card_index = 0
        self.session_total_count = len(cards)
        self.known_count = 0
        self.again_count = 0

        if not self.cards_queue:
            self.stack.setCurrentWidget(self.page_empty)
            self.lbl_counter.setText("0 / 0")
            self.progress_bar.setValue(0)
            return

        self.stack.setCurrentWidget(self.page_study)
        self._show_current_card(allow_autoplay=allow_autoplay)

    def _show_current_card(self, allow_autoplay: bool = True):
        if not self.cards_queue:
            if self.repeat_queue:
                self.cards_queue = list(self.repeat_queue)
                random.shuffle(self.cards_queue)
                self.repeat_queue = []
            else:
                self._show_completion_screen()
                return

        card = self.cards_queue[0]
        self.card_widget.set_card(card, allow_autoplay=allow_autoplay)
        self._prefetch_audio()
        self.btn_flip.setVisible(True)
        self.rating_widget.setVisible(False)

        # Aralıklı tekrar süre ipuçları
        calc_days = calculate_review_interval(card, 3)
        hard_days = calculate_review_interval(card, 2)

        active_lang = getattr(self, "lang", settings.get("ui_language", "tr"))
        rep_t = t("repeat", active_lang)
        hard_t = t("hard", active_lang)
        easy_t = t("easy", active_lang)

        min_txt = ui_text('< 1m', active_lang)
        day_txt = ui_text('{calc_days}d', active_lang, **{'calc_days': hard_days})
        days_txt = ui_text('{calc_days}d', active_lang, **{'calc_days': calc_days})

        self.btn_repeat.setText(f"{rep_t} ({min_txt})")
        self.btn_hard.setText(f"{hard_t} ({day_txt})")
        self.btn_easy.setText(f"{easy_t} ({days_txt})")

        current_num = self.session_total_count - len(self.cards_queue) - len(self.repeat_queue) + 1
        current_num = max(1, min(current_num, self.session_total_count))
        self.lbl_counter.setText(f"{current_num} / {self.session_total_count}")

        if self.session_total_count > 0:
            target_pct = int((current_num / self.session_total_count) * 100)
            self.anim_prog = QPropertyAnimation(self.progress_bar, b"value")
            self.anim_prog.setDuration(220)
            self.anim_prog.setStartValue(self.progress_bar.value())
            self.anim_prog.setEndValue(target_pct)
            self.anim_prog.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.anim_prog.start()

    def _flip_current_card(self):
        if self.stack.currentWidget() == self.page_study:
            self.card_widget.flip(animated=True)

    def _on_card_flipped(self, is_back: bool):
        self.btn_flip.setVisible(not is_back)
        self.rating_widget.setVisible(is_back)

    def _on_rating_shortcut(self, rating: int):
        if self.stack.currentWidget() != self.page_study:
            return
        if not self.card_widget.is_back_showing():
            self.card_widget.flip(animated=True)
            return
        self._rate_card(rating)

    def _rate_card(self, rating: int):
        if not self.cards_queue or self._is_transitioning:
            return

        self._is_transitioning = True
        current_card = self.cards_queue.pop(0)
        card_id = current_card["id"]

        record_study_result(card_id, rating)

        # Derecelendirme ve SRS Kaydı
        if rating == 1:
            self.again_count += 1
            sfx.play_wrong()

            # Hata yapılanı 3 adım sonrasına ve oturum sonuna tekrar ekle
            reinsert_idx = min(3, len(self.cards_queue))
            self.cards_queue.insert(reinsert_idx, current_card)
            if current_card not in self.repeat_queue:
                self.repeat_queue.append(current_card)
            if current_card not in self.session_failed_cards:
                self.session_failed_cards.append(current_card)

        elif rating == 2:
            self.known_count += 1
            sfx.play_click()

            if len(self.cards_queue) >= 3:
                reinsert_idx = min(6, len(self.cards_queue))
                self.cards_queue.insert(reinsert_idx, current_card)

        else:
            self.known_count += 1
            sfx.play_correct()

        # Kart geçiş animasyonu (Fade out -> In)
        if settings.get('reduced_motion', False):
            self._is_transitioning = False
            self._show_current_card()
            return
        self.opacity_effect = QGraphicsOpacityEffect(self.card_widget)
        self.card_widget.setGraphicsEffect(self.opacity_effect)
        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(110)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.1)
        self.anim_fade.setEasingCurve(QEasingCurve.Type.InQuad)

        def on_fade_done():
            self._show_current_card()
            self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim_in.setDuration(130)
            self.anim_in.setStartValue(0.1)
            self.anim_in.setEndValue(1.0)
            self.anim_in.setEasingCurve(QEasingCurve.Type.OutQuad)

            def on_in_done():
                self.card_widget.setGraphicsEffect(None)
                self._is_transitioning = False

            self.anim_in.finished.connect(on_in_done)
            self.anim_in.start()

        self.anim_fade.finished.connect(on_fade_done)
        self.anim_fade.start()

    def _play_current_sound(self):
        if self.stack.currentWidget() == self.page_study and self.card_widget._card_data:
            self.card_widget._play_audio()

    def _edit_current_card(self):
        if self.stack.currentWidget() == self.page_study and self.card_widget._card_data:
            self.request_edit_card.emit(self.card_widget._card_data["id"])

    def _show_completion_screen(self):
        sfx.play_complete()
        self.stack.setCurrentWidget(self.page_completed)
        self.progress_bar.setValue(100)
        self.lbl_counter.setText("100%")

        total_done = max(1, self.known_count + self.again_count)
        acc_pct = int((self.known_count / total_done) * 100)

        lang = getattr(self, "lang", settings.get("ui_language", "tr"))
        if lang == "tr":
            stats_html = (
                f"<b>🎯 Başarı Oranı:</b> <span style='color: #10b981; font-weight: 800;'>%{acc_pct}</span><br>"
                f"<b>✅ Hatırlanan:</b> <span style='color: #38bdf8; font-weight: 700;'>{self.known_count} Kart</span><br>"
                f"<b>🔄 Tekrar Edilecek:</b> <span style='color: #f87171; font-weight: 700;'>{self.again_count} Kart</span><br>"
                f"<b>📚 Toplam İncelenen:</b> <span style='color: #e2e8f0; font-weight: 700;'>{self.session_total_count} Kart</span>"
            )
        else:
            stats_html = (
                f"<b>🎯 Accuracy:</b> <span style='color: #10b981; font-weight: 800;'>{acc_pct}%</span><br>"
                f"<b>✅ Known:</b> <span style='color: #38bdf8; font-weight: 700;'>{self.known_count} Cards</span><br>"
                f"<b>🔄 Again:</b> <span style='color: #f87171; font-weight: 700;'>{self.again_count} Cards</span><br>"
                f"<b>📚 Total Cards:</b> <span style='color: #e2e8f0; font-weight: 700;'>{self.session_total_count} Cards</span>"
            )

        self.lbl_session_stats.setText(stats_html)

        # Hata yapılan kartlar varsa "Hataları Hemen Tekrar Et" butonunu göster
        if self.session_failed_cards:
            fail_count = len(self.session_failed_cards)
            txt = ui_text('⚠️ Review Mistakes ({fail_count} Cards)', lang, **{'fail_count': fail_count})
            self.btn_comp_retry_mistakes.setText(txt)
            self.btn_comp_retry_mistakes.setVisible(True)
        else:
            self.btn_comp_retry_mistakes.setVisible(False)

    def _retry_session_mistakes(self):
        """Oturumda yanlış yapılan kartlarla anında odaklanmış tekrar oturumu başlatır."""
        if not self.session_failed_cards:
            return
        cards_to_retry = list(self.session_failed_cards)
        self.reload_session(custom_cards=cards_to_retry)

    def update_language(self, lang: str):
        self.lang = lang
        self._refresh_mode_selector(lang=lang)
        self.refresh_decks_list(lang=lang)
        self.btn_flip.setText(t("flip_card", lang))
        self.btn_repeat.setText(t("repeat", lang))
        self.btn_hard.setText(t("hard", lang))
        self.btn_easy.setText(t("easy", lang))
        self.lbl_shortcuts.setText(
            ui_text('[Space] Flip • [1] Again • [2] Hard • [3] Easy • [S] Pronunciation • [C] Sentence • [F] Favorite • [R] Reverse • [W] Typing', lang)
        )
        self.lbl_congrats.setText(t("session_completed", lang))
        self.btn_comp_restart.setText(t("restart_session", lang))
        self.btn_comp_practice.setText(t("practice_mode", lang))
        self.btn_comp_new_card.setText(t("new_card", lang))
        self.lbl_empty_title.setText(t("no_reviews_today", lang))
        self.lbl_empty_desc.setText(t("no_reviews_desc", lang))
        self.btn_empty_practice.setText(t("practice_mode", lang))
        self.btn_empty_add.setText(t("new_card", lang))
        self.card_widget.update_language(lang)
        localize_tree(self,lang)

    def update_ui_language(self, lang=None):
        self.update_language(lang or settings.get("ui_language", "tr"))
