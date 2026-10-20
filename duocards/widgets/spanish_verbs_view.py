"""
Study Card - İspanyolca Düzensiz Fiiller (Verbos Irregulares) & İnteraktif Quiz
En sık kullanılan 40+ İspanyolca kuralsız fiilin Infinitivo, Presente ve Pretérito çekimleri ile quiz oyunu.
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

SPANISH_IRREGULAR_VERBS = [
    {"inf": "ser", "pres": "yo soy, él es", "pret": "yo fui, él fue", "tr": "olmak (öz nitelik)"},
    {"inf": "estar", "pres": "yo estoy, él está", "pret": "yo estuve, él estuvo", "tr": "olmak, bulunmak (durum)"},
    {"inf": "ir", "pres": "yo voy, él va", "pret": "yo fui, él fue", "tr": "gitmek"},
    {"inf": "tener", "pres": "yo tengo, él tiene", "pret": "yo tuve, él tuvo", "tr": "sahip olmak"},
    {"inf": "hacer", "pres": "yo hago, él hace", "pret": "yo hice, él hizo", "tr": "yapmak, etmek"},
    {"inf": "poder", "pres": "yo puedo, él puede", "pret": "yo pude, él pudo", "tr": "-ebilmek, yapabilmek"},
    {"inf": "poner", "pres": "yo pongo, él pone", "pret": "yo puse, él puso", "tr": "koymak, yerleştirmek"},
    {"inf": "decir", "pres": "yo digo, él dice", "pret": "yo dije, él dijo", "tr": "söylemek, demek"},
    {"inf": "ver", "pres": "yo veo, él ve", "pret": "yo vi, él vio", "tr": "görmek"},
    {"inf": "dar", "pres": "yo doy, él da", "pret": "yo di, él dio", "tr": "vermek"},
    {"inf": "saber", "pres": "yo sé, él sabe", "pret": "yo supe, él supo", "tr": "bilmek"},
    {"inf": "querer", "pres": "yo quiero, él quiere", "pret": "yo quise, él quiso", "tr": "istemek, sevmek"},
    {"inf": "llegar", "pres": "yo llego, él llega", "pret": "yo llegué, él llegó", "tr": "varmak, ulaşmak"},
    {"inf": "pasar", "pres": "yo paso, él pasa", "pret": "yo pasé, él pasó", "tr": "geçmek, olmak (olay)"},
    {"inf": "deber", "pres": "yo debo, él debe", "pret": "yo debí, él debió", "tr": "zorunda olmak, borçlu olmak"},
    {"inf": "venir", "pres": "yo vengo, él viene", "pret": "yo vine, él vino", "tr": "gelmek"},
    {"inf": "pensar", "pres": "yo pienso, él piensa", "pret": "yo pensé, él pensó", "tr": "düşünmek"},
    {"inf": "sentir", "pres": "yo siento, él siente", "pret": "yo sentí, él sintió", "tr": "hissetmek"},
    {"inf": "salir", "pres": "yo salgo, él sale", "pret": "yo salí, él salió", "tr": "çıkmak, ayrılmak"},
    {"inf": "volver", "pres": "yo vuelvo, él vuelve", "pret": "yo volví, él volvió", "tr": "geri dönmek"},
    {"inf": "conocer", "pres": "yo conozco, él conoce", "pret": "yo conocí, él conoció", "tr": "tanımak, bilmek"},
    {"inf": "pedir", "pres": "yo pido, él pide", "pret": "yo pedí, él pidió", "tr": "istemek, rica etmek, sipariş vermek"},
    {"inf": "dormir", "pres": "yo duermo, él duerme", "pret": "yo dormí, él durmió", "tr": "uyumak"},
    {"inf": "morir", "pres": "yo muero, él muere", "pret": "yo morí, él murió", "tr": "ölmek"},
    {"inf": "traer", "pres": "yo traigo, él trae", "pret": "yo traje, él trajo", "tr": "getirmek"},
    {"inf": "oír", "pres": "yo oigo, él oye", "pret": "yo oí, él oyó", "tr": "duymak, işitmek"},
    {"inf": "caer", "pres": "yo caigo, él cae", "pret": "yo caí, él cayó", "tr": "düşmek"},
    {"inf": "seguir", "pres": "yo sigo, él sigue", "pret": "yo seguí, él siguió", "tr": "takip etmek, devam etmek"},
    {"inf": "empezar", "pres": "yo empiezo, él empieza", "pret": "yo empecé, él empezó", "tr": "başlamak"},
    {"inf": "entender", "pres": "yo entiendo, él entiende", "pret": "yo entendí, él entendió", "tr": "anlamak"},
]


class SpanishVerbsView(QWidget):
    """
    İspanyolca Düzensiz Fiil Tablosu ve Quiz Modülü.
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
        self.lbl_title = QLabel(" İspanyolca: Düzensiz Fiiller (Verbos Irregulares)")
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel("En önemli İspanyolca kuralsız fiil çekimleri ve interaktif test.")
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
        self.input_search.setPlaceholderText("Fiil veya Türkçe anlam ara... (örn: ser, gitmek, hacer)")
        self.input_search.setFixedHeight(40)
        self.input_search.textChanged.connect(self._filter_table)
        t_layout.addWidget(self.input_search)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Infinitivo (Mastar)", "Presente (Geniş Zaman)", "Pretérito Indefinido", "Türkçe Anlamı", "Dinle"])
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

        self.lbl_q_form = QLabel("yo soy / él es")
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

        self._populate_table(SPANISH_IRREGULAR_VERBS)

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
        for v in SPANISH_IRREGULAR_VERBS:
            if not q or q in v["inf"].lower() or q in v["pres"].lower() or q in v["pret"].lower() or q in v["tr"].lower():
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

            it_pret = QTableWidgetItem(item["pret"])
            it_pret.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 2, it_pret)

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
            btn_play.clicked.connect(lambda ch, w=item["inf"]: audio_player.play_pronunciation(w, lang="es"))

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
                audio_player.play_pronunciation(word, lang="es")

    def _next_quiz(self):
        self._is_quiz_busy = False
        self.lbl_q_feedback.setText("")
        for btn in self.btn_choices:
            btn.setEnabled(True)
            btn.set_state_style("normal")

        target = random.choice(SPANISH_IRREGULAR_VERBS)
        self._current_quiz = target

        is_pres = random.choice([True, False])
        form_text = target["pres"] if is_pres else target["pret"]
        form_label = "Presente" if is_pres else "Pretérito"

        hint_prefix = ui_text('Which verb belongs to this', self.lang)
        hint_suffix = ui_text('conjugation?', self.lang)
        self.lbl_q_hint.setText(f"{hint_prefix} {form_label} {hint_suffix} ({target['tr']})")
        self.lbl_q_form.setText(form_text)

        wrong_candidates = [v["inf"] for v in SPANISH_IRREGULAR_VERBS if v["inf"] != target["inf"]]
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

        audio_player.play_pronunciation(correct, lang="es")

        if chosen == correct:
            sfx.play_correct()
            chosen_btn.set_state_style("correct")
            self._quiz_score += 1
            self._quiz_streak += 1
            self.lbl_q_feedback.setStyleSheet("color: #00ff88; font-size: 16px; font-weight: 900;")
            self.lbl_q_feedback.setText(f" ¡Muy bien! {correct} ({self._current_quiz['tr']})")
        else:
            sfx.play_wrong()
            chosen_btn.set_state_style("wrong")
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
            "tr": "İspanyolca Fiiller (Verbos Irregulares)",
            "en": "Spanish Verbs (Verbos Irregulares)",
            "de": "Spanische Verben (Verbos Irregulares)",
            "es": "Verbos en español (Verbos Irregulares)"
        }
        sub_map = {
            "tr": "En sık kullanılan 40+ İspanyolca kuralsız fiilin Infinitivo, Presente ve Pretérito çekimleri ile quiz oyunu.",
            "en": "Most common 40+ Spanish irregular verbs with Infinitivo, Presente, Pretérito and quiz.",
            "de": "Häufigste 40+ spanische unregelmäßige Verben mit Infinitivo, Presente, Pretérito und Quiz.",
            "es": "Más de 40 verbos irregulares comunes en español con Infinitivo, Presente, Pretérito y quiz."
        }
        self.lbl_title.setText(title_map.get(lang, title_map["en"]))
        self.lbl_subtitle.setText(sub_map.get(lang, sub_map["en"]))
        tab_t_map = {"tr": "Fiil Tablosu", "en": "Verb Table", "de": "Verbtabelle", "es": "Tabla de verbos"}
        tab_q_map = {"tr": "Çekim Testi", "en": "Conjugation Quiz", "de": "Konjugations-Quiz", "es": "Quiz de conjugación"}
        self.btn_tab_table.setText(tab_t_map.get(lang, "Verb Table"))
        self.btn_tab_quiz.setText(tab_q_map.get(lang, "Conjugation Quiz"))

        search_map = {
            "tr": "İspanyolca fiil veya Türkçe anlam ara...",
            "en": "Search verb or meaning...",
            "de": "Verb oder Bedeutung suchen...",
            "es": "Buscar verbo o significado..."
        }
        self.input_search.setPlaceholderText(search_map.get(lang, "Search verb or meaning..."))
        col_m = {"tr": "Anlamı", "en": "Meaning", "de": "Bedeutung", "es": "Significado"}.get(lang, "Meaning")
        col_a = {"tr": "Ses", "en": "Audio", "de": "Audio", "es": "Audio"}.get(lang, "Audio")
        self.table.setHorizontalHeaderLabels([
            "Infinitivo", "Presente", "Pretérito", col_m, col_a
        ])
        score_prefix = {"tr": " Doğru:", "en": " Correct:", "de": " Richtig:", "es": " Correcto:"}.get(lang, " Correct:")
        streak_prefix = {"tr": " Seri:", "en": " Streak:", "de": " Serie:", "es": " Racha:"}.get(lang, " Streak:")
        self.lbl_score.setText(f"{score_prefix} {self._quiz_score}")
        self.lbl_streak.setText(f"{streak_prefix} {self._quiz_streak}")
        localize_tree(self,lang)
