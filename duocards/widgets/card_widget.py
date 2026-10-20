"""
Study Card - Flashcard Component Widget
Kartın Ön ve Arka yüzünü modern, ferah, akıllı ipuçlu ve çok modlu olarak gösterir.
- 3D Yumuşak Çevirme Animasyonu
- Akıllı Hafıza İpucu (Mnemonic / Harf ve Bağlam İpucu - 'H' kısayolu)
- Aktif Hatırlama & Yazarak Pekiştirme Kutusu (Type-In Practice - 'W' modu)
- Cümlede Hedef Kelime Vurgulama & Örnek Cümleyi Seslendirme ('C' kısayolu)
- Ters Çevirme (Anlam ➔ Kelime Üretici Hatırlama - 'R' modu)
- Tek Tıkla Yıldızlama / Favoriye Ekleme ('F' kısayolu)
"""

import re
from duocards.languages import get_language_name, get_language_code
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QCursor
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.i18n import t
from duocards.languages import detect_card_term_language
from duocards.icons import get_icon
from duocards.sentence_memory import ensure_examples,card_language
from duocards.content_rules import useful_sentence
from duocards.db import toggle_card_favorite
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit


def highlight_target_word(sentence: str, term: str) -> str:
    """Örnek cümle içerisindeki hedef kelimeyi veya kökünü belirgin ve şık biçimde vurgular."""
    if not sentence or not term:
        return sentence
    clean_term = term.strip()
    pattern = re.compile(rf'\b({re.escape(clean_term)})\b', re.IGNORECASE)
    if pattern.search(sentence):
        return pattern.sub(
            r'<span style="color: #38bdf8; font-weight: 800; background-color: rgba(56, 189, 248, 0.16); padding: 1px 6px; border-radius: 5px;">\1</span>',
            sentence
        )
    # Kök eşleştirme (uzun kelimeler için çekim eklerini tolere et)
    if len(clean_term) >= 4:
        stem = clean_term[:max(4, len(clean_term) - 2)]
        pattern_stem = re.compile(rf'\b({re.escape(stem)}\w*)\b', re.IGNORECASE)
        if pattern_stem.search(sentence):
            return pattern_stem.sub(
                r'<span style="color: #38bdf8; font-weight: 800; background-color: rgba(56, 189, 248, 0.16); padding: 1px 6px; border-radius: 5px;">\1</span>',
                sentence
            )
    return sentence


class FlashcardWidget(QFrame):
    flipped = pyqtSignal(bool)
    card_clicked = pyqtSignal()
    favorite_toggled = pyqtSignal(int, bool)
    active_recall_tested = pyqtSignal(bool)

    def __init__(self, parent=None, is_preview=False):
        super().__init__(parent)
        self.setObjectName("studyFlashcard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.is_preview = is_preview
        self.lang = settings.get("ui_language", "tr")

        if is_preview:
            self.setMinimumWidth(320)
            self.setMaximumWidth(700)
            self.setMinimumHeight(280)
        else:
            self.setMinimumWidth(680)
            self.setMaximumWidth(900)
            self.setMinimumHeight(400)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        self._card_data = None
        self._is_back_showing = False
        self._is_animating = False
        self._target_min_width = 680 if not is_preview else 320
        self._target_max_width = 900 if not is_preview else 700

        self.reverse_mode = False       # True: Türkçe Anlam ➔ Hedef Kelime
        self.type_in_enabled = False    # True: Aktif klavye yazım kutusu aktif
        self._user_typed_text = ""      # Kullanıcının klavyeyle yazdığı cevap
        self._last_sentence_en = ""
        self._audio_request = None
        self._last_audio_state = 'idle'

        self._setup_ui()
        audio_player.request_state_changed.connect(self._audio_state)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 22, 28, 22)
        self.main_layout.setSpacing(12)

        # ---------------- 1. ÜST ROZETLER & FAVORİ BUTONU ----------------
        self.top_badges_layout = QHBoxLayout()
        self.top_badges_layout.setSpacing(8)

        self.lbl_deck_badge = QLabel(ui_text('Deck', self.lang))
        self.lbl_deck_badge.setStyleSheet("""
            background-color: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            border: none;
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
        """)

        self.lbl_pos_badge = QLabel(ui_text('Word', self.lang))
        self.lbl_pos_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pos_badge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lbl_pos_badge.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #6ee7b7;
            border: none;
            border-radius: 10px;
            padding: 4px 14px;
            font-size: 11px;
            font-weight: 700;
        """)

        self.lbl_mistake_badge = QLabel("")
        self.lbl_mistake_badge.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 800;
        """)
        self.lbl_mistake_badge.setVisible(False)

        self.lbl_lang_badge = QLabel(ui_text('Turkish', self.lang))
        self.lbl_lang_badge.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.15);
            color: #7dd3fc;
            border: none;
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
        """)

        self.lbl_status_badge = QLabel(ui_text('New', self.lang))
        self.lbl_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status_badge.setMinimumWidth(100)
        self.lbl_status_badge.setStyleSheet("""
            background-color: rgba(148, 163, 184, 0.15);
            color: #cbd5e1;
            border: none;
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
        """)

        # Yıldız / Favori Butonu
        self.btn_favorite = QPushButton()
        self.btn_favorite.setFixedSize(32, 32)
        self.btn_favorite.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_favorite.setIcon(get_icon("star", 18))
        self.btn_favorite.setToolTip(ui_text('Add to Favorites (F)', self.lang))
        self.btn_favorite.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(245, 158, 11, 0.2);
                border-color: #f59e0b;
            }
        """)
        self.btn_favorite.clicked.connect(self.toggle_favorite)

        self.top_badges_layout.addWidget(self.lbl_deck_badge)
        self.top_badges_layout.addWidget(self.lbl_pos_badge, 1)
        self.top_badges_layout.addWidget(self.lbl_mistake_badge)
        self.top_badges_layout.addWidget(self.lbl_lang_badge)
        self.top_badges_layout.addWidget(self.lbl_status_badge)
        self.top_badges_layout.addWidget(self.btn_favorite)
        self.main_layout.addLayout(self.top_badges_layout)

        # ---------------- 2. ORTA BÖLÜM: TERİM / ANLAM & AKSİYONLAR ----------------
        self.term_container = QVBoxLayout()
        self.term_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.term_container.setSpacing(8)

        self.lbl_term = QLabel("")
        self.lbl_term.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_term.setWordWrap(True)
        self.lbl_term.setStyleSheet("""
            font-size: 34px;
            font-weight: 900;
            color: #ffffff;
            background: transparent;
            margin: 4px 0;
            letter-spacing: -0.3px;
        """)
        self.term_container.addWidget(self.lbl_term)

        # Fonetik ve Telaffuz Butonu
        self.phonetic_layout = QHBoxLayout()
        self.phonetic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phonetic_layout.setSpacing(10)

        self.lbl_phonetic = QLabel("")
        self.lbl_phonetic.setStyleSheet("""
            font-size: 14px;
            color: #94a3b8;
            font-style: italic;
            background: transparent;
        """)

        self.btn_audio = QPushButton(t("listen", self.lang))
        self.btn_audio.setIcon(get_icon("volume", 16))
        self.btn_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_audio.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                color: #e2e8f0;
                border-radius: 12px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
                border-color: #10b981;
            }
        """)
        self.btn_audio.clicked.connect(self._play_audio)

        self.phonetic_layout.addWidget(self.lbl_phonetic)
        self.phonetic_layout.addWidget(self.btn_audio)
        self.term_container.addLayout(self.phonetic_layout)
        self.lbl_audio_status = QLabel()
        self.lbl_audio_status.setWordWrap(True)
        self.lbl_audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_audio_status.setStyleSheet('color: #94a3b8; font-size: 12px; background: transparent;')
        self.lbl_audio_status.hide()
        self.term_container.addWidget(self.lbl_audio_status)

        # ---------------- AKTİF HATIRLAMA / YAZARAK ÇALIŞMA KUTUSU ----------------
        self.recall_frame = QFrame()
        self.recall_frame.setObjectName("recallFrame")
        self.recall_frame.setStyleSheet("background: transparent;")
        recall_lay = QVBoxLayout(self.recall_frame)
        recall_lay.setContentsMargins(30, 4, 30, 4)
        recall_lay.setSpacing(6)

        self.input_recall = QLineEdit()
        self.input_recall.setFixedHeight(42)
        self.input_recall.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_recall.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1.5px solid #334155;
                border-radius: 12px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                padding: 0 16px;
            }
            QLineEdit:focus {
                border-color: #38bdf8;
                background-color: #131d33;
            }
        """)
        self.input_recall.returnPressed.connect(self._submit_type_in)
        recall_lay.addWidget(self.input_recall)
        self.recall_frame.setVisible(False)
        self.term_container.addWidget(self.recall_frame)

        self.main_layout.addLayout(self.term_container)

        # ---------------- KULLANICININ YAZDIĞI CEVAP BÖLÜMÜ (ARKA YÜZ) ----------------
        self.user_answer_frame = QFrame()
        self.user_answer_frame.setObjectName("userAnswerFrame")
        self.user_answer_frame.setStyleSheet("""
            QFrame#userAnswerFrame {
                background: rgba(30, 41, 59, 0.85);
                border: 1px solid #38bdf8;
                border-radius: 12px;
            }
        """)
        user_ans_layout = QVBoxLayout(self.user_answer_frame)
        user_ans_layout.setContentsMargins(14, 8, 14, 8)
        user_ans_layout.setSpacing(2)

        self.lbl_user_typed = QLabel("")
        self.lbl_user_typed.setWordWrap(True)
        self.lbl_user_typed.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_user_typed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_user_typed.setStyleSheet("font-size: 14px; background: transparent;")
        user_ans_layout.addWidget(self.lbl_user_typed)
        self.user_answer_frame.setVisible(False)
        self.main_layout.addWidget(self.user_answer_frame)

        # ---------------- 3. ANLAM BÖLÜMÜ (ARKA YÜZ) ----------------
        self.definition_frame = QFrame()
        self.definition_frame.setObjectName("definitionFrame")
        self.definition_frame.setStyleSheet("""
            QFrame#definitionFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(16, 185, 129, 0.14), stop:1 rgba(16, 185, 129, 0.03));
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-radius: 16px;
            }
        """)
        def_layout = QVBoxLayout(self.definition_frame)
        def_layout.setContentsMargins(18, 14, 18, 14)
        def_layout.setSpacing(4)

        self.lbl_definition_title = QLabel(t("turkish_meaning", self.lang))
        self.lbl_definition_title.setStyleSheet("""
            font-size: 11px;
            font-weight: 900;
            color: #34d399;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            background: transparent;
        """)

        self.lbl_definition = QLabel("")
        self.lbl_definition.setWordWrap(True)
        self.lbl_definition.setStyleSheet("""
            font-size: 21px;
            font-weight: 700;
            color: #f8fafc;
            background: transparent;
            line-height: 1.35;
        """)

        def_layout.addWidget(self.lbl_definition_title)
        def_layout.addWidget(self.lbl_definition)
        self.main_layout.addWidget(self.definition_frame)

        # ---------------- 4. ÖRNEK CÜMLE BÖLÜMÜ ----------------
        self.example_frame = QFrame()
        self.example_frame.setObjectName("exampleFrame")
        self.example_frame.setStyleSheet("""
            QFrame#exampleFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)
        ex_layout = QVBoxLayout(self.example_frame)
        ex_layout.setContentsMargins(16, 12, 16, 12)
        ex_layout.setSpacing(6)

        ex_header = QHBoxLayout()
        lbl_ex_title = QLabel(ui_text('CONTEXT & EXAMPLE', self.lang))
        lbl_ex_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748b; letter-spacing: 1px; background: transparent;")
        ex_header.addWidget(lbl_ex_title)
        ex_header.addStretch()

        self.btn_sentence_audio = QPushButton(ui_text('🔊 Listen Sentence (C)', self.lang))
        self.btn_sentence_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sentence_audio.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 8px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.25);
                color: #ffffff;
            }
        """)
        self.btn_sentence_audio.clicked.connect(self.play_sentence_audio)
        ex_header.addWidget(self.btn_sentence_audio)
        ex_layout.addLayout(ex_header)

        self.lbl_example_en = QLabel("")
        self.lbl_example_en.setWordWrap(True)
        self.lbl_example_en.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_example_en.setStyleSheet("""
            font-size: 14px;
            color: #f1f5f9;
            font-weight: 500;
            line-height: 1.45;
            background: transparent;
        """)

        self.lbl_example_tr = QLabel("")
        self.lbl_example_tr.setWordWrap(True)
        self.lbl_example_tr.setStyleSheet("""
            font-size: 13px;
            color: #6ee7b7;
            font-style: italic;
            line-height: 1.4;
            background: transparent;
        """)

        ex_layout.addWidget(self.lbl_example_en)
        ex_layout.addWidget(self.lbl_example_tr)
        self.main_layout.addWidget(self.example_frame)

        # ---------------- 5. NOTLAR BÖLÜMÜ ----------------
        self.lbl_notes = QLabel("")
        self.lbl_notes.setWordWrap(True)
        self.lbl_notes.setStyleSheet("""
            font-size: 12px;
            color: #fde68a;
            background-color: rgba(245, 158, 11, 0.08);
            padding: 9px 14px;
            border-radius: 10px;
            border: 1px solid rgba(245, 158, 11, 0.22);
        """)
        self.main_layout.addWidget(self.lbl_notes)

        # ---------------- 6. ALT ÇEVİRME İPUCU ----------------
        self.lbl_flip_hint = QLabel(t("flip_hint", self.lang))
        self.lbl_flip_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_flip_hint.setStyleSheet("""
            font-size: 11px;
            color: #64748b;
            background: transparent;
            margin-top: 2px;
        """)
        self.main_layout.addWidget(self.lbl_flip_hint)

        self._update_face()

    def set_reverse_mode(self, reverse: bool):
        """Ters çalışma modunu (Anlam ➔ Kelime) ayarlar."""
        self.reverse_mode = reverse
        self._update_input_placeholder()
        if self._card_data:
            self._render_card_content()
            self._update_face()

    def set_type_in_enabled(self, enabled: bool):
        """Yazarak çalışma kutusunu gösterir/gizler."""
        self.type_in_enabled = enabled
        self.recall_frame.setVisible(enabled and not self._is_back_showing)
        if enabled and not self._is_back_showing:
            self.input_recall.clear()
            self._update_input_placeholder()
            self.input_recall.setFocus()

    def _update_input_placeholder(self):
        if self.reverse_mode:
            placeholder = ui_text('Type word... (Enter: Flip)', self.lang)
        else:
            placeholder = ui_text('Type meaning... (Enter: Flip)', self.lang)
        self.input_recall.setPlaceholderText(placeholder)

    def toggle_favorite(self):
        """Mevcut kartı favoriye ekler veya çıkarır."""
        if not self._card_data:
            return
        card_id = self._card_data["id"]
        new_state = toggle_card_favorite(card_id)
        self._card_data["is_favorite"] = 1 if new_state else 0
        self._update_favorite_icon(new_state)
        sfx.play_click()
        self.favorite_toggled.emit(card_id, new_state)

    def _update_favorite_icon(self, is_fav: bool):
        if is_fav:
            self.btn_favorite.setIcon(get_icon("star_filled", 18))
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: rgba(245, 158, 11, 0.25);
                    border: 1px solid #f59e0b;
                    border-radius: 8px;
                }
            """)
        else:
            self.btn_favorite.setIcon(get_icon("star", 18))
            self.btn_favorite.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: rgba(245, 158, 11, 0.2);
                    border-color: #f59e0b;
                }
            """)

    def update_language(self, lang: str):
        self.lang = lang
        self.btn_audio.setText(t("listen", lang))
        self.btn_sentence_audio.setText(ui_text('🔊 Listen Sentence (C)', lang))
        self.lbl_definition_title.setText(t("col_def", lang).upper())
        self.lbl_flip_hint.setText(t("flip_hint", lang))
        self._update_input_placeholder()
        if self._card_data:
            self._apply_badges(self._card_data)
        localize_tree(self,lang)

    def _apply_badges(self, card_data: dict):
        deck_name = card_data.get("deck_name", "General")
        pos = card_data.get("part_of_speech", "Kelime") or "Kelime"
        status = card_data.get("status", "new")

        self.lbl_deck_badge.setText(deck_name)
        self.lbl_pos_badge.setText(ui_text(pos,self.lang))

        target_lang = card_data.get("target_lang") or (ui_text('English', self.lang))
        self.lbl_lang_badge.setText(get_language_name(target_lang,self.lang))

        raw_status = {
            "new": t("status_new", self.lang),
            "learning": t("status_learning", self.lang),
            "mastered": t("status_mastered", self.lang)
        }.get(status, t("status_new", self.lang))
        self.lbl_status_badge.setText(raw_status)

        mistakes = card_data.get("mistake_count", 0)
        if mistakes and mistakes > 0:
            if self.lang == "tr":
                txt = f"⚠️ {mistakes} Hata"
            elif self.lang == "de":
                txt = f"⚠️ {mistakes} Fehler"
            elif self.lang == "es":
                txt = f"⚠️ {mistakes} Errores"
            else:
                txt = f"⚠️ {mistakes} Mistakes"
            self.lbl_mistake_badge.setText(txt)
            self.lbl_mistake_badge.setVisible(True)
        else:
            self.lbl_mistake_badge.setVisible(False)

        is_fav = bool(card_data.get("is_favorite", 0))
        self._update_favorite_icon(is_fav)

    def set_card(self, card_data: dict, allow_autoplay: bool = True):
        """Kart verisini yükler ve ön yüzünü hazırlar."""
        self._card_data = card_data
        self._audio_request = None
        self._last_audio_state = 'idle'
        self.lbl_audio_status.clear()
        self.lbl_audio_status.hide()
        self._is_back_showing = False
        self._user_typed_text = ""
        self.input_recall.clear()
        self.user_answer_frame.setVisible(False)
        self._update_input_placeholder()

        self._render_card_content()
        self._update_face()

        if self.type_in_enabled and not self._is_back_showing:
            self.input_recall.setFocus()

        # Otomatik telaffuz: Kelime çıktığında (ön yüzde) seslendir
        if allow_autoplay and self.isVisible() and settings.get("auto_pronounce", False) and settings.get("pronounce_trigger", "flip") in ("appear", "both"):
            QTimer.singleShot(250, lambda: self._autoplay_if_current(card_data))

    def _autoplay_if_current(self, card):
        if self.isVisible() and self._card_data is card:
            self._play_audio()

    def _render_card_content(self):
        if not self._card_data:
            return

        term = self._card_data.get("term", "")
        definition = self._card_data.get("definition", "")
        example_en = (self._card_data.get("example_sentence") or "").strip()
        example_tr = (self._card_data.get("example_translation") or "").strip()
        phonetic = self._card_data.get("phonetic", "") or ""
        notes = self._card_data.get("notes", "") or ""
        if not settings.get('show_phonetics', True):
            phonetic = ''
        if not settings.get('show_card_notes', True):
            notes = ''

        self._apply_badges(self._card_data)

        if example_en and not useful_sentence(term,example_en,card_language(self._card_data)):
            example_en=example_tr=''
        if not example_en and not self.is_preview:
            rows = ensure_examples(self._card_data)
            genuine = [row for row in rows if row['kind'] == 'example']
            if genuine:
                row = genuine[0]
                example_en = row['text']
                example_tr = row['translations'].get(get_language_code(self._card_data.get('target_lang','tr')), '')

        self._last_sentence_en = example_en

        # Ters Mod kontrolü
        if self.reverse_mode:
            # Ön Yüz: Anlam (Türkçe)
            self.lbl_term.setText(definition)
            self.lbl_term.setStyleSheet("""
                font-size: 26px;
                font-weight: 800;
                color: #6ee7b7;
                background: transparent;
                margin: 4px 0;
            """)
            self.lbl_phonetic.setVisible(False)
            self.btn_audio.setVisible(False)

            # Arka Yüz: Hedef Kelime
            self.lbl_definition_title.setText(ui_text('TARGET TERM', self.lang))
            self.lbl_definition.setText(f"{term}  {phonetic}")
        else:
            # Normal Mod: Hedef Kelime
            self.lbl_term.setText(term)
            self.lbl_term.setStyleSheet("""
                font-size: 34px;
                font-weight: 900;
                color: #ffffff;
                background: transparent;
                margin: 4px 0;
                letter-spacing: -0.3px;
            """)
            if phonetic:
                self.lbl_phonetic.setText(phonetic)
                self.lbl_phonetic.setVisible(True)
            else:
                self.lbl_phonetic.setVisible(False)
            self.btn_audio.setVisible(True)

            # Arka Yüz: Anlam
            self.lbl_definition_title.setText(t("turkish_meaning", self.lang))
            self.lbl_definition.setText(definition)

        # Örnek Cümle Hazırla (Hedef kelime vurgulanmış)
        if example_en:
            highlighted_en = highlight_target_word(example_en, term)
            self.lbl_example_en.setText(f"\"{highlighted_en}\"")
            self.lbl_example_tr.setText(example_tr if example_tr else "")
            self.example_frame.setVisible(True)
        else:
            self.example_frame.setVisible(False)

        # Notlar
        if notes:
            self.lbl_notes.setText(notes)
            self.lbl_notes.setVisible(True)
        else:
            self.lbl_notes.setVisible(False)

    def _submit_type_in(self):
        """Kullanıcının yazdığı metni kaydeder ve kartı çevirir (değerlendirme/puanlama olmadan)."""
        if not self._card_data or self._is_back_showing:
            return
        self._user_typed_text = self.input_recall.text().strip()
        self.flip(animated=True)

    def flip(self, animated=True):
        """Kartı 3D hissiyatlı animasyonla ve ses efektiyle çevirir."""
        animated = animated and not settings.get('reduced_motion', False)
        if self._is_animating:
            return

        if not self._is_back_showing and self.type_in_enabled:
            typed = self.input_recall.text().strip()
            if typed:
                self._user_typed_text = typed

        sfx.play_flip()

        if not animated:
            self._is_back_showing = not self._is_back_showing
            self._update_face()
            self.flipped.emit(self._is_back_showing)
            if self._is_back_showing and settings.get("auto_pronounce", False) and settings.get("pronounce_trigger", "flip") in ("flip", "both"):
                self._play_audio()
            return

        self._is_animating = True
        self.setMinimumWidth(0)
        current_w = self.width()

        self.anim_shrink = QPropertyAnimation(self, b"maximumWidth")
        self.anim_shrink.setDuration(110)
        self.anim_shrink.setStartValue(current_w)
        self.anim_shrink.setEndValue(10)
        self.anim_shrink.setEasingCurve(QEasingCurve.Type.InQuad)

        def on_halfway():
            self._is_back_showing = not self._is_back_showing
            self._update_face()
            self.flipped.emit(self._is_back_showing)

            self.anim_expand = QPropertyAnimation(self, b"maximumWidth")
            self.anim_expand.setDuration(140)
            self.anim_expand.setStartValue(10)
            self.anim_expand.setEndValue(self._target_max_width)
            self.anim_expand.setEasingCurve(QEasingCurve.Type.OutQuad)

            def on_finished():
                self._is_animating = False
                self.setMaximumWidth(self._target_max_width)
                self.setMinimumWidth(self._target_min_width)
                if self._is_back_showing and settings.get("auto_pronounce", False) and settings.get("pronounce_trigger", "flip") in ("flip", "both"):
                    self._play_audio()

            self.anim_expand.finished.connect(on_finished)
            self.anim_expand.start()

        self.anim_shrink.finished.connect(on_halfway)
        self.anim_shrink.start()

    def is_back_showing(self) -> bool:
        return self._is_back_showing

    def show_front(self):
        self._is_back_showing = False
        self._update_face()

    def _update_face(self):
        self.lbl_flip_hint.setText(t("flip_hint", self.lang))

        if not self._is_back_showing:
            # Ön Yüz
            self.user_answer_frame.setVisible(False)
            self.definition_frame.setVisible(False)
            self.example_frame.setVisible(False)
            self.lbl_notes.setVisible(False)
            self.lbl_flip_hint.setVisible(True)
            self.recall_frame.setVisible(self.type_in_enabled)
            self.setStyleSheet("""
                QFrame#studyFlashcard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #151e2e, stop:1 #0c121d);
                    border: 1.5px solid #233148;
                    border-radius: 20px;
                }
                QFrame#studyFlashcard:hover {
                    border-color: #38bdf8;
                }
            """)
        else:
            # Arka Yüz
            self.recall_frame.setVisible(False)
            self.lbl_flip_hint.setVisible(False)

            # Kullanıcının yazdığı cevap varsa göster
            if self._user_typed_text:
                prefix = ui_text('Your input:', self.lang)
                self.lbl_user_typed.setText(
                    f"<span style='color: #94a3b8; font-weight: 600;'>{prefix}</span> "
                    f"<span style='color: #38bdf8; font-weight: 800; font-size: 15px;'>{self._user_typed_text}</span>"
                )
                self.user_answer_frame.setVisible(True)
            else:
                self.user_answer_frame.setVisible(False)

            self.definition_frame.setVisible(True)
            if self._last_sentence_en:
                self.example_frame.setVisible(True)
            else:
                self.example_frame.setVisible(False)

            if self._card_data and self._card_data.get("notes"):
                self.lbl_notes.setVisible(True)
            self.setStyleSheet("""
                QFrame#studyFlashcard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #13242d, stop:1 #0c161d);
                    border: 1.5px solid rgba(16, 185, 129, 0.65);
                    border-radius: 20px;
                }
            """)

    def _play_audio(self):
        if self._card_data:
            term = self._card_data.get("term", "")
            lang = detect_card_term_language(self._card_data)
            self._start_audio(term, lang)

    def _start_audio(self, text, lang, speed=None):
        self._audio_request = None
        self._show_audio_state('loading')
        if speed is None:
            self._audio_request = audio_player.play_pronunciation(text, lang=lang)
        else:
            self._audio_request = audio_player.play_pronunciation(text, lang=lang, speed=speed)

    def _audio_state(self, request, state):
        if self._audio_request is not None and request == self._audio_request:
            self._show_audio_state(state)

    def _show_audio_state(self, state):
        self._last_audio_state = state
        messages = {
            'loading': 'Preparing audio…',
            'playing': 'Playing audio…',
            'unavailable': 'Natural speech is unavailable. Check the connection and audio player.',
            'error': 'Audio could not play. Retry or choose another card.',
        }
        self.lbl_audio_status.setText(ui_text(messages[state], self.lang) if state in messages else '')
        self.lbl_audio_status.setVisible(state in messages)

    def play_sentence_audio(self):
        """Örnek cümlenin doğru telaffuzunu çalar."""
        if self._last_sentence_en and self._card_data:
            lang = detect_card_term_language(self._card_data)
            self._start_audio(self._last_sentence_en, lang, speed=0.9)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit()
            if not self._is_back_showing:
                self.flip(animated=True)
        super().mousePressEvent(event)
