"""
DuoCards Desktop - Desteler Yönetim Ekranı
Desteleri görüntüleme, yeni deste ekleme ve desteye özel çalışma başlatma.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QMessageBox,
    QProgressBar, QDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor
from duocards.db import get_all_decks, add_deck, update_deck, delete_deck
from duocards.i18n import t
from duocards.settings import settings
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit


class DeckEditDialog(QDialog):
    def __init__(self, parent=None, title: str = "Yeni Deste", name: str = "", desc: str = "", is_create: bool = True, lang: str = "tr"):
        super().__init__(parent)
        self.lang = lang
        self.is_create = is_create
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(460)
        self._drag_pos = None

        self._setup_ui(title, name, desc)

    def _setup_ui(self, title_text: str, default_name: str, default_desc: str):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 20, 24, 22)
        c_layout.setSpacing(16)

        # Başlık ve Kapat Butonu
        header = QHBoxLayout()
        header.setSpacing(10)

        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #10b981; border: none; background: transparent;")
        header.addWidget(self.lbl_title, 1)

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
                background-color: #334155;
                color: #ffffff;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)
        c_layout.addLayout(header)

        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        # Deste Adı
        lbl_name = QLabel(ui_text('Deck Name *', self.lang))
        lbl_name.setStyleSheet("font-size: 12px; font-weight: 700; color: #cbd5e1; border: none; background: transparent;")
        form_layout.addWidget(lbl_name)

        self.input_name = QLineEdit(default_name)
        self.input_name.setPlaceholderText(ui_text('e.g. Daily Conversation, B2 Vocabulary...', self.lang))
        self.input_name.setFixedHeight(40)
        self.input_name.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1.5px solid #334155;
                border-radius: 10px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit:focus {
                border-color: #10b981;
            }
        """)
        form_layout.addWidget(self.input_name)

        # Açıklama
        lbl_desc = QLabel(ui_text('Description (Optional):', self.lang))
        lbl_desc.setStyleSheet("font-size: 12px; font-weight: 700; color: #cbd5e1; border: none; background: transparent;")
        form_layout.addWidget(lbl_desc)

        self.input_desc = QLineEdit(default_desc)
        self.input_desc.setPlaceholderText(ui_text('Short description about this deck...', self.lang))
        self.input_desc.setFixedHeight(40)
        self.input_desc.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1.5px solid #334155;
                border-radius: 10px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit:focus {
                border-color: #10b981;
            }
        """)
        form_layout.addWidget(self.input_desc)

        # Hata Mesajı
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        self.lbl_error.setVisible(False)
        form_layout.addWidget(self.lbl_error)

        c_layout.addLayout(form_layout)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton(t("btn_cancel", self.lang))
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
        btn_layout.addWidget(btn_cancel)

        save_txt = ui_text("Create" if self.is_create else "Save",self.lang)
        btn_save = QPushButton(save_txt)
        btn_save.setFixedSize(90, 36)
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_save.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(btn_save)

        c_layout.addLayout(btn_layout)
        main_layout.addWidget(container)

    def _validate_and_accept(self):
        name = self.input_name.text().strip()
        if not name:
            self.lbl_error.setText(ui_text('Deck name cannot be empty!', self.lang))
            self.lbl_error.setVisible(True)
            self.input_name.setFocus()
            return
        self.accept()

    def get_data(self):
        return self.input_name.text().strip(), self.input_desc.text().strip()

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


class DeckDeleteConfirmDialog(QDialog):
    def __init__(self, parent=None, deck_name: str = "", lang: str = "tr"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)
        self._setup_ui(deck_name)

    def _setup_ui(self, deck_name: str):
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

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_text = ui_text('Delete Deck', self.lang)
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

        msg_text = (
            ui_text('Are you sure you want to delete <b>"{deck_name}"</b> and all cards inside it?<br><span style=\'color: #ef4444; font-size: 12px; font-weight: 600;\'>This action cannot be undone!</span>', self.lang, **{'deck_name': deck_name})
        )
        lbl_msg = QLabel(msg_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.4; border: none; background: transparent;")
        layout.addWidget(lbl_msg)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton(t("btn_cancel", self.lang))
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

        btn_delete = QPushButton(t("btn_delete", self.lang))
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


class DeckCardWidget(QFrame):
    study_requested = pyqtSignal(int)
    edit_requested = pyqtSignal(dict)
    delete_requested = pyqtSignal(int, str)

    def __init__(self, deck: dict, lang: str = "tr", parent=None):
        super().__init__(parent)
        self.deck = deck
        self.lang = lang
        self.setMinimumWidth(280)
        self.setStyleSheet("""
            DeckCardWidget {
                background-color: #162032;
                border: none;
                border-radius: 14px;
            }
            DeckCardWidget:hover {
                background-color: #1a273e;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Üst Satır: İsim + Tekrar Sayısı
        top_row = QHBoxLayout()

        lbl_name = QLabel(self.deck["name"])
        lbl_name.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        lbl_name.setWordWrap(True)

        top_row.addWidget(lbl_name, 1)

        due_count = self.deck.get("due_cards", 0)
        if due_count > 0:
            lbl_due = QLabel(t("deck_reps", self.lang, count=due_count))
            lbl_due.setStyleSheet("""
                background-color: #7f1d1d;
                color: #fca5a5;
                font-weight: 700;
                font-size: 11px;
                border-radius: 6px;
                padding: 3px 8px;
            """)
            top_row.addWidget(lbl_due)

        layout.addLayout(top_row)

        # Açıklama
        desc = self.deck.get("description", "")
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("font-size: 12px; color: #94a3b8;")
            layout.addWidget(lbl_desc)

        # İlerleme (Mastered / Total)
        total = self.deck.get("total_cards", 0)
        mastered = self.deck.get("mastered_cards", 0)
        pct = int((mastered / total * 100)) if total > 0 else 0

        info_row = QHBoxLayout()
        lbl_total = QLabel(t("deck_total_info", self.lang, total=total, mastered=mastered))
        lbl_total.setStyleSheet("font-size: 11px; color: #cbd5e1;")
        info_row.addWidget(lbl_total)
        info_row.addStretch()
        lbl_pct = QLabel(f"%{pct}")
        lbl_pct.setStyleSheet("font-size: 11px; font-weight: 700; color: #10b981;")
        info_row.addWidget(lbl_pct)
        layout.addLayout(info_row)

        bar = QProgressBar()
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setValue(pct)
        layout.addWidget(bar)

        # Butonlar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_study = QPushButton(t("btn_study_deck", self.lang))
        btn_study.setProperty("class", "btn-primary")
        btn_study.clicked.connect(lambda: self.study_requested.emit(self.deck["id"]))

        btn_edit = QPushButton(t("btn_edit", self.lang))
        btn_edit.setFixedHeight(34)
        btn_edit.setProperty("class", "btn-secondary")
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.deck))

        btn_del = QPushButton(t("btn_delete", self.lang))
        btn_del.setFixedHeight(34)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: #3f1a1a;
                color: #f87171;
                border: none;
                border-radius: 8px;
                padding: 4px 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                color: #ffffff;
            }
        """)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.deck["id"], self.deck["name"]))

        btn_row.addWidget(btn_study, 1)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        layout.addLayout(btn_row)


class DecksView(QWidget):
    request_study_deck = pyqtSignal(int)
    decks_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(14)

        # Başlık ve Yeni Deste Butonu
        header = QHBoxLayout()
        col_title = QVBoxLayout()
        self.lbl_title = QLabel(t("decks_title", self.lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("decks_subtitle", self.lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        col_title.addWidget(self.lbl_title)
        col_title.addWidget(self.lbl_subtitle)
        header.addLayout(col_title)

        header.addStretch()

        self.btn_new_deck = QPushButton(t("btn_create_deck", self.lang))
        self.btn_new_deck.setProperty("class", "btn-primary")
        self.btn_new_deck.setFixedHeight(42)
        self.btn_new_deck.clicked.connect(self._create_deck)
        header.addWidget(self.btn_new_deck)

        layout.addLayout(header)

        # Desteler Grid Scroll Alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(t("decks_title", lang))
        self.lbl_subtitle.setText(t("decks_subtitle", lang))
        self.btn_new_deck.setText(t("btn_create_deck", lang))
        self.reload_decks()
        localize_tree(self,lang)

    def reload_decks(self):
        # Önceki bileşenleri temizle
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        decks = get_all_decks()
        cols = 2
        for idx, deck in enumerate(decks):
            row = idx // cols
            col = idx % cols
            card = DeckCardWidget(deck, lang=self.lang)
            card.study_requested.connect(self.request_study_deck)
            card.edit_requested.connect(self._edit_deck)
            card.delete_requested.connect(self._delete_deck)
            self.grid_layout.addWidget(card, row, col)

    def _create_deck(self):
        title = ui_text('Create New Deck', self.lang)
        dlg = DeckEditDialog(self, title=title, is_create=True, lang=self.lang)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc = dlg.get_data()
            if name:
                add_deck(name, desc)
                self.reload_decks()
                self.decks_changed.emit()

    def _edit_deck(self, deck: dict):
        title = ui_text('Edit Deck', self.lang)
        dlg = DeckEditDialog(
            self, title=title, name=deck.get("name", ""),
            desc=deck.get("description", ""), is_create=False, lang=self.lang
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc = dlg.get_data()
            if name:
                update_deck(deck["id"], name, desc)
                self.reload_decks()
                self.decks_changed.emit()

    def _delete_deck(self, deck_id: int, deck_name: str):
        dlg = DeckDeleteConfirmDialog(self, deck_name=deck_name, lang=self.lang)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            delete_deck(deck_id)
            self.reload_decks()
            self.decks_changed.emit()
