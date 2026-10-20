"""
DuoCards Desktop - Kart Düzenleme Dialog Penceresi
Özel çerçevesiz ve modern başlık çubuklu kart düzenleme penceresi.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from duocards.db import get_card, update_card, get_all_decks
from duocards.audio import audio_player
from duocards.settings import settings
from duocards.i18n import t
from duocards.languages import get_language_code, get_language_name
from duocards.widgets.add_card_view import CATEGORIES_BY_UI_LANG
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit, QComboBox


class EditCardDialog(QDialog):
    def __init__(self, card_id: int, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.lang = settings.get("ui_language", "tr")
        self._drag_pos = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)

        self._setup_ui()
        self._load_card_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setStyleSheet("""
            QFrame#cardEditContainer {
                background-color: #111827;
                border: 1.5px solid #283548;
                border-radius: 16px;
            }
        """)
        container.setObjectName("cardEditContainer")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(22, 18, 22, 20)
        c_layout.setSpacing(14)

        # ---------------- 1. ÖZEL BAŞLIK ÇUBUĞU ----------------
        header = QHBoxLayout()
        header.setSpacing(10)

        title_txt = ui_text('Edit Card', self.lang)
        lbl_title = QLabel(title_txt)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #10b981; border: none; background: transparent;")
        header.addWidget(lbl_title, 1)

        btn_close = QPushButton("X")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)
        c_layout.addLayout(header)

        # ---------------- 2. FORM ALANLARI ----------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 4, 4, 4)
        form_layout.setSpacing(10)

        input_style = """
            QLineEdit, QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 6px 10px;
                min-height: 22px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #10b981;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                color: #ffffff;
                selection-background-color: #10b981;
                border: 1px solid #334155;
            }
        """

        label_style = "font-size: 12px; font-weight: 700; color: #94a3b8; margin-top: 2px;"

        # Deste
        lbl_deck = QLabel(ui_text('Deck:', self.lang))
        lbl_deck.setStyleSheet(label_style)
        form_layout.addWidget(lbl_deck)
        self.cmb_deck = QComboBox()
        self.cmb_deck.setStyleSheet(input_style)
        form_layout.addWidget(self.cmb_deck)

        from duocards.languages import get_all_language_names, get_language_code
        all_langs = get_all_language_names()

        # Kaynak Dil (Kelimenin Dili)
        lbl_src_lang = QLabel(ui_text('Term Language (Source):', self.lang))
        lbl_src_lang.setStyleSheet(label_style)
        form_layout.addWidget(lbl_src_lang)
        self.cmb_source_lang = QComboBox()
        self.cmb_source_lang.setEditable(True)
        self.cmb_source_lang.setStyleSheet(input_style)
        self.cmb_source_lang.addItems(all_langs)
        if self.cmb_source_lang.completer():
            self.cmb_source_lang.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        form_layout.addWidget(self.cmb_source_lang)

        # Kelime
        lbl_term = QLabel(ui_text('Term or Phrase *:', self.lang))
        lbl_term.setStyleSheet(label_style)
        form_layout.addWidget(lbl_term)
        term_row = QHBoxLayout()
        term_row.setSpacing(8)
        self.input_term = QLineEdit()
        self.input_term.setStyleSheet(input_style)
        btn_listen = QPushButton(ui_text('Listen', self.lang))
        btn_listen.setFixedWidth(70)
        btn_listen.setFixedHeight(34)
        btn_listen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_listen.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
            }
        """)
        btn_listen.clicked.connect(lambda: audio_player.play_pronunciation(
            self.input_term.text(),
            lang=get_language_code(self.cmb_source_lang.currentText())
        ))
        term_row.addWidget(self.input_term, 1)
        term_row.addWidget(btn_listen)
        form_layout.addLayout(term_row)

        # Anlam Dili
        lbl_target_lang = QLabel(ui_text('Meaning Language (Target):', self.lang))
        lbl_target_lang.setStyleSheet(label_style)
        form_layout.addWidget(lbl_target_lang)
        self.cmb_target_lang = QComboBox()
        self.cmb_target_lang.setEditable(True)
        self.cmb_target_lang.setStyleSheet(input_style)
        self.cmb_target_lang.addItems(all_langs)
        if self.cmb_target_lang.completer():
            self.cmb_target_lang.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        form_layout.addWidget(self.cmb_target_lang)

        # Anlam
        lbl_def = QLabel(ui_text('Definition / Translation *:', self.lang))
        lbl_def.setStyleSheet(label_style)
        form_layout.addWidget(lbl_def)
        self.input_def = QLineEdit()
        self.input_def.setStyleSheet(input_style)
        form_layout.addWidget(self.input_def)

        # Kelime Türü
        lbl_pos = QLabel(ui_text('Part of Speech:', self.lang))
        lbl_pos.setStyleSheet(label_style)
        form_layout.addWidget(lbl_pos)
        self.cmb_pos = QComboBox()
        self.cmb_pos.setStyleSheet(input_style)
        lang_dict = CATEGORIES_BY_UI_LANG.get(self.lang, CATEGORIES_BY_UI_LANG.get("en", {}))
        for key, label in lang_dict.items():
            self.cmb_pos.addItem(label, key)
        form_layout.addWidget(self.cmb_pos)

        # Örnek Cümle
        lbl_ex = QLabel(ui_text('Example Sentence', self.lang))
        lbl_ex.setStyleSheet(label_style)
        form_layout.addWidget(lbl_ex)
        self.input_example = QLineEdit()
        self.input_example.setStyleSheet(input_style)
        form_layout.addWidget(self.input_example)

        # Örnek Çeviri
        lbl_ex_tr = QLabel(ui_text('Example Translation:', self.lang))
        lbl_ex_tr.setStyleSheet(label_style)
        form_layout.addWidget(lbl_ex_tr)
        self.input_example_tr = QLineEdit()
        self.input_example_tr.setStyleSheet(input_style)
        form_layout.addWidget(self.input_example_tr)

        # Fonetik
        lbl_phonetic = QLabel(ui_text('Phonetic Pronunciation:', self.lang))
        lbl_phonetic.setStyleSheet(label_style)
        form_layout.addWidget(lbl_phonetic)
        self.input_phonetic = QLineEdit()
        self.input_phonetic.setStyleSheet(input_style)
        form_layout.addWidget(self.input_phonetic)

        # Notlar
        lbl_notes = QLabel(ui_text('Additional Notes:', self.lang))
        lbl_notes.setStyleSheet(label_style)
        form_layout.addWidget(lbl_notes)
        self.input_notes = QLineEdit()
        self.input_notes.setStyleSheet(input_style)
        form_layout.addWidget(self.input_notes)

        scroll.setWidget(form_widget)
        scroll.setFixedHeight(380)
        c_layout.addWidget(scroll)

        # ---------------- 3. BUTONLAR ----------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        btn_cancel = QPushButton(ui_text('Cancel', self.lang))
        btn_cancel.setFixedSize(90, 36)
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

        btn_save = QPushButton(ui_text('Save Changes', self.lang))
        btn_save.setFixedHeight(36)
        btn_save.setMinimumWidth(150)
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        c_layout.addLayout(btn_row)

        main_layout.addWidget(container)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _load_card_data(self):
        decks = get_all_decks()
        self.cmb_deck.clear()
        for d in decks:
            self.cmb_deck.addItem(d["name"], d["id"])

        card = get_card(self.card_id)
        if not card:
            return

        # Deste seçimi
        for i in range(self.cmb_deck.count()):
            if self.cmb_deck.itemData(i) == card["deck_id"]:
                self.cmb_deck.setCurrentIndex(i)
                break

        self.input_term.setText(card.get("term", ""))
        self.input_def.setText(card.get("definition", ""))
        source_lang = get_language_name(card.get("source_lang") or "en", self.lang)
        s_idx = self.cmb_source_lang.findText(source_lang)
        if s_idx >= 0:
            self.cmb_source_lang.setCurrentIndex(s_idx)
        else:
            self.cmb_source_lang.setEditText(source_lang)

        target_lang = get_language_name(card.get("target_lang") or "tr", self.lang)
        idx = self.cmb_target_lang.findText(target_lang)
        if idx >= 0:
            self.cmb_target_lang.setCurrentIndex(idx)
        else:
            self.cmb_target_lang.setEditText(target_lang)
        pos_val = card.get("part_of_speech", "")
        pos_key = next((key for labels in CATEGORIES_BY_UI_LANG.values()
                        for key, label in labels.items()
                        if pos_val.casefold() in (key.casefold(), label.casefold())), pos_val)
        pos_idx = self.cmb_pos.findData(pos_key)
        if pos_idx >= 0:
            self.cmb_pos.setCurrentIndex(pos_idx)
        else:
            if pos_val:
                self.cmb_pos.addItem(ui_text(pos_val, self.lang), pos_key)
                self.cmb_pos.setCurrentText(pos_val)
        self.input_example.setText(card.get("example_sentence", ""))
        self.input_example_tr.setText(card.get("example_translation", ""))
        self.input_phonetic.setText(card.get("phonetic", ""))
        self.input_notes.setText(card.get("notes", ""))

    def _save(self):
        term = self.input_term.text().strip()
        definition = self.input_def.text().strip()
        deck_id = self.cmb_deck.currentData()

        if not term or not definition:
            QMessageBox.warning(
                self,
                ui_text('Error', self.lang),
                ui_text('Term and Definition cannot be empty.', self.lang)
            )
            return

        source_lang = get_language_code(self.cmb_source_lang.currentText().strip() or "en")
        target_lang = get_language_code(self.cmb_target_lang.currentText().strip() or "tr")
        update_card(
            self.card_id,
            deck_id,
            term,
            definition,
            self.cmb_pos.currentData() or self.cmb_pos.currentText(),
            self.input_example.text().strip(),
            self.input_example_tr.text().strip(),
            self.input_phonetic.text().strip(),
            self.input_notes.text().strip(),
            target_lang=target_lang,
            source_lang=source_lang
        )
        self.accept()
