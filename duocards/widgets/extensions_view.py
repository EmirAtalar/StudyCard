"""
Study Card - Eklentiler & Dil Modülleri Yönetim Ekranı (Extensions View)
Dünyanın en çok konuşulan 15 dili için 1000'er kelimelik dil paketleri.
Kullanıcı istediği dilleri aktifleştirip doğrudan yan menüye (sidebar) ekler.
Tüm metinler 4 dilde (TR, EN, DE, ES) tam uyumludur ve alt açıklamaları kaldırılmıştır.
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QCursor, QPainter, QColor, QPainterPath,
    QPolygonF, QPen, QBrush
)
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.i18n import t
from duocards.icons import get_icon
from duocards.learning_extensions import LEARNING_EXTENSIONS
from duocards.practice_menus import NEW_CORE_MENUS
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton
from duocards.widgets.studio_dialogs import STUDIO_STYLES, label, button, apply_studio_style
from duocards.styles import transform_preferences
from duocards import custom_tables, custom_games
from duocards import personal_extensions


CORE_MENUS: List[Dict[str, Any]] = [
    {
        "id": "study",
        "setting_key": "menu_visible_study",
        "default": True,
        "icon": "study",
        "titles": {
            "tr": "Çalış (Aralıklı Tekrar & Ezber)",
            "en": "Study (Spaced Repetition)",
            "de": "Lernen (Wiederholung)",
            "es": "Estudiar (Repaso)"
        },
        "view_name": "study",
    },
    {
        "id": "add",
        "setting_key": "menu_visible_add",
        "default": True,
        "icon": "add",
        "titles": {
            "tr": "Manuel Kart Ekle (Yeni Kelime)",
            "en": "Add Card (New Word)",
            "de": "Karte hinzufügen",
            "es": "Añadir Tarjeta"
        },
        "view_name": "add",
    },
    {
        "id": "library",
        "setting_key": "menu_visible_library",
        "default": True,
        "icon": "library",
        "titles": {
            "tr": "Kütüphane & Pratik Testi (Quiz)",
            "en": "Library & Practice Quiz",
            "de": "Bibliothek & Quiz",
            "es": "Biblioteca y Test"
        },
        "view_name": "library",
    },
    {
        "id": "decks",
        "setting_key": "menu_visible_decks",
        "default": True,
        "icon": "decks",
        "titles": {
            "tr": "Desteler (Kelime Grupları)",
            "en": "Decks (Word Groups)",
            "de": "Decks (Wortgruppen)",
            "es": "Mazos (Grupos de Palabras)"
        },
        "view_name": "decks",
    },
    {
        "id": "timer",
        "setting_key": "menu_visible_timer",
        "default": True,
        "icon": "timer",
        "titles": {
            "tr": "Zamanlayıcı (Pomodoro & Kronometre)",
            "en": "Timer (Pomodoro & Stopwatch)",
            "de": "Timer (Pomodoro & Stoppuhr)",
            "es": "Temporizador (Pomodoro y Cronómetro)"
        },
        "view_name": "timer",
    },
    {
        "id": "stats",
        "setting_key": "menu_visible_stats",
        "default": True,
        "icon": "stats",
        "titles": {
            "tr": "İstatistikler & Başarı Grafikleri",
            "en": "Statistics & Progress Charts",
            "de": "Statistiken & Fortschritt",
            "es": "Estadísticas y Progreso"
        },
        "view_name": "stats",
    },
    {
        "id": "import",
        "setting_key": "menu_visible_import",
        "default": True,
        "icon": "import",
        "titles": {
            "tr": "İçe / Dışa Aktar (Yedekleme & CSV)",
            "en": "Import / Export (Backup & CSV)",
            "de": "Import / Export (Sicherung)",
            "es": "Importar / Exportar (Copia de Seguridad)"
        },
        "view_name": "import",
    },
    {
        "id": "match",
        "setting_key": "menu_visible_match",
        "default": True,
        "icon": "match",
        "titles": {
            "tr": "Kelime Eşleştirme Oyunu (Speed Match)",
            "en": "Speed Match (Vocabulary Memory)",
            "de": "Wort-Kombination (Speed Match)",
            "es": "Emparejar Palabras (Speed Match)"
        },
        "view_name": "match",
    },
    {
        "id": "dictation",
        "setting_key": "menu_visible_dictation",
        "default": True,
        "icon": "dictation",
        "titles": {
            "tr": "Dinleme",
            "en": "Listening",
            "de": "Hören",
            "es": "Escucha"
        },
        "view_name": "dictation",
    },
    {
        "id": "cloze",
        "setting_key": "menu_visible_cloze",
        "default": True,
        "icon": "cloze",
        "titles": {
            "tr": "Cümlede Boşluk Doldurma (Cloze Deletion)",
            "en": "Sentence Fill-in Practice (Cloze Deletion)",
            "de": "Lückentext-Übung (Cloze Deletion)",
            "es": "Completar Frases (Cloze Deletion)"
        },
        "view_name": "cloze",
    },
    {
        "id": "settings",
        "setting_key": "menu_visible_settings",
        "default": True,
        "icon": "settings",
        "titles": {
            "tr": "Ayarlar (Kişiselleştirme & Kısayollar)",
            "en": "Settings (Preferences & Hotkeys)",
            "de": "Einstellungen",
            "es": "Configuración"
        },
        "view_name": "settings",
    },
]


CORE_MENUS.extend(NEW_CORE_MENUS)

AVAILABLE_EXTENSIONS: List[Dict[str, Any]] = [
    {
        "id": "en_verbs",
        "setting_key": "plugin_en_verbs",
        "default": True,
        "lang_code": "EN",
        "titles": {
            "tr": "İngilizce: Düzensiz & Temel Fiiller",
            "en": "English: Irregular & Common Verbs",
            "de": "Englisch: Unregelmäßige Verben",
            "es": "Inglés: Verbos Irregulares y Comunes"
        },
        "badges": {
            "tr": "1050 Fiil / İngilizce",
            "en": "1050 Verbs / English",
            "de": "1050 Verben / Englisch",
            "es": "1050 Verbos / Inglés"
        },
        "nav_names": {
            "tr": "Kuralsız Fiiller (EN)",
            "en": "Irregular Verbs (EN)",
            "de": "Verben (EN)",
            "es": "Verbos (EN)"
        },
        "badge_color": "#38bdf8",
        "view_name": "ext_en",
        "dataset_file": "en_verbs.json",
        "term_col": "Fiil (V1)",
        "attr_col": "Past Simple (V2)",
        "extra_col": "Past Participle (V3)",
        "filters": []
    },
    {
        "id": "de_articles",
        "setting_key": "plugin_de_articles",
        "default": False,
        "lang_code": "DE",
        "titles": {
            "tr": "Almanca: En Çok Kullanılan İsimler (Der, Die, Das)",
            "en": "German: Articles (Der, Die, Das)",
            "de": "Deutsch: Artikel (Der, Die, Das)",
            "es": "Alemán: Artículos (Der, Die, Das)"
        },
        "badges": {
            "tr": "1050 İsim / Almanca",
            "en": "1050 Nouns / German",
            "de": "1050 Nomen / Deutsch",
            "es": "1050 Sustantivos / Alemán"
        },
        "nav_names": {
            "tr": "Artikeller (DE)",
            "en": "Articles (DE)",
            "de": "Artikel (DE)",
            "es": "Artículos (DE)"
        },
        "badge_color": "#f59e0b",
        "view_name": "ext_de",
        "dataset_file": "de_articles.json",
        "term_col": "İsim",
        "attr_col": "Artikel",
        "extra_col": "Çoğul Hali",
        "filters": ["der", "die", "das"]
    },
    {
        "id": "fr_verbs",
        "setting_key": "plugin_fr_verbs",
        "default": False,
        "lang_code": "FR",
        "titles": {
            "tr": "Fransızca: En Çok Kullanılan Fiiller",
            "en": "French: Essential Verbs",
            "de": "Französisch: Wichtige Verben",
            "es": "Francés: Verbos Esenciales"
        },
        "badges": {
            "tr": "1030 Fiil / Fransızca",
            "en": "1030 Verbs / French",
            "de": "1030 Verben / Französisch",
            "es": "1030 Verbos / Francés"
        },
        "nav_names": {
            "tr": "Fiiller (FR)",
            "en": "Verbs (FR)",
            "de": "Verben (FR)",
            "es": "Verbos (FR)"
        },
        "badge_color": "#818cf8",
        "view_name": "ext_fr",
        "dataset_file": "fr_verbs.json",
        "term_col": "Infinitif",
        "attr_col": "Présent",
        "extra_col": "Passé Composé",
        "filters": []
    },
    {
        "id": "es_verbs",
        "setting_key": "plugin_es_verbs",
        "default": False,
        "lang_code": "ES",
        "titles": {
            "tr": "İspanyolca: En Çok Kullanılan Fiiller",
            "en": "Spanish: Essential Verbs",
            "de": "Spanisch: Wichtige Verben",
            "es": "Español: Verbos Esenciales"
        },
        "badges": {
            "tr": "1030 Fiil / İspanyolca",
            "en": "1030 Verbs / Spanish",
            "de": "1030 Verben / Spanisch",
            "es": "1030 Verbos / Español"
        },
        "nav_names": {
            "tr": "Fiiller (ES)",
            "en": "Verbs (ES)",
            "de": "Verben (ES)",
            "es": "Verbos (ES)"
        },
        "badge_color": "#f43f5e",
        "view_name": "ext_es",
        "dataset_file": "es_verbs.json",
        "term_col": "Infinitivo",
        "attr_col": "Presente",
        "extra_col": "Pretérito",
        "filters": []
    },
    {
        "id": "it_verbs",
        "setting_key": "plugin_it_verbs",
        "default": False,
        "lang_code": "IT",
        "titles": {
            "tr": "İtalyanca: En Çok Kullanılan Fiiller",
            "en": "Italian: Essential Verbs",
            "de": "Italienisch: Wichtige Verben",
            "es": "Italiano: Verbos Esenciales"
        },
        "badges": {
            "tr": "1030 Fiil / İtalyanca",
            "en": "1030 Verbs / Italian",
            "de": "1030 Verben / Italienisch",
            "es": "1030 Verbos / Italiano"
        },
        "nav_names": {
            "tr": "Fiiller (IT)",
            "en": "Verbs (IT)",
            "de": "Verben (IT)",
            "es": "Verbos (IT)"
        },
        "badge_color": "#10b981",
        "view_name": "ext_it",
        "dataset_file": "it_verbs.json",
        "term_col": "Infinito",
        "attr_col": "Presente",
        "extra_col": "Passato Prossimo",
        "filters": []
    },
    {
        "id": "pt_verbs",
        "setting_key": "plugin_pt_verbs",
        "default": False,
        "lang_code": "PT",
        "titles": {
            "tr": "Portekizce: En Çok Kullanılan Fiiller",
            "en": "Portuguese: Essential Verbs",
            "de": "Portugiesisch: Wichtige Verben",
            "es": "Portugués: Verbos Esenciales"
        },
        "badges": {
            "tr": "1010 Fiil / Portekizce",
            "en": "1010 Verbs / Portuguese",
            "de": "1010 Verben / Portugiesisch",
            "es": "1010 Verbos / Portugués"
        },
        "nav_names": {
            "tr": "Fiiller (PT)",
            "en": "Verbs (PT)",
            "de": "Verben (PT)",
            "es": "Verbos (PT)"
        },
        "badge_color": "#06b6d4",
        "view_name": "ext_pt",
        "dataset_file": "pt_verbs.json",
        "term_col": "Infinitivo",
        "attr_col": "Presente",
        "extra_col": "Pretérito",
        "filters": []
    },
    {
        "id": "nl_articles",
        "setting_key": "plugin_nl_articles",
        "default": False,
        "lang_code": "NL",
        "titles": {
            "tr": "Felemenkçe: İsimler & Artikeller (De, Het)",
            "en": "Dutch: Nouns & Articles (De, Het)",
            "de": "Niederländisch: Artikel (De, Het)",
            "es": "Holandés: Artículos (De, Het)"
        },
        "badges": {
            "tr": "1050 İsim / Felemenkçe",
            "en": "1050 Nouns / Dutch",
            "de": "1050 Nomen / Niederländisch",
            "es": "1050 Sustantivos / Holandés"
        },
        "nav_names": {
            "tr": "Artikeller (NL)",
            "en": "Articles (NL)",
            "de": "Artikel (NL)",
            "es": "Artículos (NL)"
        },
        "badge_color": "#fb923c",
        "view_name": "ext_nl",
        "dataset_file": "nl_articles.json",
        "term_col": "İsim",
        "attr_col": "Artikel",
        "extra_col": "Çoğul",
        "filters": ["de", "het"]
    },
    {
        "id": "sv_articles",
        "setting_key": "plugin_sv_articles",
        "default": False,
        "lang_code": "SV",
        "titles": {
            "tr": "İsveççe: İsimler & Artikeller (En, Ett)",
            "en": "Swedish: Nouns & Articles (En, Ett)",
            "de": "Schwedisch: Artikel (En, Ett)",
            "es": "Sueco: Artículos (En, Ett)"
        },
        "badges": {
            "tr": "1050 İsim / İsveççe",
            "en": "1050 Nouns / Swedish",
            "de": "1050 Nomen / Schwedisch",
            "es": "1050 Sustantivos / Sueco"
        },
        "nav_names": {
            "tr": "Artikeller (SV)",
            "en": "Articles (SV)",
            "de": "Artikel (SV)",
            "es": "Artículos (SV)"
        },
        "badge_color": "#38bdf8",
        "view_name": "ext_sv",
        "dataset_file": "sv_articles.json",
        "term_col": "İsim",
        "attr_col": "Artikel",
        "extra_col": "Çoğul",
        "filters": ["en", "ett"]
    },
    {
        "id": "zh_words",
        "setting_key": "plugin_zh_words",
        "default": False,
        "lang_code": "ZH",
        "titles": {
            "tr": "Çince: En Çok Kullanılan Kelimeler (HSK)",
            "en": "Chinese: Essential Vocabulary (HSK)",
            "de": "Chinesisch: Grundwortschatz (HSK)",
            "es": "Chino: Vocabulario Esencial (HSK)"
        },
        "badges": {
            "tr": "1050 Kelime / Çince",
            "en": "1050 Words / Chinese",
            "de": "1050 Wörter / Chinesisch",
            "es": "1050 Palabras / Chino"
        },
        "nav_names": {
            "tr": "Kelimeler (ZH)",
            "en": "Words (ZH)",
            "de": "Wörter (ZH)",
            "es": "Palabras (ZH)"
        },
        "badge_color": "#e11d48",
        "view_name": "ext_zh",
        "dataset_file": "zh_words.json",
        "term_col": "Karakter",
        "attr_col": "Pinyin",
        "extra_col": "Kategori",
        "filters": []
    },
    {
        "id": "ja_words",
        "setting_key": "plugin_ja_words",
        "default": False,
        "lang_code": "JA",
        "titles": {
            "tr": "Japonca: En Çok Kullanılan Kelimeler (JLPT)",
            "en": "Japanese: Essential Vocabulary (JLPT)",
            "de": "Japanisch: Grundwortschatz (JLPT)",
            "es": "Japonés: Vocabulario Esencial (JLPT)"
        },
        "badges": {
            "tr": "1050 Kelime / Japonca",
            "en": "1050 Words / Japanese",
            "de": "1050 Wörter / Japanisch",
            "es": "1050 Palabras / Japonés"
        },
        "nav_names": {
            "tr": "Kelimeler (JA)",
            "en": "Words (JA)",
            "de": "Wörter (JA)",
            "es": "Palabras (JA)"
        },
        "badge_color": "#ec4899",
        "view_name": "ext_ja",
        "dataset_file": "ja_words.json",
        "term_col": "Kanji / Kana",
        "attr_col": "Romaji",
        "extra_col": "Kategori",
        "filters": []
    },
    {
        "id": "ko_words",
        "setting_key": "plugin_ko_words",
        "default": False,
        "lang_code": "KO",
        "titles": {
            "tr": "Korece: En Çok Kullanılan Kelimeler (TOPIK)",
            "en": "Korean: Essential Vocabulary (TOPIK)",
            "de": "Koreanisch: Grundwortschatz (TOPIK)",
            "es": "Coreano: Vocabulario Esencial (TOPIK)"
        },
        "badges": {
            "tr": "1050 Kelime / Korece",
            "en": "1050 Words / Korean",
            "de": "1050 Wörter / Koreanisch",
            "es": "1050 Palabras / Coreano"
        },
        "nav_names": {
            "tr": "Kelimeler (KO)",
            "en": "Words (KO)",
            "de": "Wörter (KO)",
            "es": "Palabras (KO)"
        },
        "badge_color": "#8b5cf6",
        "view_name": "ext_ko",
        "dataset_file": "ko_words.json",
        "term_col": "Hangul",
        "attr_col": "Romaja",
        "extra_col": "Kategori",
        "filters": []
    },
    {
        "id": "ru_words",
        "setting_key": "plugin_ru_words",
        "default": False,
        "lang_code": "RU",
        "titles": {
            "tr": "Rusça: En Çok Kullanılan Kelimeler",
            "en": "Russian: Essential Vocabulary",
            "de": "Russisch: Grundwortschatz",
            "es": "Ruso: Vocabulario Esencial"
        },
        "badges": {
            "tr": "1050 Kelime / Rusça",
            "en": "1050 Words / Russian",
            "de": "1050 Wörter / Russisch",
            "es": "1050 Palabras / Ruso"
        },
        "nav_names": {
            "tr": "Kelimeler (RU)",
            "en": "Words (RU)",
            "de": "Wörter (RU)",
            "es": "Palabras (RU)"
        },
        "badge_color": "#3b82f6",
        "view_name": "ext_ru",
        "dataset_file": "ru_words.json",
        "term_col": "Kiril",
        "attr_col": "Okunuş",
        "extra_col": "Tür",
        "filters": []
    },
    {
        "id": "ar_words",
        "setting_key": "plugin_ar_words",
        "default": False,
        "lang_code": "AR",
        "titles": {
            "tr": "Arapça: En Çok Kullanılan Kelimeler",
            "en": "Arabic: Essential Vocabulary",
            "de": "Arabisch: Grundwortschatz",
            "es": "Árabe: Vocabulario Esencial"
        },
        "badges": {
            "tr": "1050 Kelime / Arapça",
            "en": "1050 Words / Arabic",
            "de": "1050 Wörter / Arabisch",
            "es": "1050 Palabras / Árabe"
        },
        "nav_names": {
            "tr": "Kelimeler (AR)",
            "en": "Words (AR)",
            "de": "Wörter (AR)",
            "es": "Palabras (AR)"
        },
        "badge_color": "#14b8a6",
        "view_name": "ext_ar",
        "dataset_file": "ar_words.json",
        "term_col": "Arapça",
        "attr_col": "Okunuş",
        "extra_col": "Tür",
        "filters": []
    },
    {
        "id": "hi_words",
        "setting_key": "plugin_hi_words",
        "default": False,
        "lang_code": "HI",
        "titles": {
            "tr": "Hintçe: En Çok Kullanılan Kelimeler",
            "en": "Hindi: Essential Vocabulary",
            "de": "Hindi: Grundwortschatz",
            "es": "Hindi: Vocabulario Esencial"
        },
        "badges": {
            "tr": "1050 Kelime / Hintçe",
            "en": "1050 Words / Hindi",
            "de": "1050 Wörter / Hindi",
            "es": "1050 Palabras / Hindi"
        },
        "nav_names": {
            "tr": "Kelimeler (HI)",
            "en": "Words (HI)",
            "de": "Wörter (HI)",
            "es": "Palabras (HI)"
        },
        "badge_color": "#f97316",
        "view_name": "ext_hi",
        "dataset_file": "hi_words.json",
        "term_col": "Devanagari",
        "attr_col": "Okunuş",
        "extra_col": "Kategori",
        "filters": []
    },
    {
        "id": "tr_words",
        "setting_key": "plugin_tr_words",
        "default": False,
        "lang_code": "TR",
        "titles": {
            "tr": "Türkçe: En Çok Kullanılan Temel Kelimeler",
            "en": "Turkish: Essential Vocabulary",
            "de": "Türkisch: Grundwortschatz",
            "es": "Turco: Vocabulario Esencial"
        },
        "badges": {
            "tr": "1050 Kelime / Türkçe",
            "en": "1050 Words / Turkish",
            "de": "1050 Wörter / Türkisch",
            "es": "1050 Palabras / Turco"
        },
        "nav_names": {
            "tr": "Kelimeler (TR)",
            "en": "Words (TR)",
            "de": "Wörter (TR)",
            "es": "Palabras (TR)"
        },
        "badge_color": "#10b981",
        "view_name": "ext_tr",
        "dataset_file": "tr_words.json",
        "term_col": "Kelime",
        "attr_col": "Tür",
        "extra_col": "Seviye",
        "filters": []
    }
]

AVAILABLE_EXTENSIONS.extend(LEARNING_EXTENSIONS)

# Geriye dönük uyumluluk alanları
for ext in AVAILABLE_EXTENSIONS:
    ext["title"] = ext["titles"]["tr"]
    ext["badge"] = ext["badges"]["tr"]
    ext["nav_name"] = ext["nav_names"]["tr"]
    ext["desc"] = ""


CORE_MENUS.append(dict(id='maker', setting_key='menu_visible_maker', default=True, icon='maker',
                      titles={'tr':'Eklenti kur','en':'Create extension','de':'Erweiterung erstellen','es':'Crear extensión'}, view_name='maker'))


class GreenSymbolicFlag(QWidget):
    """
    Ülkelerin bayraklarını gerçek, orijinal renkleriyle (kırmızı, mavi, beyaz, sarı vb.)
    ve simgeleriyle çizen yüksek kaliteli özel bayrak widget'ı.
    """
    def __init__(self, lang_code: str, parent=None):
        super().__init__(parent)
        self.lang_code = (lang_code or "").upper().strip()
        self.setFixedSize(50, 36)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        rect = QRectF(0, 0, w, h)

        # Yuvarlatılmış kenarlı kırpma yolu
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 6, 6)
        painter.setClipPath(clip_path)

        code = self.lang_code
        if code in ("EN", "GB"):
            # Birleşik Krallık / İngiltere (Union Jack)
            painter.fillRect(rect, QColor("#012169"))
            pen_white_diag = QPen(QColor("#ffffff"), 6.0)
            painter.setPen(pen_white_diag)
            painter.drawLine(0, 0, int(w), int(h))
            painter.drawLine(0, int(h), int(w), 0)
            pen_red_diag = QPen(QColor("#c8102e"), 3.0)
            painter.setPen(pen_red_diag)
            painter.drawLine(0, 0, int(w), int(h))
            painter.drawLine(0, int(h), int(w), 0)
            pen_white_cross = QPen(QColor("#ffffff"), 9.0)
            painter.setPen(pen_white_cross)
            painter.drawLine(0, int(h / 2), int(w), int(h / 2))
            painter.drawLine(int(w / 2), 0, int(w / 2), int(h))
            pen_red_cross = QPen(QColor("#c8102e"), 5.0)
            painter.setPen(pen_red_cross)
            painter.drawLine(0, int(h / 2), int(w), int(h / 2))
            painter.drawLine(int(w / 2), 0, int(w / 2), int(h))

        elif code == "DE":
            # Almanya: Siyah, Kırmızı, Altın Sarısı
            painter.fillRect(QRectF(0, 0, w, h / 3), QColor("#000000"))
            painter.fillRect(QRectF(0, h / 3, w, h / 3), QColor("#dd0000"))
            painter.fillRect(QRectF(0, 2 * h / 3, w, h / 3), QColor("#ffce00"))

        elif code == "FR":
            # Fransa: Mavi, Beyaz, Kırmızı
            painter.fillRect(QRectF(0, 0, w / 3, h), QColor("#002654"))
            painter.fillRect(QRectF(w / 3, 0, w / 3, h), QColor("#ffffff"))
            painter.fillRect(QRectF(2 * w / 3, 0, w / 3, h), QColor("#ed2939"))

        elif code == "ES":
            # İspanya: Kırmızı, Sarı, Kırmızı + Kalkan
            painter.fillRect(QRectF(0, 0, w, h / 4), QColor("#aa151b"))
            painter.fillRect(QRectF(0, h / 4, w, h / 2), QColor("#f1bf00"))
            painter.fillRect(QRectF(0, 3 * h / 4, w, h / 4), QColor("#aa151b"))
            painter.setBrush(QBrush(QColor("#aa151b")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(w * 0.22, h * 0.38, 7, 9), 2, 2)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(w * 0.22 + 3.5, h * 0.38 + 4.5), 1.5, 1.5)

        elif code == "IT":
            # İtalya: Yeşil, Beyaz, Kırmızı
            painter.fillRect(QRectF(0, 0, w / 3, h), QColor("#009246"))
            painter.fillRect(QRectF(w / 3, 0, w / 3, h), QColor("#ffffff"))
            painter.fillRect(QRectF(2 * w / 3, 0, w / 3, h), QColor("#ce2b37"))

        elif code == "PT":
            # Portekiz: Yeşil (40%), Kırmızı (60%) + Altın Küre
            painter.fillRect(QRectF(0, 0, w * 0.4, h), QColor("#046a38"))
            painter.fillRect(QRectF(w * 0.4, 0, w * 0.6, h), QColor("#da291c"))
            painter.setBrush(QBrush(QColor("#ffce00")))
            painter.setPen(QPen(QColor("#da291c"), 1.0))
            painter.drawEllipse(QPointF(w * 0.4, h * 0.5), 6, 6)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawRoundedRect(QRectF(w * 0.4 - 3, h * 0.5 - 4, 6, 8), 1, 1)

        elif code == "NL":
            # Hollanda: Kırmızı, Beyaz, Mavi
            painter.fillRect(QRectF(0, 0, w, h / 3), QColor("#ae1c28"))
            painter.fillRect(QRectF(0, h / 3, w, h / 3), QColor("#ffffff"))
            painter.fillRect(QRectF(0, 2 * h / 3, w, h / 3), QColor("#21468b"))

        elif code == "SV":
            # İsveç: Mavi zemin + Sarı İskandinav Haçı
            painter.fillRect(rect, QColor("#006aa7"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#fecc00")))
            painter.drawRect(QRectF(w * 0.3, 0, 7, h))
            painter.drawRect(QRectF(0, h * 0.4, w, 7))

        elif code == "ZH":
            # Çin: Kırmızı zemin + Sarı Yıldızlar
            painter.fillRect(rect, QColor("#de2910"))
            painter.setBrush(QBrush(QColor("#ffde00")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(w * 0.25, h * 0.35), 5.5, 5.5)
            painter.drawEllipse(QPointF(w * 0.42, h * 0.18), 2, 2)
            painter.drawEllipse(QPointF(w * 0.48, h * 0.30), 2, 2)
            painter.drawEllipse(QPointF(w * 0.48, h * 0.44), 2, 2)
            painter.drawEllipse(QPointF(w * 0.42, h * 0.56), 2, 2)

        elif code == "JA":
            # Japonya: Beyaz zemin + Kırmızı Güneş
            painter.fillRect(rect, QColor("#ffffff"))
            painter.setBrush(QBrush(QColor("#bc002d")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(w * 0.5, h * 0.5), 8, 8)

        elif code == "KO":
            # Güney Kore: Beyaz zemin + Taegeuk
            painter.fillRect(rect, QColor("#ffffff"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#cd2e3a")))
            painter.drawChord(QRectF(w * 0.32, h * 0.25, 18, 18), 0, 180 * 16)
            painter.setBrush(QBrush(QColor("#0047a0")))
            painter.drawChord(QRectF(w * 0.32, h * 0.25, 18, 18), 180 * 16, 180 * 16)
            painter.setPen(QPen(QColor("#000000"), 1.5))
            painter.drawLine(int(w * 0.12), int(h * 0.22), int(w * 0.22), int(h * 0.14))
            painter.drawLine(int(w * 0.78), int(h * 0.86), int(w * 0.88), int(h * 0.78))

        elif code == "RU":
            # Rusya: Beyaz, Mavi, Kırmızı
            painter.fillRect(QRectF(0, 0, w, h / 3), QColor("#ffffff"))
            painter.fillRect(QRectF(0, h / 3, w, h / 3), QColor("#0039a6"))
            painter.fillRect(QRectF(0, 2 * h / 3, w, h / 3), QColor("#d52b1e"))

        elif code == "AR":
            # Arapça: Siyah, Beyaz, Yeşil + Kırmızı Üçgen
            painter.fillRect(QRectF(0, 0, w, h / 3), QColor("#000000"))
            painter.fillRect(QRectF(0, h / 3, w, h / 3), QColor("#ffffff"))
            painter.fillRect(QRectF(0, 2 * h / 3, w, h / 3), QColor("#007a3d"))
            tri = QPolygonF([QPointF(0, 0), QPointF(w * 0.35, h * 0.5), QPointF(0, h)])
            painter.setBrush(QBrush(QColor("#ce1126")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(tri)

        elif code == "HI":
            # Hintçe: Safran, Beyaz, Yeşil + Lacivert Çakra
            painter.fillRect(QRectF(0, 0, w, h / 3), QColor("#ff9933"))
            painter.fillRect(QRectF(0, h / 3, w, h / 3), QColor("#ffffff"))
            painter.fillRect(QRectF(0, 2 * h / 3, w, h / 3), QColor("#138808"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#000080"), 1.5))
            painter.drawEllipse(QPointF(w * 0.5, h * 0.5), 4.5, 4.5)

        elif code == "TR":
            # Türkiye: Kırmızı zemin + Beyaz Hilal ve Yıldız
            painter.fillRect(rect, QColor("#e30a17"))
            p_moon = QPainterPath()
            p_moon.addEllipse(QPointF(w * 0.44, h * 0.5), 7.5, 7.5)
            p_inner = QPainterPath()
            p_inner.addEllipse(QPointF(w * 0.48, h * 0.5), 6.0, 6.0)
            crescent = p_moon.subtracted(p_inner)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(crescent)
            painter.drawEllipse(QPointF(w * 0.65, h * 0.5), 2.5, 2.5)

        else:
            painter.fillRect(rect, QColor("#334155"))
            painter.setBrush(QBrush(QColor("#f8fafc")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(w * 0.5, h * 0.5), 6, 6)

        # Dış kenarlık çerçevesi
        painter.setClipping(False)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)


CountryFlagWidget = GreenSymbolicFlag


class ExtensionCard(QFrame):
    """Tekil Eklenti Kartı - Alt açıklamaları ve badge kutusu kaldırılmış, yeşil monokrom bayraklı tasarım."""
    toggled = pyqtSignal(str, bool)
    open_requested = pyqtSignal(str)

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.data = data
        self.setting_key = data["setting_key"]
        self.is_active = settings.get(self.setting_key, data.get("default", False))

        self.setObjectName("ExtensionCard")
        self.setStyleSheet("""
            QFrame#ExtensionCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: 1.2px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Sol: Menü Vektörel İkonu (arkaplansız, saydam ve net) veya Bayrak
        if data.get("icon"):
            lbl_ic = QLabel()
            lbl_ic.setFixedSize(50, 36)
            lbl_ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_ic.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")
            lbl_ic.setPixmap(get_icon(data["icon"], 26, "#10b981").pixmap(26, 26))
            layout.addWidget(lbl_ic)
        else:
            flag_widget = GreenSymbolicFlag(data.get("lang_code", ""))
            layout.addWidget(flag_widget)

        # Orta: Başlık (1050 Fiil vb. rozet kutusu tamamen kaldırıldı)
        mid_box = QVBoxLayout()
        mid_box.setSpacing(4)
        mid_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        ui_lang = settings.get("ui_language", "tr")
        t_text = self.data["titles"].get(ui_lang, self.data["titles"].get("en", ""))
        self.lbl_title = QLabel(t_text)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc; background: transparent; border: none;")

        title_row.addWidget(self.lbl_title)
        title_row.addStretch()
        mid_box.addLayout(title_row)

        layout.addLayout(mid_box, 1)

        # Sağ: Aksiyon Butonları (Aktifleştir / Aç)
        right_box = QVBoxLayout()
        right_box.setSpacing(6)
        right_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_toggle = QPushButton()
        self.btn_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle.setFixedSize(145, 34)
        self.btn_toggle.clicked.connect(self._toggle_state)

        self.btn_open = QPushButton(t("ext_open_module", ui_lang))
        self.btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open.setFixedSize(145, 30)
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                font-size: 12px;
                font-weight: 800;
                border-radius: 6px;
                border: 1px solid rgba(56, 189, 248, 0.3);
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.btn_open.clicked.connect(lambda: self.open_requested.emit(self.data["view_name"]))

        right_box.addWidget(self.btn_toggle)
        right_box.addWidget(self.btn_open)
        layout.addLayout(right_box)

        self._refresh_ui()

    def _refresh_ui(self):
        ui_lang = settings.get("ui_language", "tr")
        t_text = self.data["titles"].get(ui_lang, self.data["titles"].get("en", ""))
        self.lbl_title.setText(t_text)
        self.btn_open.setText(t("ext_open_module", ui_lang))

        if self.is_active:
            self.btn_toggle.setText(t("ext_active_in_menu", ui_lang))
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: #ffffff;
                    font-size: 12px;
                    font-weight: 800;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #ef4444;
                    color: #ffffff;
                }
            """)
            self.btn_open.setVisible(True)
        else:
            self.btn_toggle.setText(t("ext_add_to_menu", ui_lang))
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #cbd5e1;
                    font-size: 12px;
                    font-weight: 700;
                    border-radius: 6px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QPushButton:hover {
                    background-color: #10b981;
                    color: #ffffff;
                    border-color: #10b981;
                }
            """)
            self.btn_open.setVisible(False)

    def _toggle_state(self):
        self.is_active = not self.is_active
        settings.set(self.setting_key, self.is_active)
        sfx.play_click()
        self._refresh_ui()
        self.toggled.emit(self.data["id"], self.is_active)


class ExtensionsView(QWidget):
    """
    Eklentiler & Tüm Menüler Yönetim Ekranı.
    Kullanıcı yan menüdeki tüm ana menüleri ve 15 dünya dili eklentilerini
    burada görebilir, dilediğini kapatıp açabilir ve doğrudan başlatabilir.
    """
    menu_toggled = pyqtSignal(str, bool)
    extension_toggled = pyqtSignal(str, bool)
    open_module_requested = pyqtSignal(str)
    personal_menu_toggled = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: List[ExtensionCard] = []
        self.personal_cards = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # Başlık & Hızlı Eylem Alanı
        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        ui_lang = settings.get("ui_language", "tr")

        self.lbl_title = QLabel(t("ext_page_title", ui_lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_sub = QLabel(ui_text('You can toggle all main menus and language packages from here.', ui_lang))
        self.lbl_sub.setProperty("class", "page-subtitle")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_sub)
        header_row.addLayout(title_box, 1)

        self.btn_reset_defaults = QPushButton(ui_text('Enable All', ui_lang))
        self.btn_reset_defaults.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset_defaults.setFixedHeight(36)
        self.btn_reset_defaults.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10b981;
                font-size: 12px;
                font-weight: 800;
                border-radius: 8px;
                border: 1px solid rgba(16, 185, 129, 0.35);
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
            }
        """)
        self.btn_reset_defaults.clicked.connect(self._reset_all_to_menu)
        header_row.addWidget(self.btn_reset_defaults, alignment=Qt.AlignmentFlag.AlignVCenter)

        main_layout.addLayout(header_row)

        # Kaydırılabilir Kart Listesi
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(container)
        self._cards_container=container
        self._cards_layout=c_layout
        c_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        c_layout.setContentsMargins(4, 6, 4, 16)
        c_layout.setSpacing(10)

        personal_header=QHBoxLayout()
        personal_title=label('MY EXTENSIONS',ui_lang,'eyebrow');personal_title.setStyleSheet(transform_preferences('color:#10b981;font-size:11px;font-weight:800;letter-spacing:1px;'))
        personal_header.addWidget(personal_title,1)
        create_button=button('Create extension',ui_lang,lambda:self.open_module_requested.emit('maker'),'maker');apply_studio_style(create_button);personal_header.addWidget(create_button)
        c_layout.addLayout(personal_header)
        self.personal_container=QWidget();self.personal_layout=QVBoxLayout(self.personal_container);self.personal_layout.setContentsMargins(0,0,0,0);self.personal_layout.setSpacing(10)
        self.personal_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.personal_container.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum)
        c_layout.addWidget(self.personal_container)
        self.reload_personal()

        # 1. BÖLÜM: Ana Menüler
        self.lbl_sec_core = QLabel(ui_text('CORE APPLICATION MENUS', ui_lang))
        self.lbl_sec_core.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 800; letter-spacing: 0.8px; margin-top: 4px; margin-bottom: 2px;")
        c_layout.addWidget(self.lbl_sec_core)

        for menu_item in CORE_MENUS + LEARNING_EXTENSIONS:
            card = ExtensionCard(menu_item)
            card.toggled.connect(self._on_card_toggled)
            card.open_requested.connect(self.open_module_requested.emit)
            self.cards.append(card)
            c_layout.addWidget(card)

        # 2. BÖLÜM: 15 Dünya Dili Eklentileri
        self.lbl_sec_lang = QLabel(ui_text('LANGUAGE & PRACTICE EXTENSIONS', ui_lang))
        self.lbl_sec_lang.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 800; letter-spacing: 0.8px; margin-top: 14px; margin-bottom: 2px;")
        c_layout.addWidget(self.lbl_sec_lang)

        for ext in AVAILABLE_EXTENSIONS:
            if ext in LEARNING_EXTENSIONS:
                continue
            card = ExtensionCard(ext)
            card.toggled.connect(self._on_card_toggled)
            card.open_requested.connect(self.open_module_requested.emit)
            self.cards.append(card)
            c_layout.addWidget(card)

        c_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_card_toggled(self, item_id: str, active: bool):
        core_ids = [m["id"] for m in CORE_MENUS]
        if item_id in core_ids:
            self.menu_toggled.emit(item_id, active)
        else:
            self.extension_toggled.emit(item_id, active)

    def reload_personal(self):
        while self.personal_layout.count():
            item=self.personal_layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()
        self.personal_cards=[]
        lang=settings.get('ui_language','en')
        documents=personal_extensions.documents()
        for kind,document in documents:
            card=QFrame();card.setProperty('studioPanel',True);apply_studio_style(card);card.document=document;card.kind=kind
            card.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum)
            body=QHBoxLayout(card);body.setContentsMargins(20,16,20,16);body.setSpacing(16)
            icon=QLabel();icon.setPixmap(get_icon(document.get('icon','table_grid'),30).pixmap(30,30));body.addWidget(icon)
            copy=QVBoxLayout();title=QLabel(document['name']);title.setTextFormat(Qt.TextFormat.PlainText);title.setWordWrap(True);title.setStyleSheet('font-size:16px;font-weight:700;');copy.addWidget(title)
            if document.get('description'):
                desc=QLabel(document['description']);desc.setTextFormat(Qt.TextFormat.PlainText);desc.setWordWrap(True);desc.setProperty('role','muted');copy.addWidget(desc)
            if kind=='table':
                detail=ui_text('Table · {rows} rows · {columns} columns',lang,rows=len(document['rows']),columns=len(document['columns']))
            else:
                from duocards.widgets.game_player import MODE_TITLES
                stats=custom_games.game_stats(document['id'])
                detail=ui_text('Game · {mode} · Played {plays} · Best {best}%',lang,mode=ui_text(MODE_TITLES[document['mode']],lang),plays=stats['plays'],best=stats['best'] or 0)
            subtitle=QLabel(detail);subtitle.setWordWrap(True);subtitle.setProperty('role','muted');copy.addWidget(subtitle);body.addLayout(copy,1)
            identifier=document['id']
            actions=QVBoxLayout();actions.setSpacing(8)
            card.menu_key=personal_extensions.menu_key(kind,identifier)
            card.is_active=personal_extensions.in_menu(kind,identifier)
            card.toggle_button=button('',lang,lambda item=card:self._toggle_personal(item))
            actions.addWidget(card.toggle_button)
            self._refresh_personal_toggle(card)
            open_actions=QHBoxLayout();open_actions.setSpacing(6)
            if kind=='game':open_actions.addWidget(button('Edit',lang,lambda key=identifier:self.open_module_requested.emit('edit-game:'+key),'settings'))
            card.open_button=button('Play' if kind=='game' else 'Open table',lang,lambda key=identifier,type=kind:self.open_module_requested.emit(type+':'+key),document.get('icon','table_grid'),'primary')
            open_actions.addWidget(card.open_button);actions.addLayout(open_actions);body.addLayout(actions)
            self.personal_layout.addWidget(card);self.personal_cards.append(card)
        if not documents:
            self.personal_layout.addWidget(label('Your tables and games will appear here. Create your first extension.',lang,'muted'))
        self.personal_container.updateGeometry()
        self._refresh_card_geometry()

    def _refresh_card_geometry(self):
        self.personal_layout.invalidate();self.personal_layout.activate()
        self._cards_layout.invalidate();self._cards_layout.activate()
        self._cards_container.updateGeometry()

    def showEvent(self,event):
        super().showEvent(event)
        self._refresh_card_geometry()

    def _refresh_personal_toggle(self,card):
        lang=settings.get('ui_language','en')
        card.toggle_button.setText(t('ext_active_in_menu' if card.is_active else 'ext_add_to_menu',lang))
        card.toggle_button.setToolTip(ui_text('Remove from the sidebar' if card.is_active else 'Add to the sidebar',lang))
        card.toggle_button.setCheckable(True);card.toggle_button.setChecked(card.is_active)
        card.toggle_button.setIcon(get_icon('check' if card.is_active else 'add',18))

    def _toggle_personal(self,card):
        card.is_active=not card.is_active
        settings.set(card.menu_key,card.is_active)
        self._refresh_personal_toggle(card)
        self.personal_menu_toggled.emit(card.kind+':'+card.document['id'],card.is_active)

    def _reset_all_to_menu(self):
        for card in self.cards:
            if not card.is_active:
                card.is_active = True
                settings.set(card.setting_key, True)
                card._refresh_ui()
                self._on_card_toggled(card.data["id"], True)
        settings.update({card.menu_key:True for card in self.personal_cards})
        for card in self.personal_cards:
            card.is_active=True;self._refresh_personal_toggle(card)
        self.personal_menu_toggled.emit('',True)
        sfx.play_correct()

    def update_language(self, lang: str):
        self.reload_personal()
        self.lbl_title.setText(t("ext_page_title", lang))
        self.lbl_sub.setText(ui_text('You can toggle all main menus and language packages from here.', lang))
        self.btn_reset_defaults.setText(ui_text('Enable All', lang))
        self.lbl_sec_core.setText(ui_text('CORE APPLICATION MENUS', lang))
        self.lbl_sec_lang.setText(ui_text('LANGUAGE & PRACTICE EXTENSIONS', lang))
        for card in self.cards:
            card._refresh_ui()
        localize_tree(self,lang)
