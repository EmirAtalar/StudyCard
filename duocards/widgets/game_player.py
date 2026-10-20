"""Playable previews and saved games, using the app's existing visual language."""
import copy
import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QScrollArea
from duocards.ui_localization import QLineEdit, ui_text, localize_tree
from duocards.widgets.studio_dialogs import STUDIO_STYLES, label, button, apply_studio_style
from duocards.styles import transform_preferences
from duocards import custom_games
from duocards.audio import audio_player
from duocards.sfx import sfx

MODE_TITLES = {'quiz':'Multiple choice', 'matching':'Match pairs', 'typing':'Type the answer',
    'audio_dictation':'Listen and write', 'audio_translation':'Listen and translate',
    'audio_quiz':'Listening quiz', 'memory':'Memory cards', 'word_builder':'Build the word'}
MODE_DESCRIPTIONS = {
    'quiz':'Read the question and choose the right answer.',
    'matching':'Match each question with its answer.',
    'typing':'Read the question and type its answer.',
    'audio_dictation':'Listen and type exactly what you hear. Meanings are optional.',
    'audio_translation':'Listen and type the translation in the answer language.',
    'audio_quiz':'Listen and choose the matching translation.',
    'memory':'Turn over two cards to find question and answer pairs.',
    'word_builder':'Use the meaning as a clue and arrange the letters of the word.',
}


class GamePlayer(QWidget):
    finished = pyqtSignal()

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.session = None
        self.preview = True
        self._deadline = None
        self._recorded = False
        self._left = self._right = None
        self._started = 0
        self._paused_at = None
        self._paused_total = 0
        self._waiting_audio=False
        self._pending_audio=False
        self._memory_busy=False
        self._timer = QTimer(self); self._timer.setInterval(100); self._timer.timeout.connect(self._tick)
        self._memory_timer=QTimer(self);self._memory_timer.setSingleShot(True);self._memory_timer.timeout.connect(self._reset_memory_pair)
        self._audio_request=None
        audio_player.request_state_changed.connect(self._audio_state)
        from PyQt6.QtGui import QShortcut, QKeySequence
        shortcut=QShortcut(QKeySequence('Ctrl+S'),self,activated=self.listen)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        apply_studio_style(self)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.shell = QFrame(); self.shell.setProperty('studioPanel', True)
        outer.addWidget(self.shell)
        frame = QVBoxLayout(self.shell); frame.setContentsMargins(22,22,22,22); frame.setSpacing(14)
        self.badge = label('LIVE PREVIEW', lang, 'eyebrow'); frame.addWidget(self.badge)
        self.title = label('Your game takes shape here.', lang, 'heading'); frame.addWidget(self.title)
        stats = QHBoxLayout(); self.counter = label('',lang,'muted'); self.clock = label('',lang,'eyebrow'); stats.addWidget(self.counter,1); stats.addWidget(self.clock); frame.addLayout(stats)
        self.progress = QProgressBar(); self.progress.setRange(0,100); self.progress.setTextVisible(False); self.progress.setFixedHeight(6); frame.addWidget(self.progress)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.stage = QWidget(); self.stage_layout = QVBoxLayout(self.stage); self.stage_layout.setContentsMargins(0,12,0,12); self.stage_layout.setSpacing(14)
        scroll.setWidget(self.stage); frame.addWidget(scroll,1)
        self.feedback = label('',lang); self.feedback.hide(); frame.addWidget(self.feedback)
        controls = QHBoxLayout()
        self.listen_button = button('Listen',lang,self.listen,'audio')
        self.hint_button = button('Hint',lang,self.hint,'bulb')
        self.next_button = button('Next',lang,self.next,'check','primary')
        self.restart_button = button('Play again',lang,self.restart,'gamepad')
        for control in (self.listen_button,self.hint_button,self.restart_button,self.next_button): controls.addWidget(control)
        frame.addLayout(controls)
        self.placeholder()

    def _clear_stage(self):
        while self.stage_layout.count():
            item = self.stage_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide(); widget.deleteLater()

    def placeholder(self):
        self._timer.stop();self._memory_timer.stop();self._waiting_audio=False;self._pending_audio=False
        self.session = None; self._audio_request=None;self._clear_stage()
        self.stage_layout.addWidget(label('Choose a game style, add your content and press Preview. You can play before saving.',self.lang,'muted'))
        self.stage_layout.addStretch()
        self.counter.clear(); self.clock.clear(); self.progress.setValue(0)
        for control in (self.listen_button,self.hint_button,self.next_button,self.restart_button): control.hide()

    def start(self, game, preview=False):
        session = custom_games.GameSession(game)
        self._waiting_audio=False;self._pending_audio=False;self._memory_busy=False;self._memory_timer.stop()
        self._timer.stop(); audio_player.stop()
        self.session = session; self.preview = preview; self._recorded = False; self._expired=False; self._started = time.monotonic()
        self._paused_total=0;self._paused_at=None if self.isVisible() else self._started
        if hasattr(self,'_paused_remaining'): del self._paused_remaining
        self.badge.setText(ui_text('LIVE PREVIEW' if preview else MODE_TITLES[game['mode']],self.lang))
        self.title.setText(game['name']); self.feedback.hide()
        self.restart_button.show(); self.restart_button.setText(ui_text('Play again',self.lang))
        self._left = self._right = None
        if game['mode'] in custom_games.BOARD_MODES:
            (self._memory_board if game['mode']=='memory' else self._matching_board)();self._begin_clock()
        else:
            self._question()

    def _begin_clock(self):
        seconds = self.session.game['time_limit']
        self._deadline = time.monotonic()+seconds if seconds else None
        self.clock.setText(ui_text('Untimed', self.lang) if not seconds else str(seconds)+' s')
        if seconds:
            if self.isVisible(): self._timer.start()
            else: self._paused_remaining=seconds

    def _update_progress(self):
        session = self.session
        completed = len(session.matched) if session.game['mode'] in custom_games.BOARD_MODES else session.index+int(session.locked)
        self.counter.setText(ui_text('{done} / {total} · Correct: {score}', self.lang, done=completed, total=len(session.items), score=session.correct))
        self.progress.setValue(round(100*completed/len(session.items)))

    def _question(self):
        self._waiting_audio=False;self._pending_audio=False;audio_player.stop()
        self._timer.stop(); self.feedback.hide(); self.next_button.hide(); self._clear_stage()
        if self.session.complete:
            self._complete(); return
        self._update_progress()
        row = self.session.items[self.session.index]
        mode=self.session.game['mode']
        if mode in custom_games.AUDIO_MODES:
            self.stage_layout.addWidget(label(MODE_DESCRIPTIONS[mode],self.lang,'muted'))
            self.audio_status=label('Preparing audio…',self.lang,'eyebrow');self.stage_layout.addWidget(self.audio_status)
            self.stage_layout.addWidget(button('Skip question',self.lang,lambda:self.answer('',timeout=True),variant='quiet'))
        else:
            self.stage_layout.addWidget(label(row['answer'] if mode=='word_builder' else row['prompt'],self.lang,'heading',translate=False))
        self.answer_buttons = []
        if mode in custom_games.CHOICE_MODES:
            for index, choice in enumerate(self.session.choices()):
                control = button(f'{index+1}. {choice}', self.lang, lambda value=choice:self.answer(value),translate=False)
                control.setMinimumHeight(44); self.answer_buttons.append(control); self.stage_layout.addWidget(control)
            self.answer_buttons[0].setFocus()
        elif mode=='word_builder':
            self._word_tiles(row)
        else:
            self.input_answer = QLineEdit(); self.input_answer.setPlaceholderText(ui_text('Your answer',self.lang))
            self.input_answer.returnPressed.connect(lambda:self.answer(self.input_answer.text()))
            self.stage_layout.addWidget(self.input_answer)
            submit = button('Check answer',self.lang,lambda:self.answer(self.input_answer.text()),variant='primary')
            self.stage_layout.addWidget(submit); self.answer_buttons.append(submit)
            self.input_answer.setFocus()
        self.stage_layout.addStretch()
        self.listen_button.show(); self.hint_button.setVisible(self.session.game['hints'])
        if mode in custom_games.AUDIO_MODES:
            self._audio_seconds=self.session.game['time_limit'];self._deadline=None
            if self.isVisible():self.listen()
            else:self._pending_audio=True
        else:self._begin_clock()

    def answer(self, value, timeout=False):
        if hasattr(self,'_paused_remaining'): del self._paused_remaining
        if not self.session or self.session.complete or self.session.locked:
            return
        if not value.strip() and not timeout:
            return
        correct = self.session.answer(value)
        self._timer.stop()
        for control in self.answer_buttons: control.setEnabled(False)
        self._waiting_audio=False;self._pending_audio=False;audio_player.stop()
        if hasattr(self,'input_answer') and self.session.game['mode'] not in custom_games.CHOICE_MODES:self.input_answer.setEnabled(False)
        expected,_ = custom_games.expected_answer(self.session.game,self.session.items[self.session.index])
        self.feedback.setText(ui_text('Correct!' if correct else 'Correct answer: {answer}',self.lang,answer=expected)); self.feedback.show()
        self.feedback.setStyleSheet('color:#6ee7b7;' if correct else 'color:#fb7185;')
        self.next_button.show(); self.next_button.setFocus()
        self.hint_button.hide(); self._update_progress()
        if self.session.game['sound']: (sfx.play_correct if correct else sfx.play_wrong)()

    def next(self):
        if self.session and self.session.game['mode'] not in custom_games.BOARD_MODES:
            self.session.advance(); self._question()

    def _matching_board(self):
        self._clear_stage(); self.feedback.hide(); self.next_button.hide(); self.hint_button.hide(); self.listen_button.hide()
        self.stage_layout.addWidget(label('Pick a question and its matching answer.',self.lang,'muted'))
        board = QWidget(); grid = QGridLayout(board); grid.setContentsMargins(0,0,0,0); grid.setSpacing(8)
        self.left_buttons, self.right_buttons = {}, {}
        right_order = list(range(len(self.session.items))); self.session.rng.shuffle(right_order)
        for index, row in enumerate(self.session.items):
            left = button(row['prompt'], self.lang, lambda key=index:self.select_pair('left',key),translate=False); left.setCheckable(True); left.setMinimumHeight(44)
            right_id = right_order[index]
            right = button(self.session.items[right_id]['answer'],self.lang,lambda key=right_id:self.select_pair('right',key),translate=False); right.setCheckable(True); right.setMinimumHeight(44)
            grid.addWidget(left,index,0); grid.addWidget(right,index,1)
            self.left_buttons[index]=left; self.right_buttons[right_id]=right
        self.stage_layout.addWidget(board); self.stage_layout.addStretch(); self._update_progress()

    def _memory_board(self):
        self._clear_stage();self.feedback.hide();self.next_button.hide();self.hint_button.hide();self.listen_button.hide()
        self.stage_layout.addWidget(label(MODE_DESCRIPTIONS['memory'],self.lang,'muted'))
        self._memory_faces=[(index,side) for index in range(len(self.session.items)) for side in ('prompt','answer')]
        self.session.rng.shuffle(self._memory_faces)
        self._flipped=[];self._memory_busy=False;self.memory_buttons=[]
        board=QWidget();grid=QGridLayout(board);grid.setContentsMargins(0,0,0,0);grid.setSpacing(8)
        for index in range(len(self._memory_faces)):
            tile=button('',self.lang,lambda key=index:self.flip_memory(key))
            tile.setCheckable(True);tile.setMinimumHeight(80)
            tile_layout=QVBoxLayout(tile);tile_layout.setContentsMargins(6,4,6,4)
            tile.face_label=label('?',self.lang,translate=False)
            tile.face_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tile.face_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            tile_layout.addWidget(tile.face_label)
            tile.setAccessibleName(str(ui_text('Hidden card {number}',self.lang,number=index+1)))
            grid.addWidget(tile,index//4,index%4);self.memory_buttons.append(tile)
        self.stage_layout.addWidget(board);self.stage_layout.addStretch();self._update_progress()

    def flip_memory(self,index):
        if not self.session or self.session.complete or self._memory_busy or self._expired:return
        pair,side=self._memory_faces[index]
        if pair in self.session.matched or index in self._flipped:return
        tile=self.memory_buttons[index]
        text=self.session.items[pair][side]
        tile.face_label.setText(text);tile.setAccessibleName(text);tile.setChecked(True)
        self._flipped.append(index)
        if len(self._flipped)<2:return
        first,second=self._flipped
        left,left_side=self._memory_faces[first];right,right_side=self._memory_faces[second]
        correct=left==right and left_side!=right_side
        if correct:
            self.session.match(left,right)
            for position in self._flipped:self.memory_buttons[position].setEnabled(False)
            self._flipped=[]
            self.feedback.setText(ui_text('Pair matched!',self.lang))
            self._update_progress()
            if self.session.complete:self._complete()
        else:
            self.session.mistakes+=1;self._memory_busy=True
            self.feedback.setText(ui_text('Try another pair.',self.lang));self._memory_timer.start(700)
        self.feedback.setVisible(not self.session.complete)
        if self.session.game['sound']:(sfx.play_correct if correct else sfx.play_wrong)()

    def _reset_memory_pair(self):
        if not self.session or self.session.game['mode']!='memory' or self._expired:return
        for index in self._flipped:
            tile=self.memory_buttons[index];tile.face_label.setText('?');tile.setChecked(False)
            tile.setAccessibleName(str(ui_text('Hidden card {number}',self.lang,number=index+1)))
        self._flipped=[];self._memory_busy=False

    def _word_tiles(self,row):
        self.letters=list(row['prompt']);self.letter_order=[]
        indices=list(range(len(self.letters)));self.session.rng.shuffle(indices)
        self.stage_layout.addWidget(label(MODE_DESCRIPTIONS['word_builder'],self.lang,'muted'))
        self.input_answer=QLineEdit();self.input_answer.setReadOnly(True)
        self.input_answer.setPlaceholderText(ui_text('Arrange the letters below',self.lang));self.stage_layout.addWidget(self.input_answer)
        tray=QWidget();grid=QGridLayout(tray);grid.setContentsMargins(0,0,0,0);grid.setSpacing(6)
        self.letter_buttons={}
        for position,index in enumerate(indices):
            text='␣' if self.letters[index].isspace() else self.letters[index]
            tile=button(text,self.lang,lambda key=index:self.add_letter(key),translate=False)
            tile.setMinimumHeight(34);grid.addWidget(tile,position//6,position%6)
            self.letter_buttons[index]=tile;self.answer_buttons.append(tile)
        self.stage_layout.addWidget(tray)
        controls=QWidget();actions=QHBoxLayout(controls);actions.setContentsMargins(0,0,0,0)
        undo=button('Undo letter',self.lang,self.undo_letter);clear=button('Clear letters',self.lang,self.clear_letters)
        self.word_submit=button('Check answer',self.lang,lambda:self.answer(self.input_answer.text()),variant='primary')
        self.word_submit.setEnabled(False)
        for control in (undo,clear,self.word_submit):actions.addWidget(control);self.answer_buttons.append(control)
        self.stage_layout.addWidget(controls)
        self.input_answer.returnPressed.connect(lambda:len(self.letter_order)==len(self.letters) and self.answer(self.input_answer.text()))

    def add_letter(self,index):
        if self.session.locked or index in self.letter_order:return
        self.letter_order.append(index);self.letter_buttons[index].setEnabled(False);self._update_word()

    def undo_letter(self):
        if not self.session.locked and self.letter_order:
            index=self.letter_order.pop();self.letter_buttons[index].setEnabled(True);self._update_word()

    def clear_letters(self):
        if self.session.locked:return
        for index in self.letter_order:self.letter_buttons[index].setEnabled(True)
        self.letter_order=[];self._update_word()

    def _update_word(self):
        self.input_answer.setText(''.join(self.letters[index] for index in self.letter_order))
        self.word_submit.setEnabled(len(self.letter_order)==len(self.letters))

    def select_pair(self, side, index):
        if not self.session or self.session.complete or index in self.session.matched or getattr(self,'_expired',False): return
        if side=='left':
            if self._left is not None: self.left_buttons[self._left].setChecked(False)
            self._left=index; self.left_buttons[index].setChecked(True)
        else:
            if self._right is not None: self.right_buttons[self._right].setChecked(False)
            self._right=index; self.right_buttons[index].setChecked(True)
        if self._left is None or self._right is None: return
        correct = self.session.match(self._left,self._right)
        if correct:
            self.left_buttons[self._left].setEnabled(False); self.right_buttons[self._right].setEnabled(False)
        self.left_buttons[self._left].setChecked(False); self.right_buttons[self._right].setChecked(False)
        self._left=self._right=None
        self.feedback.setText(ui_text('Pair matched!' if correct else 'Try another pair.',self.lang)); self.feedback.show()
        if self.session.game['sound']: (sfx.play_correct if correct else sfx.play_wrong)()
        self._update_progress()
        if self.session.complete: self._complete()

    def _tick(self):
        if not self._deadline or not self.session or not self.isVisible(): return
        remaining = max(0,self._deadline-time.monotonic()); self.clock.setText(str(int(remaining+.99))+' s')
        if remaining <= 0:
            self._timer.stop()
            if self.session.game['mode'] in custom_games.BOARD_MODES: self._complete(expired=True)
            else: self.answer('',timeout=True)

    def _complete(self, expired=False):
        self._timer.stop();self._memory_timer.stop();self._waiting_audio=False;self._pending_audio=False;audio_player.stop()
        self._expired=expired; self._clear_stage(); self.feedback.hide()
        self.stage_layout.addWidget(label('Time is up.' if expired else 'Game complete!',self.lang,'heading'))
        self.stage_layout.addWidget(label(ui_text('{correct} correct out of {total} · {mistakes} mistakes',self.lang,correct=self.session.correct,total=len(self.session.items),mistakes=self.session.mistakes),self.lang,'muted'))
        if not self.preview and not self._recorded:
            custom_games.record_run(self.session.game['id'],self.session.correct,len(self.session.items),time.monotonic()-self._started-self._paused_total)
            self._recorded=True; self.finished.emit()
        self.stage_layout.addWidget(label('Preview results are not recorded.' if self.preview else 'Your result has been saved.',self.lang,'muted'))
        self.stage_layout.addStretch(); self.progress.setValue(100); self._update_progress()
        for control in (self.listen_button,self.hint_button,self.next_button):control.hide()
        self.restart_button.show()

    def keyPressEvent(self,event):
        if self.session and self.session.game['mode'] not in custom_games.BOARD_MODES:
            if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and self.session.locked:
                self.next();event.accept();return
            if self.session.game['mode'] in custom_games.CHOICE_MODES and not self.session.locked and Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_4:
                index=event.key()-Qt.Key.Key_1
                if index<len(self.answer_buttons):self.answer_buttons[index].click();event.accept();return
        super().keyPressEvent(event)

    def restart(self):
        if self.session:
            self._expired=False; self.start(self.session.game,self.preview)

    def listen(self):
        if self.session and not self.session.complete and self.session.game['mode'] not in custom_games.BOARD_MODES:
            if self.session.game['mode'] in custom_games.AUDIO_MODES and not self.session.locked:
                if self._deadline:self._audio_seconds=max(0,self._deadline-time.monotonic())
                self._deadline=None;self._timer.stop();self._waiting_audio=True;self._heard_audio=False
                self.audio_status.setText(ui_text('Preparing audio…',self.lang))
            self._audio_request=None
            row=self.session.items[self.session.index]
            self._audio_request=audio_player.play_pronunciation(row['prompt'],row.get('language','en'))

    def hint(self):
        if self.session and not self.session.complete:
            answer,_=custom_games.expected_answer(self.session.game,self.session.items[self.session.index]); self.feedback.setText(answer[:1]+' · '+str(len(answer))); self.feedback.show()

    def _audio_state(self,request,state):
        if request!=self._audio_request or not self._waiting_audio or not self.session or not self.isVisible():return
        if state=='loading':self.audio_status.setText(ui_text('Preparing audio…',self.lang))
        elif state=='playing':
            self._heard_audio=True;self.audio_status.setText(ui_text('Listen carefully…',self.lang))
        elif state=='idle' and self._heard_audio:
            self._waiting_audio=False;self.audio_status.setText(ui_text('Your turn.',self.lang))
            self._deadline=time.monotonic()+self._audio_seconds if self._audio_seconds else None
            if self._deadline:self._timer.start()
        elif state in ('error','unavailable'):
            self._waiting_audio=False
            self.audio_status.setText(ui_text('Audio is unavailable. Press Listen to retry or skip this question.',self.lang))

    def hideEvent(self,event):
        if self.session and not self.session.complete and not self._expired and self._paused_at is None:
            self._paused_at=time.monotonic()
        if self._timer.isActive() and self._deadline:
            self._paused_remaining=max(0,self._deadline-time.monotonic())
        if self._waiting_audio:self._waiting_audio=False;self._pending_audio=True
        if self._memory_timer.isActive():self._paused_memory_remaining=self._memory_timer.remainingTime();self._memory_timer.stop()
        self._timer.stop(); audio_player.stop(); super().hideEvent(event)

    def showEvent(self,event):
        super().showEvent(event)
        if self._paused_at is not None:
            self._paused_total+=time.monotonic()-self._paused_at;self._paused_at=None
        if self._memory_busy and hasattr(self,'_paused_memory_remaining'):
            self._memory_timer.start(max(1,self._paused_memory_remaining));del self._paused_memory_remaining
        if self._pending_audio and self.session and not self.session.complete and not self.session.locked:
            self._pending_audio=False;self.listen();return
        if hasattr(self,'_paused_remaining') and self.session and not self.session.complete and not self.session.locked and not getattr(self,'_expired',False):
            self._deadline=time.monotonic()+self._paused_remaining; del self._paused_remaining; self._timer.start()

    def update_language(self,lang):
        self.lang=lang; localize_tree(self,lang)
