"""
Study Card - Fransızca Düzensiz Fiiller (Verbes Irréguliers) & İnteraktif Quiz
En önemli 60+ Fransızca düzensiz fiilin Infinitif, Présent ve Passé Composé çekimleri ile quiz oyunu.
"""

import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.settings import settings
from duocards.icons import get_icon
from duocards.widgets.universal_module_view import QuizChoiceButton
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit

FRENCH_IRREGULAR_VERBS = [
    {"inf": "être", "pres": "je suis, il est", "pc": "été (j'ai été)", "tr": "olmak, bulunmak"},
    {"inf": "avoir", "pres": "j'ai, il a", "pc": "eu (j'ai eu)", "tr": "sahip olmak"},
    {"inf": "aller", "pres": "je vais, il va", "pc": "allé (je suis allé)", "tr": "gitmek"},
    {"inf": "faire", "pres": "je fais, il fait", "pc": "fait (j'ai fait)", "tr": "yapmak, etmek"},
    {"inf": "dire", "pres": "je dis, il dit", "pc": "dit (j'ai dit)", "tr": "söylemek, demek"},
    {"inf": "pouvoir", "pres": "je peux, il peut", "pc": "pu (j'ai pu)", "tr": "-ebilmek, gücü yetmek"},
    {"inf": "vouloir", "pres": "je veux, il veut", "pc": "voulu (j'ai voulu)", "tr": "istemek"},
    {"inf": "savoir", "pres": "je sais, il sait", "pc": "su (j'ai su)", "tr": "bilmek"},
    {"inf": "voir", "pres": "je vois, il voit", "pc": "vu (j'ai vu)", "tr": "görmek"},
    {"inf": "devoir", "pres": "je dois, il doit", "pc": "dû (j'ai dû)", "tr": "zorunda olmak, -meli"},
    {"inf": "venir", "pres": "je viens, il vient", "pc": "venu (je suis venu)", "tr": "gelmek"},
    {"inf": "prendre", "pres": "je prends, il prend", "pc": "pris (j'ai pris)", "tr": "almak, binmek (araç)"},
    {"inf": "mettre", "pres": "je mets, il met", "pc": "mis (j'ai mis)", "tr": "koymak, giymek"},
    {"inf": "partir", "pres": "je pars, il part", "pc": "parti (je suis parti)", "tr": "ayrılmak, yola çıkmak"},
    {"inf": "sortir", "pres": "je sors, il sort", "pc": "sorti (je suis sorti)", "tr": "dışarı çıkmak"},
    {"inf": "falloir", "pres": "il faut", "pc": "fallu (il a fallu)", "tr": "gerekli olmak (lazım)"},
    {"inf": "tenir", "pres": "je tiens, il tient", "pc": "tenu (j'ai tenu)", "tr": "tutmak"},
    {"inf": "croire", "pres": "je crois, il croit", "pc": "cru (j'ai cru)", "tr": "inanmak, sanmak"},
    {"inf": "boire", "pres": "je bois, il boit", "pc": "bu (j'ai bu)", "tr": "içmek"},
    {"inf": "lire", "pres": "je lis, il lit", "pc": "lu (j'ai lu)", "tr": "okumak"},
    {"inf": "écrire", "pres": "j'écris, il écrit", "pc": "écrit (j'ai écrit)", "tr": "yazmak"},
    {"inf": "connaître", "pres": "je connais, il connaît", "pc": "connu (j'ai connu)", "tr": "tanımak, bilmek"},
    {"inf": "vivre", "pres": "je vis, il vit", "pc": "vécu (j'ai vécu)", "tr": "yaşamak"},
    {"inf": "suivre", "pres": "je suis, il suit", "pc": "suivi (j'ai suivi)", "tr": "takip etmek, izlemek"},
    {"inf": "ouvrir", "pres": "j'ouvre, il ouvre", "pc": "ouvert (j'ai ouvert)", "tr": "açmak"},
    {"inf": "dormir", "pres": "je dors, il dort", "pc": "dormi (j'ai dormi)", "tr": "uyumak"},
    {"inf": "comprendre", "pres": "je comprends, il comprend", "pc": "compris (j'ai compris)", "tr": "anlamak"},
    {"inf": "apprendre", "pres": "j'apprends, il apprend", "pc": "appris (j'ai appris)", "tr": "öğrenmek"},
    {"inf": "attendre", "pres": "j'attends, il attend", "pc": "attendu (j'ai attendu)", "tr": "beklemek"},
    {"inf": "perdre", "pres": "je perds, il perd", "pc": "perdu (j'ai perdu)", "tr": "kaybetmek"},
    {"inf": "recevoir", "pres": "je reçois, il reçoit", "pc": "reçu (j'ai reçu)", "tr": "teslim almak, kabul etmek"},
    {"inf": "courir", "pres": "je cours, il court", "pc": "couru (j'ai couru)", "tr": "koşmak"},
    {"inf": "rire", "pres": "je ris, il rit", "pc": "ri (j'ai ri)", "tr": "gülmek"},
    {"inf": "mourir", "pres": "je meurs, il meurt", "pc": "mort (il est mort)", "tr": "ölmek"},
    {"inf": "naître", "pres": "je nais, il naît", "pc": "né (je suis né)", "tr": "doğmak"},
    {"inf": "sentir", "pres": "je sens, il sent", "pc": "senti (j'ai senti)", "tr": "hissetmek, kokmak"},
    {"inf": "offrir", "pres": "j'offre, il offre", "pc": "offert (j'ai offert)", "tr": "sunmak, hediye etmek"},
    {"inf": "découvrir", "pres": "je découvre, il découvre", "pc": "découvert (j'ai découvert)", "tr": "keşfetmek"},
    {"inf": "servir", "pres": "je sers, il sert", "pc": "servi (j'ai servi)", "tr": "hizmet etmek, yaramak"},
    {"inf": "battre", "pres": "je bats, il bat", "pc": "battu (j'ai battu)", "tr": "vurmak, yenmek"},
]


class FrenchVerbsView(QWidget):
    """
    Fransızca Düzensiz Fiil Tablosu ve Quiz Modülü.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")

        self._quiz_score = 0
        self._quiz_streak = 0
        self._current_quiz = None
        self._is_quiz_busy = False

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
        self.lbl_title = QLabel(" Fransızca: Düzensiz Fiiller (Verbes Irréguliers)")
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel("En önemli Fransızca kuralsız fiil çekimleri ve interaktif test.")
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        titles_box.addWidget(self.lbl_title)
        titles_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(titles_box)
        header_row.addStretch()

        self.btn_tab_table = QPushButton(" Fiil Tablosu")
        self.btn_tab_table.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_table.setFixedHeight(38)
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; border-radius: 10px; padding: 0 18px; border: none;")
        self.btn_tab_table.clicked.connect(self._show_table)

        self.btn_tab_quiz = QPushButton(" Fiil Testi")
        self.btn_tab_quiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_quiz.setFixedHeight(38)
        self.btn_tab_quiz.setStyleSheet("background-color: #162032; color: #94a3b8; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 0 18px; border: 1px solid rgba(255, 255, 255, 0.05);")
        self.btn_tab_quiz.clicked.connect(self._show_quiz)

        header_row.addWidget(self.btn_tab_table)
        header_row.addWidget(self.btn_tab_quiz)
        main_layout.addLayout(header_row)

        self.stack = QStackedWidget()

        # Sayfa 1: Tablo
        table_page = QWidget()
        t_layout = QVBoxLayout(table_page)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(12)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Fiil veya Türkçe anlam ara... (örn: être, gitmek, faire)")
        self.input_search.setFixedHeight(40)
        self.input_search.textChanged.connect(self._filter_table)
        t_layout.addWidget(self.input_search)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Infinitif (Mastar)", "Présent (Geniş Zaman)", "Passé Composé", "Türkçe Anlamı", "Dinle"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(4, 80)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        t_layout.addWidget(self.table)
        self.stack.addWidget(table_page)

        # Sayfa 2: Quiz
        quiz_page = QWidget()
        q_layout = QVBoxLayout(quiz_page)
        q_layout.setContentsMargins(0, 10, 0, 10)
        q_layout.setSpacing(20)
        q_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Skor
        s_box = QFrame()
        s_box.setStyleSheet("background-color: #111827; border-radius: 12px; border: none; padding: 8px 24px;")
        sb_lay = QHBoxLayout(s_box)
        self.lbl_score = QLabel(ui_text(' Correct: 0', self.lang))
        self.lbl_score.setStyleSheet("color: #10b981; font-weight: 800; font-size: 15px;")
        self.lbl_streak = QLabel(ui_text(' Streak: 0', self.lang))
        self.lbl_streak.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 15px;")
        sb_lay.addWidget(self.lbl_score)
        sb_lay.addSpacing(20)
        sb_lay.addWidget(self.lbl_streak)
        q_layout.addWidget(s_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Kart (Enlemesine Dikdörtgen, Çizgisiz)
        self.q_card = QFrame()
        self.q_card.setMinimumWidth(740)
        self.q_card.setMaximumWidth(1020)
        self.q_card.setFixedHeight(200)
        self.q_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.q_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: none;
                border-radius: 20px;
                padding: 16px 28px;
            }
        """)
        qc_lay = QVBoxLayout(self.q_card)
        qc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_lay.setSpacing(10)

        self.lbl_q_hint = QLabel(ui_text('Which infinitive verb does this form belong to?', self.lang))
        self.lbl_q_hint.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
        self.lbl_q_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Fiil Çekimi ve Dinleme Butonu Satırı (Hemen yanında, sıkı aralık)
        form_audio_row = QHBoxLayout()
        form_audio_row.setSpacing(8)
        form_audio_row.setContentsMargins(0, 0, 0, 0)
        form_audio_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_audio_row.addStretch()

        self.lbl_q_form = QLabel("je suis / il est")
        self.lbl_q_form.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.lbl_q_form.setStyleSheet("color: #38bdf8; font-size: 32px; font-weight: 900;")
        self.lbl_q_form.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_audio_row.addWidget(self.lbl_q_form)

        self.btn_q_audio = QPushButton()
        self.btn_q_audio.setIcon(get_icon("audio", 24, "#10b981"))
        self.btn_q_audio.setIconSize(QSize(24, 24))
        self.btn_q_audio.setToolTip(ui_text('Listen to verb', self.lang))
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
        form_audio_row.addWidget(self.btn_q_audio)
        form_audio_row.addStretch()

        self.lbl_q_feedback = QLabel("")
        self.lbl_q_feedback.setStyleSheet("font-size: 15px; font-weight: 800;")
        self.lbl_q_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qc_lay.addWidget(self.lbl_q_hint)
        qc_lay.addLayout(form_audio_row)
        qc_lay.addWidget(self.lbl_q_feedback)
        q_layout.addWidget(self.q_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Şıklar (Tek Satırda 4 Şık, Çizgisiz, Kesilmeyen Geniş Kutucuklar)
        choices_container = QWidget()
        choices_container.setMinimumWidth(740)
        choices_container.setMaximumWidth(1020)
        choices_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        c_grid = QHBoxLayout(choices_container)
        c_grid.setContentsMargins(0, 0, 0, 0)
        c_grid.setSpacing(10)

        self.btn_choices = []
        for i in range(4):
            btn = QuizChoiceButton()
            btn.clicked.connect(lambda ch, idx=i: self._on_quiz_answer(idx))
            self.btn_choices.append(btn)
            c_grid.addWidget(btn, 1)

        q_layout.addWidget(choices_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(quiz_page)
        main_layout.addWidget(self.stack)

        self._populate_table(FRENCH_IRREGULAR_VERBS)

    def _show_table(self):
        self.btn_tab_table.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; border-radius: 10px; padding: 0 18px; border: none;")
        self.btn_tab_quiz.setStyleSheet("background-color: #162032; color: #94a3b8; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 0 18px; border: 1px solid rgba(255, 255, 255, 0.05);")
        self.stack.setCurrentIndex(0)

    def _show_quiz(self):
        self.btn_tab_quiz.setStyleSheet("background-color: #10b981; color: #ffffff; font-size: 13px; font-weight: 800; border-radius: 10px; padding: 0 18px; border: none;")
        self.btn_tab_table.setStyleSheet("background-color: #162032; color: #94a3b8; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 0 18px; border: 1px solid rgba(255, 255, 255, 0.05);")
        self.stack.setCurrentIndex(1)
        if not self._current_quiz:
            self._next_quiz()

    def _filter_table(self):
        q = self.input_search.text().strip().lower()
        items = []
        for v in FRENCH_IRREGULAR_VERBS:
            if not q or q in v["inf"].lower() or q in v["pres"].lower() or q in v["pc"].lower() or q in v["tr"].lower():
                items.append(v)
        self._populate_table(items)

    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            it_inf = QTableWidgetItem(item["inf"])
            it_inf.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 0, it_inf)

            it_pres = QTableWidgetItem(item["pres"])
            it_pres.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 1, it_pres)

            it_pc = QTableWidgetItem(item["pc"])
            it_pc.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 2, it_pc)

            it_tr = QTableWidgetItem(item["tr"])
            it_tr.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 3, it_tr)

            btn_play = QPushButton("")
            btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_play.setFixedSize(36, 32)
            btn_play.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #10b981;
                    color: #ffffff;
                }
            """)
            btn_play.clicked.connect(lambda ch, w=item["inf"]: audio_player.play_pronunciation(w, lang="fr"))

            cell_w = QWidget()
            c_lay = QHBoxLayout(cell_w)
            c_lay.setContentsMargins(0, 0, 0, 0)
            c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_lay.addWidget(btn_play)
            self.table.setCellWidget(row, 4, cell_w)

    def _play_quiz_audio(self):
        if hasattr(self, "_current_quiz") and self._current_quiz:
            form = self.lbl_q_form.text().strip()
            word = form.split("/")[0].strip() if "/" in form else form
            if word:
                sfx.play_click()
                audio_player.play_pronunciation(word, lang="fr")

    def _next_quiz(self):
        self._is_quiz_busy = False
        self.lbl_q_feedback.setText("")
        for btn in self.btn_choices:
            btn.setEnabled(True)
            btn.set_state_style("normal")

        target = random.choice(FRENCH_IRREGULAR_VERBS)
        self._current_quiz = target

        # Soru türü: Présent veya Passé Composé
        is_pres = random.choice([True, False])
        form_text = target["pres"] if is_pres else target["pc"]
        form_label = "Présent" if is_pres else "Passé Composé"

        hint_prefix = ui_text('Which verb belongs to this', self.lang)
        hint_suffix = ui_text('conjugation?', self.lang)
        self.lbl_q_hint.setText(f"{hint_prefix} {form_label} {hint_suffix} ({target['tr']})")
        self.lbl_q_form.setText(form_text)

        # 4 seçenek
        wrong_candidates = [v["inf"] for v in FRENCH_IRREGULAR_VERBS if v["inf"] != target["inf"]]
        choices = random.sample(wrong_candidates, 3) + [target["inf"]]
        random.shuffle(choices)

        for i, text in enumerate(choices):
            self.btn_choices[i].setText(text)

    def _on_quiz_answer(self, idx):
        if self._is_quiz_busy or not self._current_quiz:
            return

        self._is_quiz_busy = True
        chosen_btn = self.btn_choices[idx]
        chosen = chosen_btn.text()
        correct = self._current_quiz["inf"]

        audio_player.play_pronunciation(correct, lang="fr")

        if chosen == correct:
            sfx.play_correct()
            chosen_btn.set_state_style("correct")
            self._quiz_score += 1
            self._quiz_streak += 1
            self.lbl_q_feedback.setStyleSheet("color: #00ff88; font-size: 16px; font-weight: 900;")
            self.lbl_q_feedback.setText(f" Bravo! {correct} ({self._current_quiz['tr']})")
        else:
            sfx.play_wrong()
            chosen_btn.set_state_style("wrong")
            # Doğru olanı yeşil yak
            for btn in self.btn_choices:
                if btn.text() == correct:
                    btn.set_state_style("correct")
            self._quiz_streak = 0
            self.lbl_q_feedback.setStyleSheet("color: #ef4444; font-size: 16px; font-weight: 800;")
            self.lbl_q_feedback.setText(ui_text(' Wrong! Correct: {correct}', self.lang, **{'correct': correct}))

        self.lbl_score.setText(ui_text(' Correct: {self._quiz_score}', self.lang, **{'self._quiz_score': self._quiz_score}))
        self.lbl_streak.setText(ui_text(' Streak: {self._quiz_streak}', self.lang, **{'self._quiz_streak': self._quiz_streak}))

        QTimer.singleShot(1400, self._next_quiz)

    def keyPressEvent(self, event):
        key = event.key()
        if self.stack.currentIndex() == 1 and not self._is_quiz_busy:
            if key in (Qt.Key.Key_1, Qt.Key.Key_A):
                self._on_quiz_answer(0)
                return
            elif key in (Qt.Key.Key_2, Qt.Key.Key_B):
                self._on_quiz_answer(1)
                return
            elif key in (Qt.Key.Key_3, Qt.Key.Key_C):
                self._on_quiz_answer(2)
                return
            elif key in (Qt.Key.Key_4, Qt.Key.Key_D):
                self._on_quiz_answer(3)
                return
            elif key == Qt.Key.Key_Space:
                self._play_quiz_audio()
                return
        super().keyPressEvent(event)

    def update_language(self, lang: str):
        self.lang = lang
        title_map = {
            "tr": "Fransızca Fiiller (Verbes Irréguliers)",
            "en": "French Verbs (Verbes Irréguliers)",
            "de": "Französische Verben (Verbes Irréguliers)",
            "es": "Verbos en francés (Verbes Irréguliers)"
        }
        sub_map = {
            "tr": "En önemli 60+ Fransızca düzensiz fiilin Infinitif, Présent ve Passé Composé çekimleri ile quiz oyunu.",
            "en": "Most important 60+ French irregular verbs with Infinitif, Présent, Passé Composé and quiz.",
            "de": "Wichtigste 60+ französische unregelmäßige Verben mit Infinitif, Présent, Passé Composé und Quiz.",
            "es": "Más de 60 verbos irregulares franceses esenciales con Infinitif, Présent, Passé Composé y quiz."
        }
        self.lbl_title.setText(title_map.get(lang, title_map["en"]))
        self.lbl_subtitle.setText(sub_map.get(lang, sub_map["en"]))
        tab_t_map = {"tr": "Fiil Tablosu", "en": "Verb Table", "de": "Verbtabelle", "es": "Tabla de verbos"}
        tab_q_map = {"tr": "Çekim Testi", "en": "Conjugation Quiz", "de": "Konjugations-Quiz", "es": "Quiz de conjugación"}
        self.btn_tab_table.setText(tab_t_map.get(lang, "Verb Table"))
        self.btn_tab_quiz.setText(tab_q_map.get(lang, "Conjugation Quiz"))

        search_map = {
            "tr": "Fransızca fiil veya Türkçe anlam ara...",
            "en": "Search verb or meaning...",
            "de": "Verb oder Bedeutung suchen...",
            "es": "Buscar verbo o significado..."
        }
        self.input_search.setPlaceholderText(search_map.get(lang, "Search verb or meaning..."))
        col_m = {"tr": "Anlamı", "en": "Meaning", "de": "Bedeutung", "es": "Significado"}.get(lang, "Meaning")
        col_a = {"tr": "Ses", "en": "Audio", "de": "Audio", "es": "Audio"}.get(lang, "Audio")
        self.table.setHorizontalHeaderLabels([
            "Infinitif", "Présent", "Passé Composé", col_m, col_a
        ])
        score_prefix = {"tr": " Doğru:", "en": " Correct:", "de": " Richtig:", "es": " Correcto:"}.get(lang, " Correct:")
        streak_prefix = {"tr": " Seri:", "en": " Streak:", "de": " Serie:", "es": " Racha:"}.get(lang, " Streak:")
        self.lbl_score.setText(f"{score_prefix} {self._quiz_score}")
        self.lbl_streak.setText(f"{streak_prefix} {self._quiz_streak}")
        localize_tree(self,lang)
