import time
"""
Study Card - Evrensel Dil Modülü Görünümü (Universal Language Module View)
15 Dünya Dili eklentisinin her biri için ortak, esnek, tamamen duyarlı (responsive)
ve emojilerden arındırılmış zengin kelime tablosu ve pratik testi ekranı.
"""

import json
import os
import random
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedWidget, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor, QColor

from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.ui_localization import ui_text
from duocards.sentence_memory import term_pattern
from duocards.icons import get_icon
from duocards.i18n import t
from duocards.widgets.quiz_keyboard import QuizKeyboard, keyboard_help, keyboard_text
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit


class QuizChoiceButton(QPushButton):
    """
    Kenarlıksız, duyarlı ve metinleri hiçbir dilde kesmeyen quiz şık butonu.
    İçerideki QLabel ile otomatik kelime kaydırma (WordWrap) ve dinamik yazı boyutu sağlar.
    """
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(0)
        self.lbl_text = QLabel(text)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_text.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(self.lbl_text)

        self.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #10b981;
                border: none;
            }
        """)
        self.set_state_style("normal")

    def set_choice_text(self, text: str):
        self.lbl_text.setText(text)
        self.setToolTip(text)
        if len(text) > 35:
            self.lbl_text.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        elif len(text) > 22:
            self.lbl_text.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 700; background: transparent; border: none;")
        else:
            self.lbl_text.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700; background: transparent; border: none;")

    def choice_text(self) -> str:
        return self.lbl_text.text()

    def setText(self, text: str):
        self.set_choice_text(text)

    def text(self) -> str:
        return self.lbl_text.text()

    def set_state_style(self, state: str):
        if state == "correct":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    border: none;
                    border-radius: 10px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800; background: transparent; border: none;")
        elif state == "wrong":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    border: none;
                    border-radius: 10px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800; background: transparent; border: none;")
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #10b981;
                    border: none;
                }
            """)
        self.setStyleSheet(self.styleSheet() + '\nQPushButton:focus { border: 2px solid #ffffff; }')


class UniversalLanguageModuleView(QWidget):
    """
    15 Dünya Dili için standartlaştırılmış, ekran boyutuna göre otomatik uyum sağlayan,
    kesilme/taşma yapmayan ve arayüz diline göre dinamik çeviri sunan modül görünümü.
    """

    def __init__(self, module_id: str, title: str, lang_code: str, dataset_file: str,
                 term_col_name: str = "Kelime",
                 attr_col_name: str = "Çekim / Artikel",
                 extra_col_name: str = "Ek Bilgi / Çoğul",
                 filter_options: Optional[List[str]] = None,
                 titles: Optional[Dict[str, str]] = None,
                 parent=None,
                 column_titles: Optional[Dict[str, List[str]]] = None):
        super().__init__(parent)
        self.module_id = module_id
        self.titles = titles or {"tr": title, "en": title}
        self.module_title = self.titles.get(settings.get("ui_language", "tr"), title)
        self.lang_code = lang_code
        self.dataset_file = dataset_file
        self.term_col_name = term_col_name
        self.attr_col_name = attr_col_name
        self.extra_col_name = extra_col_name
        self.column_titles = column_titles or {}
        self.filter_options = filter_options or []

        self.ui_lang = settings.get("ui_language", "tr")
        self.items: List[Dict[str, Any]] = []
        self._quiz_score = 0
        self._quiz_streak = 0
        self._current_quiz: Optional[Dict[str, Any]] = None
        self._current_filter: Optional[str] = None
        self._table_loaded = False
        self._visible_items: List[Dict[str, Any]] = []
        self._quiz_locked = False

        self._load_dataset()
        self._set_column_titles(self.ui_lang)
        self._setup_ui()
        self._keyboard = QuizKeyboard(
            self, buttons=lambda: self.btn_choices,
            typing=self.input_typed_answer, submit=self._on_submit_typed_answer,
            next_button=self.btn_next_question, listen=self._play_quiz_audio,
            restart=self._restart_keyboard_quiz,
            active=lambda: self.stack.currentIndex() == 1)
        self._update_keyboard_labels()

    def _load_dataset(self):
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", self.dataset_file
        )
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
            except Exception as e:
                print(f"Error loading dataset {self.dataset_file}: {e}")
                self.items = []
        else:
            print(f"Dataset file not found: {data_path}")
            self.items = []

    def _set_column_titles(self, lang: str):
        names = self.column_titles.get(lang, self.column_titles.get("en"))
        if not names:
            names = [ui_text(name,lang) for name in (self.term_col_name,self.attr_col_name,self.extra_col_name)]
        if names:
            self.term_col_name, self.attr_col_name, self.extra_col_name = names

    def _search_placeholder(self, lang: str) -> str:
        count = len(self.items)
        return {
            "tr": f"Kelime, ipucu veya anlam ara... ({count} kayıt)",
            "en": f"Search term, tip or meaning... ({count} entries)",
            "de": f"Wort, Hinweis oder Bedeutung suchen... ({count} Einträge)",
            "es": f"Buscar palabra, pista o significado... ({count} entradas)",
        }.get(lang, f"Search... ({count})")

    @staticmethod
    def _get_translation_for(item, lang):
        translations=item.get('translations',{})
        return translations.get(lang,translations.get('en',translations.get('tr',item.get('term',''))))

    def _get_translation(self, item: Dict[str, Any]) -> str:
        translations = item.get("translations", {})
        if self.ui_lang in translations:
            return translations[self.ui_lang]
        if "en" in translations:
            return translations["en"]
        if "tr" in translations:
            return translations["tr"]
        return item.get("meaning", "-")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # 1. Üst Başlık ve Sekmeler (Table vs Quiz)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        # Dil Kodu Rozeti (Örn: [DE], [FR], [ES] - Temiz, emojisz, çizgisiz)
        lbl_badge = QLabel(self.lang_code.upper())
        lbl_badge.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #10b981;
            font-size: 13px;
            font-weight: 900;
            border-radius: 8px;
            padding: 4px 10px;
            border: none;
        """)
        lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(lbl_badge)

        self.lbl_title = QLabel(self.module_title)
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()

        self.btn_tab_table = QPushButton(ui_text('Word Table', self.ui_lang))
        self.btn_tab_table.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_table.setFixedHeight(36)
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_table.clicked.connect(self._show_table)

        self.btn_tab_quiz = QPushButton(ui_text('Practice Quiz', self.ui_lang))
        self.btn_tab_quiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_quiz.setFixedHeight(36)
        self.btn_tab_quiz.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_quiz.clicked.connect(self._show_quiz)

        header_row.addWidget(self.btn_tab_table)
        header_row.addWidget(self.btn_tab_quiz)
        main_layout.addLayout(header_row)

        # 2. İçerik Alanı (Stacked Widget)
        self.stack = QStackedWidget()

        # Sayfa 1: Tablo Sayfası
        table_page = QWidget()
        t_layout = QVBoxLayout(table_page)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(10)

        # Arama ve Filtre Satırı
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(self._search_placeholder(self.ui_lang))
        self.input_search.setFixedHeight(38)
        self.input_search.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.input_search, 1)

        # Kategori Filtre Butonları (Örn: Der, Die, Das / De, Het / Tümü)
        if self.filter_options:
            self.filter_buttons = []
            btn_all = QPushButton(ui_text('All', self.ui_lang))
            btn_all.setFixedHeight(38)
            btn_all.setStyleSheet("background-color: #10b981; color: #ffffff; font-weight: 800; border-radius: 8px; padding: 0 14px; border: none;")
            btn_all.clicked.connect(lambda: self._set_filter(None))
            filter_bar.addWidget(btn_all)
            self.filter_buttons.append((None, btn_all))

            for opt in self.filter_options:
                btn_opt = QPushButton(opt.capitalize())
                btn_opt.setFixedHeight(38)
                btn_opt.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-weight: 700; border-radius: 8px; padding: 0 14px; border: 1px solid rgba(255, 255, 255, 0.08);")
                btn_opt.clicked.connect(lambda ch, o=opt: self._set_filter(o))
                filter_bar.addWidget(btn_opt)
                self.filter_buttons.append((opt, btn_opt))

        t_layout.addLayout(filter_bar)

        # Kelime Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        meaning_header = ui_text('Meaning', self.ui_lang)
        audio_header = ui_text('Audio', self.ui_lang)
        self.table.setHorizontalHeaderLabels([
            self.term_col_name, self.attr_col_name, self.extra_col_name, meaning_header, audio_header
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(4, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        t_layout.addWidget(self.table)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        # Alt Sayaç
        self.lbl_table_count = QLabel("")
        self.lbl_table_count.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        t_layout.addWidget(self.lbl_table_count)

        self.stack.addWidget(table_page)

        # Sayfa 2: Pratik Quiz Sayfası (KAYDIRILABİLİR, EKRANA SIĞAN, KESİLMEYEN)
        quiz_scroll = QScrollArea()
        quiz_scroll.setWidgetResizable(True)
        quiz_scroll.setFrameShape(QFrame.Shape.NoFrame)
        quiz_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        quiz_container = QWidget()
        quiz_container.setStyleSheet("background: transparent;")
        q_layout = QVBoxLayout(quiz_container)
        q_layout.setContentsMargins(10, 10, 10, 20)
        q_layout.setSpacing(16)
        q_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Skor & Seri Kartı (Çizgisiz, sade ve minimalist)
        s_box = QFrame()
        s_box.setStyleSheet("background-color: #111827; border-radius: 10px; border: none; padding: 6px 20px;")
        sb_lay = QHBoxLayout(s_box)
        sb_lay.setSpacing(24)

        score_text = ui_text('Correct: 0', self.ui_lang)
        streak_text = ui_text('Streak: 0', self.ui_lang)

        self.lbl_score = QLabel(score_text)
        self.lbl_score.setStyleSheet("color: #10b981; font-weight: 800; font-size: 14px; background: transparent;")
        self.lbl_streak = QLabel(streak_text)
        self.lbl_streak.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 14px; background: transparent;")
        sb_lay.addWidget(self.lbl_score)
        sb_lay.addWidget(self.lbl_streak)
        q_layout.addWidget(s_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Soru Kartı (Enlemesine genişletilmiş diktörtgen, çizgisiz/kenarlıksız)
        self.q_card = QFrame()
        self.q_card.setMinimumWidth(740)
        self.q_card.setMaximumWidth(1020)
        self.q_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.q_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: none;
                border-radius: 16px;
                padding: 14px 28px;
            }
        """)
        qc_lay = QVBoxLayout(self.q_card)
        qc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_lay.setSpacing(6)

        self.lbl_q_hint = QLabel(ui_text('What is the meaning or correct form of this word?', self.ui_lang))
        self.lbl_q_hint.setWordWrap(True)
        self.lbl_q_hint.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600; background: transparent;")
        self.lbl_q_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Kelime ve Dinleme Butonu Satırı (Kelimeden hemen sonra, aralık sıkı ve ortalı)
        term_row = QHBoxLayout()
        term_row.setSpacing(8)
        term_row.setContentsMargins(0, 0, 0, 0)
        term_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        term_row.addStretch()

        self.lbl_q_term = QLabel("")
        self.lbl_q_term.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.lbl_q_term.setStyleSheet("color: #38bdf8; font-size: 28px; font-weight: 900; background: transparent;")
        self.lbl_q_term.setAlignment(Qt.AlignmentFlag.AlignCenter)
        term_row.addWidget(self.lbl_q_term)

        self.btn_q_audio = QPushButton()
        self.btn_q_audio.setIcon(get_icon("audio", 24, "#10b981"))
        self.btn_q_audio.setIconSize(QSize(24, 24))
        self.btn_q_audio.setToolTip(ui_text('Listen to pronunciation', self.ui_lang))
        self.btn_q_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_q_audio.setFixedSize(36, 36)
        self.btn_q_audio.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.15);
            }
        """)
        self.btn_q_audio.clicked.connect(self._play_quiz_audio)
        term_row.addWidget(self.btn_q_audio)
        term_row.addStretch()

        self.lbl_q_sub = QLabel("")
        self.lbl_q_sub.setWordWrap(True)
        self.lbl_q_sub.setStyleSheet("color: #cbd5e1; font-size: 14px; font-style: italic; background: transparent;")
        self.lbl_q_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_q_feedback = QLabel("")
        self.lbl_q_feedback.setWordWrap(True)
        self.lbl_q_feedback.setStyleSheet("font-size: 14px; font-weight: 800; background: transparent;")
        self.lbl_q_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qc_lay.addWidget(self.lbl_q_hint)
        qc_lay.addLayout(term_row)
        qc_lay.addWidget(self.lbl_q_sub)
        qc_lay.addWidget(self.lbl_q_feedback)
        self.lbl_keyboard_help = QLabel()
        self.lbl_keyboard_help.setWordWrap(True)
        self.lbl_keyboard_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_keyboard_help.setStyleSheet('color:#94a3b8; font-size:12px; background:transparent; border:none;')
        qc_lay.addWidget(self.lbl_keyboard_help)
        q_layout.addWidget(self.q_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Şıklar (Tek Satırda 4 Şık, Çizgisiz, Kesilmeyen Geniş Kutucuklar)
        self.choices_container = QWidget()
        self.choices_container.setMinimumWidth(740)
        self.choices_container.setMaximumWidth(1020)
        self.choices_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        c_row = QHBoxLayout(self.choices_container)
        c_row.setSpacing(10)
        c_row.setContentsMargins(0, 0, 0, 0)

        self.btn_choices = []
        for i in range(4):
            btn = QuizChoiceButton()
            btn.clicked.connect(lambda ch, idx=i: self._on_quiz_answer(idx))
            self.btn_choices.append(btn)
            c_row.addWidget(btn, 1)

        q_layout.addWidget(self.choices_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Klavye İle Cevap Yazma Alanı (V1, V2, V3 soruları için)
        self.typing_container = QWidget()
        self.typing_container.setMinimumWidth(640)
        self.typing_container.setMaximumWidth(820)
        self.typing_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        t_box = QVBoxLayout(self.typing_container)
        t_box.setContentsMargins(0, 0, 0, 0)
        t_box.setSpacing(8)

        t_row = QHBoxLayout()
        t_row.setSpacing(10)

        self.input_typed_answer = QLineEdit()
        self.input_typed_answer.setFixedHeight(48)
        self.input_typed_answer.setStyleSheet("""
            QLineEdit {
                background-color: #0d1527;
                border: 2px solid #283548;
                border-radius: 12px;
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
                padding: 0 16px;
            }
            QLineEdit:focus {
                border-color: #10b981;
                background-color: #0f1d32;
            }
        """)
        self.input_typed_answer.returnPressed.connect(self._on_submit_typed_answer)

        self.btn_submit_typed = QPushButton(ui_text('Check', self.ui_lang))
        self.btn_submit_typed.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_submit_typed.setFixedHeight(48)
        self.btn_submit_typed.setFixedWidth(130)
        self.btn_submit_typed.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.btn_submit_typed.clicked.connect(self._on_submit_typed_answer)

        t_row.addWidget(self.input_typed_answer, 1)
        t_row.addWidget(self.btn_submit_typed)
        t_box.addLayout(t_row)

        self.lbl_typing_hint = QLabel(ui_text('Type your answer with keyboard and press Enter', self.ui_lang))
        self.lbl_typing_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_typing_hint.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600; background: transparent;")
        t_box.addWidget(self.lbl_typing_hint)

        self.typing_container.setVisible(False)
        q_layout.addWidget(self.typing_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sonraki Soru Butonu (Temiz metin, emojisz, çizgisiz, Enter ile geçiş destekli)
        self.btn_next_question = QPushButton(ui_text('Next Question', self.ui_lang))
        self.btn_next_question.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_question.setMinimumWidth(280)
        self.btn_next_question.setFixedHeight(36)
        self.btn_next_question.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0369a1;
                border: none;
            }
        """)
        self.btn_next_question.clicked.connect(self._next_quiz)
        self.btn_next_question.setVisible(False)
        q_layout.addWidget(self.btn_next_question, alignment=Qt.AlignmentFlag.AlignCenter)

        quiz_scroll.setWidget(quiz_container)
        self.stack.addWidget(quiz_scroll)

        main_layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._table_loaded and self.stack.currentIndex() == 0:
            self._filter_table()
        QTimer.singleShot(0, self._keyboard.focus_answer)

    def _update_keyboard_labels(self):
        self.btn_submit_typed.setText(keyboard_text('check', self.ui_lang) + ' (Enter)')
        self.btn_next_question.setText(keyboard_text('next_button', self.ui_lang)
                                      + ' (Enter / ' + keyboard_text('space', self.ui_lang) + ')')
        self.btn_q_audio.setToolTip(keyboard_text('listen', self.ui_lang))
        if self._quiz_locked:
            state = 'next' if self.btn_next_question.isEnabled() else 'waiting'
        else:
            state = 'typing' if getattr(self, '_is_typing_mode', False) else 'choices'
        self.lbl_keyboard_help.setText(keyboard_help(self.ui_lang, state, choices=len(getattr(self,"_choices_data",[])) or 4))

    def _restart_keyboard_quiz(self):
        self._feedback_until = 0
        self._quiz_score = self._quiz_streak = 0
        self.update_language(self.ui_lang)
        self._next_quiz()

    def _show_table(self):
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_quiz.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.stack.setCurrentIndex(0)
        if not self._table_loaded:
            self._filter_table()

    def _get_audio_text(self, item: Dict[str, Any]) -> str:
        if not item:
            return ""
        term = str(item.get("term", "")).strip()
        attr = str(item.get("attr", "")).strip()
        extra = str(item.get("extra", "")).strip()

        # 1. İngilizce Kuralsız Fiiller (en_verbs): V1, V2, V3 sırasıyla okunur (örn: "eat, ate, eaten")
        if self.module_id == "en_verbs" or (self.lang_code.upper() in ("EN", "GB") and "verb" in self.module_id):
            clean_attr = attr.replace("/", " ").strip()
            clean_extra = extra.replace("/", " ").strip()
            parts = [p for p in [term, clean_attr, clean_extra] if p]
            if len(parts) >= 2:
                return ", ".join(parts)
            return term

        # 2. Artikeller (Almanca, Felemenkçe, İsveççe): Kesinlikle ÖNCE artikel, SONRA kelime söylenir (örn: "der Tisch", "die Katze", "das Haus")
        is_article = (
            self.module_id in ("de_articles", "nl_articles", "sv_articles") or
            "article" in self.module_id or
            attr.lower() in ("der", "die", "das", "de", "het", "en", "ett")
        )
        if is_article and attr:
            if not term.lower().startswith(attr.lower() + " "):
                return f"{attr} {term}".strip()
            return term

        return term

    def _play_item_audio(self, item: Dict[str, Any]):
        audio_text = self._get_audio_text(item)
        if audio_text:
            sfx.play_click()
            audio_player.play_pronunciation(audio_text, lang=self.lang_code.lower())

    def _on_cell_clicked(self, row: int, col: int):
        if 0 <= row < len(self._visible_items):
            # 4. sütundaki Ses butonuna veya kelime/çekim sütunlarına tıklandığında doğru telaffuzu çal
            if col in (0, 1, 2, 4):
                self._play_item_audio(self._visible_items[row])

    def _on_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self._visible_items):
            self._play_item_audio(self._visible_items[row])

    def _play_quiz_audio(self):
        if self._current_quiz:
            term = self.lbl_q_term.text().strip()
            if "(" in term:
                term = term.split("(")[0].strip()
            if "/" in term:
                term = term.split("/")[0].strip()
            if term:
                sfx.play_click()
                audio_player.play_pronunciation(term, lang=self.lang_code.lower())
            else:
                self._play_item_audio(self._current_quiz)

    def _show_quiz(self):
        self.btn_tab_quiz.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_table.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.stack.setCurrentIndex(1)
        if not self._current_quiz:
            self._next_quiz()
        self._keyboard.focus_answer()

    def _set_filter(self, opt: Optional[str]):
        self._current_filter = opt
        if hasattr(self, "filter_buttons"):
            for val, btn in self.filter_buttons:
                if val == opt:
                    btn.setStyleSheet("background-color: #10b981; color: #ffffff; font-weight: 800; border-radius: 8px; padding: 0 14px; border: none;")
                else:
                    btn.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-weight: 700; border-radius: 8px; padding: 0 14px; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._filter_table()

    def _filter_table(self):
        q = self.input_search.text().strip().lower()
        matched = []
        for item in self.items:
            # Filtre seçeneği
            if self._current_filter and item.get("attr", "").lower() != self._current_filter.lower():
                continue

            if not q:
                matched.append(item)
                continue

            term = item.get("term", "").lower()
            attr = item.get("attr", "").lower()
            extra = item.get("extra", "").lower()
            meaning = self._get_translation(item).lower()

            if q in term or q in attr or q in extra or q in meaning:
                matched.append(item)

        self._populate_table(matched)

    def _populate_table(self, item_list: List[Dict[str, Any]]):
        self._visible_items = item_list
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(item_list))
        audio_text = ui_text('Audio', self.ui_lang)
        green_color = QColor("#10b981")
        listen_tip = ui_text('Click to listen', self.ui_lang)

        for row_idx, item in enumerate(item_list):
            term = item.get("term", "")
            attr = item.get("attr", "")
            extra = item.get("extra", "")
            meaning = self._get_translation(item)

            # Col 0: Term
            t_item = QTableWidgetItem(term)
            t_item.setToolTip(term)
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row_idx, 0, t_item)

            # Col 1: Attr (Artikel / Çekim)
            a_item = QTableWidgetItem(attr)
            a_item.setToolTip(attr)
            a_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row_idx, 1, a_item)

            # Col 2: Extra (Çoğul / Seviye)
            e_item = QTableWidgetItem(extra)
            e_item.setToolTip(extra)
            e_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row_idx, 2, e_item)

            # Col 3: Dinamik Anlamı
            m_item = QTableWidgetItem(meaning)
            m_item.setToolTip(meaning)
            m_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row_idx, 3, m_item)

            # Col 4: Sadece Ses Simgesi (Satırlardan "Ses" yazısı silindi)
            s_item = QTableWidgetItem("")
            s_item.setIcon(get_icon("audio", 18, "#10b981"))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            s_item.setToolTip(listen_tip)
            self.table.setItem(row_idx, 4, s_item)

        self.table.setUpdatesEnabled(True)
        self._table_loaded = True
        count_text = ui_text('Total {len(item_list)} items listed', self.ui_lang, **{'len(item_list)': len(item_list)})
        self.lbl_table_count.setText(count_text)

    def _wait_for_feedback(self):
        self._quiz_locked = True
        self._feedback_until = time.monotonic() + .25
        self.btn_next_question.setVisible(True)
        self.btn_next_question.setEnabled(False)
        if not hasattr(self, '_feedback_timer'):
            self._feedback_timer = QTimer(self)
            self._feedback_timer.setSingleShot(True)
            self._feedback_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self._feedback_timer.timeout.connect(self._unlock_feedback)
        self._feedback_timer.start(250)
        self._update_keyboard_labels()
        if self.isVisible():
            self.setFocus()

    def _unlock_feedback(self):
        if self._quiz_locked:
            self.btn_next_question.setEnabled(True)
            self._update_keyboard_labels()
            self._keyboard.focus_answer()

    def _next_quiz(self):
        if time.monotonic() < getattr(self, '_feedback_until', 0):
            return
        if not self.items:
            return

        self._quiz_locked = False
        self._is_typing_mode = False
        if hasattr(self, '_feedback_timer'):
            self._feedback_timer.stop()

        self.btn_next_question.setVisible(False)
        self.lbl_q_feedback.setText("")

        # Rastgele soru seç
        target = random.choice(self.items)
        self._current_quiz = target

        is_irregular_verbs = (
            self.module_id == "en_verbs" or
            ("verb" in self.module_id and self.lang_code.upper() in ("EN", "GB"))
        )

        is_article = (
            self.module_id in ("de_articles", "nl_articles", "sv_articles") or
            "article" in self.module_id or
            target.get("attr", "").lower() in ("der", "die", "das", "de", "het", "en", "ett")
        )

        if self.module_id == 'en_confusing_words':
            self._is_typing_mode=False
            correct_ans=target['term']
            sentence=target['example']
            self.lbl_q_term.setText(term_pattern(correct_ans,'en').sub('____',sentence))
            self.lbl_q_hint.setText(ui_text('Choose the word that fits this sentence.',self.ui_lang))
            self.lbl_q_sub.setText(' / '.join((correct_ans,target['confused_with'])))
            choices=[correct_ans,target['confused_with']]
            random.shuffle(choices)
            self._quiz_correct_answer=correct_ans
            self._choices_data=choices
        elif is_irregular_verbs and target.get("attr") and target.get("extra"):
            # Çeşitli soru modları: V2 nedir, V3 nedir, çekim hangi fiile aittir, anlamı nedir
            modes = ["verb_v2", "verb_v3", "verb_v1", "meaning"]
            mode = random.choice(modes)

            meaning = self._get_translation(target)
            v1 = target["term"].strip()
            v2 = target["attr"].strip()
            v3 = target["extra"].strip()

            if mode == "verb_v2":
                self._is_typing_mode = True
                self.lbl_q_term.setText(v1)
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('Type the V2 (Past Simple) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V2 form and press Enter... (e.g. ate, swam)', self.ui_lang))
                elif self.ui_lang == "de":
                    self.lbl_q_hint.setText(ui_text('Type the V2 (Past Simple) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V2 form and press Enter... (e.g. ate, swam)', self.ui_lang))
                elif self.ui_lang == "es":
                    self.lbl_q_hint.setText(ui_text('Type the V2 (Past Simple) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V2 form and press Enter... (e.g. ate, swam)', self.ui_lang))
                else:
                    self.lbl_q_hint.setText(ui_text('Type the V2 (Past Simple) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V2 form and press Enter... (e.g. ate, swam)', self.ui_lang))
                correct_ans = v2.strip()
                choices = []

            elif mode == "verb_v3":
                self._is_typing_mode = True
                self.lbl_q_term.setText(v1)
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('Type the V3 (Past Participle) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} (V2: {v2}) | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'v2': v2, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V3 form and press Enter... (e.g. eaten, swum)', self.ui_lang))
                elif self.ui_lang == "de":
                    self.lbl_q_hint.setText(ui_text('Type the V3 (Past Participle) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} (V2: {v2}) | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'v2': v2, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V3 form and press Enter... (e.g. eaten, swum)', self.ui_lang))
                elif self.ui_lang == "es":
                    self.lbl_q_hint.setText(ui_text('Type the V3 (Past Participle) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} (V2: {v2}) | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'v2': v2, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V3 form and press Enter... (e.g. eaten, swum)', self.ui_lang))
                else:
                    self.lbl_q_hint.setText(ui_text('Type the V3 (Past Participle) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('V1: {v1} (V2: {v2}) | Meaning: {meaning}', self.ui_lang, **{'v1': v1, 'v2': v2, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type V3 form and press Enter... (e.g. eaten, swum)', self.ui_lang))
                correct_ans = v3.strip()
                choices = []

            elif mode == "verb_v1":
                self._is_typing_mode = True
                prompt_form, form_name = (v2, "V2 (Past Simple)") if random.random() < 0.5 else (v3, "V3 (Past Participle)")
                self.lbl_q_term.setText(prompt_form.split("/")[0].strip())
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('Type the base (V1) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('{form_name} | Meaning: {meaning}', self.ui_lang, **{'form_name': form_name, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type base (V1) form and press Enter... (e.g. eat, swim)', self.ui_lang))
                elif self.ui_lang == "de":
                    self.lbl_q_hint.setText(ui_text('Type the base (V1) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('{form_name} | Meaning: {meaning}', self.ui_lang, **{'form_name': form_name, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type base (V1) form and press Enter... (e.g. eat, swim)', self.ui_lang))
                elif self.ui_lang == "es":
                    self.lbl_q_hint.setText(ui_text('Type the base (V1) form using your keyboard:',self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('{form_name} | Meaning: {meaning}', self.ui_lang, **{'form_name': form_name, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type base (V1) form and press Enter... (e.g. eat, swim)', self.ui_lang))
                else:
                    self.lbl_q_hint.setText(ui_text('Type the base (V1) form using your keyboard:', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('{form_name} | Meaning: {meaning}', self.ui_lang, **{'form_name': form_name, 'meaning': meaning}))
                    self.input_typed_answer.setPlaceholderText(ui_text('Type base (V1) form and press Enter... (e.g. eat, swim)', self.ui_lang))
                correct_ans = v1.strip()
                choices = []

            else:  # mode == "meaning"
                self._is_typing_mode = False
                self.lbl_q_term.setText(v1)
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this verb?',self.ui_lang))
                else:
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this verb?', self.ui_lang))
                self.lbl_q_sub.setText(f"({v2}, {v3})")
                correct_ans = meaning

                wrongs = []
                pool = [x for x in self.items if x["term"] != v1]
                random.shuffle(pool)
                for w in pool:
                    w_tr = self._get_translation(w)
                    if w_tr != correct_ans and w_tr not in wrongs:
                        wrongs.append(w_tr)
                    if len(wrongs) == 3:
                        break

                choices = [correct_ans] + wrongs
                random.shuffle(choices)

            self._quiz_correct_answer = correct_ans
            self._choices_data = choices

        elif is_article:
            # Artikel sorusu veya anlam sorusu
            mode = random.choice(["attr", "meaning"])
            if mode == "attr":
                self.lbl_q_term.setText(target["term"])
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('What is the article of this word?', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('Meaning: {self._get_translation(target)}', self.ui_lang, **{'self._get_translation(target)': self._get_translation(target)}))
                elif self.ui_lang == "de":
                    self.lbl_q_hint.setText(ui_text('What is the article of this word?', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('Meaning: {self._get_translation(target)}', self.ui_lang, **{'self._get_translation(target)': self._get_translation(target)}))
                elif self.ui_lang == "es":
                    self.lbl_q_hint.setText(ui_text('What is the article of this word?', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('Meaning: {self._get_translation(target)}', self.ui_lang, **{'self._get_translation(target)': self._get_translation(target)}))
                else:
                    self.lbl_q_hint.setText(ui_text('What is the article of this word?', self.ui_lang))
                    self.lbl_q_sub.setText(ui_text('Meaning: {self._get_translation(target)}', self.ui_lang, **{'self._get_translation(target)': self._get_translation(target)}))
                correct_ans = target["attr"]

                choices = [correct_ans]
                for opt in (self.filter_options or ["der", "die", "das"]):
                    if opt not in choices and len(choices) < 4:
                        choices.append(opt)
                random.shuffle(choices)
                self._quiz_correct_answer = correct_ans
                self._choices_data = choices
            else:
                self.lbl_q_term.setText(target["term"])
                if self.ui_lang == "tr":
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
                elif self.ui_lang == "de":
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
                elif self.ui_lang == "es":
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
                else:
                    self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
                extra_info = f"({target.get('attr', '')})" if target.get("attr") else ""
                self.lbl_q_sub.setText(extra_info)
                correct_ans = self._get_translation(target)

                wrongs = []
                pool = [x for x in self.items if x["term"] != target["term"]]
                random.shuffle(pool)
                for w in pool:
                    w_tr = self._get_translation(w)
                    if w_tr != correct_ans and w_tr not in wrongs:
                        wrongs.append(w_tr)
                    if len(wrongs) == 3:
                        break

                choices = [correct_ans] + wrongs
                random.shuffle(choices)
                self._quiz_correct_answer = correct_ans
                self._choices_data = choices
        else:
            # Standart kelime anlamı
            self.lbl_q_term.setText(target["term"])
            if self.ui_lang == "tr":
                self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
            elif self.ui_lang == "de":
                self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
            elif self.ui_lang == "es":
                self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
            else:
                self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', self.ui_lang))
            extra_info = f"({target.get('attr', '')})" if target.get("attr") else ""
            self.lbl_q_sub.setText(extra_info)
            correct_ans = self._get_translation(target)

            wrongs = []
            pool = [x for x in self.items if x["term"] != target["term"]]
            random.shuffle(pool)
            for w in pool:
                w_tr = self._get_translation(w)
                if w_tr != correct_ans and w_tr not in wrongs:
                    wrongs.append(w_tr)
                if len(wrongs) == 3:
                    break

            choices = [correct_ans] + wrongs
            random.shuffle(choices)
            self._quiz_correct_answer = correct_ans
            self._choices_data = choices

        if self.isVisible():
            audio_player.prefetch(self._get_audio_text(target),self.lang_code.lower())
        if getattr(self, "_is_typing_mode", False):
            self.choices_container.setVisible(False)
            self.typing_container.setVisible(True)
            self.input_typed_answer.clear()
            self.input_typed_answer.setEnabled(True)
            self.btn_submit_typed.setEnabled(True)
        else:
            self.typing_container.setVisible(False)
            self.choices_container.setVisible(True)
            # Butonları sıfırla ve metinleri yükle
            for idx, btn in enumerate(self.btn_choices):
                if idx < len(choices):
                    btn.set_choice_text(f'{idx + 1}. {choices[idx]}')
                    btn.set_state_style("normal")
                    btn.setEnabled(True)
                    btn.setVisible(True)
                else:
                    btn.setVisible(False)
        self._update_keyboard_labels()
        self._keyboard.focus_answer()

    def _on_submit_typed_answer(self):
        if self._quiz_locked or not self._current_quiz or not getattr(self, "_is_typing_mode", False):
            return

        typed = self.input_typed_answer.text().strip().lower()
        if not typed:
            return

        self.input_typed_answer.setEnabled(False)
        self.btn_submit_typed.setEnabled(False)

        correct = self._quiz_correct_answer.strip()
        # Virgül veya eğik çizgi ile ayrılmış alternatif formları ayıkla (örn: "burnt / burned" veya "dreamt / dreamed")
        valid_answers = [ans.strip().lower() for ans in correct.replace(",", "/").split("/") if ans.strip()]
        valid_answers.append(correct.lower())

        self._play_quiz_audio()

        if typed in valid_answers:
            sfx.play_correct()
            self._quiz_score += 1
            self._quiz_streak += 1
            if self.ui_lang == "tr":
                msg = ui_text('Correct! ({correct})', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "de":
                msg = ui_text('Correct! ({correct})', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "es":
                msg = ui_text('Correct! ({correct})', self.ui_lang, **{'correct':correct})
            else:
                msg = ui_text('Correct! ({correct})', self.ui_lang, **{'correct':correct})
            self.lbl_q_feedback.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 800; background: transparent; border: none;")
            self.lbl_q_feedback.setText(msg)
            self._wait_for_feedback()
        else:
            sfx.play_wrong()
            self._quiz_streak = 0
            if self.ui_lang == "tr":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "de":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "es":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            else:
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            self.lbl_q_feedback.setStyleSheet("color: #ef4444; font-size: 15px; font-weight: 800; background: transparent; border: none;")
            self.lbl_q_feedback.setText(msg)
            self._wait_for_feedback()

        score_lbl = ui_text('Correct', self.ui_lang)
        streak_lbl = ui_text('Streak', self.ui_lang)
        self.lbl_score.setText(f"{score_lbl}: {self._quiz_score}")
        self.lbl_streak.setText(f"{streak_lbl}: {self._quiz_streak}")

    def _on_quiz_answer(self, btn_idx: int):
        if (self._quiz_locked or not self._current_quiz
                or not 0 <= btn_idx < len(self._choices_data)):
            return

        user_choice = self._choices_data[btn_idx]
        correct = self._quiz_correct_answer

        for btn in self.btn_choices:
            btn.setEnabled(False)

        # Doğru telaffuzu (artikeliyle veya V1, V2, V3 olarak) seslendir
        self._play_quiz_audio()

        if user_choice.lower() == correct.lower():
            sfx.play_correct()
            self._quiz_score += 1
            self._quiz_streak += 1
            self.btn_choices[btn_idx].set_state_style("correct")
            if self.ui_lang == "tr":
                msg = ui_text('Correct! Answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "de":
                msg = ui_text('Correct! Answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "es":
                msg = ui_text('Correct! Answer: {correct}', self.ui_lang, **{'correct':correct})
            else:
                msg = ui_text('Correct! Answer: {correct}', self.ui_lang, **{'correct':correct})
            self.lbl_q_feedback.setStyleSheet("color: #10b981; font-size: 14px; font-weight: 800; background: transparent; border: none;")
            self.lbl_q_feedback.setText(msg)
            self._wait_for_feedback()
        else:
            sfx.play_wrong()
            self._quiz_streak = 0
            self.btn_choices[btn_idx].set_state_style("wrong")
            for index, b in enumerate(self.btn_choices):
                if index < len(self._choices_data) and self._choices_data[index].lower() == correct.lower():
                    b.set_state_style("correct")
            if self.ui_lang == "tr":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "de":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            elif self.ui_lang == "es":
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            else:
                msg = ui_text('Wrong! Correct answer: {correct}', self.ui_lang, **{'correct':correct})
            self.lbl_q_feedback.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: 800; background: transparent; border: none;")
            self.lbl_q_feedback.setText(msg)
            self._wait_for_feedback()

        score_lbl = ui_text('Correct', self.ui_lang)
        streak_lbl = ui_text('Streak', self.ui_lang)
        self.lbl_score.setText(f"{score_lbl}: {self._quiz_score}")
        self.lbl_streak.setText(f"{streak_lbl}: {self._quiz_streak}")

    def update_language(self, lang: str):
        previous_lang=self.ui_lang
        self.ui_lang = lang
        if self._current_quiz:
            old_meanings={self._get_translation_for(item,previous_lang):self._get_translation(item) for item in self.items}
            self._quiz_correct_answer=old_meanings.get(self._quiz_correct_answer,self._quiz_correct_answer) if self.module_id!='en_confusing_words' else self._quiz_correct_answer
            self._choices_data=[old_meanings.get(choice,choice) for choice in self._choices_data] if self.module_id!='en_confusing_words' else self._choices_data
            for index,button in enumerate(self.btn_choices):
                if index<len(self._choices_data):button.set_choice_text(f'{index+1}. {self._choices_data[index]}')
            for label in (self.lbl_q_hint,self.lbl_q_sub,self.lbl_q_feedback):
                binding=getattr(label,'_text_binding',None)
                if binding:
                    kind,key,values=binding
                    values={name:old_meanings.get(value,value) if isinstance(value,str) else value for name,value in values.items()}
                    from duocards.ui_localization import render
                    label.setText(render((kind,key,values),lang))
        if self.titles:
            self.module_title = self.titles.get(lang, self.titles.get("en", self.module_title))
            self.lbl_title.setText(self.module_title)
        self.btn_tab_table.setText(t("tab_word_table", lang))
        self.btn_tab_quiz.setText(t("tab_practice_quiz", lang))
        self.btn_next_question.setText(
            ui_text('Next Question', lang)
        )
        self.input_search.setPlaceholderText(self._search_placeholder(lang))
        self._set_column_titles(lang)
        meaning_header = ui_text('Meaning', lang)
        audio_header = ui_text('Audio', lang)
        self.table.setHorizontalHeaderLabels([
            self.term_col_name, self.attr_col_name, self.extra_col_name, meaning_header, audio_header
        ])
        score_lbl = ui_text('Correct', lang)
        streak_lbl = ui_text('Streak', lang)
        self.lbl_score.setText(f"{score_lbl}: {self._quiz_score}")
        self.lbl_streak.setText(f"{streak_lbl}: {self._quiz_streak}")

        if self.isVisible() and self.stack.currentIndex() == 0:
            self._filter_table()
        else:
            self._table_loaded = False
        self._update_keyboard_labels()
        localize_tree(self,lang)
