"""
Study Card - Almanca Artikeller (Der, Die, Das) ve İnteraktif Quiz Modülü
En sık kullanılan 120+ Almanca ismin artikelleri, çoğul halleri, telaffuzları ve artikel tahmin oyunu.
"""

import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedWidget, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.icons import get_icon
from duocards.i18n import t
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit

# 120+ En Sık Kullanılan Almanca İsimler & Artikeller
GERMAN_NOUNS = [
    # DER (Eril / Männlich)
    {"article": "der", "word": "Tisch", "plural": "die Tische", "meaning": "masa", "example": "Der Tisch ist groß."},
    {"article": "der", "word": "Stuhl", "plural": "die Stühle", "meaning": "sandalye", "example": "Der Stuhl ist bequem."},
    {"article": "der", "word": "Mann", "plural": "die Männer", "meaning": "adam, erkek", "example": "Der Mann liest ein Buch."},
    {"article": "der", "word": "Hund", "plural": "die Hunde", "meaning": "köpek", "example": "Der Hund bellt."},
    {"article": "der", "word": "Apfel", "plural": "die Äpfel", "meaning": "elma", "example": "Der Apfel ist süß."},
    {"article": "der", "word": "Kaffee", "plural": "-", "meaning": "kahve", "example": "Der Kaffee ist heiß."},
    {"article": "der", "word": "Tag", "plural": "die Tage", "meaning": "gün", "example": "Guten Tag!"},
    {"article": "der", "word": "Monat", "plural": "die Monate", "meaning": "ay (zaman)", "example": "Der Monat Mai ist schön."},
    {"article": "der", "word": "Morgen", "plural": "die Morgen", "meaning": "sabah", "example": "Guten Morgen!"},
    {"article": "der", "word": "Abend", "plural": "die Abende", "meaning": "akşam", "example": "Guten Abend!"},
    {"article": "der", "word": "Name", "plural": "die Namen", "meaning": "isim", "example": "Mein Name ist Max."},
    {"article": "der", "word": "Freund", "plural": "die Freunde", "meaning": "arkadaş, dost", "example": "Er ist mein bester Freund."},
    {"article": "der", "word": "Lehrer", "plural": "die Lehrer", "meaning": "öğretmen", "example": "Der Lehrer erklärt die Regel."},
    {"article": "der", "word": "Schlüssel", "plural": "die Schlüssel", "meaning": "anahtar", "example": "Wo ist der Schlüssel?"},
    {"article": "der", "word": "Weg", "plural": "die Wege", "meaning": "yol", "example": "Das ist der richtige Weg."},
    {"article": "der", "word": "Bahnhof", "plural": "die Bahnhöfe", "meaning": "tren istasyonu", "example": "Wir treffen uns am Bahnhof."},
    {"article": "der", "word": "Zug", "plural": "die Züge", "meaning": "tren", "example": "Der Zug kommt pünktlich."},
    {"article": "der", "word": "Bus", "plural": "die Busse", "meaning": "otobüs", "example": "Der Bus fährt ab."},
    {"article": "der", "word": "Flughafen", "plural": "die Flughäfen", "meaning": "havalimanı", "example": "Der Flughafen ist modern."},
    {"article": "der", "word": "Baum", "plural": "die Bäume", "meaning": "ağaç", "example": "Der Baum ist sehr alt."},
    {"article": "der", "word": "Kopf", "plural": "die Köpfe", "meaning": "baş, kafa", "example": "Mein Kopf tut weh."},
    {"article": "der", "word": "Arm", "plural": "die Arme", "meaning": "kol", "example": "Der Arm ist verletzt."},
    {"article": "der", "word": "Fuß", "plural": "die Füße", "meaning": "ayak", "example": "Wir gehen zu Fuß."},
    {"article": "der", "word": "Bauch", "plural": "die Bäuche", "meaning": "karın, göbek", "example": "Mein Bauch ist voll."},
    {"article": "der", "word": "Kuchen", "plural": "die Kuchen", "meaning": "kek, pasta", "example": "Der Kuchen schmeckt lecker."},
    {"article": "der", "word": "Tee", "plural": "-", "meaning": "çay", "example": "Ich trinke gern grünen Tee."},
    {"article": "der", "word": "Zucker", "plural": "-", "meaning": "şeker", "example": "Der Zucker ist weiß."},
    {"article": "der", "word": "Reis", "plural": "-", "meaning": "pirinç", "example": "Der Reis ist gekocht."},
    {"article": "der", "word": "Käse", "plural": "-", "meaning": "peynir", "example": "Der Käse schmeckt gut."},
    {"article": "der", "word": "Schrank", "plural": "die Schränke", "meaning": "dolap", "example": "Der Schrank ist aus Holz."},
    {"article": "der", "word": "Computer", "plural": "die Computer", "meaning": "bilgisayar", "example": "Der Computer ist neu."},
    {"article": "der", "word": "Fernseher", "plural": "die Fernseher", "meaning": "televizyon", "example": "Der Fernseher läuft."},
    {"article": "der", "word": "Kühlschrank", "plural": "die Kühlschränke", "meaning": "buzdolabı", "example": "Im Kühlschrank ist Milch."},
    {"article": "der", "word": "Brief", "plural": "die Briefe", "meaning": "mektup", "example": "Ich habe einen Brief erhalten."},
    {"article": "der", "word": "Kugelschreiber", "plural": "die Kugelschreiber", "meaning": "tükenmez kalem", "example": "Hier ist dein Kugelschreiber."},
    {"article": "der", "word": "Sommer", "plural": "die Sommer", "meaning": "yaz mevsimi", "example": "Der Sommer ist warm."},
    {"article": "der", "word": "Winter", "plural": "die Winter", "meaning": "kış mevsimi", "example": "Im Winter schneit es."},
    {"article": "der", "word": "Regen", "plural": "-", "meaning": "yağmur", "example": "Der Regen hört auf."},
    {"article": "der", "word": "Wind", "plural": "die Winde", "meaning": "rüzgar", "example": "Der Wind weht stark."},

    # DIE (Dişil / Weiblich)
    {"article": "die", "word": "Frau", "plural": "die Frauen", "meaning": "kadın, bayan", "example": "Die Frau arbeitet hier."},
    {"article": "die", "word": "Katze", "plural": "die Katzen", "meaning": "kedi", "example": "Die Katze schläft."},
    {"article": "die", "word": "Sonne", "plural": "-", "meaning": "güneş", "example": "Die Sonne scheint."},
    {"article": "die", "word": "Blume", "plural": "die Blumen", "meaning": "çiçek", "example": "Die Blume riecht gut."},
    {"article": "die", "word": "Stadt", "plural": "die Städte", "meaning": "şehir", "example": "Berlin ist eine große Stadt."},
    {"article": "die", "word": "Straße", "plural": "die Straßen", "meaning": "cadde, sokak", "example": "Die Straße ist breit."},
    {"article": "die", "word": "Schule", "plural": "die Schulen", "meaning": "okul", "example": "Die Schule fängt um 8 an."},
    {"article": "die", "word": "Zeit", "plural": "die Zeiten", "meaning": "zaman, vakit", "example": "Ich habe leider keine Zeit."},
    {"article": "die", "word": "Uhr", "plural": "die Uhren", "meaning": "saat", "example": "Wie viel Uhr ist es?"},
    {"article": "die", "word": "Nacht", "plural": "die Nächte", "meaning": "gece", "example": "Gute Nacht!"},
    {"article": "die", "word": "Woche", "plural": "die Wochen", "meaning": "hafta", "example": "Die Woche hat sieben Tage."},
    {"article": "die", "word": "Mutter", "plural": "die Mütter", "meaning": "anne", "example": "Meine Mutter kocht gern."},
    {"article": "die", "word": "Tochter", "plural": "die Töchter", "meaning": "kız evlat", "example": "Ihre Tochter ist Studentin."},
    {"article": "die", "word": "Schwester", "plural": "die Schwestern", "meaning": "kız kardeş", "example": "Das ist meine Schwester."},
    {"article": "die", "word": "Arbeit", "plural": "die Arbeiten", "meaning": "iş, çalışma", "example": "Die Arbeit macht Spaß."},
    {"article": "die", "word": "Tür", "plural": "die Türen", "meaning": "kapı", "example": "Bitte schließen Sie die Tür."},
    {"article": "die", "word": "Tasche", "plural": "die Taschen", "meaning": "çanta", "example": "Die Tasche ist schwer."},
    {"article": "die", "word": "Wohnung", "plural": "die Wohnungen", "meaning": "daire, ev", "example": "Die Wohnung ist modern."},
    {"article": "die", "word": "Küche", "plural": "die Küchen", "meaning": "mutfak", "example": "Wir sitzen in der Küche."},
    {"article": "die", "word": "Lampe", "plural": "die Lampen", "meaning": "lamba", "example": "Die Lampe ist hell."},
    {"article": "die", "word": "Zeitung", "plural": "die Zeitungen", "meaning": "gazete", "example": "Er liest die Zeitung."},
    {"article": "die", "word": "Sprache", "plural": "die Sprachen", "meaning": "dil, lisan", "example": "Deutsch ist eine schöne Sprache."},
    {"article": "die", "word": "Frage", "plural": "die Fragen", "meaning": "soru", "example": "Ich habe eine Frage."},
    {"article": "die", "word": "Antwort", "plural": "die Antworten", "meaning": "cevap", "example": "Die Antwort ist richtig."},
    {"article": "die", "word": "Flasche", "plural": "die Flaschen", "meaning": "şişe", "example": "Eine Flasche Wasser, bitte."},
    {"article": "die", "word": "Milch", "plural": "-", "meaning": "süt", "example": "Die Milch steht im Kühlschrank."},
    {"article": "die", "word": "Schokolade", "plural": "die Schokoladen", "meaning": "çikolata", "example": "Ich liebe Schokolade."},
    {"article": "die", "word": "Suppe", "plural": "die Suppen", "meaning": "çorba", "example": "Die Suppe ist heiß."},
    {"article": "die", "word": "Hand", "plural": "die Hände", "meaning": "el", "example": "Gib mir deine Hand."},
    {"article": "die", "word": "Nase", "plural": "die Nasen", "meaning": "burun", "example": "Meine Nase läuft."},
    {"article": "die", "word": "Brille", "plural": "die Brillen", "meaning": "gözlük", "example": "Wo ist meine Brille?"},
    {"article": "die", "word": "Reise", "plural": "die Reisen", "meaning": "seyahat, yolculuk", "example": "Gute Reise!"},
    {"article": "die", "word": "Musik", "plural": "-", "meaning": "müzik", "example": "Ich höre gern Musik."},
    {"article": "die", "word": "Familie", "plural": "die Familien", "meaning": "aile", "example": "Meine Familie ist groß."},
    {"article": "die", "word": "Freundin", "plural": "die Freundinnen", "meaning": "kız arkadaş", "example": "Sie ist meine Freundin."},
    {"article": "die", "word": "Hilfe", "plural": "-", "meaning": "yardım", "example": "Brauchst du Hilfe?"},

    # DAS (Nötr / Sächlich)
    {"article": "das", "word": "Haus", "plural": "die Häuser", "meaning": "ev, bina", "example": "Das Haus ist neu."},
    {"article": "das", "word": "Kind", "plural": "die Kinder", "meaning": "çocuk", "example": "Das Kind spielt im Garten."},
    {"article": "das", "word": "Auto", "plural": "die Autos", "meaning": "araba", "example": "Das Auto fährt schnell."},
    {"article": "das", "word": "Buch", "plural": "die Bücher", "meaning": "kitap", "example": "Das Buch ist spannend."},
    {"article": "das", "word": "Bett", "plural": "die Betten", "meaning": "yatak", "example": "Das Bett ist weich."},
    {"article": "das", "word": "Zimmer", "plural": "die Zimmer", "meaning": "oda", "example": "Das Zimmer ist sauber."},
    {"article": "das", "word": "Fenster", "plural": "die Fenster", "meaning": "pencere", "example": "Bitte öffne das Fenster."},
    {"article": "das", "word": "Bild", "plural": "die Bilder", "meaning": "resim, tablo", "example": "Das Bild gefällt mir."},
    {"article": "das", "word": "Mädchen", "plural": "die Mädchen", "meaning": "genç kız", "example": "Das Mädchen lacht."},
    {"article": "das", "word": "Wasser", "plural": "-", "meaning": "su", "example": "Das Wasser ist frisch."},
    {"article": "das", "word": "Brot", "plural": "die Brote", "meaning": "ekmek", "example": "Frisches Brot riecht gut."},
    {"article": "das", "word": "Geld", "plural": "-", "meaning": "para", "example": "Zeit ist Geld."},
    {"article": "das", "word": "Telefon", "plural": "die Telefone", "meaning": "telefon", "example": "Das Telefon klingelt."},
    {"article": "das", "word": "Handy", "plural": "die Handys", "meaning": "cep telefonu", "example": "Mein Handy ist leer."},
    {"article": "das", "word": "Jahr", "plural": "die Jahre", "meaning": "yıl, sene", "example": "Frohes neues Jahr!"},
    {"article": "das", "word": "Leben", "plural": "die Leben", "meaning": "hayat, yaşam", "example": "Das Leben ist schön."},
    {"article": "das", "word": "Wort", "plural": "die Wörter", "meaning": "kelime", "example": "Was bedeutet dieses Wort?"},
    {"article": "das", "word": "Problem", "plural": "die Probleme", "meaning": "sorun, problem", "example": "Kein Problem!"},
    {"article": "das", "word": "Thema", "plural": "die Themen", "meaning": "konu, tema", "example": "Das ist ein wichtiges Thema."},
    {"article": "das", "word": "Beispiel", "plural": "die Beispiele", "meaning": "örnek", "example": "Zum Beispiel..."},
    {"article": "das", "word": "Essen", "plural": "-", "meaning": "yemek", "example": "Das Essen ist fertig."},
    {"article": "das", "word": "Trinken", "plural": "-", "meaning": "içecek", "example": "Möchtest du etwas zu trinken?"},
    {"article": "das", "word": "Fleisch", "plural": "-", "meaning": "et", "example": "Ich esse kein Fleisch."},
    {"article": "das", "word": "Ei", "plural": "die Eier", "meaning": "yumurta", "example": "Möchtest du ein gekochtes Ei?"},
    {"article": "das", "word": "Salz", "plural": "-", "meaning": "tuz", "example": "Kannst du mir das Salz reichen?"},
    {"article": "das", "word": "Bier", "plural": "die Biere", "meaning": "bira", "example": "Ein kühles Bier."},
    {"article": "das", "word": "Auge", "plural": "die Augen", "meaning": "göz", "example": "Sie hat blaue Augen."},
    {"article": "das", "word": "Ohr", "plural": "die Ohren", "meaning": "kulak", "example": "Meine Ohren tun weh."},
    {"article": "das", "word": "Gesicht", "plural": "die Gesichter", "meaning": "yüz, çehre", "example": "Ein freundliches Gesicht."},
    {"article": "das", "word": "Haar", "plural": "die Haare", "meaning": "saç, kıl", "example": "Sie hat langes Haar."},
    {"article": "das", "word": "Herz", "plural": "die Herzen", "meaning": "kalp", "example": "Aus ganzem Herzen."},
    {"article": "das", "word": "Fahrrad", "plural": "die Fahrräder", "meaning": "bisiklet", "example": "Er fährt mit dem Fahrrad."},
    {"article": "das", "word": "Flugzeug", "plural": "die Flugzeuge", "meaning": "uçak", "example": "Das Flugzeug landet."},
    {"article": "das", "word": "Schiff", "plural": "die Schiffe", "meaning": "gemi", "example": "Das Schiff fährt auf dem Meer."},
    {"article": "das", "word": "Hotel", "plural": "die Hotels", "meaning": "otel", "example": "Das Hotel ist zentral."},
    {"article": "das", "word": "Restaurant", "plural": "die Restaurants", "meaning": "restoran", "example": "Ein italienisches Restaurant."},
    {"article": "das", "word": "Kino", "plural": "die Kinos", "meaning": "sinema", "example": "Wir gehen heute ins Kino."},
    {"article": "das", "word": "Wetter", "plural": "-", "meaning": "hava, hava durumu", "example": "Das Wetter ist herrlich."},
    {"article": "das", "word": "Tier", "plural": "die Tiere", "meaning": "hayvan", "example": "Ich liebe Tiere."},
]


class GermanArticlesView(QWidget):
    """
    Almanca Artikeller (Der, Die, Das) Rehberi ve İnteraktif Quiz Oyunu.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")

        # Quiz durumu
        self._quiz_score = 0
        self._quiz_streak = 0
        self._current_quiz_item = None
        self._is_quiz_busy = False

        self._filter_article = "all"  # "all", "der", "die", "das"

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 24)
        main_layout.setSpacing(16)

        # Üst Başlık & Sekmeler
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        titles_box = QVBoxLayout()
        titles_box.setSpacing(2)
        self.lbl_title = QLabel(" Almanca: Artikeller (Der, Die, Das)")
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel("En çok kullanılan 120+ ismin artikelleri, çoğulları ve pratik artikel testi.")
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        titles_box.addWidget(self.lbl_title)
        titles_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(titles_box)
        header_row.addStretch()

        # Mod Değiştirici Butonlar (Tablo vs Quiz Oyunu)
        self.btn_tab_table = QPushButton(" Kelime Tablosu")
        self.btn_tab_table.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_table.setFixedHeight(38)
        self.btn_tab_table.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 10px;
                padding: 0 18px;
                border: none;
            }
        """)
        self.btn_tab_table.clicked.connect(self._show_table_view)

        self.btn_tab_quiz = QPushButton(" Artikel Testi")
        self.btn_tab_quiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_quiz.setFixedHeight(38)
        self.btn_tab_quiz.setStyleSheet("""
            QPushButton {
                background-color: #162032;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 0 18px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        self.btn_tab_quiz.clicked.connect(self._show_quiz_view)

        header_row.addWidget(self.btn_tab_table)
        header_row.addWidget(self.btn_tab_quiz)
        main_layout.addLayout(header_row)

        # Yığın (Stacked Widget: Tablo ve Quiz)
        self.stack = QStackedWidget()

        # ---------------- SAYFA 1: KELİME TABLOSU ----------------
        table_page = QWidget()
        t_layout = QVBoxLayout(table_page)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(12)

        # Filtre ve Arama Çubuğu
        f_row = QHBoxLayout()
        f_row.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("İsim veya Türkçe anlam ara... (örn: Hund, ev, masa)")
        self.input_search.setFixedHeight(40)
        self.input_search.textChanged.connect(self._filter_table)
        f_row.addWidget(self.input_search, 1)

        # Artikel Hızlı Filtre Butonları
        self.btn_filter_all = self._create_filter_btn("Tümü (120+)", "all", is_active=True)
        self.btn_filter_der = self._create_filter_btn("DER (Eril)", "der", color="#38bdf8")
        self.btn_filter_die = self._create_filter_btn("DIE (Dişil)", "die", color="#f43f5e")
        self.btn_filter_das = self._create_filter_btn("DAS (Nötr)", "das", color="#10b981")

        f_row.addWidget(self.btn_filter_all)
        f_row.addWidget(self.btn_filter_der)
        f_row.addWidget(self.btn_filter_die)
        f_row.addWidget(self.btn_filter_das)
        t_layout.addLayout(f_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Artikel", "İsim (Wort)", "Çoğul (Plural)", "Anlamı", "Telaffuz"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(4, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        t_layout.addWidget(self.table)
        self.stack.addWidget(table_page)

        # ---------------- SAYFA 2: İNTERAKTİF ARTİKEL TESTİ (QUIZ) ----------------
        quiz_page = QWidget()
        q_layout = QVBoxLayout(quiz_page)
        q_layout.setContentsMargins(0, 10, 0, 10)
        q_layout.setSpacing(20)
        q_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Skor ve Seri Kartı (Çizgisiz)
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 12px;
                border: none;
                padding: 8px 24px;
            }
        """)
        s_layout = QHBoxLayout(stats_frame)
        s_layout.setSpacing(30)

        self.lbl_quiz_score = QLabel(ui_text(' Correct: 0', self.lang))
        self.lbl_quiz_score.setStyleSheet("color: #10b981; font-weight: 800; font-size: 15px;")
        self.lbl_quiz_streak = QLabel(ui_text(' Streak: 0', self.lang))
        self.lbl_quiz_streak.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 15px;")

        s_layout.addWidget(self.lbl_quiz_score)
        s_layout.addWidget(self.lbl_quiz_streak)
        q_layout.addWidget(stats_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Ana Quiz Kartı (Enlemesine Dikdörtgen, Çizgisiz)
        self.quiz_card = QFrame()
        self.quiz_card.setMinimumWidth(740)
        self.quiz_card.setMaximumWidth(1020)
        self.quiz_card.setFixedHeight(210)
        self.quiz_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.quiz_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: none;
                border-radius: 20px;
                padding: 16px 28px;
            }
        """)
        qc_layout = QVBoxLayout(self.quiz_card)
        qc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_layout.setSpacing(12)

        self.lbl_quiz_hint = QLabel(ui_text('What is the article for this noun?', self.lang))
        self.lbl_quiz_hint.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
        self.lbl_quiz_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Kelime ve Dinleme Butonu Satırı (Kelimeden hemen sonra, aralık sıkı ve ortalı)
        word_row = QHBoxLayout()
        word_row.setSpacing(8)
        word_row.setContentsMargins(0, 0, 0, 0)
        word_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_row.addStretch()

        self.lbl_quiz_word = QLabel("Hund")
        self.lbl_quiz_word.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.lbl_quiz_word.setStyleSheet("""
            color: #ffffff;
            font-size: 40px;
            font-weight: 900;
            letter-spacing: 1px;
            background: transparent;
        """)
        self.lbl_quiz_word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_row.addWidget(self.lbl_quiz_word)

        self.btn_quiz_audio = QPushButton()
        self.btn_quiz_audio.setIcon(get_icon("audio", 24, "#10b981"))
        self.btn_quiz_audio.setIconSize(QSize(24, 24))
        self.btn_quiz_audio.setToolTip(ui_text('Listen to word', self.lang))
        self.btn_quiz_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_quiz_audio.setFixedSize(36, 36)
        self.btn_quiz_audio.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.15);
            }
        """)
        self.btn_quiz_audio.clicked.connect(self._play_quiz_audio)
        word_row.addWidget(self.btn_quiz_audio)
        word_row.addStretch()

        self.lbl_quiz_meaning = QLabel("köpek (die Hunde)")
        self.lbl_quiz_meaning.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 700;")
        self.lbl_quiz_meaning.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_quiz_feedback = QLabel("")
        self.lbl_quiz_feedback.setStyleSheet("font-size: 15px; font-weight: 800;")
        self.lbl_quiz_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qc_layout.addWidget(self.lbl_quiz_hint)
        qc_layout.addLayout(word_row)
        qc_layout.addWidget(self.lbl_quiz_meaning)
        qc_layout.addWidget(self.lbl_quiz_feedback)
        q_layout.addWidget(self.quiz_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Artikel Seçim Butonları: DER, DIE, DAS (Tek Satırda, Çizgisiz)
        btn_container = QWidget()
        btn_container.setMinimumWidth(740)
        btn_container.setMaximumWidth(1020)
        btn_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_box = QHBoxLayout(btn_container)
        btn_box.setContentsMargins(0, 0, 0, 0)
        btn_box.setSpacing(14)

        self.btn_der = self._create_article_btn("DER", "#38bdf8", "der")
        self.btn_die = self._create_article_btn("DIE", "#f43f5e", "die")
        self.btn_das = self._create_article_btn("DAS", "#10b981", "das")

        btn_box.addWidget(self.btn_der, 1)
        btn_box.addWidget(self.btn_die, 1)
        btn_box.addWidget(self.btn_das, 1)
        q_layout.addWidget(btn_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sonraki Soru Butonu
        self.btn_next_question = QPushButton(ui_text('Next Word', self.lang))
        self.btn_next_question.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_question.setFixedSize(170, 38)
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
        self.btn_next_question.clicked.connect(self._next_quiz_question)
        q_layout.addWidget(self.btn_next_question, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(quiz_page)
        main_layout.addWidget(self.stack)

        # Tabloyu doldur
        self._populate_table(GERMAN_NOUNS)

    def _create_filter_btn(self, text: str, article_val: str, color: str = "#10b981", is_active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(38)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color if is_active else '#111827'};
                color: {'#ffffff' if is_active else '#94a3b8'};
                font-size: 12px;
                font-weight: 700;
                border-radius: 8px;
                padding: 0 14px;
                border: 1px solid {color if is_active else 'rgba(255, 255, 255, 0.08)'};
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #ffffff;
            }}
        """)
        btn.clicked.connect(lambda: self._set_article_filter(article_val))
        return btn

    def _create_article_btn(self, text: str, color: str, article_val: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(52)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1e293b;
                color: {color};
                font-size: 18px;
                font-weight: 900;
                border-radius: 12px;
                border: none;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #ffffff;
                border: none;
            }}
        """)
        btn.clicked.connect(lambda: self._on_article_chosen(article_val))
        return btn

    def _show_table_view(self):
        self.btn_tab_table.setStyleSheet("""
            background-color: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; border-radius: 10px; padding: 0 18px; border: none;
        """)
        self.btn_tab_quiz.setStyleSheet("""
            background-color: #162032; color: #94a3b8; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 0 18px; border: 1px solid rgba(255, 255, 255, 0.05);
        """)
        self.stack.setCurrentIndex(0)

    def _show_quiz_view(self):
        self.btn_tab_quiz.setStyleSheet("""
            background-color: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; border-radius: 10px; padding: 0 18px; border: none;
        """)
        self.btn_tab_table.setStyleSheet("""
            background-color: #162032; color: #94a3b8; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 0 18px; border: 1px solid rgba(255, 255, 255, 0.05);
        """)
        self.stack.setCurrentIndex(1)
        if not self._current_quiz_item:
            self._next_quiz_question()

    def _set_article_filter(self, article_val: str):
        self._filter_article = article_val
        for btn, val in [
            (self.btn_filter_all, "all"),
            (self.btn_filter_der, "der"),
            (self.btn_filter_die, "die"),
            (self.btn_filter_das, "das")
        ]:
            is_cur = (val == article_val)
            col = "#38bdf8" if val == "der" else ("#f43f5e" if val == "die" else "#10b981")
            btn.setChecked(is_cur)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {col if is_cur else '#111827'};
                    color: {'#ffffff' if is_cur else '#94a3b8'};
                    font-size: 12px;
                    font-weight: 700;
                    border-radius: 8px;
                    padding: 0 14px;
                    border: 1px solid {col if is_cur else 'rgba(255, 255, 255, 0.08)'};
                }}
            """)
        self._filter_table()

    def _filter_table(self):
        q = self.input_search.text().strip().lower()
        items = []
        for n in GERMAN_NOUNS:
            if self._filter_article != "all" and n["article"] != self._filter_article:
                continue
            if q:
                if (q not in n["word"].lower() and
                    q not in n["meaning"].lower() and
                    q not in n["plural"].lower()):
                    continue
            items.append(n)
        self._populate_table(items)

    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            art = item["article"].upper()
            art_color = "#38bdf8" if item["article"] == "der" else ("#f43f5e" if item["article"] == "die" else "#10b981")

            # 0: Artikel
            lbl_art = QLabel(f" {art} ")
            lbl_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_art.setStyleSheet(f"color: {art_color}; font-weight: 900; font-size: 13px; background: transparent;")
            self.table.setCellWidget(row, 0, lbl_art)

            # 1: İsim
            it_word = QTableWidgetItem(item["word"])
            it_word.setFont(self.font())
            it_word.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 1, it_word)

            # 2: Çoğul
            it_plural = QTableWidgetItem(item["plural"])
            it_plural.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 2, it_plural)

            # 3: Anlamı
            it_mean = QTableWidgetItem(item["meaning"])
            it_mean.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 3, it_mean)

            # 4: Ses Butonu
            btn_play = QPushButton()
            btn_play.setIcon(get_icon("audio", 18, "#10b981"))
            btn_play.setIconSize(QSize(18, 18))
            btn_play.setToolTip("Artikeli ile dinle")
            btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_play.setFixedSize(36, 32)
            btn_play.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #10b981;
                    color: #ffffff;
                }
            """)
            full_word = f"{item['article']} {item['word']}"
            btn_play.clicked.connect(lambda ch, w=full_word: audio_player.play_pronunciation(w, lang="de"))

            cell_w = QWidget()
            c_lay = QHBoxLayout(cell_w)
            c_lay.setContentsMargins(0, 0, 0, 0)
            c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_lay.addWidget(btn_play)
            self.table.setCellWidget(row, 4, cell_w)

    # ---------------- QUIZ MANTIĞI ----------------

    def _play_quiz_audio(self):
        if getattr(self, "_current_quiz_item", None):
            word = self._current_quiz_item.get("word", "")
            article = self._current_quiz_item.get("article", "")
            if word:
                full_word = f"{article} {word}".strip()
                sfx.play_click()
                audio_player.play_pronunciation(full_word, lang="de")

    def _next_quiz_question(self):
        self._is_quiz_busy = False
        self.btn_der.setEnabled(True)
        self.btn_die.setEnabled(True)
        self.btn_das.setEnabled(True)
        self.lbl_quiz_feedback.setText("")

        self._current_quiz_item = random.choice(GERMAN_NOUNS)
        self.lbl_quiz_word.setText(self._current_quiz_item["word"])
        self.lbl_quiz_meaning.setText(f"{self._current_quiz_item['meaning']}  •  Çoğul: {self._current_quiz_item['plural']}")

    def _on_article_chosen(self, chosen_article: str):
        if self._is_quiz_busy or not self._current_quiz_item:
            return

        self._is_quiz_busy = True
        correct_article = self._current_quiz_item["article"]
        word = self._current_quiz_item["word"]

        # Doğru telaffuzu çal
        audio_player.play_pronunciation(f"{correct_article} {word}", lang="de")

        if chosen_article == correct_article:
            sfx.play_correct()
            self._quiz_score += 1
            self._quiz_streak += 1
            self.lbl_quiz_feedback.setStyleSheet("color: #00ff88; font-size: 17px; font-weight: 900;")
            self.lbl_quiz_feedback.setText(f" Harika! {correct_article.upper()} {word}")
        else:
            sfx.play_wrong()
            self._quiz_streak = 0
            self.lbl_quiz_feedback.setStyleSheet("color: #ef4444; font-size: 16px; font-weight: 800;")
            self.lbl_quiz_feedback.setText(f" Yanlış! Doğrusu: {correct_article.upper()} {word}")

        self.lbl_quiz_score.setText(ui_text(' Correct: {self._quiz_score}', self.lang, **{'self._quiz_score': self._quiz_score}))
        self.lbl_quiz_streak.setText(ui_text(' Streak: {self._quiz_streak}', self.lang, **{'self._quiz_streak': self._quiz_streak}))

        # 1.4 saniye sonra otomatik bir sonraki kelimeye geç
        QTimer.singleShot(1400, self._next_quiz_question)

    def keyPressEvent(self, event):
        key = event.key()
        if self.stack.currentIndex() == 1 and not self._is_quiz_busy:
            if key in (Qt.Key.Key_1, Qt.Key.Key_R):
                self._on_article_chosen("der")
                return
            elif key in (Qt.Key.Key_2, Qt.Key.Key_E):
                self._on_article_chosen("die")
                return
            elif key in (Qt.Key.Key_3, Qt.Key.Key_S):
                self._on_article_chosen("das")
                return
            elif key == Qt.Key.Key_Space:
                self._play_quiz_audio()
                return
        super().keyPressEvent(event)

    def update_language(self, lang: str):
        self.lang = lang
        title_map = {
            "tr": "Almanca Artikeller (Der, Die, Das)",
            "en": "German Articles (Der, Die, Das)",
            "de": "Deutsche Artikel (Der, Die, Das)",
            "es": "Artículos en alemán (Der, Die, Das)"
        }
        sub_map = {
            "tr": "En sık kullanılan 120+ Almanca ismin artikelleri ve interaktif artikel tahmin oyunu.",
            "en": "Most common 120+ German nouns with articles, plurals and interactive guessing quiz.",
            "de": "Häufigste deutsche Nomen mit Artikeln, Pluralformen und interaktivem Quiz.",
            "es": "Sustantivos más comunes en alemán con artículos, plurales y quiz interactivo."
        }
        self.lbl_title.setText(title_map.get(lang, title_map["en"]))
        self.lbl_subtitle.setText(sub_map.get(lang, sub_map["en"]))
        tab_t_map = {"tr": "İsim Tablosu", "en": "Noun Table", "de": "Nomentabelle", "es": "Tabla de sustantivos"}
        tab_q_map = {"tr": "Artikel Testi", "en": "Article Quiz", "de": "Artikel-Quiz", "es": "Quiz de artículos"}
        self.btn_tab_table.setText(tab_t_map.get(lang, "Noun Table"))
        self.btn_tab_quiz.setText(tab_q_map.get(lang, "Article Quiz"))

        search_map = {
            "tr": "Almanca isim veya Türkçe anlam ara...",
            "en": "Search noun or meaning...",
            "de": "Nomen oder Bedeutung suchen...",
            "es": "Buscar sustantivo o significado..."
        }
        self.input_search.setPlaceholderText(search_map.get(lang, "Search noun or meaning..."))
        col_w = {"tr": "İsim (Wort)", "en": "Noun (Wort)", "de": "Nomen (Wort)", "es": "Sustantivo (Wort)"}.get(lang, "Noun (Wort)")
        col_m = {"tr": "Anlamı", "en": "Meaning", "de": "Bedeutung", "es": "Significado"}.get(lang, "Meaning")
        col_a = {"tr": "Telaffuz", "en": "Audio", "de": "Audio", "es": "Audio"}.get(lang, "Audio")
        self.table.setHorizontalHeaderLabels(["Artikel", col_w, "Plural", col_m, col_a])

        hint_map = {
            "tr": "Bu ismin artikeli nedir?",
            "en": "What is the article for this noun?",
            "de": "Welcher Artikel gehört zu diesem Nomen?",
            "es": "¿Cuál es el artículo de este sustantivo?"
        }
        self.lbl_quiz_hint.setText(hint_map.get(lang, hint_map["en"]))
        next_w_map = {"tr": "Sonraki Kelime", "en": "Next Word", "de": "Nächstes Wort", "es": "Siguiente palabra"}
        self.btn_next_question.setText(next_w_map.get(lang, "Next Word"))
        score_prefix = {"tr": " Doğru:", "en": " Correct:", "de": " Richtig:", "es": " Correcto:"}.get(lang, " Correct:")
        streak_prefix = {"tr": " Seri:", "en": " Streak:", "de": " Serie:", "es": " Racha:"}.get(lang, " Streak:")
        self.lbl_quiz_score.setText(f"{score_prefix} {self._quiz_score}")
        self.lbl_quiz_streak.setText(f"{streak_prefix} {self._quiz_streak}")
        localize_tree(self,lang)
