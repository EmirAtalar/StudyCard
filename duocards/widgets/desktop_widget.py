"""
Study Card - Masaüstü Mini Widget (Floating Desktop Widget)
Kullanıcının masaüstünde diğer pencerelerin üzerinde yüzen, pürüzsüz sürüklenebilir kompakt çalışma aracı.
Wayland ve X11 uyumlu sürükleme sistemi, klavye kısayolları ve sesli telaffuz desteği.
"""

import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QEvent, QTimer
from PyQt6.QtGui import QCursor, QKeyEvent
from duocards.db import get_study_cards, get_all_cards, get_all_decks, get_distinct_target_languages
from duocards.languages import get_language_name, detect_card_term_language
from duocards.icons import get_icon
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.i18n import t
from duocards.kwin_helper import set_kwin_keep_above
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QComboBox


class MiniWidgetSettingsDialog(QDialog):
    """
    Masaüstü Mini Widget için Deste Grubu ve Dil Filtresi ayar penceresi.
    """
    def __init__(self, current_deck_id=None, current_lang_filter=None, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "en")
        self.selected_deck_id = current_deck_id
        self.selected_lang = current_lang_filter

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(320, 240)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1.5px solid #10b981;
                border-radius: 14px;
            }
        """)
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(16, 14, 16, 14)
        p_layout.setSpacing(10)

        # Başlık ve Kapat Butonu
        h_row = QHBoxLayout()
        lbl_title = QLabel(t("mini_filter_title", self.lang))
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #10b981; background: transparent; border: none;")
        btn_close = QPushButton("X")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 11px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.reject)
        h_row.addWidget(lbl_title)
        h_row.addStretch()
        h_row.addWidget(btn_close)
        p_layout.addLayout(h_row)

        # 1. Deste Grubu Seçimi
        lbl_deck = QLabel(t("mini_filter_deck", self.lang))
        lbl_deck.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; background: transparent; border: none;")
        p_layout.addWidget(lbl_deck)

        self.cmb_deck = QComboBox()
        self.cmb_deck.setFixedHeight(34)
        self.cmb_deck.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.cmb_deck.addItem(t("mini_filter_all_decks", self.lang), None)
        decks = get_all_decks()
        card_word = ui_text('cards', self.lang)
        for d in decks:
            count = d.get('total_cards', d.get('card_count', 0))
            self.cmb_deck.addItem(f"{d['name']} ({count} {card_word})", d['id'])

        idx = self.cmb_deck.findData(self.selected_deck_id)
        if idx >= 0:
            self.cmb_deck.setCurrentIndex(idx)
        p_layout.addWidget(self.cmb_deck)

        # 2. Hedef Dil Filtresi
        lbl_lang = QLabel(t("mini_filter_lang", self.lang))
        lbl_lang.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; background: transparent; border: none;")
        p_layout.addWidget(lbl_lang)

        self.cmb_lang = QComboBox()
        self.cmb_lang.setFixedHeight(34)
        self.cmb_lang.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.cmb_lang.addItem(t("mini_filter_all_langs", self.lang), None)
        target_langs = get_distinct_target_languages()
        for tl in target_langs:
            display_name = get_language_name(tl, self.lang)
            self.cmb_lang.addItem(display_name, tl)

        idx_l = self.cmb_lang.findData(self.selected_lang)
        if idx_l >= 0:
            self.cmb_lang.setCurrentIndex(idx_l)
        p_layout.addWidget(self.cmb_lang)

        p_layout.addStretch()

        # Butonlar
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton(t("btn_cancel", self.lang))
        btn_cancel.setFixedHeight(32)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_apply = QPushButton(t("btn_apply", self.lang))
        btn_apply.setFixedHeight(32)
        btn_apply.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_apply.clicked.connect(self._on_apply)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_apply)
        p_layout.addLayout(btn_row)

        root.addWidget(panel)

    def _on_apply(self):
        self.selected_deck_id = self.cmb_deck.currentData()
        self.selected_lang = self.cmb_lang.currentData()
        self.accept()


class DraggableCardFrame(QFrame):
    """
    Tıklanıldığında ana pencerenin masaüstünde sürüklenmesini sağlayan zemin çerçevesi.
    """
    def __init__(self, parent_widget, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.parent_widget.windowHandle()
            if handle and handle.startSystemMove():
                self.parent_widget._drag_pos = None
                event.accept()
                return
            self.parent_widget._drag_pos = event.globalPosition().toPoint() - self.parent_widget.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self.parent_widget, "_drag_pos", None) is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.parent_widget.move(event.globalPosition().toPoint() - self.parent_widget._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.parent_widget._drag_pos = None
        super().mouseReleaseEvent(event)


class DesktopMiniWidget(QWidget):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(None)  # Bağımsız masaüstü penceresi
        self.lang = settings.get("ui_language", "en")
        
        # Pencere bayrakları: bağımsız pencere, çerçevesiz, tüm sekmelerin ve pencerelerin her zaman üstünde
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(360, 230)
        self.setMinimumSize(320, 200)
        self.setWindowTitle("Study Card Mini")
        self.setObjectName("studyCardMiniWidget")
        self._drag_pos = None

        self.selected_deck_id = settings.get("mini_widget_deck_id", None)
        self.selected_lang = settings.get("mini_widget_lang", None)

        self.cards = []
        self.current_idx = 0
        self.is_flipped = False

        self._setup_ui()
        self.reload_cards()

        # Sekmeler ve pencereler arasında her zaman en üstte kalma güvencesi
        set_kwin_keep_above("Study Card Mini", True)
        self._top_timer = QTimer(self)
        self._top_timer.setInterval(1000)
        self._top_timer.timeout.connect(self._keep_on_top)
        self._top_timer.start()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)

        # Kart Zemin Çerçevesi (Sürüklenebilir)
        self.card_frame = DraggableCardFrame(self, self)
        self.card_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1.5px solid rgba(16, 185, 129, 0.45);
                border-radius: 16px;
            }
        """)
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(16, 12, 16, 14)
        card_layout.setSpacing(8)

        # ---------------- ÜST ÇUBUK (Sürükleme Tutamacı, Başlık, Ayarlar, Sayaç ve Kapat) ----------------
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        # Sürükleme Tutamaç Simgesi
        self.lbl_grip = QLabel("⠿")
        self.lbl_grip.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.lbl_grip.setStyleSheet("font-size: 14px; font-weight: 900; color: #10b981; background: transparent; border: none;")
        self.lbl_grip.setToolTip(ui_text('Click & drag to move', self.lang))

        self.lbl_title = QLabel("Study Card Mini")
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #94a3b8; background: transparent; border: none;")

        # Yeşil Ayarlar / Filtre Simgesi (Mavi sayacın solunda)
        self.btn_settings = QPushButton()
        self.btn_settings.setFixedSize(22, 22)
        self.btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings.setIcon(get_icon("settings", 14))
        self.btn_settings.setToolTip(t("mini_filter_title", self.lang))
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
            }
        """)
        self.btn_settings.clicked.connect(self._open_settings_dialog)

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8; background: transparent; border: none;")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 12px;
                font-weight: bold;
                border-radius: 11px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.close)

        header_bar.addWidget(self.lbl_grip)
        header_bar.addWidget(self.lbl_title)
        header_bar.addStretch()
        header_bar.addWidget(self.btn_settings)
        header_bar.addWidget(self.lbl_counter)
        header_bar.addWidget(btn_close)
        card_layout.addLayout(header_bar)

        # ---------------- ORTA ALAN (Kelime, Fonetik ve Çevrilen Anlam) ----------------
        body_container = QWidget()
        body_container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        body_layout = QVBoxLayout(body_container)
        body_layout.setContentsMargins(0, 4, 0, 4)
        body_layout.setSpacing(4)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_term = QLabel(ui_text('Loading...', self.lang))
        self.lbl_term.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_term.setWordWrap(True)
        self.lbl_term.setStyleSheet("font-size: 22px; font-weight: 900; color: #ffffff; background: transparent; border: none;")
        self.lbl_term.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        body_layout.addWidget(self.lbl_term)

        self.lbl_phonetic = QLabel("")
        self.lbl_phonetic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_phonetic.setStyleSheet("font-size: 12px; font-style: italic; color: #94a3b8; background: transparent; border: none;")
        self.lbl_phonetic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        body_layout.addWidget(self.lbl_phonetic)

        self.lbl_def = QLabel("")
        self.lbl_def.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_def.setWordWrap(True)
        self.lbl_def.setStyleSheet("font-size: 15px; font-weight: 700; color: #34d399; background: transparent; border: none; margin-top: 4px;")
        self.lbl_def.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.lbl_def.setVisible(False)
        body_layout.addWidget(self.lbl_def)

        # Gövdeye tıklanınca da kart çevrilsin
        body_container.mousePressEvent = lambda e: self._toggle_flip() if e.button() == Qt.MouseButton.LeftButton else None

        card_layout.addWidget(body_container, 1)

        # ---------------- ALT BUTONLAR (Önceki, Ses, Çevir, Sonraki) ----------------
        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(34, 30)
        self.btn_prev.setToolTip(ui_text('Previous Card (A / ←)', self.lang))
        self.btn_prev.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.btn_prev.clicked.connect(self._prev_card)

        self.btn_audio = QPushButton(t("listen", self.lang))
        self.btn_audio.setFixedHeight(30)
        self.btn_audio.setMinimumWidth(54)
        self.btn_audio.setToolTip(ui_text('Listen to Pronunciation (S)', self.lang))
        self.btn_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_audio.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #38bdf8;
            }
        """)
        self.btn_audio.clicked.connect(self._play_audio)

        self.btn_flip = QPushButton(ui_text('Flip (W)', self.lang))
        self.btn_flip.setFixedHeight(30)
        self.btn_flip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_flip.setToolTip(ui_text('Flip Card (W / Space)', self.lang))
        self.btn_flip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_flip.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 12px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_flip.clicked.connect(self._toggle_flip)

        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(34, 30)
        self.btn_next.setToolTip(ui_text('Next Card (D / →)', self.lang))
        self.btn_next.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.btn_next.clicked.connect(self._next_card)

        nav_row.addWidget(self.btn_prev)
        nav_row.addWidget(self.btn_audio)
        nav_row.addWidget(self.btn_flip, 1)
        nav_row.addWidget(self.btn_next)
        card_layout.addLayout(nav_row)

        root_layout.addWidget(self.card_frame)

    def _open_settings_dialog(self):
        sfx.play_click()
        dlg = MiniWidgetSettingsDialog(
            current_deck_id=self.selected_deck_id,
            current_lang_filter=self.selected_lang,
            parent=self
        )
        dlg.move(self.x() + 20, self.y() + 10)
        if dlg.exec():
            self.selected_deck_id = dlg.selected_deck_id
            self.selected_lang = dlg.selected_lang
            settings.set("mini_widget_deck_id", self.selected_deck_id)
            settings.set("mini_widget_lang", self.selected_lang)
            settings.save()
            self.reload_cards()

    def reload_cards(self):
        # Seçilen deste ve dil filtresine göre kartları yükle
        deck_id = self.selected_deck_id
        target_lang = self.selected_lang
        cards = get_study_cards(deck_id=deck_id, limit=50, practice_mode=True, target_lang=target_lang)
        if not cards:
            cards = get_all_cards(deck_id=deck_id, target_lang=target_lang)
        self.cards = cards
        self.current_idx = 0
        self._load_current_card()

    def _load_current_card(self):
        if not self.cards:
            self.lbl_term.setText(ui_text('No cards yet', self.lang))
            self.lbl_phonetic.setText("")
            self.lbl_def.setText(ui_text('Add cards in library', self.lang))
            self.lbl_def.setVisible(True)
            self.lbl_counter.setText("0 / 0")
            return

        total = len(self.cards)
        self.current_idx = max(0, min(self.current_idx, total - 1))
        card = self.cards[self.current_idx]

        self.lbl_term.setText(card.get("term", ""))
        phonetic = card.get("phonetic", "")
        self.lbl_phonetic.setText(f"/{phonetic}/" if phonetic else "")
        self.lbl_phonetic.setVisible(bool(phonetic))

        self.lbl_def.setText(card.get("definition", ""))
        self.is_flipped = False
        self.lbl_def.setVisible(False)
        self.btn_flip.setText(ui_text('Flip (W / Space)', self.lang))
        self.lbl_counter.setText(f"{self.current_idx + 1} / {total}")

        # Otomatik telaffuz: Kelime ilk çıktığında (ön yüzde)
        if settings.get("auto_pronounce", False) and settings.get("pronounce_trigger", "flip") in ("appear", "both"):
            QTimer.singleShot(250, self._play_audio)

    def _toggle_flip(self):
        if not self.cards:
            return
        sfx.play_flip()
        self.is_flipped = not self.is_flipped
        self.lbl_def.setVisible(self.is_flipped)
        self.btn_flip.setText(ui_text('Front Side (W)' if self.is_flipped else 'Flip (W / Space)', self.lang))
        
        # Otomatik seslendirme ayarı açıksa (kart çevrildiğinde veya her ikisinde)
        if self.is_flipped and settings.get("auto_pronounce", False):
            if settings.get("pronounce_trigger", "flip") in ("flip", "both"):
                self._play_audio()

    def _play_audio(self):
        if self.cards and self.current_idx < len(self.cards):
            card = self.cards[self.current_idx]
            sfx.play_click()
            lang = detect_card_term_language(card)
            audio_player.play_pronunciation(card.get("term", ""), lang=lang)

    def _next_card(self):
        if not self.cards:
            return
        sfx.play_click()
        self.current_idx = (self.current_idx + 1) % len(self.cards)
        self._load_current_card()

    def _prev_card(self):
        if not self.cards:
            return
        sfx.play_click()
        self.current_idx = (self.current_idx - 1) % len(self.cards)
        self._load_current_card()

    # ---------------- KLAVYE KISAYOLLARI (W: Çevir, A: Önceki, S: Dinle, D: Sonraki) ----------------
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_W):
            self._toggle_flip()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self._next_card()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self._prev_card()
        elif key == Qt.Key.Key_S:
            self._play_audio()
        elif key == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # ---------------- SÜRÜKLEME ETKİLEŞİMİ ----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            if handle and handle.startSystemMove():
                self._drag_pos = None
                event.accept()
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _keep_on_top(self):
        if self.isVisible():
            self.raise_()

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange:
            if self.isVisible():
                self.raise_()
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        set_kwin_keep_above("Study Card Mini", True)

    def update_language(self, lang: str):
        self.lang = lang
        self.btn_audio.setText(t("listen", lang))
        self.lbl_grip.setToolTip(ui_text('Click & drag to move', lang))
        if hasattr(self, "btn_settings"):
            self.btn_settings.setToolTip(t("mini_filter_title", lang))
        self._load_current_card()
        localize_tree(self,lang)

    def closeEvent(self, event):
        self._top_timer.stop()
        self.closed.emit()
        super().closeEvent(event)
