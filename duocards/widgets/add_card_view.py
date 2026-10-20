"""
Study Card - Çok Dilli Manuel Kart Ekleme Ekranı
Dünyadaki tüm diller arasında çift yönlü kelime kartı oluşturma,
kaynak dilin fonetik okunuşu, anadilde telaffuz ve Cambridge / Evrensel çeviri önerisi.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame,
    QScrollArea, QButtonGroup, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QCursor
from duocards.db import get_all_decks, add_card, add_deck, find_existing_cards
from duocards.content_rules import useful_sentence
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.translator import TranslationWorker, detect_category
from duocards.settings import settings
from duocards.i18n import t
from duocards.phonetics import get_phonetic
from duocards.languages import get_all_language_names, get_language_code, get_language_name
from duocards.icons import get_icon
from duocards import sentence_memory
from duocards.languages import LANGUAGES_DATA, normalize_string
from duocards.ui_localization import ui_text
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit, QComboBox
from duocards.widgets.studio_dialogs import StudioDialog, label as dialog_label


EXAMPLE_TEXT = {
    "tr": {
        "title": "Kullanım cümleleri", "idle": "Kelimeyi yazınca kullanım örnekleri otomatik aranır.",
        "waiting": "Kelime için örnekler hazırlanıyor…", "loading": "Kullanım örnekleri aranıyor… Kartı şimdi kaydedebilirsin.",
        "ready": "{count} kullanım örneği hazır. Seçtiğin cümle karta eklenir.",
        "more": "{count} örnek hazır; diğer örnekler aranıyor…",
        "empty": "Bu kelime ve dil için kullanım örneği bulunamadı. Yazımı ve kaynak dili kontrol edip yeniden ara.",
        "error": "Örnek hizmetine ulaşılamadı. Bağlantını kontrol edip yeniden deneyebilirsin.",
        "limited": "Örnek hizmeti şu an yoğun. Biraz sonra yeniden deneyebilirsin.",
        "language": "Örnek aramak için listeden kaynak ve hedef dili seç.",
        "retry": "Yeniden ara", "source": "Kaynak: {source}", "local": "Uygulama sözlüğü", "user": "Kullanıcı örneği",
        "saved_ready": "{term} kaydedildi; kullanım cümlesi karta eklendi.",
        "saved_pending": "{term} kaydedildi. Örnek araması arka planda devam ediyor; sonuçlar karta otomatik eklenir.",
        "saved_empty": "{term} kaydedildi. Henüz örnek yok; Cümle Hafızası’ndan yeniden arayabilirsin.",
    },
    "en": {
        "title": "Usage examples", "idle": "Usage examples are searched automatically when you enter a word.",
        "waiting": "Preparing examples for this word…", "loading": "Searching for usage examples… You can save the card now.",
        "ready": "{count} usage examples ready. Your selected sentence will be added to the card.",
        "more": "{count} examples ready; searching for more…",
        "empty": "No usage example was found for this word and language. Check the spelling and source language, then retry.",
        "error": "The example service could not be reached. Check your connection and retry.",
        "limited": "The example service is busy. Please try again shortly.",
        "language": "Select the source and target languages from the lists to search for examples.",
        "retry": "Search again", "source": "Source: {source}", "local": "App dictionary", "user": "User example",
        "saved_ready": "{term} saved with its usage example.",
        "saved_pending": "{term} saved. The example search continues in the background; results will be added to the card automatically.",
        "saved_empty": "{term} saved. No example is available yet; retry in Sentence Memory.",
    },
    "de": {
        "title": "Verwendungsbeispiele", "idle": "Nach der Worteingabe werden Beispiele automatisch gesucht.",
        "waiting": "Beispiele für dieses Wort werden vorbereitet…", "loading": "Beispiele werden gesucht… Du kannst die Karte bereits speichern.",
        "ready": "{count} Beispiele verfügbar. Der ausgewählte Satz wird der Karte hinzugefügt.",
        "more": "{count} Beispiele verfügbar; weitere werden gesucht…",
        "empty": "Für dieses Wort und diese Sprache wurde kein Beispiel gefunden. Prüfe Schreibweise und Quellsprache und suche erneut.",
        "error": "Der Beispieldienst ist nicht erreichbar. Prüfe deine Verbindung und versuche es erneut.",
        "limited": "Der Beispieldienst ist ausgelastet. Bitte versuche es später erneut.",
        "language": "Wähle Quell- und Zielsprache aus den Listen, um Beispiele zu suchen.",
        "retry": "Erneut suchen", "source": "Quelle: {source}", "local": "App-Wörterbuch", "user": "Nutzerbeispiel",
        "saved_ready": "{term} wurde mit einem Verwendungsbeispiel gespeichert.",
        "saved_pending": "{term} gespeichert. Die Suche läuft im Hintergrund weiter; Ergebnisse werden der Karte automatisch hinzugefügt.",
        "saved_empty": "{term} gespeichert. Noch kein Beispiel verfügbar; suche im Satzspeicher erneut.",
    },
    "es": {
        "title": "Ejemplos de uso", "idle": "Los ejemplos se buscan automáticamente al escribir una palabra.",
        "waiting": "Preparando ejemplos para esta palabra…", "loading": "Buscando ejemplos de uso… Ya puedes guardar la tarjeta.",
        "ready": "{count} ejemplos disponibles. La frase seleccionada se añadirá a la tarjeta.",
        "more": "{count} ejemplos disponibles; buscando más…",
        "empty": "No se encontró ningún ejemplo para esta palabra e idioma. Revisa la ortografía y el idioma de origen e inténtalo de nuevo.",
        "error": "No se pudo conectar al servicio de ejemplos. Revisa tu conexión e inténtalo de nuevo.",
        "limited": "El servicio de ejemplos está ocupado. Inténtalo de nuevo en unos momentos.",
        "language": "Selecciona los idiomas de origen y destino de las listas para buscar ejemplos.",
        "retry": "Buscar de nuevo", "source": "Fuente: {source}", "local": "Diccionario de la aplicación", "user": "Ejemplo del usuario",
        "saved_ready": "{term} guardada con su ejemplo de uso.",
        "saved_pending": "{term} guardada. La búsqueda continúa en segundo plano; los resultados se añadirán automáticamente a la tarjeta.",
        "saved_empty": "{term} guardada. Aún no hay ejemplos; vuelve a buscar en Memoria de frases.",
    },
}


CATEGORIES_BY_UI_LANG = {
    "tr": {
        "word": "Kelime",
        "noun": "İsim",
        "verb": "Fiil",
        "adjective": "Sıfat",
        "adverb": "Zarf",
        "idiom": "Deyim",
        "phrase": "Kalıp İfade",
        "phrasal_verb": "Phrasal Verb",
        "article": "Artikel (der/die/das)",
        "conjunction": "Bağlaç / Edat"
    },
    "en": {
        "word": "Word",
        "noun": "Noun",
        "verb": "Verb",
        "adjective": "Adjective",
        "adverb": "Adverb",
        "idiom": "Idiom",
        "phrase": "Phrase",
        "phrasal_verb": "Phrasal Verb",
        "article": "Article",
        "conjunction": "Conjunction / Prep"
    },
    "de": {
        "word": "Wort",
        "noun": "Nomen",
        "verb": "Verb",
        "adjective": "Adjektiv",
        "adverb": "Adverb",
        "idiom": "Redewendung",
        "phrase": "Ausdruck",
        "phrasal_verb": "Phrasal Verb",
        "article": "Artikel (der/die/das)",
        "conjunction": "Konjunktion / Präp"
    },
    "es": {
        "word": "Palabra",
        "noun": "Sustantivo",
        "verb": "Verbo",
        "adjective": "Adjetivo",
        "adverb": "Adverbio",
        "idiom": "Modismo",
        "phrase": "Frase",
        "phrasal_verb": "Verbo Frasal",
        "article": "Artículo",
        "conjunction": "Conjunción / Prep"
    }
}


def _category_label(value, lang):
    """Read both stable category keys and labels saved by older app versions."""
    value = (value or "word").strip()
    key = next((key for labels in CATEGORIES_BY_UI_LANG.values()
                for key, label in labels.items()
                if value.casefold() in (key.casefold(), label.casefold())), None)
    return CATEGORIES_BY_UI_LANG.get(lang, CATEGORIES_BY_UI_LANG["en"]).get(key, value)


def _duplicate_notice(card, lang):
    category = _category_label(card.get("part_of_speech"), lang)
    if lang == "tr":
        category = category.lower().replace("i\u0307", "i")
    return ui_text("This word is already saved as {part_of_speech} in your library.",
                   lang, part_of_speech=category)


class DuplicateCardDialog(StudioDialog):
    """Show the saved senses before explicitly adding another card."""
    def __init__(self, cards, category, lang, parent=None):
        super().__init__("Word already exists", parent=parent, icon="library", width=560)
        self.lang = lang
        for card in cards:
            panel = QFrame()
            panel.setProperty("studioPanel", True)
            layout = QVBoxLayout(panel)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.addWidget(dialog_label(_duplicate_notice(card, lang), lang))
            layout.addWidget(dialog_label(f"{card['term']} — {card['definition']}", lang, translate=False))
            languages = f"{get_language_name(card['source_lang'], lang)} → {get_language_name(card['target_lang'], lang)}"
            layout.addWidget(dialog_label(f"{card['deck_name']} · {languages}", lang, "muted", translate=False))
            self.form.addWidget(panel)
        self.form.addWidget(dialog_label(ui_text("Add another card as {part_of_speech}?", lang,
                                                part_of_speech=_category_label(category, lang)), lang))
        self.submit_button.setText(ui_text("Add card", lang))
        self.submit_button.setAutoDefault(False)
        self.submit_button.setDefault(False)
        self.cancel_button.setDefault(True)
        self.cancel_button.setFocus()
        self.resize(self.width(), min(560, 260 + 115 * len(cards)))
        localize_tree(self, lang)


class CustomAlertModal(QDialog):
    """Modern, çerçevesiz ve koyu temalı özel uyarı penceresi."""
    def __init__(self, parent=None, title: str = "Uyarı", message: str = "", lang: str = "tr"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1.5px solid rgba(245, 158, 11, 0.4);
                border-radius: 16px;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(22, 20, 22, 20)
        c_layout.setSpacing(14)

        # Üst Satır
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #f59e0b; background: transparent; border: none;")
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
        btn_close.clicked.connect(self.accept)
        top_row.addWidget(btn_close)
        c_layout.addLayout(top_row)

        # Mesaj
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("color: #e2e8f0; font-size: 13px; line-height: 1.45; background: transparent; border: none;")
        c_layout.addWidget(lbl_msg)

        # Tamam Butonu
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton(ui_text('Got It', lang))
        btn_ok.setFixedSize(100, 36)
        btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ok.setStyleSheet("""
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
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        c_layout.addLayout(btn_box)

        main_layout.addWidget(container)


class AddCardView(QWidget):
    card_saved = pyqtSignal()
    open_library = pyqtSignal()
    edit_existing = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trans_worker = None
        self._translation_workers = set()
        self._translation_request = None
        self._translation_serial = 0
        self._translation_revision = 0
        self._manual_pos_key = None
        self._last_suggestion_context = None
        self._last_suggestion_text = ""
        self._selected_pos = "Kelime"
        self.lang = settings.get("ui_language", "tr")
        self._requested_example_key = None
        self._example_rows = []
        self._example_status = "idle"
        self._example_error = ""
        self._saved_example_state = "empty"
        self._example_debounce = QTimer(self)
        self._example_debounce.setSingleShot(True)
        self._example_debounce.setInterval(550)
        self._example_debounce.timeout.connect(self._request_examples)
        self._example_poll = QTimer(self)
        self._example_poll.setInterval(500)
        self._example_poll.timeout.connect(self._refresh_examples)

        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(0)

        # ---------------- FORM PANELİ ----------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        form_container = QWidget()
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(12, 4, 12, 16)
        form_layout.setSpacing(14)

        # Başlık
        self.lbl_title = QLabel(t("add_page_title", self.lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("add_page_subtitle", self.lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        form_layout.addWidget(self.lbl_title)
        form_layout.addWidget(self.lbl_subtitle)

        # Deste Seçimi + Yeni Deste Butonu
        deck_box = QHBoxLayout()
        self.cmb_deck = QComboBox()
        self.cmb_deck.setMinimumHeight(42)

        self.btn_new_deck = QPushButton(t("btn_new_deck", self.lang))
        self.btn_new_deck.setProperty("class", "btn-secondary")
        self.btn_new_deck.setFixedHeight(42)
        self.btn_new_deck.clicked.connect(self._create_new_deck)

        deck_box.addWidget(self.cmb_deck, 1)
        deck_box.addWidget(self.btn_new_deck)
        form_layout.addLayout(deck_box)

        # ---------------- ÇOK DİLLİ SEÇİM PANELİ (KAYNAK VE HEDEF DİL) ----------------
        lang_panel = QFrame()
        lang_panel.setStyleSheet("""
            QFrame#langPanelMain {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)
        lang_panel.setObjectName("langPanelMain")
        lang_panel_layout = QHBoxLayout(lang_panel)
        lang_panel_layout.setContentsMargins(12, 10, 12, 10)
        lang_panel_layout.setSpacing(14)

        combo_style = """
            QComboBox {
                background-color: #0b1120;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f1f5f9;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
                min-height: 36px;
            }
            QComboBox:focus, QComboBox:hover {
                border-color: #10b981;
            }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                color: #f8fafc;
                selection-background-color: #10b981;
                selection-color: #ffffff;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
            }
        """

        # 1. Kaynak Dil Kartı (Kelimenin Dili)
        card_src = QFrame()
        card_src.setStyleSheet("""
            QFrame {
                background-color: #131b2e;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 10px;
            }
        """)
        src_box = QVBoxLayout(card_src)
        src_box.setContentsMargins(12, 10, 12, 10)
        src_box.setSpacing(6)

        src_badge_map = {"tr": "KAYNAK DİL", "en": "SOURCE LANGUAGE", "de": "QUELLSPRACHE", "es": "IDIOMA DE ORIGEN"}
        src_sub_map = {"tr": "Kelime ve Fonetik", "en": "Word & Phonetics", "de": "Wort & Phonetik", "es": "Palabra y Fonética"}
        tgt_badge_map = {"tr": "HEDEF DİL", "en": "TARGET LANGUAGE", "de": "ZIELSPRACHE", "es": "IDIOMA DE DESTINO"}
        tgt_sub_map = {"tr": "Anlam ve Sözlük", "en": "Meaning & Dictionary", "de": "Bedeutung & Wörterbuch", "es": "Significado y Diccionario"}

        self.lbl_src_badge = QLabel(src_badge_map.get(self.lang, "SOURCE LANGUAGE"))
        self.lbl_src_badge.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; background: transparent; border: none;")
        self.lbl_src_sub = QLabel(src_sub_map.get(self.lang, "Word & Phonetics"))
        self.lbl_src_sub.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")

        src_header = QHBoxLayout()
        src_header.addWidget(self.lbl_src_badge)
        src_header.addStretch()
        src_header.addWidget(self.lbl_src_sub)
        src_box.addLayout(src_header)

        self.cmb_source_lang = QComboBox()
        self.cmb_source_lang.setEditable(True)
        self.cmb_source_lang.setStyleSheet(combo_style)
        src_box.addWidget(self.cmb_source_lang)

        # 2. Hedef Dil Kartı (Anlamın Dili)
        card_tgt = QFrame()
        card_tgt.setStyleSheet("""
            QFrame {
                background-color: #102322;
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 10px;
            }
        """)
        tgt_box = QVBoxLayout(card_tgt)
        tgt_box.setContentsMargins(12, 10, 12, 10)
        tgt_box.setSpacing(6)

        self.lbl_tgt_badge = QLabel(tgt_badge_map.get(self.lang, "TARGET LANGUAGE"))
        self.lbl_tgt_badge.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; background: transparent; border: none;")
        self.lbl_tgt_sub = QLabel(tgt_sub_map.get(self.lang, "Meaning & Dictionary"))
        self.lbl_tgt_sub.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")

        tgt_header = QHBoxLayout()
        tgt_header.addWidget(self.lbl_tgt_badge)
        tgt_header.addStretch()
        tgt_header.addWidget(self.lbl_tgt_sub)
        tgt_box.addLayout(tgt_header)

        self.cmb_target_lang = QComboBox()
        self.cmb_target_lang.setEditable(True)
        self.cmb_target_lang.setStyleSheet(combo_style)
        tgt_box.addWidget(self.cmb_target_lang)

        # Tüm dünya dillerini ekle ve içerme (Contains) filtreli arama bağla
        all_langs = get_all_language_names(self.lang)
        self.cmb_source_lang.addItems(all_langs)
        self.cmb_target_lang.addItems(all_langs)

        # QCompleter MatchContains filtresi (Kullanıcı yazarak veya kaydırarak bulur)
        src_comp = self.cmb_source_lang.completer()
        if src_comp:
            src_comp.setFilterMode(Qt.MatchFlag.MatchContains)
            src_comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        tgt_comp = self.cmb_target_lang.completer()
        if tgt_comp:
            tgt_comp.setFilterMode(Qt.MatchFlag.MatchContains)
            tgt_comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Kayıtlı son dilleri seç (mevcut arayüz diline göre)
        saved_src_raw = settings.get("last_source_lang", "en")
        saved_tgt_raw = settings.get("last_target_lang", "tr")
        saved_src = get_language_name(saved_src_raw, self.lang)
        saved_tgt = get_language_name(saved_tgt_raw, self.lang)

        src_idx = self.cmb_source_lang.findText(saved_src)
        if src_idx >= 0:
            self.cmb_source_lang.setCurrentIndex(src_idx)
        else:
            self.cmb_source_lang.setEditText(saved_src)

        tgt_idx = self.cmb_target_lang.findText(saved_tgt)
        if tgt_idx >= 0:
            self.cmb_target_lang.setCurrentIndex(tgt_idx)
        else:
            self.cmb_target_lang.setEditText(saved_tgt)

        self.cmb_source_lang.currentTextChanged.connect(self._on_source_lang_changed)
        self.cmb_target_lang.currentTextChanged.connect(self._on_target_lang_changed)

        lang_panel_layout.addWidget(card_src, 1)
        lang_panel_layout.addWidget(card_tgt, 1)
        form_layout.addWidget(lang_panel)

        # ---------------- 1. KELİME / KALIP (TERM) ----------------
        self.lbl_term_title = QLabel(t("term_title", self.lang))
        self.lbl_term_title.setStyleSheet("font-weight: 700; color: #cbd5e1;")
        form_layout.addWidget(self.lbl_term_title)

        term_row = QHBoxLayout()
        self.input_term = QLineEdit()
        self.input_term.setPlaceholderText(ui_text('{saved_src} word or phrase...', self.lang, **{'saved_src': saved_src}))
        self.input_term.textChanged.connect(self._on_term_changed)

        self.btn_test_audio = QPushButton(t("listen", self.lang))
        self.btn_test_audio.setIcon(get_icon("audio", 18))
        self.btn_test_audio.setProperty("class", "btn-secondary")
        self.btn_test_audio.setFixedHeight(38)
        self.btn_test_audio.clicked.connect(self._test_audio)

        term_row.addWidget(self.input_term, 1)
        term_row.addWidget(self.btn_test_audio)
        form_layout.addLayout(term_row)

        # ---------------- 2. ANLAMI (DEFINITION) ----------------
        self.lbl_def_title = QLabel(t("def_title", self.lang))
        self.lbl_def_title.setStyleSheet("font-weight: 700; color: #cbd5e1;")
        form_layout.addWidget(self.lbl_def_title)

        def_row = QHBoxLayout()
        self.input_definition = QLineEdit()
        self.input_definition.setPlaceholderText(ui_text('{saved_tgt} translation...', self.lang, **{'saved_tgt': saved_tgt}))

        self.btn_suggest = QPushButton(t("btn_suggest", self.lang))
        self.btn_suggest.setProperty("class", "btn-secondary")
        self.btn_suggest.setFixedHeight(38)
        self.btn_suggest.clicked.connect(self._fetch_translation_suggestion)

        def_row.addWidget(self.input_definition, 1)
        def_row.addWidget(self.btn_suggest)
        form_layout.addLayout(def_row)

        # Ağ işi arka planda sürer; önizleme yalnızca güncel kelime ve dile aittir.
        example_panel = QFrame()
        example_panel.setObjectName("manualExamples")
        example_panel.setStyleSheet("""
            QFrame#manualExamples { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; }
            QFrame#manualExamples QLabel { background: transparent; border: none; color: #f1f5f9; }
            QFrame#manualExamples QComboBox { background: #0b1120; color: #f1f5f9; border: 1px solid #334155; border-radius: 8px; padding: 7px; }
            QFrame#manualExamples QComboBox QAbstractItemView { background: #0f172a; color: #ffffff; selection-background-color: #10b981; }
            QFrame#manualExamples QPushButton { background: #10b981; color: #ffffff; border: none; border-radius: 8px; padding: 9px 14px; font-weight: 700; }
            QFrame#manualExamples QPushButton:hover { background: #059669; }
            QFrame#manualExamples QPushButton:disabled { background: #134e4a; color: #cbd5e1; }
        """)
        example_layout = QVBoxLayout(example_panel)
        example_layout.setContentsMargins(14, 12, 14, 12)
        example_header = QHBoxLayout()
        self.lbl_examples_title = QLabel()
        self.lbl_examples_title.setStyleSheet("font-weight: 700;")
        example_header.addWidget(self.lbl_examples_title, 1)
        self.btn_retry_examples = QPushButton()
        self.btn_retry_examples.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retry_examples.clicked.connect(lambda: self._request_examples(force=True))
        example_header.addWidget(self.btn_retry_examples)
        example_layout.addLayout(example_header)
        self.lbl_examples_status = QLabel()
        self.lbl_examples_status.setWordWrap(True)
        self.lbl_examples_status.setTextFormat(Qt.TextFormat.PlainText)
        example_layout.addWidget(self.lbl_examples_status)
        self.cmb_example = QComboBox()
        self.cmb_example.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_example.setMinimumContentsLength(20)
        self.cmb_example.currentIndexChanged.connect(self._show_selected_example)
        example_layout.addWidget(self.cmb_example)
        self.lbl_example_sentence = QLabel()
        self.lbl_example_translation = QLabel()
        self.lbl_example_source = QLabel()
        for label in (self.lbl_example_sentence, self.lbl_example_translation, self.lbl_example_source):
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            example_layout.addWidget(label)
        self.lbl_example_sentence.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.lbl_example_translation.setStyleSheet("color: #cbd5e1;")
        self.lbl_example_source.setStyleSheet("font-size: 11px; color: #94a3b8;")
        example_layout.addWidget(QLabel(ui_text('Example sentence', self.lang)))
        self.input_example_sentence = QLineEdit()
        self.input_example_sentence.setPlaceholderText(ui_text('Selected example sentence', self.lang))
        example_layout.addWidget(self.input_example_sentence)
        example_layout.addWidget(QLabel(ui_text('Example translation', self.lang)))
        self.input_example_translation = QLineEdit()
        self.input_example_translation.setPlaceholderText(ui_text('Translation of the selected sentence', self.lang))
        example_layout.addWidget(self.input_example_translation)
        self._selected_example_text = None
        form_layout.addWidget(example_panel)
        self.lbl_duplicates = QLabel()
        self.lbl_duplicates.setWordWrap(True)
        self.lbl_duplicates.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_duplicates.setStyleSheet('color:#fbbf24; padding:10px;')
        form_layout.addWidget(self.lbl_duplicates)
        self.btn_edit_existing = QPushButton()
        self.btn_edit_existing.clicked.connect(lambda: self._existing_cards and self.edit_existing.emit(self._existing_cards[0]['id']))
        form_layout.addWidget(self.btn_edit_existing)
        self._existing_cards = []
        self._refresh_duplicates()
        self._render_examples()

        # ---------------- 3. KELİME TÜRÜ (CHIPS) ----------------
        self.lbl_pos_title = QLabel(t("pos_title", self.lang))
        self.lbl_pos_title.setStyleSheet("font-weight: 700; color: #cbd5e1;")
        form_layout.addWidget(self.lbl_pos_title)

        self.chips_container = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(6)

        self.pos_group = QButtonGroup(self)
        self.pos_group.setExclusive(True)
        form_layout.addWidget(self.chips_container)

        self._selected_pos_key = "word"
        self._refresh_pos_chips()

        # ---------------- 4. KİŞİSEL NOTLAR ----------------
        self.lbl_notes_title = QLabel(t("notes_title", self.lang))
        self.lbl_notes_title.setStyleSheet("font-weight: 700; color: #cbd5e1;")
        form_layout.addWidget(self.lbl_notes_title)

        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText(t("notes_placeholder", self.lang))
        form_layout.addWidget(self.input_notes)

        # Bildirim & Geri Bildirim Alanı
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")
        form_layout.addWidget(self.lbl_feedback)

        # ---------------- 5. AKSİYON BUTONLARI ----------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_save_and_new = QPushButton(t("btn_save_and_new", self.lang))
        self.btn_save_and_new.setProperty("class", "btn-primary")
        self.btn_save_and_new.setFixedHeight(46)
        self.btn_save_and_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save_and_new.clicked.connect(self._save_and_new)

        self.btn_save_and_exit = QPushButton(t("btn_go_library", self.lang))
        self.btn_save_and_exit.setProperty("class", "btn-secondary")
        self.btn_save_and_exit.setFixedHeight(46)
        self.btn_save_and_exit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save_and_exit.clicked.connect(self._save_and_exit)

        btn_row.addWidget(self.btn_save_and_new, 3)
        btn_row.addWidget(self.btn_save_and_exit, 2)
        form_layout.addLayout(btn_row)

        form_layout.addStretch()

        scroll_area.setWidget(form_container)
        main_layout.addWidget(scroll_area)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._save_and_new)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._save_and_new)

    def _get_available_category_keys(self, source_lang_name: str) -> list:
        src_code = get_language_code(source_lang_name).lower()
        if src_code in ("de", "nl", "sv"):
            return ["word", "noun", "article", "verb", "adjective", "adverb", "idiom", "phrase"]
        elif src_code in ("en", "gb"):
            return ["word", "noun", "verb", "phrasal_verb", "adjective", "adverb", "idiom", "phrase"]
        else:
            return ["word", "noun", "verb", "adjective", "adverb", "idiom", "phrase", "conjunction"]

    def _refresh_pos_chips(self):
        selected_key = getattr(self, "_selected_pos_key", "word")

        if hasattr(self, "pos_group"):
            for btn in list(self.pos_group.buttons()):
                self.pos_group.removeButton(btn)
                btn.hide()
                btn.deleteLater()

        if hasattr(self, "chips_layout"):
            while self.chips_layout.count() > 0:
                item = self.chips_layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()

            src_lang = self.get_current_source_lang()
            cat_keys = self._get_available_category_keys(src_lang)
            if selected_key not in cat_keys:
                selected_key = cat_keys[0]
                self._manual_pos_key = None
            self._selected_pos_key = selected_key

            lang_dict = CATEGORIES_BY_UI_LANG.get(self.lang, CATEGORIES_BY_UI_LANG.get("en", {}))

            for key in cat_keys:
                label = lang_dict.get(key, key.capitalize())
                btn = QPushButton(label)
                btn.setProperty("class", "chip-btn")
                btn.setProperty("category_key", key)
                btn.setCheckable(True)
                if key == selected_key:
                    btn.setChecked(True)
                    self._selected_pos = label
                btn.clicked.connect(lambda checked, k=key, l=label: self._on_chip_selected(k, l))
                self.pos_group.addButton(btn)
                self.chips_layout.addWidget(btn)

            self.chips_layout.addStretch()

    def select_category(self, cat_key: str):
        """Kategoriyi otomatik veya programatik olarak seçer ve butonunu aktif eder."""
        cat_key = (cat_key or "word").lower().strip()
        lang_dict = CATEGORIES_BY_UI_LANG.get(self.lang, CATEGORIES_BY_UI_LANG.get("en", {}))
        available_keys = self._get_available_category_keys(self.get_current_source_lang())
        if cat_key not in available_keys:
            if cat_key == "phrasal_verb" and "verb" in available_keys:
                cat_key = "verb"
            elif "word" in available_keys:
                cat_key = "word"
            elif available_keys:
                cat_key = available_keys[0]

        self._selected_pos_key = cat_key
        self._selected_pos = lang_dict.get(cat_key, cat_key.capitalize())

        for btn in self.pos_group.buttons():
            if btn.property("category_key") == cat_key:
                btn.setChecked(True)
                break

    def _on_chip_selected(self, key: str, label: str):
        sfx.play_click()
        context = self._translation_context()
        refresh_suggestion = self._translation_request is not None or (
            context is not None and self._last_suggestion_context is not None
            and context[:3] == self._last_suggestion_context[:3]
            and self.input_definition.text() == self._last_suggestion_text
        )
        if refresh_suggestion and self.input_definition.text() == self._last_suggestion_text:
            self.input_definition.clear()
            self.lbl_feedback.clear()
        self._selected_pos_key = key
        self._selected_pos = label
        self._manual_pos_key = key if key != "word" else None
        self._translation_revision += 1
        if refresh_suggestion:
            self._fetch_translation_suggestion()

    def _on_term_changed(self):
        self._translation_revision += 1
        self._refresh_duplicates()
        self._recalc_phonetic()
        self._schedule_examples()

    def _refresh_duplicates(self):
        if not hasattr(self, 'lbl_duplicates'):
            return
        self._existing_cards = find_existing_cards(self.input_term.text())
        self.lbl_duplicates.setVisible(bool(self._existing_cards))
        self.btn_edit_existing.setVisible(bool(self._existing_cards))
        self.btn_edit_existing.setText(ui_text('Edit existing card', self.lang))
        lines = []
        for card in self._existing_cards[:5]:
            lines.append(str(_duplicate_notice(card, self.lang)))
            lines.append(f"{card['term']} — {card['definition']} · {card['deck_name']}")
        self.lbl_duplicates.setText('\n'.join(lines))

    def _example_text(self, key, **values):
        return EXAMPLE_TEXT.get(self.lang, EXAMPLE_TEXT["en"])[key].format(**values)

    def _example_card(self):
        """Editable language boxes must contain a known language, not partial input."""
        term = self.input_term.text().strip()
        if not term:
            return None
        codes = []
        for box in (self.cmb_source_lang, self.cmb_target_lang):
            name = normalize_string(box.currentText().strip())
            code = next((item["code"] for item in LANGUAGES_DATA
                         if any(normalize_string(item.get(key, "")) == name
                                for key in ("code", "tr", "en", "de", "es"))), None)
            if not code:
                return None
            codes.append(code)
        return dict(term=term, source_lang=codes[0], target_lang=codes[1])

    @staticmethod
    def _example_key(card):
        return (card["term"], card["source_lang"], card["target_lang"]) if card else None

    def _schedule_examples(self):
        self._example_debounce.stop()
        self._example_poll.stop()
        self._requested_example_key = None
        self._example_rows = []
        self._example_error = ""
        card = self._example_card()
        self._example_status = ("waiting" if card else
                                "language" if self.input_term.text().strip() else "idle")
        self._render_examples()
        if card and self.isVisible():
            self._example_debounce.start()

    def _request_examples(self, force=False):
        self._example_debounce.stop()
        card = self._example_card()
        if not card:
            self._schedule_examples()
            return
        self._requested_example_key = self._example_key(card)
        try:
            sentence_memory.request_examples(card, force=force)
            self._refresh_examples()
        except Exception:
            self._example_status = "offline"
            self._example_error = "service"
            self._render_examples()
        if self.isVisible():
            self._example_poll.start()

    @staticmethod
    def _authentic_examples(card):
        pattern = sentence_memory.term_pattern(card["term"], card["source_lang"])
        return [row for row in sentence_memory.read_examples(card)
                if row.get("kind") == "example"
                and useful_sentence(card['term'], row.get('text',''), card['source_lang'])
                and row.get("source") not in ("offline_example", "practice")
                and pattern.search(row.get("text", ""))]

    def _refresh_examples(self):
        card = self._example_card()
        if not card or self._example_key(card) != self._requested_example_key:
            return
        try:
            self._example_rows = self._authentic_examples(card)
            self._example_status = sentence_memory.fetch_status(card)
            self._example_error = sentence_memory.fetch_error(card)
        except Exception:
            self._example_status, self._example_error = "offline", "service"
        self._render_examples()

    def _render_examples(self):
        selected_text = self.cmb_example.currentData()
        self.lbl_examples_title.setText(self._example_text("title"))
        self.btn_retry_examples.setText(self._example_text("retry"))
        status = self._example_status
        count = len(self._example_rows)
        if count:
            text = self._example_text("more" if status == "loading" else "ready", count=count)
            if status in ("offline", "error"):
                text += " " + self._example_text("limited" if self._example_error == "http_429" else "error")
        elif status in ("idle", "waiting", "language"):
            text = self._example_text(status)
        elif status == "loading":
            text = self._example_text("loading")
        elif status in ("offline", "error"):
            text = self._example_text("limited" if self._example_error == "http_429" else "error")
        else:
            text = self._example_text("empty")
        self.lbl_examples_status.setText(text)
        self.btn_retry_examples.setEnabled(bool(self._example_card()) and status != "loading")
        self.cmb_example.blockSignals(True)
        self.cmb_example.clear()
        for index, row in enumerate(self._example_rows, 1):
            self.cmb_example.addItem(f"{index}. {row['text']}", row["text"])
        selected_index = self.cmb_example.findData(selected_text)
        if selected_index >= 0:
            self.cmb_example.setCurrentIndex(selected_index)
        self.cmb_example.blockSignals(False)
        self.cmb_example.setVisible(count > 1)
        self._show_selected_example()

    def _show_selected_example(self):
        row = next((row for row in self._example_rows
                    if row["text"] == self.cmb_example.currentData()), None)
        card = self._example_card()
        text = row["text"] if row else ""
        translation = row.get("translations", {}).get(card["target_lang"], "") if row and card else ""
        selection = (text, card['target_lang'] if card else '')
        if selection != self._selected_example_text:
            self._selected_example_text = selection
            self.input_example_sentence.setText(text)
            self.input_example_translation.setText(translation)
        elif translation and not self.input_example_translation.isModified():
            self.input_example_translation.setText(translation)
        source = ""
        if row:
            provider = row.get("source", "")
            provider = self._example_text(provider) if provider in ("local", "user") else provider
            source = self._example_text("source", source=provider)
            for value in (row.get("author"), row.get("license"), row.get("url")):
                if value:
                    source += " · " + value
        for label, value in ((self.lbl_example_sentence, text),
                             (self.lbl_example_translation, translation),
                             (self.lbl_example_source, source)):
            label.setText(value)
            label.setVisible(bool(value))

    def showEvent(self, event):
        super().showEvent(event)
        card = self._example_card()
        if card and self._example_key(card) == self._requested_example_key:
            self._refresh_examples()
            self._example_poll.start()
        else:
            self._schedule_examples()

    def hideEvent(self, event):
        self._example_debounce.stop()
        self._example_poll.stop()
        super().hideEvent(event)

    def get_current_source_lang(self) -> str:
        if hasattr(self, "cmb_source_lang"):
            val = self.cmb_source_lang.currentText().strip()
            if val:
                return val
        return settings.get("last_source_lang", "İngilizce")

    def get_current_target_lang(self) -> str:
        if hasattr(self, "cmb_target_lang"):
            val = self.cmb_target_lang.currentText().strip()
            if val:
                return val
        return settings.get("last_target_lang", "Türkçe")

    def _on_source_lang_changed(self, text: str):
        self._translation_revision += 1
        lang_name = text.strip() or (ui_text('English', self.lang))
        settings.set("last_source_lang", lang_name)
        self.input_term.setPlaceholderText(
            ui_text('{lang_name} word or phrase...', self.lang, **{'lang_name': lang_name})
        )
        self._refresh_pos_chips()
        self._schedule_examples()

    def _on_target_lang_changed(self, text: str):
        self._translation_revision += 1
        lang_name = text.strip() or (ui_text('Turkish', self.lang))
        settings.set("last_target_lang", lang_name)
        self.input_definition.setPlaceholderText(
            ui_text('{lang_name} translation or definition...', self.lang, **{'lang_name': lang_name})
        )
        self._schedule_examples()
        self._refresh_duplicates()

    def _recalc_phonetic(self):
        pass

    def get_current_phonetic(self) -> str:
        term = self.input_term.text().strip()
        src_code = get_language_code(self.get_current_source_lang())
        return get_phonetic(term, src_code) if term else ""

    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(t("add_page_title", lang))
        self.lbl_subtitle.setText(t("add_page_subtitle", lang))
        self.btn_new_deck.setText(t("btn_new_deck", lang))
        if hasattr(self, "lbl_src_badge"):
            src_badge_map = {"tr": "KAYNAK DİL", "en": "SOURCE LANGUAGE", "de": "QUELLSPRACHE", "es": "IDIOMA DE ORIGEN"}
            src_sub_map = {"tr": "Kelime ve Fonetik", "en": "Word & Phonetics", "de": "Wort & Phonetik", "es": "Palabra y Fonética"}
            tgt_badge_map = {"tr": "HEDEF DİL", "en": "TARGET LANGUAGE", "de": "ZIELSPRACHE", "es": "IDIOMA DE DESTINO"}
            tgt_sub_map = {"tr": "Anlam ve Sözlük", "en": "Meaning & Dictionary", "de": "Bedeutung & Wörterbuch", "es": "Significado y Diccionario"}
            self.lbl_src_badge.setText(src_badge_map.get(lang, "SOURCE LANGUAGE"))
            self.lbl_src_sub.setText(src_sub_map.get(lang, "Word & Phonetics"))
            self.lbl_tgt_badge.setText(tgt_badge_map.get(lang, "TARGET LANGUAGE"))
            self.lbl_tgt_sub.setText(tgt_sub_map.get(lang, "Meaning & Dictionary"))
        self.lbl_term_title.setText(t("term_title", lang))
        self.lbl_def_title.setText(t("def_title", lang))
        self.btn_suggest.setText(t("btn_suggest", lang))
        self.btn_test_audio.setText(t("listen", lang))
        self.btn_test_audio.setIcon(get_icon("audio", 18))
        self.lbl_pos_title.setText(t("pos_title", lang))
        self.lbl_notes_title.setText(t("notes_title", lang))
        self.btn_save_and_new.setText(t("btn_save_and_new", lang))
        self.btn_save_and_exit.setText(t("btn_go_library", lang))

        # Dil listelerini arayüz diline göre güncelle
        if hasattr(self, "cmb_source_lang") and hasattr(self, "cmb_target_lang"):
            src_code = get_language_code(self.get_current_source_lang())
            tgt_code = get_language_code(self.get_current_target_lang())

            self.cmb_source_lang.blockSignals(True)
            self.cmb_target_lang.blockSignals(True)
            self.cmb_source_lang.clear()
            self.cmb_target_lang.clear()

            all_langs = get_all_language_names(lang)
            self.cmb_source_lang.addItems(all_langs)
            self.cmb_target_lang.addItems(all_langs)

            src_name = get_language_name(src_code, lang)
            tgt_name = get_language_name(tgt_code, lang)

            src_idx = self.cmb_source_lang.findText(src_name)
            if src_idx >= 0:
                self.cmb_source_lang.setCurrentIndex(src_idx)
            else:
                self.cmb_source_lang.setEditText(src_name)

            tgt_idx = self.cmb_target_lang.findText(tgt_name)
            if tgt_idx >= 0:
                self.cmb_target_lang.setCurrentIndex(tgt_idx)
            else:
                self.cmb_target_lang.setEditText(tgt_name)

            self.cmb_source_lang.blockSignals(False)
            self.cmb_target_lang.blockSignals(False)

            self.input_term.setPlaceholderText(
                ui_text('{src_name} word or phrase...', lang, **{'src_name': src_name})
            )
            self.input_definition.setPlaceholderText(
                ui_text('{tgt_name} translation or definition...', lang, **{'tgt_name': tgt_name})
            )

        self._refresh_pos_chips()

        self._render_examples()
        self._refresh_duplicates()
        localize_tree(self,lang)

    def refresh_decks(self):
        current_id = self.cmb_deck.currentData()
        self.cmb_deck.blockSignals(True)
        self.cmb_deck.clear()

        decks = get_all_decks()
        idx_to_select = 0
        for i, d in enumerate(decks):
            self.cmb_deck.addItem(d['name'], d["id"])
            if current_id == d["id"]:
                idx_to_select = i

        self.cmb_deck.setCurrentIndex(idx_to_select)
        self.cmb_deck.blockSignals(False)

    def _create_new_deck(self):
        from duocards.widgets.decks_view import DeckEditDialog
        from PyQt6.QtWidgets import QDialog
        sfx.play_click()
        title = ui_text('Create New Deck', self.lang)
        dlg = DeckEditDialog(self, title=title, is_create=True, lang=self.lang)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc = dlg.get_data()
            if name and name.strip():
                deck_id = add_deck(name.strip(), desc)
                self.refresh_decks()
                for i in range(self.cmb_deck.count()):
                    if self.cmb_deck.itemData(i) == deck_id:
                        self.cmb_deck.setCurrentIndex(i)
                        break

    def _test_audio(self):
        """Kelimeyi seçilen Kaynak Dilde telaffuz ederek çalar."""
        term = self.input_term.text().strip()
        if term:
            src_lang = self.get_current_source_lang()
            src_code = get_language_code(src_lang)
            audio_player.play_pronunciation(term, lang=src_code)

    def _translation_context(self):
        card = self._example_card()
        if not card:
            return None
        return (card["term"], card["source_lang"], card["target_lang"],
                self._manual_pos_key or "", self._translation_revision)

    def _release_translation_worker(self, worker):
        self._translation_workers.discard(worker)
        if self._trans_worker is worker:
            self._trans_worker = None

    def _fetch_translation_suggestion(self):
        """Kaynak dilden hedef dile çeviri önerisi çeker."""
        context = self._translation_context()
        if context is None:
            return

        term, source_lang, target_lang, category, _ = context
        self._translation_serial += 1
        request = (self._translation_serial, context, self.input_definition.text())
        self._translation_request = request
        sfx.play_click()
        self.btn_suggest.setEnabled(False)
        self.btn_suggest.setText("...")

        worker = TranslationWorker(term, target_lang=target_lang, source_lang=source_lang,
                                   part_of_speech=category, parent=self)
        self._trans_worker = worker
        self._translation_workers.add(worker)
        worker.result_ready.connect(lambda result: self._on_translation_finished(result, request))
        worker.finished.connect(lambda: self._release_translation_worker(worker))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _on_translation_finished(self, result: dict, request):
        if request != self._translation_request:
            return
        self._translation_request = None
        self.btn_suggest.setEnabled(True)
        self.btn_suggest.setText(t("btn_suggest", self.lang))
        if request[1] != self._translation_context() or request[2] != self.input_definition.text():
            return
        if result.get("translation"):
            self.input_definition.setText(result["translation"])
            self._last_suggestion_context = request[1]
            self._last_suggestion_text = result["translation"]
            sfx.play_correct()
            src_lbl = result.get("source", "Sözlük")
            self.lbl_feedback.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")
            self.lbl_feedback.setText(f"{src_lbl}: {result['translation']}")

            # Kategori otomatik algılama ve seçme (Arayüz aynı kalır, buton işaretlenir)
            term = self.input_term.text().strip()
            detected_cat = detect_category(
                term=term,
                definition=result["translation"],
                source_lang=self.get_current_source_lang(),
                target_lang=self.get_current_target_lang(),
                raw_pos=result.get("pos", "")
            )
            if self._manual_pos_key is None:
                self.select_category(detected_cat)
        elif result.get("error"):
            self.lbl_feedback.setStyleSheet("color: #f59e0b; font-weight: 700; font-size: 12px;")
            if result["error"] == "part_of_speech_not_found":
                self.lbl_feedback.setText(ui_text(
                    "No translation was found for {part_of_speech}. Enter its meaning manually or choose another word type.",
                    self.lang, part_of_speech=_category_label(self._selected_pos_key, self.lang)))
            else:
                self.lbl_feedback.setText(result['error'])

    def _validate_and_save(self) -> bool:
        term = self.input_term.text().strip()
        definition = self.input_definition.text().strip()
        deck_id = self.cmb_deck.currentData()

        title_err = ui_text('Missing Information', self.lang)
        if not deck_id:
            msg = ui_text('Please select a deck to add the card to.', self.lang)
            dlg = CustomAlertModal(self, title=title_err, message=msg, lang=self.lang)
            dlg.exec()
            return False

        if not term or not definition:
            msg = ui_text('Please fill in the word and definition fields.', self.lang)
            dlg = CustomAlertModal(self, title=title_err, message=msg, lang=self.lang)
            dlg.exec()
            return False

        source_lang = self.get_current_source_lang()
        target_lang = self.get_current_target_lang()
        settings.set("last_source_lang", source_lang)
        settings.set("last_target_lang", target_lang)
        existing = find_existing_cards(term)
        if existing:
            dialog = DuplicateCardDialog(existing, self._selected_pos_key, self.lang, self)
            accepted = dialog.exec() == QDialog.DialogCode.Accepted
            dialog.deleteLater()
            if not accepted:
                return False

        phonetic = self.get_current_phonetic()
        notes = self.input_notes.text().strip()
        example_card = self._example_card()
        try:
            rows = self._authentic_examples(example_card) if example_card else []
        except Exception:
            rows = []
        selected_text = (self.cmb_example.currentData()
                         if self._example_key(example_card) == self._requested_example_key else None)
        selected = next((row for row in rows if row["text"] == selected_text), rows[0] if rows else {})

        add_card(
            deck_id=deck_id,
            term=term,
            definition=definition,
            part_of_speech=self._selected_pos,
            example_sentence=self.input_example_sentence.text().strip(),
            example_translation=self.input_example_translation.text().strip(),
            phonetic=phonetic,
            notes=notes,
            target_lang=target_lang,
            source_lang=source_lang
        )
        try:
            fetching = example_card and sentence_memory.fetch_status(example_card) == "loading"
        except Exception:
            fetching = False
        self._saved_example_state = "ready" if selected else "pending" if fetching else "empty"
        self.lbl_feedback.setText(self._example_text("saved_" + self._saved_example_state, term=term))
        sfx.play_correct()
        self.card_saved.emit()
        return True

    def _save_and_new(self):
        if self._validate_and_save():
            self.input_term.clear()
            self.input_definition.clear()
            self.input_notes.clear()
            self.input_term.setFocus()

    def _save_and_exit(self):
        term = self.input_term.text().strip()
        definition = self.input_definition.text().strip()
        # Eğer hiçbir şey yazılmamışsa, kullanıcı doğrudan kütüphaneye dönmek istiyordur (hata gösterme)
        if not term and not definition:
            self.open_library.emit()
            return
        if self._validate_and_save():
            self.open_library.emit()
