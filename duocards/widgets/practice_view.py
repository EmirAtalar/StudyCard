"""Filtreye sadık, yanlış cevap üretmeyen ortak pratik ekranı."""
import html
import random
import time
import threading
from datetime import date
from PyQt6.QtCore import Qt, QTimer, QSignalBlocker, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QGridLayout, QProgressBar, QCheckBox, QScrollArea)
from duocards import db
from duocards.settings import settings
from duocards.audio import audio_player
from duocards.sfx import sfx
from duocards.languages import get_language_name, get_language_code
from duocards.sentence_memory import card_language, ensure_examples, request_examples
from duocards.practice import normalize_answer, accepted_answers, make_cloze, record_attempt, mistake_ids
from duocards.practice_menus import title
from duocards.widgets.universal_module_view import QuizChoiceButton as ChoiceButton
from duocards.widgets.practice_styles import PRACTICE_STYLES
from duocards.widgets.quiz_keyboard import QuizKeyboard, keyboard_help, keyboard_text
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QCheckBox, QLineEdit, QComboBox

TEXT = {
 'audio_loading': ['Ses hazırlanıyor…','Preparing audio…','Audio wird vorbereitet…','Preparando audio…'],
'audio_playing': ['Ses çalınıyor…','Playing audio…','Audio wird abgespielt…','Reproduciendo audio…'],
'audio_error': ['Ses çalınamadı. Yeniden deneyebilir veya başka kart seçebilirsin.','Audio could not play. Retry or choose another card.','Audio konnte nicht abgespielt werden. Erneut versuchen.','No se pudo reproducir el audio. Inténtalo de nuevo.'],
'audio_unavailable': ['Doğal ses şu an kullanılamıyor. İnternet bağlantısını ve ses oynatıcısını kontrol et.','Natural speech is unavailable. Check the connection and audio player.','Natürliche Sprache ist nicht verfügbar. Prüfe Verbindung und Audioplayer.','La voz natural no está disponible. Revisa la conexión y el reproductor.'],
'shadow_prompt': ['Cümleyi dinle, sesli tekrar et ve devam et.','Listen, repeat the sentence aloud, then continue.','Höre den Satz, sprich ihn nach und fahre fort.','Escucha la frase, repítela en voz alta y continúa.'],
'repeated': ['Sesli Tekrar Ettim','Repeated Aloud','Laut Wiederholt','Repetida en Voz Alta'],
'all_decks': ['Tüm Desteler','All Decks','Alle Decks','Todos los Mazos'],
'all_langs': ['Tüm Kelime Dilleri','All Word Languages','Alle Wortsprachen','Todos los Idiomas'],
'word': ['Kelimeyi Yaz','Write the Word','Wort Schreiben','Escribir la Palabra'],
'translate': ['Anlamını Yaz','Write the Meaning','Bedeutung Schreiben','Escribir el Significado'],
'sentence': ['Cümleyi Yaz','Write the Sentence','Satz Schreiben','Escribir la Frase'],
'choice': ['Seçeneklerle','Multiple Choice','Multiple Choice','Opciones'],
'write': ['Yazarak','Typing','Eingabe','Escribir'],
'listen': ['Dinle','Listen','Anhören','Escuchar'],
'slow': ['Yavaş Dinle','Listen Slowly','Langsam Anhören','Escuchar Despacio'],
'auto': ['Otomatik Dinlet','Auto Play','Automatisch Abspielen','Reproducir Automáticamente'],
'hint': ['İpucunu Göster','Show Hint','Hinweis Anzeigen','Mostrar Pista'],
'check': ['Kontrol Et','Check','Prüfen','Comprobar'],
'next': ['Sonraki','Next','Weiter','Siguiente'],
'restart': ['Yeni Oturum','New Session','Neue Sitzung','Nueva Sesión'],
'placeholder': ['Cevabını yaz ve Enter’a bas…','Type your answer and press Enter…','Antwort eingeben und Enter drücken…','Escribe y pulsa Enter…'],
'listen_prompt': ['Dinle ve duyduğunu yaz.','Listen and write what you hear.','Höre zu und schreibe, was du hörst.','Escucha y escribe lo que oyes.'],
'translate_prompt': ['Kelimeyi dinle ve anlamını yaz.','Listen to the word and write its meaning.','Höre das Wort und schreibe die Bedeutung.','Escucha la palabra y escribe su significado.'],
'writing_prompt': ['Bu anlama karşılık gelen kelimeyi yaz.','Write the word matching this meaning.','Schreibe das Wort zu dieser Bedeutung.','Escribe la palabra con este significado.'],
'meaning_prompt': ['Bu kelimenin anlamı nedir?','What does this word mean?','Was bedeutet dieses Wort?','¿Qué significa esta palabra?'],
'cloze_prompt': ['Cümledeki eksik kelimeyi tamamla.','Complete the missing word in the sentence.','Ergänze das fehlende Wort im Satz.','Completa la palabra que falta.'],
'empty': ['Bu seçimde uygun kart yok. Kart ekleyebilir veya filtreyi değiştirebilirsin.','No suitable cards for this selection. Add cards or change the filters.','Keine passenden Karten. Füge Karten hinzu oder ändere die Filter.','No hay tarjetas adecuadas. Añade tarjetas o cambia los filtros.'],
'no_sentence': ['Bu seçimde hedef kelimenin geçtiği kullanım cümlesi yok. Cümle Hafızası’ndan örnek ekleyebilir veya internetten örnek arayabilirsin.','No usage sentences contain the target words. Add or fetch examples in Sentence Memory.','Keine passenden Beispielsätze. Ergänze Beispiele im Satzspeicher.','No hay frases con las palabras. Añade ejemplos en el Banco de Frases.'],
'correct': ['Doğru!','Correct!','Richtig!','¡Correcto!'],
'wrong': ['Doğru cevap: ','Correct answer: ','Richtige Antwort: ','Respuesta correcta: '],
'blank': ['Önce bir cevap yaz.','Enter an answer first.','Gib zuerst eine Antwort ein.','Escribe una respuesta primero.'],
'complete': ['Oturum tamamlandı.','Session complete.','Sitzung abgeschlossen.','Sesión completada.'],
'score': ['Doğru','Correct','Richtig','Correctas'],
'answered': ['Yanıtlanan','Answered','Beantwortet','Respondidas'],
'star': ['Favoriden Çıkar','Remove Favorite','Favorit Entfernen','Quitar Favorito'],
'one_card': ['Seçenek için tek kelime var; yazarak cevapla.','Only one word is available; type your answer.','Nur ein Wort verfügbar; gib die Antwort ein.','Solo hay una palabra; escribe la respuesta.'],
'help': ['Enter: kontrol / sonraki · 1–4: seçenek · S: dinle. Pratik, Çalış ekranındaki ilerlemeni korur.','Enter: check / next · 1–4: choices · S: listen. Practice keeps your Study progress intact.','Enter: prüfen / weiter · 1–4: Optionen · S: anhören. Die Lernsitzung bleibt erhalten.','Enter: comprobar / siguiente · 1–4: opciones · S: escuchar. La sesión de repaso se conserva.'],
}


def text(key, lang):
    return TEXT[key][('tr','en','de','es').index(lang) if lang in ('tr','en','de','es') else 1]


class CardFilters(QWidget):
    changed = pyqtSignal()
    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.cmb_deck, self.cmb_lang = QComboBox(), QComboBox()
        for control in (self.cmb_deck,self.cmb_lang):
            control.setMinimumHeight(36)
            layout.addWidget(control,1)
            control.currentIndexChanged.connect(lambda: self.changed.emit())
        self.refresh()

    def refresh(self):
        deck, lang = self.cmb_deck.currentData(), self.cmb_lang.currentData()
        blockers = [QSignalBlocker(c) for c in (self.cmb_deck,self.cmb_lang)]
        self.cmb_deck.clear()
        self.cmb_deck.addItem(text('all_decks',self.lang),None)
        for d in db.get_all_decks():
            self.cmb_deck.addItem(d['name'],d['id'])
        self.cmb_lang.clear()
        self.cmb_lang.addItem(text('all_langs',self.lang),None)
        for code in sorted({card_language(c) for c in db.get_all_cards()}):
            self.cmb_lang.addItem(get_language_name(code,self.lang),code)
        for control,value in ((self.cmb_deck,deck),(self.cmb_lang,lang)):
            idx=control.findData(value)
            control.setCurrentIndex(max(0,idx))
        for blocker in blockers:
            blocker.unblock()

    def cards(self):
        cards=db.get_all_cards(deck_id=self.cmb_deck.currentData())
        code=self.cmb_lang.currentData()
        return [c for c in cards if not code or card_language(c)==code]


class PracticeView(QWidget):
    data_changed = pyqtSignal()
    pool_ready = pyqtSignal(int, object, str)
    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.setObjectName("practicePage")
        self.setStyleSheet(PRACTICE_STYLES)
        self.kind=kind
        self.lang=settings.get('ui_language','tr')
        self.current_card=None
        self.current_item=None
        self.score=self.streak=self.best_streak=0
        self._quiz_locked=False
        self._cards_pool=[]
        self._remaining=[]
        self._choices_data=[]
        self._generation=0
        self._autoplay_timer=QTimer(self)
        self._autoplay_timer.setSingleShot(True)
        self._autoplay_timer.timeout.connect(self._run_scheduled_audio)
        self._signature=None
        self._load_generation = 0
        self._load_cancel = threading.Event()
        self._pool_loading = False
        self.pool_ready.connect(self._accept_pool)
        self._expected=''
        self._audio_text=''
        self._completed=0
        self._total=0
        self.mode='word'
        self.hard_mode=False
        self._setup_ui()
        self._keyboard=QuizKeyboard(
            self, buttons=lambda:self.btn_choices, columns=2,
            typing=self.input_spelling, submit=self._submit_answer,
            next_button=self.btn_next, listen=self._play_audio_normal,
            slow=self._play_audio_slow, hint=self._show_hint,
            restart=lambda:self.reload_cards(force=True))
        self._next_item()

    def _setup_ui(self):
        outer=QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)
        page=QWidget()
        page.setObjectName("practiceContent")
        scroll.viewport().setObjectName("practiceViewport")
        scroll.setWidget(page)
        layout=QVBoxLayout(page)
        layout.setContentsMargins(24,22,24,22)
        layout.setSpacing(14)
        self.lbl_title=QLabel(title(self.kind,self.lang))
        self.lbl_title.setProperty('class','page-title')
        layout.addWidget(self.lbl_title)
        self.filters=CardFilters(self.lang)
        self.cmb_deck,self.cmb_lang=self.filters.cmb_deck,self.filters.cmb_lang
        self.filters.changed.connect(lambda:self.reload_cards(force=True))
        layout.addWidget(self.filters)
        toolbar=QHBoxLayout()
        self.cmb_mode=QComboBox()
        if self.kind=='dictation':
            for key in ('word','translate','sentence'):
                self.cmb_mode.addItem(text(key,self.lang),key)
        elif self.kind=='cloze':
            for key in ('choice','write'):
                self.cmb_mode.addItem(text(key,self.lang),key)
        self.cmb_mode.setVisible(self.kind in ('dictation','cloze'))
        self.cmb_mode.currentIndexChanged.connect(self._mode_changed)
        toolbar.addWidget(self.cmb_mode)
        self.chk_autoplay=QCheckBox(text('auto',self.lang))
        self.chk_autoplay.setChecked(settings.get('practice_autoplay', True))
        self.chk_autoplay.setVisible(self.kind in ('dictation','shadowing'))
        toolbar.addWidget(self.chk_autoplay)
        self.btn_hint=QPushButton(text('hint',self.lang))
        self.btn_hint.clicked.connect(self._show_hint)
        toolbar.addWidget(self.btn_hint)
        self.btn_reload=QPushButton(text('restart',self.lang))
        self.btn_reload.clicked.connect(lambda:self.reload_cards(force=True))
        toolbar.addWidget(self.btn_reload)
        layout.addLayout(toolbar)
        stats=QHBoxLayout()
        self.lbl_score=QLabel()
        self.lbl_counter=QLabel()
        stats.addWidget(self.lbl_score)
        stats.addStretch()
        stats.addWidget(self.lbl_counter)
        layout.addLayout(stats)
        self.progress_bar=QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        frame=QFrame()
        frame.setObjectName('practiceQuestion')
        frame.setStyleSheet('QFrame#practiceQuestion {background:#111827; border:none; border-radius:16px;}')
        body=QVBoxLayout(frame)
        body.setContentsMargins(24,24,24,24)
        body.setSpacing(16)
        self.lbl_instruction=QLabel()
        self.lbl_instruction.setWordWrap(True)
        body.addWidget(self.lbl_instruction)
        self.lbl_prompt=QLabel()
        self.lbl_prompt.setWordWrap(True)
        self.lbl_prompt.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_prompt.setStyleSheet('font-size:24px; font-weight:700; color:#ffffff; background:transparent; border:none;')
        self.lbl_prompt.setMinimumHeight(72)
        body.addWidget(self.lbl_prompt)
        self.lbl_cloze_sentence=self.lbl_prompt
        self.lbl_hint=QLabel()
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_hint.setStyleSheet('color:#ffffff; background:transparent; border:none;')
        body.addWidget(self.lbl_hint)
        self.lbl_sentence_translation=self.lbl_hint
        audio=QHBoxLayout()
        self.btn_play_audio=QPushButton(text('listen',self.lang))
        self.btn_slow_audio=QPushButton(text('slow',self.lang))
        self.btn_play_audio.clicked.connect(self._play_audio_normal)
        self.btn_slow_audio.clicked.connect(self._play_audio_slow)
        audio.addWidget(self.btn_play_audio)
        audio.addWidget(self.btn_slow_audio)
        audio.addStretch()
        self.btn_favorite=QPushButton(text('star',self.lang))
        self.btn_favorite.setVisible(self.kind=='favorites')
        self.btn_favorite.clicked.connect(self._remove_favorite)
        audio.addWidget(self.btn_favorite)
        body.addLayout(audio)
        self.lbl_audio_status=QLabel()
        self.lbl_audio_status.setWordWrap(True)
        self.lbl_audio_status.hide()
        body.addWidget(self.lbl_audio_status)
        audio_player.state_changed.connect(self._audio_state)
        self.lbl_help=QLabel()
        self.lbl_help.setWordWrap(True)
        self.lbl_help.setStyleSheet('color:#94a3b8; font-size:12px; background:transparent;')
        body.addWidget(self.lbl_help)
        self.typing_container=QWidget()
        typed=QHBoxLayout(self.typing_container)
        typed.setContentsMargins(0,0,0,0)
        self.input_spelling=QLineEdit()
        self.input_spelling.setPlaceholderText(text('placeholder',self.lang))
        self.input_spelling.setMinimumHeight(46)
        self.input_spelling.returnPressed.connect(self._enter)
        self.input_typing=self.input_spelling
        self.btn_check=QPushButton(text('check',self.lang))
        self.btn_check.setProperty('class','btn-primary')
        self.btn_check.setMinimumHeight(46)
        self.btn_check.clicked.connect(self._submit_answer)
        typed.addWidget(self.input_spelling,1)
        typed.addWidget(self.btn_check)
        body.addWidget(self.typing_container)
        self.choices_container=QWidget()
        grid=QGridLayout(self.choices_container)
        grid.setContentsMargins(0,0,0,0)
        self.btn_choices=[]
        for i in range(4):
            button=ChoiceButton()
            button.lbl_text.setTextFormat(Qt.TextFormat.PlainText)
            button.clicked.connect(lambda checked,index=i:self._on_choice_clicked(index))
            grid.addWidget(button,i//2,i%2)
            self.btn_choices.append(button)
        body.addWidget(self.choices_container)
        self.lbl_feedback=QLabel()
        self.lbl_feedback.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_feedback.setWordWrap(True)
        body.addWidget(self.lbl_feedback)
        self.btn_next=QPushButton(text('next',self.lang))
        self.btn_next.setProperty('class','btn-primary')
        self.btn_next.setMinimumHeight(42)
        self.btn_next.clicked.connect(self._next_item)
        body.addWidget(self.btn_next)
        body.addStretch(1)
        layout.addWidget(frame,1)
        self._update_keyboard_labels()

    def _update_keyboard_labels(self):
        for button,key,shortcut in (
                (self.btn_play_audio,'listen','Ctrl+S'),
                (self.btn_slow_audio,'slow','Ctrl+Shift+S'),
                (self.btn_hint,'hint','Ctrl+H'),
                (self.btn_reload,'restart','Ctrl+R'),
                (self.btn_check,'repeated' if self.kind=='shadowing' else 'check','Enter'),
                (self.btn_next,'next','Enter / '+keyboard_text('space',self.lang))):
            button.setText(f'{text(key,self.lang)} ({shortcut})')
        if not self.current_card:
            state=None
        elif self._quiz_locked:
            state='next' if self.btn_next.isEnabled() else 'waiting'
        else:
            state='choices' if not self.choices_container.isHidden() else 'typing'
        self.lbl_help.setText(keyboard_help(self.lang,state,hints=bool(self.current_card)))

    def refresh_filters(self):
        self.reload_cards()

    def reload_cards(self, force=False):
        self.filters.refresh()
        cards=[c for c in self.filters.cards() if c.get('term','').strip() and c.get('definition','').strip()]
        if self.kind=='favorites':
            cards=[c for c in cards if c.get('is_favorite')]
        if self.kind=='mistakes':
            ids=mistake_ids()
            cards=[c for c in cards if c['id'] in ids]
        signature=(self.mode,self.hard_mode,self.cmb_deck.currentData(),self.cmb_lang.currentData(),
                   tuple((c['id'],c['term'],c['definition'],c.get('example_sentence'),c.get('source_lang')) for c in cards),
                   None)
        needs_sentence=self.kind in ("cloze","shadowing") or (self.kind=="dictation" and self.mode=="sentence")
        if not force and signature==self._signature and (not needs_sentence or self._total > 0 or self._pool_loading):
            return
        self._signature=signature
        self._cards_pool=cards
        if self.kind == 'shadowing':
            self._load_cancel.set()
            self._load_cancel = threading.Event()
            cancelled = self._load_cancel
            self._load_generation += 1
            generation = self._load_generation
            self._pool_loading = True
            self._remaining = []
            self._total = self._completed = 0
            self._feedback_until = 0
            self._autoplay_timer.stop()
            self._next_item()
            self.lbl_prompt.setText(ui_text('Preparing sentences… You can keep using the app.', self.lang))
            signal = self.pool_ready
            def prepare():
                from duocards.sentence_memory import available_examples
                pool = []
                error = ''
                try:
                    for card, usable in available_examples(cards, cancelled):
                        if usable:
                            row = random.choice(usable)
                            pool.append(dict(card, example_sentence=row['text'], example_translation=row.get('translations', {}).get(get_language_code(card.get('target_lang', 'tr')), '')))
                except Exception as exc:
                    error = str(exc)
                if not cancelled.is_set():
                    try:
                        signal.emit(generation, pool, error)
                    except RuntimeError:
                        pass  # The window was closed while preparing.
            threading.Thread(target=prepare, daemon=True, name='shadowing-pool').start()
            return
        pool=[]
        needs_sentence=self.kind in ('cloze','shadowing') or (self.kind=='dictation' and self.mode=='sentence')
        for card in cards:
            if needs_sentence:
                usable=[row for row in request_examples(card) if row['kind']=='example'
                        and (self.kind!='cloze' or make_cloze(card,row['text']))]
                if usable:
                    row=random.choice(usable)
                    pool.append(dict(card,example_sentence=row['text'],
                                     example_translation=row['translations'].get(get_language_code(card.get('target_lang','tr')),'')))
            else:
                pool.append(card)
        random.shuffle(pool)
        self.score=self.streak=self.best_streak=self._completed=0
        self._total=len(pool)
        self._remaining=pool
        self._feedback_until=0
        if hasattr(self, '_feedback_timer'):
            self._feedback_timer.stop()
        self._next_item()

    def _accept_pool(self, generation, pool, error):
        if generation != self._load_generation:
            return
        self._pool_loading = False
        if error:
            self._signature = None
        random.shuffle(pool)
        self.score = self.streak = self.best_streak = self._completed = 0
        self._total = len(pool)
        self._remaining = pool
        self._feedback_until = 0
        self._next_item()
        if error:
            self.lbl_prompt.setText(ui_text('Unable to prepare sentences. Try again.', self.lang))

    def invalidate_session(self):
        self._load_cancel.set()
        self._load_generation += 1
        self._pool_loading = False
        self._signature = None
        self._remaining = []
        self.current_card = self.current_item = None
        self._autoplay_timer.stop()
        if hasattr(self, '_feedback_timer'):
            self._feedback_timer.stop()

    def _mode_changed(self):
        self.mode=self.cmb_mode.currentData() or 'word'
        self.hard_mode=self.mode=='write'
        self.reload_cards(force=True)

    def _set_mode(self, mode):
        idx=self.cmb_mode.findData(mode)
        if idx>=0:
            self.cmb_mode.setCurrentIndex(idx)

    def _update_badges(self):
        self.lbl_score.setText(f"{text('score',self.lang)}: {self.score}")
        self.lbl_counter.setText(f"{text('answered',self.lang)}: {self._completed} / {self._total}")
        self.progress_bar.setValue(round(100*self._completed/self._total) if self._total else 0)

    def _next_item(self):
        if time.monotonic() < getattr(self, '_feedback_until', 0):
            return
        self._generation+=1
        self._quiz_locked=False
        self._feedback_key=None
        self.lbl_feedback.clear()
        self.lbl_feedback.hide()
        self.lbl_hint.clear()
        self.lbl_hint.hide()
        self.input_spelling.clear()
        self.input_spelling.setEnabled(True)
        self.btn_check.setEnabled(True)
        self.btn_next.hide()
        self._choices_data=[]
        self._update_badges()
        if not self._remaining:
            self.current_card=self.current_item=None
            self._expected=self._audio_text=''
            self._quiz_locked=True
            self.lbl_instruction.clear()
            emptykey='no_sentence' if self._cards_pool and (self.kind in ('cloze','shadowing') or self.mode=='sentence') else 'empty'
            self.lbl_prompt.setText(text('complete' if self._total else emptykey,self.lang))
            self.typing_container.hide()
            self.choices_container.hide()
            self.btn_play_audio.setEnabled(False)
            self.btn_slow_audio.setEnabled(False)
            self.btn_hint.setEnabled(False)
            self.btn_favorite.setEnabled(False)
            self._update_keyboard_labels()
            self._keyboard.focus_answer()
            return
        self.current_card=self._remaining.pop(0)
        self.current_item=self.current_card
        card=self.current_card
        self._expected=card['term']
        self._audio_text=card['term']
        self._hint=card['definition']
        self.btn_play_audio.setEnabled(True)
        self.btn_slow_audio.setEnabled(True)
        self.btn_hint.setEnabled(True)
        self.btn_favorite.setEnabled(True)
        self.lbl_prompt.setTextFormat(Qt.TextFormat.PlainText)
        choice_mode=False
        if self.kind=='shadowing':
            self.lbl_instruction.setText(text('shadow_prompt',self.lang))
            self._audio_text=card['example_sentence']
            self._hint=card.get('example_translation','') or card['definition']
            self.lbl_prompt.setText(card['example_sentence'])
        elif self.kind=='dictation':
            self.lbl_instruction.setText(text('translate_prompt' if self.mode=='translate' else 'listen_prompt',self.lang))
            self.lbl_prompt.setText('♪')
            if self.mode=='translate':
                self._expected=card['definition']
                self._hint=card.get('part_of_speech','')
            elif self.mode=='sentence':
                self._expected=self._audio_text=card['example_sentence']
                self._hint=card.get('example_translation','')
        elif self.kind=='cloze':
            self.lbl_instruction.setText(text('cloze_prompt',self.lang))
            left,answer,right=make_cloze(card,card['example_sentence'])
            self._expected=answer
            self._audio_text=card['example_sentence']
            self._hint=card.get('example_translation','') or card['definition']
            self.lbl_prompt.setTextFormat(Qt.TextFormat.RichText)
            self.lbl_prompt.setText(html.escape(left)+'<span style="color:#34d399"> [ … ] </span>'+html.escape(right))
            choice_mode=not self.hard_mode
        elif self.kind=='favorites':
            self.lbl_instruction.setText(text('meaning_prompt',self.lang))
            self.lbl_prompt.setText(card['term'])
            self._expected=card['definition']
            self._hint=card.get('example_sentence','')
            choice_mode=True
        else:
            self.lbl_instruction.setText(text('writing_prompt',self.lang))
            self.lbl_prompt.setText(card['definition'])
            self._hint=card['term'][:1]+' · '+str(len(card['term']))
        if choice_mode:
            field='definition' if self.kind=='favorites' else 'term'
            alternatives=list({c[field].strip() for c in self._cards_pool
                               if card_language(c)==card_language(card) and get_language_code(c.get('target_lang','tr'))==get_language_code(card.get('target_lang','tr')) and normalize_answer(c[field])!=normalize_answer(self._expected)})
            random.shuffle(alternatives)
            self._choices_data=[self._expected]+alternatives[:3]
            random.shuffle(self._choices_data)
            if len(self._choices_data)<2:
                choice_mode=False
                self._feedback_key='one_card'
                self.lbl_feedback.setText(text('one_card',self.lang))
                self.lbl_feedback.show()
        for i,button in enumerate(self.btn_choices):
            button.setVisible(choice_mode and i<len(self._choices_data))
            button.setEnabled(True)
            button.set_state_style('normal')
            if i<len(self._choices_data):
                button.set_choice_text(f'{i+1}. {self._choices_data[i]}')
        self.choices_container.setVisible(choice_mode)
        self.typing_container.setVisible(not choice_mode)
        self.input_spelling.setVisible(self.kind!='shadowing')
        self.btn_check.setText(text('repeated' if self.kind=='shadowing' else 'check',self.lang))
        self._prefetch_audio()
        self._update_keyboard_labels()
        self._keyboard.focus_answer()
        if self.kind in ('dictation','shadowing') and self.chk_autoplay.isChecked() and self.isVisible():
            card=self.current_card
            generation=self._generation
            self._schedule_audio(card,generation)

    _next_cloze=_next_item

    def _prefetch_audio(self):
        if self.isVisible() and self.current_card:
            audio_player.prefetch(self._audio_text,card_language(self.current_card))
            for upcoming in self._remaining[:2]:
                spoken=upcoming.get('example_sentence','') if self.kind in ('cloze','shadowing') or self.mode=='sentence' else upcoming['term']
                audio_player.prefetch(spoken,card_language(upcoming))

    def _schedule_audio(self,card,generation):
        self._scheduled_audio=(card,generation)
        self._autoplay_timer.start(30)

    def _run_scheduled_audio(self):
        card,generation=self._scheduled_audio
        self._autoplay_if_current(card,generation)

    def _autoplay_if_current(self, card, generation=None):
        if self.isVisible() and self.current_card is card and (generation is None or generation==self._generation):
            self._play_audio_normal()

    def _play_audio_normal(self):
        if self.current_card and self._audio_text:
            audio_player.play_pronunciation(self._audio_text,lang=card_language(self.current_card),speed=1.0)

    def _play_audio_slow(self):
        if self.current_card and self._audio_text:
            audio_player.play_pronunciation(self._audio_text,lang=card_language(self.current_card),speed=0.75)

    _play_sentence_audio=_play_audio_normal

    def _show_hint(self):
        if self.current_card:
            self.lbl_hint.setText(self._hint)
            self.lbl_hint.setVisible(bool(self._hint))

    def _enter(self):
        self._keyboard._enter()

    def _submit_answer(self):
        if not self.current_card or self._quiz_locked:
            return
        if self.kind=='shadowing':
            self._evaluate(self._expected)
            return
        answer=self.input_spelling.text().strip()
        if not answer:
            self._feedback_key='blank'
            self.lbl_feedback.setText(text('blank',self.lang))
            self.lbl_feedback.show()
            return
        self._evaluate(answer)

    _submit_typing=_submit_answer

    def _on_choice_clicked(self, idx):
        if self.current_card and not self._quiz_locked and 0<=idx<len(self._choices_data):
            self._evaluate(self._choices_data[idx])

    def _evaluate(self, answer):
        self._quiz_locked=True
        synonyms=(self.kind=='favorites' or (self.kind=='dictation' and self.mode=='translate'))
        expected_lang=get_language_code(self.current_card.get('target_lang','tr')) if synonyms else card_language(self.current_card)
        valid=accepted_answers(self._expected,expected_lang) if synonyms else {normalize_answer(self._expected,expected_lang)}
        correct=normalize_answer(answer,expected_lang) in valid
        record_attempt(self.current_card,self.kind,answer,self._expected,correct)
        self._completed+=1
        self.score+=int(correct)
        self.streak=self.streak+1 if correct else 0
        self.best_streak=max(self.best_streak,self.streak)
        self.input_spelling.setEnabled(False)
        self.btn_check.setEnabled(False)
        for i,button in enumerate(self.btn_choices):
            button.setEnabled(False)
            if i<len(self._choices_data) and normalize_answer(self._choices_data[i],expected_lang) in valid:
                button.set_state_style('correct')
            elif i<len(self._choices_data) and self._choices_data[i]==answer:
                button.set_state_style('wrong')
        self._feedback_key='correct' if correct else 'wrong'
        self.lbl_feedback.setText(text('correct',self.lang)+' '+self._expected if correct else text('wrong',self.lang)+self._expected)
        self.lbl_feedback.show()
        self.lbl_feedback.setStyleSheet('color:#34d399; background:transparent; border:none; padding:12px;' if correct else 'color:#fb7185; background:transparent; border:none; padding:12px;')
        self._show_hint()
        delay = settings.get('practice_advance_ms', 300) if correct else 0
        self._feedback_until=time.monotonic()+delay/1000
        self.btn_next.show()
        self.btn_next.setEnabled(not correct)
        if not hasattr(self, '_feedback_timer'):
            self._feedback_timer=QTimer(self)
            self._feedback_timer.setSingleShot(True)
            self._feedback_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self._feedback_timer.timeout.connect(self._unlock_feedback)
        self._feedback_timer.start(delay)
        self._update_keyboard_labels()
        if self.isVisible():
            self.setFocus()
        (sfx.play_correct if correct else sfx.play_wrong)()
        self._update_badges()

    def _unlock_feedback(self):
        if self._quiz_locked and self.current_card:
            if self._feedback_key == 'correct' and self.isVisible() and settings.get('practice_auto_next', True):
                self._feedback_until = 0
                self._next_item()
                return
            self.btn_next.setEnabled(True)
            self._update_keyboard_labels()
            if self.isVisible():
                self.btn_next.setFocus()

    def _remove_favorite(self):
        if self.current_card and self.current_card.get('is_favorite'):
            db.toggle_card_favorite(self.current_card['id'])
            self.data_changed.emit()
            self.reload_cards(force=True)

    def showEvent(self,event):
        super().showEvent(event)
        self._prefetch_audio()
        QTimer.singleShot(0,self._keyboard.focus_answer)
        if self.kind in ('dictation','shadowing') and self.current_card and self.chk_autoplay.isChecked():
            card,generation=self.current_card,self._generation
            self._schedule_audio(card,generation)

    def _audio_state(self,state):
        self._last_audio_state=state
        if self.isVisible():
            self.lbl_audio_status.setVisible(state in ("loading","playing","error","unavailable"))
            self.lbl_audio_status.setText(text("audio_"+state,self.lang) if state in ("loading","playing","error","unavailable") else "")

    def hideEvent(self,event):
        self._autoplay_timer.stop()
        self._generation+=1
        if self.kind in ("dictation","cloze","shadowing"):
            audio_player.stop()
        super().hideEvent(event)

    def update_language(self,lang):
        self.lang=lang
        self.lbl_title.setText(title(self.kind,lang))
        self.filters.lang=lang
        self.filters.refresh()
        for button,key in [(self.btn_play_audio,'listen'),(self.btn_slow_audio,'slow'),(self.btn_check,'repeated' if self.kind=='shadowing' else 'check'),
                           (self.btn_next,'next'),(self.btn_hint,'hint'),(self.btn_reload,'restart'),(self.btn_favorite,'star')]:
            button.setText(text(key,lang))
        self.chk_autoplay.setText(text('auto',lang))
        self.input_spelling.setPlaceholderText(text('placeholder',lang))
        blocker=QSignalBlocker(self.cmb_mode)
        for i in range(self.cmb_mode.count()):
            self.cmb_mode.setItemText(i,text(self.cmb_mode.itemData(i),lang))
        blocker.unblock()
        if self.current_card:
            key='shadow_prompt' if self.kind=='shadowing' else ('translate_prompt' if self.mode=='translate' else 'listen_prompt') if self.kind=='dictation' else 'cloze_prompt' if self.kind=='cloze' else 'meaning_prompt' if self.kind=='favorites' else 'writing_prompt'
            self.lbl_instruction.setText(text(key,lang))
        else:
            emptykey='no_sentence' if self._cards_pool and (self.kind in ('cloze','shadowing') or self.mode=='sentence') else 'empty'
            self.lbl_prompt.setText(text('complete' if self._total else emptykey,lang))
        feedback=getattr(self,'_feedback_key',None)
        if feedback:
            suffix=(' '+self._expected if feedback=='correct' else self._expected) if feedback in ('correct','wrong') else ''
            self.lbl_feedback.setText(text(feedback,lang)+suffix)
        if self.lbl_audio_status.text():
            self._audio_state(getattr(self,'_last_audio_state','idle'))
        if self._signature is not None:
            self._update_badges()
        self._update_keyboard_labels()
        localize_tree(self,lang)
