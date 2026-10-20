import time
"""
DuoCards Desktop - Kart Kütüphanesi Ekranı
Eklenen tüm kelime ve kelime gruplarını listeleme, arama, filtreleme, düzenleme ve silme.
Ayrıca kütüphanedeki kartlarla deste ve dil bazında filtrelenebilir pratik testi (Quiz) içerir.
"""

import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QDialog, QCheckBox,
    QStackedWidget, QSizePolicy, QScrollArea,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QCursor, QColor, QBrush, QPalette
from duocards.db import (
    get_all_cards, get_all_decks, delete_card,
    record_quiz_mistake, get_top_quiz_mistakes, clear_quiz_mistakes
)
from duocards.widgets.edit_card_dialog import EditCardDialog
from duocards.audio import audio_player
from duocards.icons import get_icon
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.languages import get_language_name
from duocards.i18n import t
from duocards.languages import get_language_code, detect_card_term_language
from duocards.widgets.quiz_keyboard import QuizKeyboard, keyboard_help, keyboard_text
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QCheckBox, QLineEdit, QComboBox


class QuizFilterHighlightDelegate(QStyledItemDelegate):
    """'Tüm Desteler' ve 'Tüm Diller' seçeneğini belirgin zümrüt background rengiyle vurgulayan delege."""
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        if index.row() == 0:
            if not (opt.state & QStyle.StateFlag.State_Selected):
                painter.fillRect(opt.rect, QColor("#065f46"))
                opt.palette.setColor(QPalette.ColorRole.Text, QColor("#6ee7b7"))
            else:
                painter.fillRect(opt.rect, QColor("#047857"))
                opt.palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            opt.font.setBold(True)
        super().paint(painter, opt, index)


class DeleteCardConfirmDialog(QDialog):
    def __init__(self, parent=None, term: str = "", lang: str = "tr"):
        super().__init__(parent)
        self.term = term
        self.lang = lang
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Başlık ve İkon
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_text = ui_text('Delete Card', self.lang)
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ef4444; border: none; background: transparent;")
        top_row.addWidget(lbl_title, 1)

        btn_close = QPushButton("X")
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
                background-color: #334155;
                color: #ffffff;
            }
        """)
        btn_close.clicked.connect(self.reject)
        top_row.addWidget(btn_close)
        layout.addLayout(top_row)

        # Mesaj
        if self.lang == "tr":
            msg_text = f"<b>\"{self.term}\"</b> kartını silmek istediğinize emin misiniz?<br><span style='color: #94a3b8; font-size: 12px;'>Bu işlem geri alınamaz.</span>"
        else:
            msg_text = f"Are you sure you want to delete <b>\"{self.term}\"</b>?<br><span style='color: #94a3b8; font-size: 12px;'>This action cannot be undone.</span>"

        lbl_msg = QLabel(msg_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4; border: none; background: transparent;")
        layout.addWidget(lbl_msg)

        # Bir daha sorma tiki
        chk_text = ui_text("Don't ask again", self.lang)
        self.chk_dont_ask = QCheckBox(chk_text)
        self.chk_dont_ask.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.chk_dont_ask.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
                spacing: 8px;
                border: none;
                background: transparent;
            }
            QCheckBox:hover {
                color: #f1f5f9;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1.5px solid #475569;
                background-color: #0f172a;
            }
            QCheckBox::indicator:hover {
                border-color: #10b981;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border-color: #10b981;
            }
        """)
        layout.addWidget(self.chk_dont_ask)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton(ui_text('Cancel', self.lang))
        btn_cancel.setFixedSize(85, 34)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
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
        btn_layout.addWidget(btn_cancel)

        btn_delete = QPushButton(ui_text('Delete', self.lang))
        btn_delete.setFixedSize(85, 34)
        btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        btn_delete.clicked.connect(self.accept)
        btn_layout.addWidget(btn_delete)

        layout.addLayout(btn_layout)
        main_layout.addWidget(container)

    def dont_ask_again(self) -> bool:
        return self.chk_dont_ask.isChecked()


class LibraryQuizChoiceButton(QPushButton):
    """Kenarlıksız, duyarlı ve metinleri kesmeyen quiz şık butonu."""
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
                background-color: #1e293b;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #10b981;
                border: none;
            }
        """)
        self.setStyleSheet(self.styleSheet() + '\nQPushButton:focus { border: 2px solid #ffffff; }')

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
                    background-color: #1e293b;
                    border: none;
                    border-radius: 10px;
                }
            """)
        self.setStyleSheet(self.styleSheet() + '\nQPushButton:focus { border: 2px solid #ffffff; }')





class QuizMistakesDialog(QDialog):
    """Kütüphane testinde en çok yanlış yapılan kelimeleri listeleyen modern diyalog."""
    def __init__(self, parent=None, lang: str = "tr"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(540, 520)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1.5px solid #ef4444;
                border-radius: 16px;
            }
        """)
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(20, 18, 20, 18)
        c_lay.setSpacing(12)

        # Üst Başlık Satırı
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_text = ui_text('Most Mistaken Words', self.lang)
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

        desc_text = (
            ui_text('Words you mistakenly answered in library quiz are tracked here. You can listen and review them anytime.', self.lang)
        )
        lbl_desc = QLabel(desc_text)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4; background: transparent; border: none;")
        c_lay.addWidget(lbl_desc)

        # Liste Alanı (ScrollArea)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.list_widget)
        c_lay.addWidget(scroll, 1)

        # Alt Butonlar: Sıfırla & Kapat
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_clear = QPushButton(ui_text('Clear Statistics', self.lang))
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.setFixedHeight(34)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_clear.clicked.connect(self._clear_mistakes)
        btn_row.addWidget(self.btn_clear)

        btn_row.addStretch()

        btn_ok = QPushButton(ui_text('Close', self.lang))
        btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ok.setFixedSize(85, 34)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)

        c_lay.addLayout(btn_row)
        main_layout.addWidget(container)
        self._populate_list()

    def _populate_list(self):
        while self.list_layout.count() > 0:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        mistakes = get_top_quiz_mistakes(40)
        if not mistakes:
            lbl_empty = QLabel(
                ui_text('No mistaken words recorded in quiz yet. Great job!', self.lang)
            )
            lbl_empty.setWordWrap(True)
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px; padding: 40px 10px; background: transparent; border: none;")
            self.list_layout.addWidget(lbl_empty)
            self.btn_clear.setEnabled(False)
            return

        self.btn_clear.setEnabled(True)
        for m in mistakes:
            row_frame = QFrame()
            row_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e293b;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 4px;
                }
            """)
            r_lay = QHBoxLayout(row_frame)
            r_lay.setContentsMargins(12, 8, 12, 8)
            r_lay.setSpacing(10)

            # Sol Bilgi
            info_col = QVBoxLayout()
            info_col.setSpacing(2)

            t_row = QHBoxLayout()
            t_row.setSpacing(8)
            lbl_term = QLabel(m["term"])
            lbl_term.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 800; background: transparent; border: none;")
            t_row.addWidget(lbl_term)

            lbl_badge = QLabel(ui_text("{m['wrong_count']}x Errors", self.lang, **{"m['wrong_count']": m['wrong_count']}))
            lbl_badge.setStyleSheet("""
                background-color: rgba(239, 68, 68, 0.2);
                color: #f87171;
                font-size: 11px;
                font-weight: 800;
                border-radius: 6px;
                padding: 2px 6px;
                border: 1px solid rgba(239, 68, 68, 0.4);
            """)
            t_row.addWidget(lbl_badge)
            t_row.addStretch()
            info_col.addLayout(t_row)

            lbl_def = QLabel(m["definition"])
            lbl_def.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent; border: none;")
            info_col.addWidget(lbl_def)

            r_lay.addLayout(info_col, 1)

            # Ses Dinle Butonu (Minimalist yeşil simge)
            btn_audio = QPushButton()
            btn_audio.setIcon(get_icon("audio", 22, "#10b981"))
            btn_audio.setIconSize(QSize(22, 22))
            btn_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_audio.setFixedSize(32, 32)
            btn_audio.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(16, 185, 129, 0.15);
                }
            """)
            lc = detect_card_term_language(m)
            btn_audio.clicked.connect(lambda checked, t=m["term"], lang_c=lc: audio_player.play_pronunciation(t, lang=lang_c))
            r_lay.addWidget(btn_audio)

            self.list_layout.addWidget(row_frame)

    def _clear_mistakes(self):
        sfx.play_click()
        clear_quiz_mistakes()
        self._populate_list()


class LibraryView(QWidget):
    card_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._needs_reload = True
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(120)
        self._search_timer.timeout.connect(self.reload_cards)

        self._quiz_score = 0
        self._quiz_streak = 0
        self._current_quiz_card = None
        self._quiz_correct_answer = ""
        self._choices_data = []
        self._quiz_locked = False
        self._audio_request = None

        self.lang=settings.get('ui_language','tr')
        self._setup_ui()
        audio_player.request_state_changed.connect(self._audio_state)
        self._keyboard = QuizKeyboard(
            self, buttons=lambda: self.btn_choices,
            next_button=self.btn_next_question, listen=self._play_quiz_audio,
            restart=self._start_quiz,
            active=lambda: self.content_stack.currentIndex() == 1)
        self._update_keyboard_labels()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(14)

        # 1. Üst Başlık & Sekme Geçiş Butonları (Kart Tablosu vs Kütüphane Testi)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        ui_lang = self.lang
        self.lbl_title = QLabel(t("lib_title", ui_lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("lib_subtitle", ui_lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box, 1)

        self.btn_tab_table = QPushButton(ui_text('Card Table', ui_lang))
        self.btn_tab_table.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_table.setFixedHeight(36)
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_table.clicked.connect(self._show_table)

        self.btn_tab_quiz = QPushButton(ui_text('Library Quiz', ui_lang))
        self.btn_tab_quiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_quiz.setFixedHeight(36)
        self.btn_tab_quiz.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_quiz.clicked.connect(self._show_quiz)

        header_row.addWidget(self.btn_tab_table)
        header_row.addWidget(self.btn_tab_quiz)
        main_layout.addLayout(header_row)

        self.lbl_audio_status = QLabel()
        self.lbl_audio_status.setWordWrap(True)
        self.lbl_audio_status.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_audio_status.setStyleSheet('color: #94a3b8; font-size: 12px; background: transparent;')
        self.lbl_audio_status.hide()
        main_layout.addWidget(self.lbl_audio_status)

        # 2. İçerik Alanı: Stacked Widget (Tablo vs Quiz)
        self.content_stack = QStackedWidget()

        # ---------- SAYFA 0: KART TABLOSU ----------
        page_table = QWidget()
        page_table_layout = QVBoxLayout(page_table)
        page_table_layout.setContentsMargins(0, 0, 0, 0)
        page_table_layout.setSpacing(12)

        # Filtre ve Arama Çubuğu
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_placeholder", ui_lang))
        self.search_input.textChanged.connect(self._search_timer.start)
        filter_bar.addWidget(self.search_input, 2)

        self.deck_filter = QComboBox()
        self.deck_filter.currentIndexChanged.connect(self.reload_cards)
        filter_bar.addWidget(self.deck_filter, 1)

        self.status_filter = QComboBox()
        self.status_filter.addItem(t("status_all", ui_lang), "")
        self.status_filter.addItem(t("status_new", ui_lang), "new")
        self.status_filter.addItem(t("status_learning", ui_lang), "learning")
        self.status_filter.addItem(t("status_mastered", ui_lang), "mastered")
        self.status_filter.currentIndexChanged.connect(self.reload_cards)
        filter_bar.addWidget(self.status_filter, 1)

        self.lang_filter = QComboBox()
        self.lang_filter.currentIndexChanged.connect(self.reload_cards)
        filter_bar.addWidget(self.lang_filter, 1)

        page_table_layout.addLayout(filter_bar)

        self.lbl_count = QLabel("0 kart bulundu")
        self.lbl_count.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 2px;")
        page_table_layout.addWidget(self.lbl_count)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            t("col_term", ui_lang), t("col_def", ui_lang), t("col_lang", ui_lang),
            t("col_pos", ui_lang), t("col_deck", ui_lang), t("col_status", ui_lang),
            t("col_reps", ui_lang), t("col_actions", ui_lang)
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(2, 85)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 95)
        self.table.setColumnWidth(6, 65)
        self.table.setColumnWidth(7, 260)  # Geniş ve ferah sütun genişliği, butonlar asla çakışmaz!

        self.table.setStyleSheet("""
            QPushButton[action_btn='audio'] {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 6px;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton[action_btn='audio']:hover {
                background-color: #10b981;
                color: #ffffff;
            }
            QPushButton[action_btn='edit'] {
                background-color: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.35);
                border-radius: 6px;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton[action_btn='edit']:hover {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton[action_btn='del'] {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-radius: 6px;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton[action_btn='del']:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_row_double_click)

        page_table_layout.addWidget(self.table)
        self.content_stack.addWidget(page_table)

        # ---------- SAYFA 1: KÜTÜPHANE QUIZ MODÜLÜ ----------
        page_quiz = QWidget()
        page_quiz_layout = QVBoxLayout(page_quiz)
        page_quiz_layout.setContentsMargins(0, 0, 0, 0)
        page_quiz_layout.setSpacing(16)
        page_quiz_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Quiz Filtre Çubuğu (Deste ve Dil Filtresi)
        quiz_filter_frame = QFrame()
        quiz_filter_frame.setStyleSheet("background-color: #111827; border-radius: 12px; padding: 6px 14px; border: none;")
        quiz_filter_lay = QHBoxLayout(quiz_filter_frame)
        quiz_filter_lay.setSpacing(12)

        lbl_f_icon = QLabel(ui_text('Filter:', self.lang))
        lbl_f_icon.setStyleSheet("color: #10b981; font-weight: 800; font-size: 13px; background: transparent;")
        quiz_filter_lay.addWidget(lbl_f_icon)

        self.quiz_deck_filter = QComboBox()
        self.quiz_deck_filter.setMinimumWidth(180)
        self.quiz_deck_filter.setItemDelegate(QuizFilterHighlightDelegate(self.quiz_deck_filter))
        self.quiz_deck_filter.currentIndexChanged.connect(self._on_quiz_filter_changed)
        quiz_filter_lay.addWidget(self.quiz_deck_filter)

        self.quiz_lang_filter = QComboBox()
        self.quiz_lang_filter.setMinimumWidth(160)
        self.quiz_lang_filter.setItemDelegate(QuizFilterHighlightDelegate(self.quiz_lang_filter))
        self.quiz_lang_filter.currentIndexChanged.connect(self._on_quiz_filter_changed)
        quiz_filter_lay.addWidget(self.quiz_lang_filter)

        self.btn_restart_quiz = QPushButton(ui_text('Restart Quiz', ui_lang))
        self.btn_restart_quiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_restart_quiz.setFixedHeight(32)
        self.btn_restart_quiz.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.btn_restart_quiz.clicked.connect(self._start_quiz)
        quiz_filter_lay.addWidget(self.btn_restart_quiz)

        self.btn_show_mistakes = QPushButton(ui_text('Mistakes', ui_lang))
        self.btn_show_mistakes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_show_mistakes.setFixedHeight(32)
        self.btn_show_mistakes.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_show_mistakes.clicked.connect(self._open_mistakes_dialog)
        quiz_filter_lay.addWidget(self.btn_show_mistakes)

        page_quiz_layout.addWidget(quiz_filter_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Skor ve Seri Kartı
        stats_box = QFrame()
        stats_box.setStyleSheet("background-color: #111827; border-radius: 10px; border: none; padding: 6px 20px;")
        sb_lay = QHBoxLayout(stats_box)
        sb_lay.setSpacing(24)

        score_text = ui_text('Correct: 0', ui_lang)
        streak_text = ui_text('Streak: 0', ui_lang)
        self.lbl_quiz_score = QLabel(score_text)
        self.lbl_quiz_score.setStyleSheet("color: #10b981; font-weight: 800; font-size: 14px; background: transparent;")
        self.lbl_quiz_streak = QLabel(streak_text)
        self.lbl_quiz_streak.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 14px; background: transparent;")
        sb_lay.addWidget(self.lbl_quiz_score)
        sb_lay.addWidget(self.lbl_quiz_streak)
        page_quiz_layout.addWidget(stats_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Soru Kartı (Enlemesine Dikdörtgen, Çizgisiz/Kenarlıksız)
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

        self.lbl_q_hint = QLabel(ui_text('What is the meaning of this term?', ui_lang))
        self.lbl_q_hint.setWordWrap(True)
        self.lbl_q_hint.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600; background: transparent;")
        self.lbl_q_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_lay.addWidget(self.lbl_q_hint)

        # Kelime ve Dinleme Butonu Satırı (Kelimeden hemen sonra, aralık sıkı ve ortalı)
        word_audio_row = QHBoxLayout()
        word_audio_row.setSpacing(8)
        word_audio_row.setContentsMargins(0, 0, 0, 0)
        word_audio_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_audio_row.addStretch()

        self.lbl_q_term = QLabel("")
        self.lbl_q_term.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.lbl_q_term.setStyleSheet("color: #38bdf8; font-size: 30px; font-weight: 900; background: transparent;")
        self.lbl_q_term.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_audio_row.addWidget(self.lbl_q_term)

        self.btn_q_audio = QPushButton()
        self.btn_q_audio.setIcon(get_icon("audio", 24, "#10b981"))
        self.btn_q_audio.setIconSize(QSize(24, 24))
        self.btn_q_audio.setToolTip(ui_text('Listen pronunciation', ui_lang))
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
        word_audio_row.addWidget(self.btn_q_audio)
        word_audio_row.addStretch()
        qc_lay.addLayout(word_audio_row)

        self.lbl_q_meta = QLabel("")
        self.lbl_q_meta.setStyleSheet("color: #cbd5e1; font-size: 13px; font-style: italic; background: transparent;")
        self.lbl_q_meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_lay.addWidget(self.lbl_q_meta)

        self.lbl_q_feedback = QLabel("")
        self.lbl_q_feedback.setStyleSheet("font-size: 14px; font-weight: 800; background: transparent;")
        self.lbl_q_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_lay.addWidget(self.lbl_q_feedback)
        self.lbl_keyboard_help = QLabel()
        self.lbl_keyboard_help.setWordWrap(True)
        self.lbl_keyboard_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_keyboard_help.setStyleSheet('color:#94a3b8; font-size:12px; background:transparent; border:none;')
        qc_lay.addWidget(self.lbl_keyboard_help)

        page_quiz_layout.addWidget(self.q_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Şıklar (Tek Satırda 4 Şık, Çizgisiz, Kesilmeyen Geniş Kutucuklar)
        choices_container = QWidget()
        choices_container.setMinimumWidth(740)
        choices_container.setMaximumWidth(1020)
        choices_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        c_row = QHBoxLayout(choices_container)
        c_row.setSpacing(10)
        c_row.setContentsMargins(0, 0, 0, 0)

        self.btn_choices = []
        for i in range(4):
            btn = LibraryQuizChoiceButton()
            btn.clicked.connect(lambda ch, idx=i: self._on_quiz_answer(idx))
            self.btn_choices.append(btn)
            c_row.addWidget(btn, 1)

        page_quiz_layout.addWidget(choices_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sonraki Soru Butonu
        self.btn_next_question = QPushButton(ui_text('Next Question', ui_lang))
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
        page_quiz_layout.addWidget(self.btn_next_question, alignment=Qt.AlignmentFlag.AlignCenter)

        self.content_stack.addWidget(page_quiz)
        main_layout.addWidget(self.content_stack)

    def _show_table(self):
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_quiz.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.content_stack.setCurrentIndex(0)

    def _show_quiz(self):
        self.btn_tab_quiz.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 12px; font-weight: 800; border-radius: 8px; padding: 0 16px; border: none;")
        self.btn_tab_table.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 0 16px; border: none;")
        self.content_stack.setCurrentIndex(1)
        self._sync_quiz_filters()
        if not self._current_quiz_card:
            self._start_quiz()
        self._keyboard.focus_answer()

    def _update_keyboard_labels(self, lang=None):
        lang = lang or self.lang
        self.btn_next_question.setText(keyboard_text('next_button', lang)
                                      + ' (Enter / ' + keyboard_text('space', lang) + ')')
        self.btn_restart_quiz.setToolTip(keyboard_text('restart', lang))
        self.btn_q_audio.setToolTip(keyboard_text('listen', lang))
        state = ('next' if self.btn_next_question.isEnabled() else 'waiting') if self._quiz_locked else 'choices'
        if not self._current_quiz_card:
            state = None
        self.lbl_keyboard_help.setText(keyboard_help(lang, state))

    def _sync_quiz_filters(self):
        """Kütüphane quiz filtrelerini veritabanı desteleri ve dilleri ile senkronize eder."""
        ui_lang = self.lang
        cur_deck = self.quiz_deck_filter.currentData()
        self.quiz_deck_filter.blockSignals(True)
        self.quiz_deck_filter.clear()
        self.quiz_deck_filter.addItem(ui_text('All Decks', ui_lang), None)
        self.quiz_deck_filter.setItemData(0, QBrush(QColor("#065f46")), Qt.ItemDataRole.BackgroundRole)
        self.quiz_deck_filter.setItemData(0, QBrush(QColor("#6ee7b7")), Qt.ItemDataRole.ForegroundRole)
        for d in get_all_decks():
            self.quiz_deck_filter.addItem(d["name"], d["id"])
        deck_idx = self.quiz_deck_filter.findData(cur_deck)
        if deck_idx >= 0:
            self.quiz_deck_filter.setCurrentIndex(deck_idx)
        self.quiz_deck_filter.blockSignals(False)

        cur_lang = self.quiz_lang_filter.currentData()
        self.quiz_lang_filter.blockSignals(True)
        self.quiz_lang_filter.clear()
        self.quiz_lang_filter.addItem(ui_text('All Languages', ui_lang), None)
        self.quiz_lang_filter.setItemData(0, QBrush(QColor("#065f46")), Qt.ItemDataRole.BackgroundRole)
        self.quiz_lang_filter.setItemData(0, QBrush(QColor("#6ee7b7")), Qt.ItemDataRole.ForegroundRole)
        from duocards.db import get_distinct_target_languages
        for l in get_distinct_target_languages():
            self.quiz_lang_filter.addItem(get_language_name(l, self.lang), l)
        lang_idx = self.quiz_lang_filter.findData(cur_lang)
        if lang_idx >= 0:
            self.quiz_lang_filter.setCurrentIndex(lang_idx)
        self.quiz_lang_filter.blockSignals(False)

        self._update_quiz_filters_style()

    def _on_quiz_filter_changed(self):
        self._update_quiz_filters_style()
        self._start_quiz()

    def _update_quiz_filters_style(self):
        """'Tüm Desteler' ve 'Tüm Diller' seçildiğinde combobox background rengini belirgin zümrüt tonuna ayarlar."""
        # Deste Filtresi
        if self.quiz_deck_filter.currentIndex() == 0:
            self.quiz_deck_filter.setStyleSheet("""
                QComboBox {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064e3b, stop:1 #065f46);
                    border: 1.5px solid #10b981;
                    border-radius: 8px;
                    color: #a7f3d0;
                    font-size: 13px;
                    font-weight: 800;
                    padding: 6px 12px;
                }
                QComboBox:hover {
                    border-color: #34d399;
                    background-color: #047857;
                }
                QComboBox QAbstractItemView {
                    background-color: #111827;
                    color: #f8fafc;
                    selection-background-color: #10b981;
                    border: 1px solid #334155;
                }
            """)
        else:
            self.quiz_deck_filter.setStyleSheet("""
                QComboBox {
                    background-color: #162032;
                    border: 1.5px solid #283548;
                    border-radius: 8px;
                    color: #f8fafc;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 6px 12px;
                }
                QComboBox:hover {
                    border-color: #10b981;
                    background-color: #1b263b;
                }
                QComboBox QAbstractItemView {
                    background-color: #111827;
                    color: #f8fafc;
                    selection-background-color: #10b981;
                    border: 1px solid #334155;
                }
            """)

        # Dil Filtresi
        if self.quiz_lang_filter.currentIndex() == 0:
            self.quiz_lang_filter.setStyleSheet("""
                QComboBox {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064e3b, stop:1 #065f46);
                    border: 1.5px solid #10b981;
                    border-radius: 8px;
                    color: #a7f3d0;
                    font-size: 13px;
                    font-weight: 800;
                    padding: 6px 12px;
                }
                QComboBox:hover {
                    border-color: #34d399;
                    background-color: #047857;
                }
                QComboBox QAbstractItemView {
                    background-color: #111827;
                    color: #f8fafc;
                    selection-background-color: #10b981;
                    border: 1px solid #334155;
                }
            """)
        else:
            self.quiz_lang_filter.setStyleSheet("""
                QComboBox {
                    background-color: #162032;
                    border: 1.5px solid #283548;
                    border-radius: 8px;
                    color: #f8fafc;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 6px 12px;
                }
                QComboBox:hover {
                    border-color: #10b981;
                    background-color: #1b263b;
                }
                QComboBox QAbstractItemView {
                    background-color: #111827;
                    color: #f8fafc;
                    selection-background-color: #10b981;
                    border: 1px solid #334155;
                }
            """)

    def _start_quiz(self):
        self._feedback_until = 0
        self._quiz_score = 0
        self._quiz_streak = 0
        ui_lang = self.lang
        self.lbl_quiz_score.setText(ui_text('Correct: {n}', ui_lang, n=0))
        self.lbl_quiz_streak.setText(ui_text('Streak: {n}', ui_lang, n=0))
        self._next_quiz()

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
        self._quiz_locked = False
        if hasattr(self, '_feedback_timer'):
            self._feedback_timer.stop()
        self.btn_next_question.setVisible(False)
        self.lbl_q_feedback.setText("")

        deck_id = self.quiz_deck_filter.currentData()
        target_lang = self.quiz_lang_filter.currentData()
        cards = get_all_cards(deck_id=deck_id, target_lang=target_lang)
        ui_lang = self.lang

        if len(cards) < 4:
            self._current_quiz_card = None
            msg = ui_text('Please add at least 4 cards in this filter to start quiz.', ui_lang)
            self.lbl_q_term.setText(msg)
            self.lbl_q_meta.setText(f"{len(cards)} / 4")
            self.btn_q_audio.setVisible(False)
            for btn in self.btn_choices:
                btn.setVisible(False)
            self._update_keyboard_labels()
            self._keyboard.focus_answer()
            return

        self.btn_q_audio.setVisible(True)
        target = random.choice(cards)
        self._current_quiz_card = target
        if self.isVisible():
            audio_player.prefetch(target["term"],detect_card_term_language(target))

        self.lbl_q_term.setText(target["term"])
        deck_name = target.get("deck_name", "")
        lang_name = get_language_name(target.get("target_lang", ""),self.lang)
        pos_name = ui_text(target.get("part_of_speech", ""),self.lang)
        meta_parts = [p for p in [deck_name, lang_name, pos_name] if p]
        self.lbl_q_meta.setText(" • ".join(meta_parts))

        correct_ans = target["definition"]
        self._quiz_correct_answer = correct_ans

        # 3 Yanlış seçenek oluştur
        pool = [c for c in cards if c["term"] != target["term"] and c["definition"] != correct_ans]
        random.shuffle(pool)
        wrong_choices = []
        for w in pool:
            w_def = w["definition"]
            if w_def not in wrong_choices:
                wrong_choices.append(w_def)
            if len(wrong_choices) == 3:
                break

        # Havuzda yeterli farklı tanım yoksa tüm kartlardan takviye et
        if len(wrong_choices) < 3:
            all_c = get_all_cards()
            random.shuffle(all_c)
            for w in all_c:
                w_def = w["definition"]
                if w_def != correct_ans and w_def not in wrong_choices:
                    wrong_choices.append(w_def)
                if len(wrong_choices) == 3:
                    break

        choices = [correct_ans] + wrong_choices
        random.shuffle(choices)
        self._choices_data = choices

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

    def _open_mistakes_dialog(self):
        ui_lang = self.lang
        dlg = QuizMistakesDialog(self, lang=ui_lang)
        dlg.exec()

    def _play_quiz_audio(self):
        if self._current_quiz_card:
            sfx.play_click()
            self._play_card_audio(self._current_quiz_card)

    def _play_card_audio(self, card):
        term = card.get('term', '').strip()
        if not term:
            return
        self._audio_request = None
        self._show_audio_state('loading')
        self._audio_request = audio_player.play_pronunciation(term, lang=detect_card_term_language(card))

    def _audio_state(self, request, state):
        if self._audio_request is not None and request == self._audio_request:
            self._show_audio_state(state)

    def _show_audio_state(self, state):
        messages = {
            'loading': 'Preparing audio…',
            'playing': 'Playing audio…',
            'unavailable': 'Natural speech is unavailable. Check the connection and audio player.',
            'error': 'Audio could not play. Retry or choose another card.',
        }
        self.lbl_audio_status.setText(ui_text(messages[state], self.lang) if state in messages else '')
        self.lbl_audio_status.setVisible(state in messages)

    def _on_quiz_answer(self, btn_idx: int):
        if (self._quiz_locked or not self._current_quiz_card
                or not 0 <= btn_idx < len(self._choices_data)):
            return

        user_choice = self._choices_data[btn_idx]
        correct = self._quiz_correct_answer
        ui_lang = self.lang

        for btn in self.btn_choices:
            btn.setEnabled(False)

        if user_choice == correct:
            sfx.play_correct()
            self.btn_choices[btn_idx].set_state_style("correct")
            self._quiz_score += 1
            self._quiz_streak += 1
            self.lbl_q_feedback.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 800;")
            self.lbl_q_feedback.setText(ui_text('Correct! Well done!', ui_lang))
            # Doğru bilindiğinde kelimeyi telaffuz et
            self._play_quiz_audio()
        else:
            sfx.play_wrong()
            self.btn_choices[btn_idx].set_state_style("wrong")
            for index, btn in enumerate(self.btn_choices):
                if index < len(self._choices_data) and self._choices_data[index] == correct:
                    btn.set_state_style("correct")
            self._quiz_streak = 0
            self.lbl_q_feedback.setStyleSheet("color: #ef4444; font-size: 15px; font-weight: 800;")
            self.lbl_q_feedback.setText(ui_text('Wrong! Correct answer: {answer}', ui_lang, answer=correct))
            # Yanlış cevabı veritabanında hatırla
            record_quiz_mistake(
                term=self._current_quiz_card.get("term", ""),
                definition=correct,
                card_id=self._current_quiz_card.get("id")
            )

        self.lbl_quiz_score.setText(ui_text('Correct: {n}', ui_lang, n=self._quiz_score))
        self.lbl_quiz_streak.setText(ui_text('Streak: {n}', ui_lang, n=self._quiz_streak))
        self._wait_for_feedback()

    def refresh_filter_languages(self):
        current_data = self.lang_filter.currentData()
        self.lang_filter.blockSignals(True)
        self.lang_filter.clear()
        all_langs_label = ui_text('All Languages', self.lang)
        self.lang_filter.addItem(all_langs_label, None)

        from duocards.db import get_distinct_target_languages
        langs = get_distinct_target_languages()
        idx_to_select = 0
        for i, l in enumerate(langs):
            self.lang_filter.addItem(get_language_name(l, self.lang), l)
            if current_data == l:
                idx_to_select = i + 1

        self.lang_filter.setCurrentIndex(idx_to_select)
        self.lang_filter.blockSignals(False)

    def refresh_filter_decks(self):
        self.refresh_filter_languages()
        current_data = self.deck_filter.currentData()
        self.deck_filter.blockSignals(True)
        self.deck_filter.clear()
        self.deck_filter.addItem(ui_text('All Decks', self.lang), None)

        decks = get_all_decks()
        idx_to_select = 0
        for i, d in enumerate(decks):
            self.deck_filter.addItem(d["name"], d["id"])
            if current_data == d["id"]:
                idx_to_select = i + 1

        self.deck_filter.setCurrentIndex(idx_to_select)
        self.deck_filter.blockSignals(False)
        self._sync_quiz_filters()

    def reload_cards(self):
        deck_id = self.deck_filter.currentData()
        status = self.status_filter.currentData()
        target_lang = self.lang_filter.currentData()
        search = self.search_input.text().strip()
        lang = self.lang

        cards = get_all_cards(deck_id=deck_id, search_query=search, status=status, target_lang=target_lang)
        found_txt = ui_text('{len(cards)} cards found', lang, **{'len(cards)': len(cards)})
        self.lbl_count.setText(found_txt)

        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(cards))
        for row_idx, card in enumerate(cards):
            card_id = card["id"]

            # 0: Kelime
            item_term = QTableWidgetItem(card["term"])
            item_term.setData(Qt.ItemDataRole.UserRole, card_id)
            item_term.setFont(self.font())
            item_term.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row_idx, 0, item_term)

            # 1: Anlamı
            item_def = QTableWidgetItem(card["definition"])
            self.table.setItem(row_idx, 1, item_def)

            # 2: Dil
            item_lang = QTableWidgetItem(get_language_name(card.get("target_lang"),self.lang) if card.get("target_lang") else "-")
            item_lang.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, item_lang)

            # 3: Tür
            item_pos = QTableWidgetItem(ui_text(card.get("part_of_speech", ""),self.lang))
            self.table.setItem(row_idx, 3, item_pos)

            # 4: Deste
            item_deck = QTableWidgetItem(card.get('deck_name', ''))
            self.table.setItem(row_idx, 4, item_deck)

            # 5: Durum
            status_map = {
                "new": ui_text('New', lang),
                "learning": ui_text('Learning', lang),
                "mastered": ui_text('Mastered', lang)
            }
            item_status = QTableWidgetItem(status_map.get(card.get("status"), "Yeni"))
            self.table.setItem(row_idx, 5, item_status)

            # 6: Tekrar sayısı
            item_reps = QTableWidgetItem(f"{card.get('repetition_count', 0)}")
            item_reps.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 6, item_reps)

            # 7: İşlem Butonları (Ses, Düzenle, Sil) - Asla birbirine girmez
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 0, 4, 0)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_audio = QPushButton(ui_text('Audio', lang))
            btn_audio.setProperty("action_btn", "audio")
            btn_audio.setFixedSize(60, 30)
            btn_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_audio.clicked.connect(lambda checked, c=card: self._play_card_audio(c))

            btn_edit = QPushButton(ui_text('Edit', lang))
            btn_edit.setProperty("action_btn", "edit")
            btn_edit.setFixedSize(76, 30)
            btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_edit.clicked.connect(lambda checked, cid=card_id: self.open_edit_dialog(cid))

            btn_del = QPushButton(ui_text('Delete', lang))
            btn_del.setProperty("action_btn", "del")
            btn_del.setFixedSize(58, 30)
            btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_del.clicked.connect(lambda checked, cid=card_id, t=card["term"]: self._delete_card(cid, t))

            action_layout.addWidget(btn_audio)
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 7, action_widget)
            self.table.setRowHeight(row_idx, 60)
        self.table.setUpdatesEnabled(True)

    def _on_row_double_click(self, row, column):
        item = self.table.item(row, 0)
        if item:
            card_id = item.data(Qt.ItemDataRole.UserRole)
            if card_id:
                self.open_edit_dialog(card_id)

    def open_edit_dialog(self, card_id: int):
        dlg = EditCardDialog(card_id, self)
        if dlg.exec():
            self.reload_cards()
            self.card_updated.emit()

    def _delete_card(self, card_id: int, term: str):
        if settings.get("dont_ask_delete_card", False):
            delete_card(card_id)
            self.reload_cards()
            self.card_updated.emit()
            return

        dlg = DeleteCardConfirmDialog(self, term=term, lang=self.lang)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.dont_ask_again():
                settings.set("dont_ask_delete_card", True)
                settings.save()
            delete_card(card_id)
            self.reload_cards()
            self.card_updated.emit()

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_needs_reload", False):
            self._needs_reload = False
            self.reload_cards()
            self._sync_quiz_filters()
        QTimer.singleShot(0, self._keyboard.focus_answer)

    def hideEvent(self, event):
        self._audio_request = None
        self._show_audio_state('idle')
        super().hideEvent(event)

    def update_language(self, lang: str):
        self.lang=lang
        self.lbl_title.setText(t("lib_title", lang))
        self.lbl_subtitle.setText(t("lib_subtitle", lang))
        self.btn_tab_table.setText(ui_text('Card Table', lang))
        self.btn_tab_quiz.setText(ui_text('Library Quiz', lang))
        self.btn_restart_quiz.setText(ui_text('Restart Quiz', lang))
        if hasattr(self, "btn_show_mistakes"):
            self.btn_show_mistakes.setText(ui_text('Mistakes', lang))
        self.btn_next_question.setText(ui_text('Next Question', lang))
        self.lbl_q_hint.setText(ui_text('What is the meaning of this term?', lang))
        self.search_input.setPlaceholderText(t("search_placeholder", lang))
        self.table.setHorizontalHeaderLabels([
            t("col_term", lang), t("col_def", lang), t("col_lang", lang),
            t("col_pos", lang), t("col_deck", lang), t("col_status", lang),
            t("col_reps", lang), t("col_actions", lang)
        ])
        self.status_filter.setItemText(0, t("status_all", lang))
        self.status_filter.setItemText(1, t("status_new", lang))
        self.status_filter.setItemText(2, t("status_learning", lang))
        self.status_filter.setItemText(3, t("status_mastered", lang))
        self.refresh_filter_decks()
        if self._current_quiz_card:
            card = self._current_quiz_card
            self.lbl_q_meta.setText(' • '.join(str(part) for part in (
                card.get('deck_name', ''), get_language_name(card.get('target_lang', ''), lang),
                ui_text(card.get('part_of_speech', ''), lang)) if part))
        if self.isVisible():
            self.reload_cards()
        else:
            self._needs_reload = True
        self._update_keyboard_labels(lang)
        localize_tree(self,lang)
