"""
Study Card - Kelime Eşleştirme & Hızlı Refleks Oyunu (Speed Match Game)
Kullanıcının destelerindeki kelime ve anlamları karışık bir ızgara üzerinde eşleştirmesini sağlar.
Süreye karşı yarış, kombo çarpanı, ses efektleri ve dinamik çok dilli arayüz.
"""

import random
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QComboBox, QFrame, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor, QColor
from duocards.db import get_all_decks, get_cards, get_distinct_target_languages
from duocards.sfx import sfx
from duocards.audio import audio_player
from duocards.settings import settings
from duocards.i18n import t
from duocards.icons import get_icon
from duocards.languages import get_language_name, get_language_code
from duocards.sentence_memory import card_language
from duocards.practice import normalize_answer, record_attempt
from duocards.widgets.quiz_keyboard import QuizKeyboard, keyboard_help, keyboard_text
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QComboBox


class MatchTileButton(QPushButton):
    """Eşleştirme kutucuğu butonu."""
    def __init__(self, text: str, pair_id: int, is_term: bool, parent=None):
        super().__init__(parent)
        self.pair_id = pair_id
        self.is_term = is_term
        self.raw_text = text
        self.is_matched = False
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self.lbl_text = QLabel(text)
        self.lbl_text.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_text.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(self.lbl_text)

        self.set_state("normal")

    def set_state(self, state: str):
        if state == "normal":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #162032;
                    border: 2px solid #283548;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    border-color: #3b82f6;
                }
            """)
            self.lbl_text.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: 700; background: transparent; border: none;")
        elif state == "selected":
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(59, 130, 246, 0.25);
                    border: 2px solid #3b82f6;
                    border-radius: 14px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #60a5fa; font-size: 14px; font-weight: 800; background: transparent; border: none;")
        elif state == "correct":
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.25);
                    border: 2px solid #10b981;
                    border-radius: 14px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #34d399; font-size: 14px; font-weight: 800; background: transparent; border: none;")
        elif state == "wrong":
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(239, 68, 68, 0.25);
                    border: 2px solid #ef4444;
                    border-radius: 14px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #f87171; font-size: 14px; font-weight: 800; background: transparent; border: none;")
        elif state == "matched":
            self.setEnabled(False)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0b1120;
                    border: 2px solid #1e293b;
                    border-radius: 14px;
                }
            """)
            self.lbl_text.setStyleSheet("color: #334155; font-size: 14px; font-weight: 600; text-decoration: line-through; background: transparent; border: none;")
        self.setStyleSheet(self.styleSheet() + '\nQPushButton:focus { border: 2px solid #ffffff; }')


class MatchGameView(QWidget):
    """
    Duolingo Match Madness & Quizlet Match tarzı
    Kelime ve Anlam Hızlı Eşleştirme Oyunu.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")

        self.score = 0
        self.combo = 0
        self.time_left = 60
        self.total_pairs = 6
        self.matched_pairs = 0
        self.best_score = settings.get("match_game_best_score", 0)

        self._selected_tile: Optional[MatchTileButton] = None
        self._is_checking = False
        self._round_generation = 0
        self._game_initialized = False
        self._round_cards = {}
        self._all_tiles: List[MatchTileButton] = []

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

        self._setup_ui()
        self._keyboard = QuizKeyboard(
            self, buttons=lambda: self._all_tiles, choice_keys=False,
            listen=self._listen_focused_tile, restart=self._start_new_game,
            enter=self._keyboard_enter)
        self.refresh_filters()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        # Üst Panel: Başlık & Deste / Dil Filtreleri
        header_row = QHBoxLayout()
        header_info = QVBoxLayout()
        header_info.setSpacing(2)

        self.lbl_title = QLabel(t("nav_match", self.lang) if t("nav_match", self.lang) != "nav_match" else "Kelime Eşleştirme Oyunu")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; background: transparent;")
        self.lbl_subtitle = QLabel(ui_text('Match words with their definitions as fast as you can.', self.lang))
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #94a3b8; background: transparent;")

        header_info.addWidget(self.lbl_title)
        header_info.addWidget(self.lbl_subtitle)
        header_row.addLayout(header_info, 1)

        # Deste & Dil Seçicileri
        self.cmb_deck = QComboBox()
        self.cmb_deck.setMinimumWidth(180)
        from duocards.widgets.library_view import QuizFilterHighlightDelegate
        self.cmb_deck.setItemDelegate(QuizFilterHighlightDelegate(self.cmb_deck))
        self.cmb_deck.currentIndexChanged.connect(self._start_new_game)
        header_row.addWidget(self.cmb_deck)

        self.cmb_lang = QComboBox()
        self.cmb_lang.setMinimumWidth(160)
        self.cmb_lang.setItemDelegate(QuizFilterHighlightDelegate(self.cmb_lang))
        self.cmb_lang.currentIndexChanged.connect(self._start_new_game)
        header_row.addWidget(self.cmb_lang)

        main_layout.addLayout(header_row)

        # Skor ve Sayaç Paneli (Modern Rozetler)
        stats_panel = QFrame()
        stats_panel.setStyleSheet("""
            QFrame {
                background-color: #131b2e;
                border: 1px solid #1e293b;
                border-radius: 14px;
                padding: 6px 16px;
            }
        """)
        s_layout = QHBoxLayout(stats_panel)
        s_layout.setSpacing(18)

        # Kalan Süre
        self.lbl_time = QLabel(ui_text('Time: 60s', self.lang))
        self.lbl_time.setStyleSheet("font-size: 14px; font-weight: 800; color: #38bdf8; background: transparent;")
        s_layout.addWidget(self.lbl_time)

        # İlerleme Çubuğu
        self.time_bar = QProgressBar()
        self.time_bar.setFixedHeight(8)
        self.time_bar.setMaximum(60)
        self.time_bar.setValue(60)
        self.time_bar.setTextVisible(False)
        self.time_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 4px;
            }
        """)
        s_layout.addWidget(self.time_bar, 1)

        # Skor
        self.lbl_score = QLabel(ui_text('Score: {self.score}', self.lang, **{'self.score': self.score}))
        self.lbl_score.setStyleSheet("font-size: 14px; font-weight: 800; color: #10b981; background: transparent;")
        s_layout.addWidget(self.lbl_score)

        # Kombo
        self.lbl_combo = QLabel(ui_text('Combo: x1', self.lang))
        self.lbl_combo.setStyleSheet("font-size: 13px; font-weight: 800; color: #f59e0b; background: transparent;")
        s_layout.addWidget(self.lbl_combo)

        # En Yüksek Skor
        self.lbl_best = QLabel(ui_text('Best: {self.best_score}', self.lang, **{'self.best_score': self.best_score}))
        self.lbl_best.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8; background: transparent;")
        s_layout.addWidget(self.lbl_best)

        # Yeniden Başlat Butonu
        self.btn_restart = QPushButton(ui_text('Restart', self.lang))
        self.btn_restart.setProperty("class", "btn-secondary")
        self.btn_restart.setFixedHeight(34)
        self.btn_restart.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_restart.clicked.connect(self._start_new_game)
        s_layout.addWidget(self.btn_restart)

        main_layout.addWidget(stats_panel)
        self.lbl_keyboard_help = QLabel(keyboard_help(self.lang, 'match'))
        self.lbl_keyboard_help.setWordWrap(True)
        self.lbl_keyboard_help.setStyleSheet('color:#94a3b8; font-size:12px; background:transparent;')
        main_layout.addWidget(self.lbl_keyboard_help)
        self.btn_restart.setToolTip(keyboard_text('restart', self.lang))

        # Kartlar Izgarası Kapsayıcısı (Grid)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setSpacing(12)
        main_layout.addWidget(self.grid_container, 1)

        # Oyun Sonu / Tebrik Paneli
        self.panel_finish = QFrame()
        self.panel_finish.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #162032, stop:1 #0f172a);
                border: 2px solid #10b981;
                border-radius: 20px;
                padding: 24px;
            }
        """)
        f_layout = QVBoxLayout(self.panel_finish)
        f_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_layout.setSpacing(12)

        self.lbl_finish_title = QLabel(ui_text('Awesome! Round Completed!', self.lang))
        self.lbl_finish_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #10b981; background: transparent;")
        f_layout.addWidget(self.lbl_finish_title)

        self.lbl_finish_details = QLabel("")
        self.lbl_finish_details.setStyleSheet("font-size: 15px; color: #cbd5e1; background: transparent;")
        f_layout.addWidget(self.lbl_finish_details)

        self.btn_next_round = QPushButton(ui_text('Next Round', self.lang))
        self.btn_next_round.setProperty("class", "btn-primary")
        self.btn_next_round.setFixedHeight(44)
        self.btn_next_round.setFixedWidth(200)
        self.btn_next_round.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_next_round.clicked.connect(self._start_new_game)
        f_layout.addWidget(self.btn_next_round)

        self.panel_finish.setVisible(False)
        main_layout.addWidget(self.panel_finish, 1)

    def reload_cards(self):
        self.refresh_filters()

    def refresh_filters(self):
        current_deck,current_lang=self.cmb_deck.currentData(),self.cmb_lang.currentData()
        self.cmb_deck.blockSignals(True)
        self.cmb_deck.clear()
        self.cmb_deck.addItem(t("filter_all_decks",self.lang),None)
        for deck in get_all_decks():
            self.cmb_deck.addItem(deck['name'],deck['id'])
        self.cmb_deck.setCurrentIndex(max(0,self.cmb_deck.findData(current_deck)))
        self.cmb_deck.blockSignals(False)
        self.cmb_lang.blockSignals(True)
        self.cmb_lang.clear()
        self.cmb_lang.addItem(ui_text('All Word Languages', self.lang),None)
        for lang in sorted({card_language(c) for c in get_cards()}):
            self.cmb_lang.addItem(get_language_name(lang,self.lang),lang)
        self.cmb_lang.setCurrentIndex(max(0,self.cmb_lang.findData(current_lang)))
        self.cmb_lang.blockSignals(False)
        if not self._game_initialized:
            self._start_new_game()

    def _start_new_game(self):
        self._round_generation += 1
        self._game_initialized = True
        self._timer.stop()
        self.score = 0
        self.combo = 1
        self.time_left = 60
        self.matched_pairs = 0
        self._selected_tile = None
        self._is_checking = False

        self._update_badges()
        self.time_bar.setValue(60)

        # Kartları çek
        deck_id = self.cmb_deck.currentData()
        lang = self.cmb_lang.currentData()
        cards = [c for c in get_cards(deck_id=deck_id) if not lang or card_language(c)==lang]
        terms,meanings,unique=set(),set(),[]
        for card in cards:
            term=normalize_answer(card['term'])
            meaning=normalize_answer(card['definition'].split(',')[0].split('/')[0])
            if term and meaning and term not in terms and meaning not in meanings:
                terms.add(term)
                meanings.add(meaning)
                unique.append(card)
        cards=unique

        if len(cards) < 4:
            # Boş durum uyarısı
            self._render_empty_grid()
            return

        # Rastgele 6 kelime seç
        chosen = random.sample(cards, min(len(cards), 6))
        self._round_cards = {c["id"]: c for c in chosen}
        self.total_pairs = len(chosen)

        # 12 adet karo oluştur (6 kelime + 6 anlam)
        items = []
        for c in chosen:
            term_lang = card_language(c)
            items.append((c["term"], c["id"], True, term_lang))
            # Anlamı temizle, ilk anlamı al
            clean_def = c["definition"].split(",")[0].split("/")[0].strip()
            items.append((clean_def, c["id"], False, get_language_code(c.get("target_lang", "tr"))))

        random.shuffle(items)

        # Grid'i temizle ve yerleştir (3 satır x 4 sütun)
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_tiles.clear()
        for idx, (text, pair_id, is_term, lang_code) in enumerate(items):
            row = idx // 4
            col = idx % 4
            tile = MatchTileButton(text, pair_id, is_term)
            tile.lang_code = lang_code
            tile.clicked.connect(lambda ch, t=tile: self._on_tile_clicked(t))
            self.grid_layout.addWidget(tile, row, col)
            self._all_tiles.append(tile)

        self.lbl_finish_title.setText(ui_text('Well Done!', self.lang))
        self.lbl_finish_title.setStyleSheet("font-size:24px; font-weight:900; color:#34d399;")
        self.grid_container.setVisible(True)
        self.panel_finish.setVisible(False)
        if self.isVisible():
            self._timer.start()
        self._keyboard.focus_answer()

    def _keyboard_enter(self):
        if self.panel_finish.isVisible():
            self._start_new_game()
        else:
            buttons = self._keyboard.available_buttons()
            focused = self.focusWidget()
            if focused in buttons:
                focused.click()
            elif buttons:
                buttons[0].setFocus()

    def _listen_focused_tile(self):
        tile = self.focusWidget()
        if tile in self._all_tiles:
            audio_player.play_pronunciation(tile.raw_text, lang=getattr(tile, 'lang_code', 'en'))

    def _render_empty_grid(self):
        self.total_pairs = 0
        self._all_tiles.clear()
        self.grid_container.show()
        self.panel_finish.hide()
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lbl = QLabel(ui_text('Add at least 4 distinct word/meaning pairs to this selection to play.', self.lang))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: 700; background: transparent;")
        self.grid_layout.addWidget(lbl, 0, 0, 1, 4)

    def _on_tile_clicked(self, tile: MatchTileButton):
        if self._is_checking or tile.is_matched:
            return

        # Aynı karoya tekrar basıldıysa seçimi iptal et
        if self._selected_tile == tile:
            tile.set_state("normal")
            self._selected_tile = None
            return

        # Birinci kart seçimi
        if self._selected_tile is None:
            sfx.play_click()
            self._selected_tile = tile
            tile.set_state("selected")
            if tile.is_term:
                audio_player.play_pronunciation(tile.raw_text, lang=getattr(tile, "lang_code", "en"))
            return

        # İkinci kart seçimi (Eşleşme Kontrolü)
        first = self._selected_tile
        second = tile
        second.set_state("selected")
        if second.is_term:
            audio_player.play_pronunciation(second.raw_text, lang=getattr(second, "lang_code", "en"))

        # Aynı türse (örn: iki kelime veya iki anlam) seçimi değiştir
        if first.is_term == second.is_term:
            first.set_state("normal")
            self._selected_tile = second
            return

        self._is_checking = True
        generation = self._round_generation
        term_tile = first if first.is_term else second
        meaning_tile = second if first.is_term else first
        card = self._round_cards.get(term_tile.pair_id)
        if card:
            record_attempt(card, 'match', meaning_tile.raw_text, card['definition'], first.pair_id == second.pair_id)

        if first.pair_id == second.pair_id:
            # DOĞRU EŞLEŞME
            sfx.play_correct()
            first.set_state("correct")
            second.set_state("correct")

            # Puan & Kombo artır
            added = 100 * self.combo
            self.score += added
            self.combo = min(10, self.combo + 1)
            self.matched_pairs += 1

            if self.score > self.best_score:
                self.best_score = self.score
                settings.set("match_game_best_score", self.best_score)

            self._update_badges()

            QTimer.singleShot(350, lambda: self._finish_if_current(generation, first, second, True))
        else:
            # YANLIŞ EŞLEŞME
            sfx.play_wrong()
            first.set_state("wrong")
            second.set_state("wrong")
            self.combo = 1
            self._update_badges()

            QTimer.singleShot(500, lambda: self._finish_if_current(generation, first, second, False))

    def _finish_if_current(self, generation, first, second, correct):
        if generation == self._round_generation:
            (self._finalize_match if correct else self._reset_mismatch)(first, second)

    def showEvent(self, event):
        super().showEvent(event)
        if self.total_pairs and not self.grid_container.isHidden() and self.time_left > 0:
            self._timer.start()
        QTimer.singleShot(0, self._keyboard.focus_answer)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _finalize_match(self, t1: MatchTileButton, t2: MatchTileButton):
        t1.is_matched = True
        t2.is_matched = True
        t1.set_state("matched")
        t2.set_state("matched")
        self._selected_tile = None
        self._is_checking = False

        if self.matched_pairs >= self.total_pairs:
            self._on_round_completed()
        elif self.isVisible():
            self._keyboard.focus_answer()

    def _reset_mismatch(self, t1: MatchTileButton, t2: MatchTileButton):
        t1.set_state("normal")
        t2.set_state("normal")
        self._selected_tile = None
        self._is_checking = False

    def _on_tick(self):
        self.time_left -= 1
        self.time_bar.setValue(self.time_left)
        time_lbl = ui_text('Time', self.lang)
        self.lbl_time.setText(f"{time_lbl}: {self.time_left}s")

        if self.time_left <= 0:
            self._timer.stop()
            self._on_time_over()

    def _on_round_completed(self):
        self._timer.stop()
        sfx.play_complete()
        bonus = self.time_left * 20
        self.score += bonus

        if self.score > self.best_score:
            self.best_score = self.score
            settings.set("match_game_best_score", self.best_score)
        self._update_badges()

        self.grid_container.setVisible(False)
        self.panel_finish.setVisible(True)
        if self.isVisible():
            self.btn_next_round.setFocus()

        detail_text = ui_text('Awesome! Time Bonus: +{bonus} pts | Total Score: {self.score}', self.lang, **{'bonus': bonus, 'self.score': self.score})
        self.lbl_finish_details.setText(detail_text)

    def _on_time_over(self):
        self._round_generation += 1
        sfx.play_wrong()
        self.grid_container.setVisible(False)
        self.panel_finish.setVisible(True)
        if self.isVisible():
            self.btn_next_round.setFocus()
        self.lbl_finish_title.setText(ui_text("Time's Up!", self.lang))
        self.lbl_finish_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #ef4444; background: transparent;")
        self.lbl_finish_details.setText(ui_text('Total Score Earned: {self.score}', self.lang, **{'self.score': self.score}))

    def _update_badges(self):
        score_lbl = ui_text('Score', self.lang)
        combo_lbl = ui_text('Combo', self.lang)
        best_lbl = ui_text('Best', self.lang)

        self.lbl_score.setText(f"{score_lbl}: {self.score}")
        self.lbl_combo.setText(f"{combo_lbl}: x{self.combo}")
        self.lbl_best.setText(f"{best_lbl}: {self.best_score}")

    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(ui_text('Word Match Game', lang))
        self.lbl_subtitle.setText(ui_text('Match words with their definitions as fast as you can.', lang))
        self.btn_restart.setText(ui_text('Restart', lang))
        self.btn_next_round.setText(ui_text('Next Round', lang))
        self.lbl_keyboard_help.setText(keyboard_help(lang, 'match'))
        self.btn_restart.setToolTip(keyboard_text('restart', lang))
        self._update_badges()
        time_lbl = ui_text('Time', self.lang)
        self.lbl_time.setText(f"{time_lbl}: {self.time_left}s")
        localize_tree(self,lang)
