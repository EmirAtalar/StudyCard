"""
Study Card - İngilizce Kuralsız Fiil Çekimleri (Irregular Verbs) & Quiz Oyunu
Kapsamlı V1, V2, V3 fiil listesi ve "Bu çekim hangi kelimeye aittir ve V kaçtır?" interaktif quiz oyunu.
"""

import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedWidget, QFrame, QGridLayout, QSizePolicy, QGraphicsBlurEffect
)
from PyQt6.QtCore import Qt, QTimer, QSize, QEvent
from PyQt6.QtGui import QCursor, QKeyEvent
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.icons import get_icon
from duocards.i18n import t
from duocards.widgets.universal_module_view import QuizChoiceButton
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit

# 110+ Kapsamlı ve Temel İngilizce Kuralsız Fiil Veritabanı
IRREGULAR_VERBS = [
    {"v1": "awake", "v2": "awoke", "v3": "awoken", "tr": "uyanmak, uyandırmak"},
    {"v1": "be", "v2": "was / were", "v3": "been", "tr": "olmak, bulunmak"},
    {"v1": "bear", "v2": "bore", "v3": "born / borne", "tr": "katlanmak, taşımak, doğurmak"},
    {"v1": "become", "v2": "became", "v3": "become", "tr": "haline gelmek, dönüşmek, olmak"},
    {"v1": "begin", "v2": "began", "v3": "begun", "tr": "başlamak"},
    {"v1": "bend", "v2": "bent", "v3": "bent", "tr": "bükmek, eğilmek"},
    {"v1": "bet", "v2": "bet", "v3": "bet", "tr": "bahse girmek"},
    {"v1": "bind", "v2": "bound", "v3": "bound", "tr": "bağlamak, ciltlemek"},
    {"v1": "bite", "v2": "bit", "v3": "bitten", "tr": "ısırmak"},
    {"v1": "bleed", "v2": "bled", "v3": "bled", "tr": "kanamak"},
    {"v1": "blow", "v2": "blew", "v3": "blown", "tr": "esmek, üflemek"},
    {"v1": "break", "v2": "broke", "v3": "broken", "tr": "kırmak, bozulmak, parçalamak"},
    {"v1": "bring", "v2": "brought", "v3": "brought", "tr": "getirmek"},
    {"v1": "build", "v2": "built", "v3": "built", "tr": "inşa etmek, kurmak"},
    {"v1": "burn", "v2": "burnt", "v3": "burnt", "tr": "yakmak, yanmak"},
    {"v1": "burst", "v2": "burst", "v3": "burst", "tr": "patlamak, patlatmak"},
    {"v1": "buy", "v2": "bought", "v3": "bought", "tr": "satın almak"},
    {"v1": "catch", "v2": "caught", "v3": "caught", "tr": "yakalamak, tutmak, yetişmek"},
    {"v1": "choose", "v2": "chose", "v3": "chosen", "tr": "seçmek, tercih etmek"},
    {"v1": "come", "v2": "came", "v3": "come", "tr": "gelmek"},
    {"v1": "cost", "v2": "cost", "v3": "cost", "tr": "mal olmak, tutmak (fiyat/maliyet)"},
    {"v1": "creep", "v2": "crept", "v3": "crept", "tr": "sessizce sokulmak, sürünmek"},
    {"v1": "cut", "v2": "cut", "v3": "cut", "tr": "kesmek, kısmak"},
    {"v1": "deal", "v2": "dealt", "v3": "dealt", "tr": "ilgilenmek, anlaşmak, başa çıkmak"},
    {"v1": "dig", "v2": "dug", "v3": "dug", "tr": "kazmak"},
    {"v1": "do", "v2": "did", "v3": "done", "tr": "yapmak, etmek"},
    {"v1": "draw", "v2": "drew", "v3": "drawn", "tr": "çizmek, çekmek"},
    {"v1": "dream", "v2": "dreamt", "v3": "dreamt", "tr": "rüya görmek, hayal kurmak"},
    {"v1": "drink", "v2": "drank", "v3": "drunk", "tr": "içmek"},
    {"v1": "drive", "v2": "drove", "v3": "driven", "tr": "sürmek, kullanmak (araç)"},
    {"v1": "eat", "v2": "ate", "v3": "eaten", "tr": "yemek, yemek yemek"},
    {"v1": "fall", "v2": "fell", "v3": "fallen", "tr": "düşmek"},
    {"v1": "feed", "v2": "fed", "v3": "fed", "tr": "beslemek, doyurmak"},
    {"v1": "feel", "v2": "felt", "v3": "felt", "tr": "hissetmek"},
    {"v1": "fight", "v2": "fought", "v3": "fought", "tr": "savaşmak, dövüşmek, mücadele etmek"},
    {"v1": "find", "v2": "found", "v3": "found", "tr": "bulmak"},
    {"v1": "flee", "v2": "fled", "v3": "fled", "tr": "kaçmak, firar etmek"},
    {"v1": "fly", "v2": "flew", "v3": "flown", "tr": "uçmak, uçurmak"},
    {"v1": "forbid", "v2": "forbade", "v3": "forbidden", "tr": "yasaklamak, menetmek"},
    {"v1": "forget", "v2": "forgot", "v3": "forgotten", "tr": "unutmak"},
    {"v1": "forgive", "v2": "forgave", "v3": "forgiven", "tr": "affetmek, bağışlamak"},
    {"v1": "freeze", "v2": "froze", "v3": "frozen", "tr": "donmak, dondurmak"},
    {"v1": "get", "v2": "got", "v3": "gotten", "tr": "elde etmek, almak, edinmek"},
    {"v1": "give", "v2": "gave", "v3": "given", "tr": "vermek"},
    {"v1": "go", "v2": "went", "v3": "gone", "tr": "gitmek"},
    {"v1": "grow", "v2": "grew", "v3": "grown", "tr": "büyümek, yetiştirmek, geliştirmek"},
    {"v1": "hang", "v2": "hung", "v3": "hung", "tr": "asmak, asılı durmak"},
    {"v1": "have", "v2": "had", "v3": "had", "tr": "sahip olmak"},
    {"v1": "hear", "v2": "heard", "v3": "heard", "tr": "duymak, işitmek"},
    {"v1": "hide", "v2": "hid", "v3": "hidden", "tr": "saklamak, gizlenmek, saklanmak"},
    {"v1": "hit", "v2": "hit", "v3": "hit", "tr": "vurmak, çarpmak"},
    {"v1": "hold", "v2": "held", "v3": "held", "tr": "tutmak, elde bulundurmak, düzenlemek"},
    {"v1": "hurt", "v2": "hurt", "v3": "hurt", "tr": "acıtmak, incitmek, ağrımak"},
    {"v1": "keep", "v2": "kept", "v3": "kept", "tr": "saklamak, korumak, sürdürmek"},
    {"v1": "kneel", "v2": "knelt", "v3": "knelt", "tr": "diz çökmek"},
    {"v1": "know", "v2": "knew", "v3": "known", "tr": "bilmek, tanımak"},
    {"v1": "lay", "v2": "laid", "v3": "laid", "tr": "sermek, koymak, yatırmak"},
    {"v1": "lead", "v2": "led", "v3": "led", "tr": "önderlik etmek, yol göstermek, yönetmek"},
    {"v1": "learn", "v2": "learnt", "v3": "learnt", "tr": "öğrenmek"},
    {"v1": "leave", "v2": "left", "v3": "left", "tr": "ayrılmak, terk etmek, bırakmak"},
    {"v1": "lend", "v2": "lent", "v3": "lent", "tr": "ödünç vermek"},
    {"v1": "let", "v2": "let", "v3": "let", "tr": "izin vermek, bırakmak"},
    {"v1": "lie", "v2": "lay", "v3": "lain", "tr": "uzanmak, yatmak"},
    {"v1": "light", "v2": "lit", "v3": "lit", "tr": "yakmak, aydınlatmak"},
    {"v1": "lose", "v2": "lost", "v3": "lost", "tr": "kaybetmek, yitirmek"},
    {"v1": "make", "v2": "made", "v3": "made", "tr": "yapmak, üretmek, oluşturmak"},
    {"v1": "mean", "v2": "meant", "v3": "meant", "tr": "anlamına gelmek, kastetmek, demek istemek"},
    {"v1": "meet", "v2": "met", "v3": "met", "tr": "tanışmak, buluşmak, karşılamak"},
    {"v1": "pay", "v2": "paid", "v3": "paid", "tr": "ödemek"},
    {"v1": "put", "v2": "put", "v3": "put", "tr": "koymak, yerleştirmek"},
    {"v1": "quit", "v2": "quit", "v3": "quit", "tr": "bırakmak, vazgeçmek, çıkmak"},
    {"v1": "read", "v2": "read", "v3": "read", "tr": "okumak"},
    {"v1": "ride", "v2": "rode", "v3": "ridden", "tr": "binmek (bisiklet, at vb.)"},
    {"v1": "ring", "v2": "rang", "v3": "rung", "tr": "çalmak (zil, telefon), çınlamak"},
    {"v1": "rise", "v2": "rose", "v3": "risen", "tr": "yükselmek, doğmak (güneş), artmak"},
    {"v1": "run", "v2": "ran", "v3": "run", "tr": "koşmak, çalıştırmak, işletmek"},
    {"v1": "say", "v2": "said", "v3": "said", "tr": "söylemek, demek"},
    {"v1": "see", "v2": "saw", "v3": "seen", "tr": "görmek, anlamak"},
    {"v1": "seek", "v2": "sought", "v3": "sought", "tr": "aramak, peşinde koşmak, çabalamak"},
    {"v1": "sell", "v2": "sold", "v3": "sold", "tr": "satmak"},
    {"v1": "send", "v2": "sent", "v3": "sent", "tr": "göndermek, yollamak"},
    {"v1": "set", "v2": "set", "v3": "set", "tr": "ayarlamak, kurmak, belirlemek"},
    {"v1": "sew", "v2": "sewed", "v3": "sewn", "tr": "dikmek (dikiş)"},
    {"v1": "shake", "v2": "shook", "v3": "shaken", "tr": "sallamak, sarsmak, titremek"},
    {"v1": "shine", "v2": "shone", "v3": "shone", "tr": "parlamak, ışıldamak"},
    {"v1": "shoot", "v2": "shot", "v3": "shot", "tr": "ateş etmek, vurmak, çekim yapmak"},
    {"v1": "show", "v2": "showed", "v3": "shown", "tr": "göstermek, sergilemek"},
    {"v1": "shrink", "v2": "shrank", "v3": "shrunk", "tr": "küçülmek, çekmek (kumaş)"},
    {"v1": "shut", "v2": "shut", "v3": "shut", "tr": "kapatmak, yummak"},
    {"v1": "sing", "v2": "sang", "v3": "sung", "tr": "şarkı söylemek, ötmek"},
    {"v1": "sink", "v2": "sank", "v3": "sunk", "tr": "batmak, batırmak"},
    {"v1": "sit", "v2": "sat", "v3": "sat", "tr": "oturmak"},
    {"v1": "sleep", "v2": "slept", "v3": "slept", "tr": "uyumak"},
    {"v1": "slide", "v2": "slid", "v3": "slid", "tr": "kaymak, kaydırmak"},
    {"v1": "smell", "v2": "smelt", "v3": "smelt", "tr": "koklamak, kokmak"},
    {"v1": "speak", "v2": "spoke", "v3": "spoken", "tr": "konuşmak"},
    {"v1": "speed", "v2": "sped", "v3": "sped", "tr": "hızlanmak, hız yapmak"},
    {"v1": "spend", "v2": "spent", "v3": "spent", "tr": "harcamak (para), geçirmek (zaman)"},
    {"v1": "spill", "v2": "spilt", "v3": "spilt", "tr": "dökmek, dökülmek (sıvı)"},
    {"v1": "spin", "v2": "spun", "v3": "spun", "tr": "dönmek, döndürmek"},
    {"v1": "split", "v2": "split", "v3": "split", "tr": "bölmek, ayrılmak, yarılmak"},
    {"v1": "spoil", "v2": "spoilt", "v3": "spoilt", "tr": "bozmak, bozulmak, şımartmak"},
    {"v1": "spread", "v2": "spread", "v3": "spread", "tr": "yaymak, yayılmak, sürmek (ekmeğe)"},
    {"v1": "stand", "v2": "stood", "v3": "stood", "tr": "ayakta durmak, dayanmak, katlanmak"},
    {"v1": "steal", "v2": "stole", "v3": "stolen", "tr": "çalmak, aşırmak (hırsızlık)"},
    {"v1": "stick", "v2": "stuck", "v3": "stuck", "tr": "yapışmak, saplamak, takılmak"},
    {"v1": "sting", "v2": "stung", "v3": "stung", "tr": "sokmak (arı/böcek), batmak, acıtmak"},
    {"v1": "strike", "v2": "struck", "v3": "struck", "tr": "çarpmak, vurmak, grev yapmak"},
    {"v1": "swear", "v2": "swore", "v3": "sworn", "tr": "yemin etmek, küfretmek"},
    {"v1": "sweep", "v2": "swept", "v3": "swept", "tr": "süpürmek"},
    {"v1": "swim", "v2": "swam", "v3": "swum", "tr": "yüzmek"},
    {"v1": "swing", "v2": "swung", "v3": "swung", "tr": "sallanmak, sallamak"},
    {"v1": "take", "v2": "took", "v3": "taken", "tr": "almak, götürmek"},
    {"v1": "teach", "v2": "taught", "v3": "taught", "tr": "öğretmek"},
    {"v1": "tear", "v2": "tore", "v3": "torn", "tr": "yırtmak, koparmak"},
    {"v1": "tell", "v2": "told", "v3": "told", "tr": "anlatmak, söylemek, bildirmek"},
    {"v1": "think", "v2": "thought", "v3": "thought", "tr": "düşünmek, sanmak"},
    {"v1": "throw", "v2": "threw", "v3": "thrown", "tr": "fırlatmak, atmak"},
    {"v1": "understand", "v2": "understood", "v3": "understood", "tr": "anlamak, kavramak"},
    {"v1": "wake", "v2": "woke", "v3": "woken", "tr": "uyanmak, uyandırmak"},
    {"v1": "wear", "v2": "wore", "v3": "worn", "tr": "giymek, takmak"},
    {"v1": "weep", "v2": "wept", "v3": "wept", "tr": "ağlamak, sızlamak"},
    {"v1": "win", "v2": "won", "v3": "won", "tr": "kazanmak"},
    {"v1": "wind", "v2": "wound", "v3": "wound", "tr": "sarmak, dolamak, kurmak (saat)"},
    {"v1": "withdraw", "v2": "withdrew", "v3": "withdrawn", "tr": "geri çekilmek, para çekmek"},
    {"v1": "write", "v2": "wrote", "v3": "written", "tr": "yazmak"}
]


class IrregularVerbsView(QWidget):
    """
    Kuralsız Fiiller Tablosu ve İnteraktif Quiz Oyunu.
    Kullanıcıya verilen çekimin (örn: 'swam') hangi kelimeye ait olduğunu
    ve V kaç olduğunu (örn: 'swim — V2 (Past Simple)') sorar.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "en")
        
        # Oyun İstatistikleri
        self.game_score = 0
        self.game_streak = 0
        self.best_streak = 0
        self.current_question = None
        self._quiz_locked = False
        self._hint_revealed = False
        self._current_meaning = ""

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(120)
        self._search_timer.timeout.connect(self._do_search)

        self._setup_ui()
        self._populate_table(IRREGULAR_VERBS)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(18)

        # ---------------- ÜST BAŞLIK ALANI ----------------
        header_row = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(3)

        self.lbl_title = QLabel(t("verbs_title", self.lang))
        self.lbl_title.setObjectName("pageTitle")

        self.lbl_subtitle = QLabel(t("verbs_subtitle", self.lang))
        self.lbl_subtitle.setObjectName("pageSubtitle")

        header_text_layout.addWidget(self.lbl_title)
        header_text_layout.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_text_layout, 1)

        # Mod Değiştirme Butonu (Oyuna Başla / Listeye Dön)
        self.btn_toggle_mode = QPushButton(t("btn_start_verb_game", self.lang))
        self.btn_toggle_mode.setProperty("class", "btn-primary")
        self.btn_toggle_mode.setFixedHeight(40)
        self.btn_toggle_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_mode.clicked.connect(self._toggle_mode)
        header_row.addWidget(self.btn_toggle_mode)

        main_layout.addLayout(header_row)

        # ---------------- İÇERİK STACK (0: Liste, 1: Oyun) ----------------
        self.stack = QStackedWidget()

        # Sayfa 0: Fiil Listesi & Arama
        self.page_list = self._create_list_page()
        self.stack.addWidget(self.page_list)

        # Sayfa 1: Quiz Oyunu
        self.page_game = self._create_game_page()
        self.stack.addWidget(self.page_game)

        main_layout.addWidget(self.stack, 1)

    # =========================================================================
    # SAYFA 0: FİİL LİSTESİ VE TABLOSU
    # =========================================================================
    def _create_list_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Arama ve Filtre Çubuğu
        search_row = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(t("verb_search_placeholder", self.lang))
        self.input_search.setFixedHeight(40)
        self.input_search.textChanged.connect(self._search_timer.start)
        search_row.addWidget(self.input_search, 1)

        self.lbl_count = QLabel(t("verb_count_label", self.lang, count=len(IRREGULAR_VERBS)))
        self.lbl_count.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600; padding: 0 8px;")
        search_row.addWidget(self.lbl_count)
        layout.addLayout(search_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("col_v1", self.lang),
            t("col_v2", self.lang),
            t("col_v3", self.lang),
            t("col_meaning", self.lang),
            t("col_listen", self.lang)
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 160)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(58)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table, 1)
        return page

    def _populate_table(self, verbs_list):
        self.table.setRowCount(len(verbs_list))
        for row, item in enumerate(verbs_list):
            v1_item = QTableWidgetItem(item["v1"])
            v1_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            v1_item.setForeground(Qt.GlobalColor.white)
            
            v2_item = QTableWidgetItem(item["v2"])
            v2_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            v2_item.setForeground(Qt.GlobalColor.white)

            v3_item = QTableWidgetItem(item["v3"])
            v3_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            v3_item.setForeground(Qt.GlobalColor.white)

            tr_item = QTableWidgetItem(item["tr"])
            tr_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            self.table.setItem(row, 0, v1_item)
            self.table.setItem(row, 1, v2_item)
            self.table.setItem(row, 2, v3_item)
            self.table.setItem(row, 3, tr_item)

            # Dinle Butonu (Ortalanmış ve tam genişlikte)
            cell_w = QWidget()
            cell_layout = QHBoxLayout(cell_w)
            cell_layout.setContentsMargins(4, 0, 4, 0)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_listen = QPushButton(t("listen", self.lang))
            btn_listen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_listen.setFixedSize(116, 32)
            btn_listen.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    border-radius: 8px;
                    padding: 2px 8px;
                    font-size: 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #10b981;
                    color: #ffffff;
                }
            """)
            # Tıklanınca V1, V2, V3 formlarını sırayla telaffuz ettir
            pronounce_text = f"{item['v1']}, {item['v2'].replace('/', ' ')}, {item['v3']}"
            btn_listen.clicked.connect(lambda ch, text=pronounce_text: self._play_verb_audio(text))
            cell_layout.addWidget(btn_listen)
            self.table.setCellWidget(row, 4, cell_w)
            self.table.setRowHeight(row, 58)

    def _do_search(self):
        self._on_search_changed(self.input_search.text())

    def _on_search_changed(self, query: str):
        query = query.strip().lower()
        if not query:
            filtered = IRREGULAR_VERBS
        else:
            filtered = [
                v for v in IRREGULAR_VERBS
                if query in v["v1"].lower() or query in v["v2"].lower()
                or query in v["v3"].lower() or query in v["tr"].lower()
            ]
        self.lbl_count.setText(t("verb_count_label", self.lang, count=len(filtered)))
        self._populate_table(filtered)

    def _play_verb_audio(self, text: str):
        sfx.play_click()
        audio_player.play_pronunciation(text, lang="en")

    # =========================================================================
    # SAYFA 1: QUİZ OYUNU
    # =========================================================================
    def _create_game_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # Üst Skor & Seri Şeridi
        stats_strip = QHBoxLayout()
        stats_strip.setSpacing(12)

        self.badge_score = QLabel(t("verb_score", self.lang, score=0))
        self.badge_score.setStyleSheet("""
            background-color: #111827;
            color: #38bdf8;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 16px;
            border-radius: 12px;
            border: none;
        """)

        self.badge_streak = QLabel(t("verb_streak", self.lang, streak=0))
        self.badge_streak.setStyleSheet("""
            background-color: #111827;
            color: #10b981;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 16px;
            border-radius: 12px;
            border: none;
        """)

        self.badge_best = QLabel(t("verb_best_streak", self.lang, best=0))
        self.badge_best.setStyleSheet("""
            background-color: #111827;
            color: #f59e0b;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 16px;
            border-radius: 12px;
            border: none;
        """)

        stats_strip.addWidget(self.badge_score)
        stats_strip.addWidget(self.badge_streak)
        stats_strip.addWidget(self.badge_best)
        stats_strip.addStretch()
        layout.addLayout(stats_strip)

        # ---------------- MERKEZİ SORU KARTI (Enlemesine Dikdörtgen, Çizgisiz) ----------------
        self.card_box = QFrame()
        self.card_box.setMinimumWidth(740)
        self.card_box.setMaximumWidth(1020)
        self.card_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.card_box.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: none;
                border-radius: 20px;
                padding: 20px 28px;
            }
        """)
        card_layout = QVBoxLayout(self.card_box)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(14)

        # Soru Başlığı ("Bu çekim hangi kelimeye aittir ve V kaçtır?")
        self.lbl_question_title = QLabel(t("verb_question_title", self.lang))
        self.lbl_question_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question_title.setStyleSheet("""
            color: #94a3b8;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.2px;
            background: transparent;
        """)
        card_layout.addWidget(self.lbl_question_title)

        # Dev Hedef Çekim Kelimesi ve Seslendirme Butonu (Hemen yanında, sıkı aralık)
        word_row = QHBoxLayout()
        word_row.setSpacing(8)
        word_row.setContentsMargins(0, 0, 0, 0)
        word_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_row.addStretch()

        self.lbl_target_word = QLabel("...")
        self.lbl_target_word.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.lbl_target_word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_target_word.setStyleSheet("""
            color: #ffffff;
            font-size: 38px;
            font-weight: 900;
            letter-spacing: 1px;
            background: transparent;
            margin: 4px 0;
        """)
        word_row.addWidget(self.lbl_target_word)

        self.btn_audio_quick = QPushButton()
        self.btn_audio_quick.setIcon(get_icon("audio", 24, "#10b981"))
        self.btn_audio_quick.setIconSize(QSize(24, 24))
        self.btn_audio_quick.setToolTip(t("listen", self.lang))
        self.btn_audio_quick.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_audio_quick.setFixedSize(36, 36)
        self.btn_audio_quick.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.15);
            }
        """)
        self.btn_audio_quick.clicked.connect(self._listen_target_word)
        word_row.addWidget(self.btn_audio_quick)
        word_row.addStretch()
        card_layout.addLayout(word_row)

        # İpucu Anlam Rozeti & Telaffuz Butonu
        word_meta_row = QHBoxLayout()
        word_meta_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_meta_row.setSpacing(10)

        self.btn_meaning_hint = QPushButton("")
        self.btn_meaning_hint.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_meaning_hint.clicked.connect(self._toggle_hint_blur)

        self.btn_listen_word = QPushButton(t("listen", self.lang))
        self.btn_listen_word.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_listen_word.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10b981;
                border: none;
                border-radius: 10px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #10b981;
                color: #ffffff;
            }
        """)
        self.btn_listen_word.clicked.connect(self._listen_target_word)

        word_meta_row.addWidget(self.btn_meaning_hint)
        word_meta_row.addWidget(self.btn_listen_word)
        card_layout.addLayout(word_meta_row)

        # 4 Çoktan Seçmeli Seçenek Butonları (Tek Satırda 4 Şık, Çizgisiz, Kesilmeyen Geniş Kutucuklar)
        self.options_container = QWidget()
        self.options_container.setMinimumWidth(740)
        self.options_container.setMaximumWidth(1020)
        self.options_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.options_layout = QHBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(10)
        self.option_buttons = []

        for i in range(4):
            btn = QuizChoiceButton()
            btn.clicked.connect(lambda ch, idx=i: self._on_option_clicked(idx))
            self.option_buttons.append(btn)
            self.options_layout.addWidget(btn, 1)

        card_layout.addWidget(self.options_container)

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
        self.input_typed_answer.installEventFilter(self)

        self.btn_submit_typed = QPushButton(ui_text('Check', self.lang))
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

        self.lbl_typing_hint = QLabel(ui_text('Type your answer with keyboard and press Enter', self.lang))
        self.lbl_typing_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_typing_hint.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600; background: transparent;")
        t_box.addWidget(self.lbl_typing_hint)

        self.typing_container.setVisible(True)
        self.options_container.setVisible(False)
        card_layout.addWidget(self.typing_container)

        # Sonuç / Geri Bildirim Etiketi
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_feedback.setStyleSheet("font-size: 14px; font-weight: 700; min-height: 22px; background: transparent;")
        card_layout.addWidget(self.lbl_feedback)

        # Sonraki Soru Butonu (İsteğe bağlı hızlı geçiş veya Enter ile geçiş)
        self.btn_next_question = QPushButton(t("verb_btn_next", self.lang))
        self.btn_next_question.setFixedHeight(38)
        self.btn_next_question.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_question.setAutoDefault(True)
        self.btn_next_question.setDefault(True)
        self.btn_next_question.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                border-radius: 8px;
                border: none;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0369a1;
                border: none;
            }
        """)
        self.btn_next_question.setVisible(False)
        self.btn_next_question.clicked.connect(self._next_question)
        card_layout.addWidget(self.btn_next_question, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.card_box, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    # =========================================================================
    # MOD GEÇİŞİ VE QUİZ MANTIĞI
    # =========================================================================
    def _toggle_mode(self):
        sfx.play_click()
        if self.stack.currentIndex() == 0:
            # Oyuna Geç
            self.stack.setCurrentIndex(1)
            self.btn_toggle_mode.setText(t("btn_back_to_list", self.lang))
            self.btn_toggle_mode.setProperty("class", "btn-secondary")
            self.btn_toggle_mode.setStyle(self.btn_toggle_mode.style())
            self._next_question()
        else:
            # Listeye Dön
            self.stack.setCurrentIndex(0)
            self.btn_toggle_mode.setText(t("btn_start_verb_game", self.lang))
            self.btn_toggle_mode.setProperty("class", "btn-primary")
            self.btn_toggle_mode.setStyle(self.btn_toggle_mode.style())

    def eventFilter(self, obj, event):
        if obj == getattr(self, "input_typed_answer", None) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.btn_next_question.isVisible():
                    self._next_question()
                    return True
                else:
                    self._on_submit_typed_answer()
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.btn_next_question.isVisible():
                self._next_question()
                event.accept()
                return
        super().keyPressEvent(event)

    def _listen_target_word(self):
        if self.current_question:
            word = self.current_question.get("target_word", "")
            if not word and self.current_question.get("verb"):
                word = self.current_question["verb"].get("v1", "")
            text = word.split("/")[0].strip()
            if text:
                sfx.play_click()
                audio_player.play_pronunciation(text, lang="en")

    def _set_hint_blurred(self, blurred: bool):
        self._hint_revealed = not blurred
        hint_text = t("verb_hint_meaning", self.lang, meaning=self._current_meaning)
        self.btn_meaning_hint.setText(hint_text)

        if blurred:
            blur = QGraphicsBlurEffect(self)
            blur.setBlurRadius(10)
            self.btn_meaning_hint.setGraphicsEffect(blur)
            self.btn_meaning_hint.setToolTip(
                ui_text('Click to reveal hint (Blurred)', self.lang)
            )
            self.btn_meaning_hint.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 41, 59, 0.75);
                    color: #94a3b8;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 5px 14px;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(51, 65, 85, 0.85);
                }
            """)
        else:
            self.btn_meaning_hint.setGraphicsEffect(None)
            self.btn_meaning_hint.setToolTip(
                ui_text('Click to blur hint', self.lang)
            )
            self.btn_meaning_hint.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    color: #6ee7b7;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 5px 14px;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(16, 185, 129, 0.25);
                }
            """)

    def _toggle_hint_blur(self):
        sfx.play_click()
        self._set_hint_blurred(self._hint_revealed)

    def _next_question(self):
        self._quiz_locked = False
        self.btn_next_question.setVisible(False)
        self.lbl_feedback.setText("")

        # Buton stillerini sıfırla (Çizgisiz, sade)
        for btn in self.option_buttons:
            btn.setEnabled(True)
            btn.set_state_style("normal")

        # Yeni Soru Üret:
        # Rastgele bir kuralsız fiil seç
        verb = random.choice(IRREGULAR_VERBS)

        # Hangi form sorulacak? (%45 V2, %45 V3, %10 V1)
        r = random.random()
        if r < 0.45:
            form_type = "V2"
            form_label = "V2 (Past Simple)"
            prompt_word = verb["v1"]
            target_typed = verb["v2"]
            q_hint = ui_text('Type the V2 (Past Simple) form using your keyboard:', self.lang)
            p_holder = ui_text('Type V2 form and press Enter...', self.lang)
        elif r < 0.90:
            form_type = "V3"
            form_label = "V3 (Past Participle)"
            prompt_word = verb["v1"]
            target_typed = verb["v3"]
            q_hint = ui_text('Type the V3 (Past Participle) form using your keyboard:', self.lang)
            p_holder = ui_text('Type V3 form and press Enter...', self.lang)
        else:
            form_type = "V1"
            form_label = "V1 (Infinitive / Base)"
            prompt_word = verb["v2"]
            target_typed = verb["v1"]
            q_hint = ui_text('Type the base (V1) form using your keyboard:', self.lang)
            p_holder = ui_text('Type V1 form and press Enter...', self.lang)

        self.current_question = {
            "verb": verb,
            "form_type": form_type,
            "target_word": prompt_word,
            "target_typed": target_typed,
        }

        # UI Güncelle
        self.lbl_target_word.setText(prompt_word)
        self.lbl_question_title.setText(q_hint)
        self.input_typed_answer.setPlaceholderText(p_holder)
        self._current_meaning = verb["tr"]
        self._set_hint_blurred(True)

        self.options_container.setVisible(False)
        self.typing_container.setVisible(True)
        self.input_typed_answer.clear()
        self.input_typed_answer.setEnabled(True)
        self.btn_submit_typed.setEnabled(True)
        QTimer.singleShot(60, self.input_typed_answer.setFocus)

    def _on_submit_typed_answer(self):
        if self._quiz_locked or not self.current_question:
            return

        typed = self.input_typed_answer.text().strip().lower()
        if not typed:
            return

        self._quiz_locked = True
        self.input_typed_answer.setEnabled(False)
        self.btn_submit_typed.setEnabled(False)
        self._listen_target_word()

        target_expected = self.current_question["target_typed"].strip()
        valid_answers = [ans.strip().lower() for ans in target_expected.replace(",", "/").split("/") if ans.strip()]
        valid_answers.append(target_expected.lower())

        if typed in valid_answers:
            sfx.play_correct()
            self.game_score += 10
            self.game_streak += 1
            if self.game_streak > self.best_streak:
                self.best_streak = self.game_streak
            self.lbl_feedback.setText(ui_text('Correct! Awesome: {target_expected}', self.lang, **{'target_expected': target_expected}))
            self.lbl_feedback.setStyleSheet("color: #10b981; font-weight: 800; font-size: 15px;")
            QTimer.singleShot(1100, self._next_question)
        else:
            sfx.play_wrong()
            self.game_streak = 0
            self.lbl_feedback.setText(ui_text('Wrong! Correct answer: {target_expected}', self.lang, **{'target_expected': target_expected}))
            self.lbl_feedback.setStyleSheet("color: #f87171; font-weight: 800; font-size: 15px;")
            self.btn_next_question.setVisible(True)
            self.btn_next_question.setFocus()

        self.badge_score.setText(t("verb_score", self.lang, score=self.game_score))
        self.badge_streak.setText(t("verb_streak", self.lang, streak=self.game_streak))
        self.badge_best.setText(t("verb_best_streak", self.lang, best=self.best_streak))

    def _on_option_clicked(self, idx: int):
        if self._quiz_locked or not self.current_question:
            return

        self._quiz_locked = True
        self._listen_target_word()
        correct_idx = self.current_question["correct_index"]
        correct_btn = self.option_buttons[correct_idx]
        clicked_btn = self.option_buttons[idx]

        if idx == correct_idx:
            # Doğru Cevap
            sfx.play_correct()
            clicked_btn.set_state_style("correct")
            self.game_score += 10
            self.game_streak += 1
            if self.game_streak > self.best_streak:
                self.best_streak = self.game_streak
            self.lbl_feedback.setText(ui_text('Correct! Awesome!', self.lang))
            self.lbl_feedback.setStyleSheet("color: #10b981; font-weight: 800; font-size: 14px;")
            
            # Otomatik sonraki soruya geç
            QTimer.singleShot(1100, self._next_question)
        else:
            # Yanlış Cevap
            sfx.play_wrong()
            clicked_btn.set_state_style("wrong")
            # Doğru olanı yeşil yak
            correct_btn.set_state_style("correct")
            self.game_streak = 0
            correct_answer = self.current_question["correct_text"]
            self.lbl_feedback.setText(
                ui_text('Correct: {correct_answer}', self.lang, **{'correct_answer': correct_answer})
            )
            self.lbl_feedback.setStyleSheet("color: #f87171; font-weight: 800; font-size: 14px;")
            self.btn_next_question.setVisible(True)
            self.btn_next_question.setFocus()

        # Skor rozetlerini güncelle
        self.badge_score.setText(t("verb_score", self.lang, score=self.game_score))
        self.badge_streak.setText(t("verb_streak", self.lang, streak=self.game_streak))
        self.badge_best.setText(t("verb_best_streak", self.lang, best=self.best_streak))

    # =========================================================================
    # DİL GÜNCELLEMESİ
    # =========================================================================
    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(t("verbs_title", lang))
        self.lbl_subtitle.setText(t("verbs_subtitle", lang))
        if self.stack.currentIndex() == 0:
            self.btn_toggle_mode.setText(t("btn_start_verb_game", lang))
        else:
            self.btn_toggle_mode.setText(t("btn_back_to_list", lang))

        self.input_search.setPlaceholderText(t("verb_search_placeholder", lang))
        self.lbl_question_title.setText(t("verb_question_title", lang))
        self.btn_next_question.setText(t("verb_btn_next", lang))
        self.btn_listen_word.setText(t("listen", lang))
        
        self.table.setHorizontalHeaderLabels([
            t("col_v1", lang),
            t("col_v2", lang),
            t("col_v3", lang),
            t("col_meaning", lang),
            t("col_listen", lang)
        ])

        self.badge_score.setText(t("verb_score", lang, score=self.game_score))
        self.badge_streak.setText(t("verb_streak", lang, streak=self.game_streak))
        self.badge_best.setText(t("verb_best_streak", lang, best=self.best_streak))

        if getattr(self, "_current_meaning", ""):
            self._set_hint_blurred(not self._hint_revealed)
        localize_tree(self,lang)
