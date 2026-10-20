"""No-code game studio: reusable data, configurable rules and a playable canvas."""
import copy
from PyQt6.QtCore import Qt, pyqtSignal, QSignalBlocker
from PyQt6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
    QSplitter, QSpinBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from duocards.ui_localization import QLineEdit, QComboBox, QCheckBox, ui_text, localize_tree
from duocards.widgets.studio_dialogs import STUDIO_STYLES, label, button, IconPicker, ConfirmDialog, apply_studio_style
from duocards.widgets.game_player import GamePlayer, MODE_TITLES, MODE_DESCRIPTIONS
from duocards.styles import transform_preferences
from duocards.icons import get_icon
from duocards import db, custom_games, custom_tables
from duocards.languages import get_languages


class GameStudio(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang; self.document = custom_games.new_game(); self._loading = True; self._dirty = False
        apply_studio_style(self)
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(14)
        toolbar = QHBoxLayout()
        self.saved = QComboBox(); self.saved.setMinimumWidth(130); self.saved.currentIndexChanged.connect(self._selected); toolbar.addWidget(self.saved,1)
        self.new_button=button('New game',lang,self.new,'add'); toolbar.addWidget(self.new_button)
        self.preview_button=button('Preview',lang,self.preview,'gamepad'); toolbar.addWidget(self.preview_button)
        self.publish_button=button('Save to Extensions',lang,self.publish,'check','primary'); toolbar.addWidget(self.publish_button)
        layout.addLayout(toolbar)
        split = QSplitter(Qt.Orientation.Horizontal); split.setChildrenCollapsible(False); layout.addWidget(split,1)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setMinimumWidth(280)
        form_panel = QFrame(); form_panel.setProperty('studioPanel',True)
        form = QVBoxLayout(form_panel); form.setContentsMargins(18,20,18,22); form.setSpacing(12)
        scroll.setWidget(form_panel); split.addWidget(scroll)
        form.addWidget(label('GAME DESIGN',lang,'eyebrow'))
        form.addWidget(label('Small choices. Your own game.',lang,'heading'))
        form.addWidget(label('Everything you create stays in Studycard and uses the same theme.',lang,'muted'))
        self.name=QLineEdit(); self.name.setMaxLength(120); self.name.setPlaceholderText(ui_text('e.g. Vocabulary sprint',lang)); self._field(form,'Game name',self.name)
        self.description=QLineEdit(); self.description.setMaxLength(300); self._field(form,'Description',self.description)
        self.mode=QComboBox()
        for key,title in MODE_TITLES.items():self.mode.addItem(ui_text(title,lang),key)
        self._field(form,'Game style',self.mode)
        self.mode_help=label('',lang,'muted');form.addWidget(self.mode_help)
        self.icons=IconPicker('gamepad',columns=4); self._field(form,'Choose an icon',self.icons)
        form.addWidget(label('CONTENT',lang,'eyebrow'))
        self.source=QComboBox()
        for text,key in [('My own questions','manual'),('Library','library'),('My tables','table')]: self.source.addItem(ui_text(text,lang),key)
        self._field(form,'Content source',self.source)
        self.source_pick=QComboBox(); self.source_label=label('Choose data',lang); form.addWidget(self.source_label); form.addWidget(self.source_pick)
        self.columns_panel=QWidget(); columns=QFormLayout(self.columns_panel); columns.setContentsMargins(0,0,0,0)
        self.prompt_col=QComboBox(); self.answer_col=QComboBox()
        self.answer_column_label=label('Answer column',lang)
        columns.addRow(label('Question column',lang),self.prompt_col); columns.addRow(self.answer_column_label,self.answer_col); form.addWidget(self.columns_panel)
        self.manual_panel=QWidget(); manual=QVBoxLayout(self.manual_panel); manual.setContentsMargins(0,0,0,0); manual.setSpacing(9)
        self.pairs=QTableWidget(6,2); self.pairs.setHorizontalHeaderLabels([str(ui_text('Question',lang)),str(ui_text('Answer',lang))]); self.pairs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.pairs.setMinimumHeight(220); self.pairs.verticalHeader().setDefaultSectionSize(42)
        manual.addWidget(self.pairs)
        actions=QHBoxLayout(); actions.addWidget(button('Add pair',lang,lambda:self.pairs.insertRow(self.pairs.rowCount()),'add')); actions.addWidget(button('Remove pair',lang,self.remove_pair)); manual.addLayout(actions)
        self.language=QComboBox()
        for text,code in get_languages(lang): self.language.addItem(text,code)
        self.language.setCurrentIndex(max(0,self.language.findData('en'))); self._field(manual,'Question language',self.language)
        self.answer_language=QComboBox()
        for text,code in get_languages(lang):self.answer_language.addItem(text,code)
        self.answer_language.setCurrentIndex(max(0,self.answer_language.findData('tr')))
        self.answer_language_label=label('Answer language',lang);manual.addWidget(self.answer_language_label);manual.addWidget(self.answer_language)
        form.addWidget(self.manual_panel)
        form.addWidget(label('RULES',lang,'eyebrow'))
        rules=QFormLayout(); self.count=QSpinBox();self.count.setRange(1,100);self.count.setValue(10)
        self.time_limit=QSpinBox();self.time_limit.setRange(0,300);self.time_limit.setSpecialValueText(ui_text('Untimed',lang));self.time_limit.setSuffix(' s')
        rules.addRow(label('Questions per game',lang),self.count);rules.addRow(label('Time limit',lang),self.time_limit);form.addLayout(rules)
        form.addWidget(label('Time is per question; matching and memory use one timer for the board.',lang,'muted'))
        self.shuffle=QCheckBox(ui_text('Shuffle questions',lang));self.hints=QCheckBox(ui_text('Allow hints',lang));self.sound=QCheckBox(ui_text('Game sound effects',lang))
        for control in (self.shuffle,self.hints,self.sound):control.setChecked(True);form.addWidget(control)
        self.delete_button=button('Delete game',lang,self.delete,variant='danger');form.addWidget(self.delete_button)
        form.addStretch()
        self.player=GamePlayer(lang);self.player.setMinimumWidth(300);split.addWidget(self.player);split.setSizes([350,500])
        self.status=label('Try your game before saving it to Extensions.',lang,'muted');layout.addWidget(self.status)
        for control in (self.name,self.description):control.textChanged.connect(self._changed)
        for control in (self.prompt_col,self.answer_col,self.language,self.answer_language):control.currentIndexChanged.connect(self._changed)
        for control in (self.count,self.time_limit):control.valueChanged.connect(self._changed)
        for control in (self.shuffle,self.hints,self.sound):control.toggled.connect(self._changed)
        self.pairs.itemChanged.connect(self._changed);self.icons.group.buttonClicked.connect(self._changed)
        self.source.currentIndexChanged.connect(self._source_changed)
        self.source_pick.currentIndexChanged.connect(self._columns_changed)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self._loading=False;self.load(custom_games.new_game(),force=True)

    def _field(self,layout,text,control):
        layout.addWidget(label(text,self.lang));layout.addWidget(control)

    def _changed(self,*args):
        if not self._loading:
            self._dirty=True;self.status.setText(ui_text('Draft changed. Preview or save when ready.',self.lang))

    def _source_changed(self):
        current=self.source.currentData()
        self.manual_panel.setVisible(current=='manual');self.columns_panel.setVisible(current!='manual')
        self.source_pick.setVisible(current!='manual');self.source_label.setVisible(current!='manual')
        blocker=QSignalBlocker(self.source_pick);self.source_pick.clear()
        if current=='library':
            self.source_pick.addItem(ui_text('All decks',self.lang),'')
            for deck in db.get_all_decks():self.source_pick.addItem(deck['name'],str(deck['id']))
        elif current=='table':
            for table in custom_tables.list_tables():self.source_pick.addItem(get_icon(table.get('icon','table_grid')),table['name'],table['id'])
        del blocker;self._columns_changed();self._changed()

    def _columns_changed(self):
        blockers=[QSignalBlocker(c) for c in (self.prompt_col,self.answer_col)]
        self.prompt_col.clear();self.answer_col.clear()
        if self.source.currentData()=='library':
            for text,key in [('Word','term'),('Meaning','definition')]:
                self.prompt_col.addItem(ui_text(text,self.lang),key);self.answer_col.addItem(ui_text(text,self.lang),key)
        elif self.source.currentData()=='table':
            table=next((t for t in custom_tables.list_tables() if t['id']==self.source_pick.currentData()),None)
            if table:
                for col in table['columns']:self.prompt_col.addItem(col['name'],col['id']);self.answer_col.addItem(col['name'],col['id'])
        if self.answer_col.count()>1:self.answer_col.setCurrentIndex(self.answer_col.count()-1)
        for blocker in blockers:blocker.unblock()
        self._changed()

    def _mode_changed(self):
        mode=self.mode.currentData()
        self.count.setMaximum(8 if mode in custom_games.BOARD_MODES else 100)
        self.hints.setEnabled(mode not in custom_games.BOARD_MODES)
        self.answer_column_label.setVisible(mode!='audio_dictation');self.answer_col.setVisible(mode!='audio_dictation')
        self.answer_language_label.setVisible(mode!='audio_dictation');self.answer_language.setVisible(mode!='audio_dictation')
        self.mode_help.setText(ui_text(MODE_DESCRIPTIONS[mode],self.lang))
        self.pairs.setHorizontalHeaderLabels([str(ui_text('Question',self.lang)),str(ui_text('Meaning (optional)' if mode=='audio_dictation' else 'Answer',self.lang))])
        self._changed()

    def refresh_saved(self,selected=None):
        selected=selected or self.document['id'];blocker=QSignalBlocker(self.saved);self.saved.clear();self.saved.addItem(ui_text('New game',self.lang),'')
        for game in custom_games.list_games():self.saved.addItem(get_icon(game['icon']),game['name'],game['id'])
        self.saved.setCurrentIndex(max(0,self.saved.findData(selected)));del blocker

    def _selected(self):
        ident=self.saved.currentData()
        game=custom_games.get_game(ident) if ident else custom_games.new_game()
        if game and not self.load(game):self.refresh_saved(self.document['id'])

    def load(self,game,force=False):
        if self._dirty and not force and not ConfirmDialog.ask(self,'Unsaved game','Open another game and discard this draft?','Discard changes'):return False
        self._loading=True;self.document=copy.deepcopy(game)
        self.name.setText(game['name']);self.description.setText(game['description']);self.icons.set_value(game['icon'])
        self.mode.setCurrentIndex(max(0,self.mode.findData(game['mode'])));self.source.setCurrentIndex(max(0,self.source.findData(game['source'])));self._source_changed()
        self._mode_changed()
        if game['source_id']:
            self.source_pick.setCurrentIndex(self.source_pick.findData(game['source_id']))
        self._columns_changed()
        for combo,key in [(self.prompt_col,'prompt_column'),(self.answer_col,'answer_column')]:
            index=combo.findData(game[key]);combo.setCurrentIndex(index if index>=0 else (combo.currentIndex() if not game['source_id'] else -1))
        self.count.setValue(game['question_count']);self.time_limit.setValue(game['time_limit'])
        self.shuffle.setChecked(game['shuffle']);self.hints.setChecked(game['hints']);self.sound.setChecked(game['sound'])
        self.language.setCurrentIndex(max(0,self.language.findData(game['language'])))
        self.answer_language.setCurrentIndex(max(0,self.answer_language.findData(game.get('answer_language','tr'))))
        self.pairs.clearContents();self.pairs.setRowCount(max(6,len(game['manual_pairs'])))
        for index,pair in enumerate(game['manual_pairs']):
            self.pairs.setItem(index,0,QTableWidgetItem(pair['prompt']));self.pairs.setItem(index,1,QTableWidgetItem(pair['answer']))
        self.delete_button.setVisible(custom_games.get_game(game['id']) is not None)
        self._loading=False;self._dirty=False;self.refresh_saved(game['id']);self.player.placeholder()
        self.status.setText(ui_text('Try your game before saving it to Extensions.',self.lang));return True

    def new(self):
        self.load(custom_games.new_game())

    def collect(self,preview=False):
        pairs=[]
        for index in range(self.pairs.rowCount()):
            prompt=self.pairs.item(index,0);answer=self.pairs.item(index,1)
            if prompt and prompt.text().strip() or answer and answer.text().strip():
                if self.mode.currentData()=='audio_dictation' and prompt and prompt.text().strip():
                    pairs.append(dict(prompt=prompt.text().strip(),answer=answer.text().strip() if answer else ''))
                    continue
                if not prompt or not answer or not prompt.text().strip() or not answer.text().strip():
                    if self.source.currentData()=='manual':
                        raise ValueError('Every question needs an answer. Complete or remove the unfinished pair.')
                    continue
                pairs.append(dict(prompt=prompt.text().strip(),answer=answer.text().strip()))
        game=dict(self.document,name=self.name.text().strip() or (str(ui_text('Untitled game',self.lang)) if preview else ''),description=self.description.text().strip(),icon=self.icons.value(),mode=self.mode.currentData(),source=self.source.currentData(),source_id=self.source_pick.currentData() or '',prompt_column=self.prompt_col.currentData() or '',answer_column=self.answer_col.currentData() or '',question_count=self.count.value(),time_limit=self.time_limit.value(),shuffle=self.shuffle.isChecked(),hints=self.hints.isChecked(),sound=self.sound.isChecked(),manual_pairs=pairs,language=self.language.currentData() or 'en')
        game['answer_language']=self.answer_language.currentData() or 'tr'
        custom_games.questions(game);return game

    def preview(self):
        try:
            self.player.start(self.collect(preview=True),preview=True);self.status.setText(ui_text('Playable preview · your results are not recorded.',self.lang))
        except ValueError as exc:self.status.setText(ui_text(str(exc),self.lang))

    def publish(self):
        try:
            game=self.collect();custom_games.save_game(game);self.document=game;self._dirty=False;self.refresh_saved();self.delete_button.show()
            self.status.setText(ui_text('Saved to Extensions. Your game is ready to play.',self.lang));self.data_changed.emit()
        except Exception as exc:self.status.setText(ui_text(str(exc),self.lang))

    def remove_pair(self):
        index=self.pairs.currentRow()
        if index>=0:self.pairs.removeRow(index);self._changed()

    def delete(self):
        if custom_games.get_game(self.document['id']) and ConfirmDialog.ask(self,'Delete game','Delete this game and its play history?'):
            custom_games.delete_game(self.document['id']);self.load(custom_games.new_game(),force=True);self.data_changed.emit()

    def update_language(self,lang):
        self.lang=lang;localize_tree(self,lang);self.player.update_language(lang)
        self.icons.update_language(lang)
        for combo in (self.language,self.answer_language):
            selected=combo.currentData();blocker=QSignalBlocker(combo);combo.clear()
            for name,code in get_languages(lang):combo.addItem(name,code)
            combo.setCurrentIndex(max(0,combo.findData(selected)));del blocker
        self.time_limit.setSpecialValueText(ui_text('Untimed',lang))
        was_loading=self._loading;self._loading=True;self._mode_changed();self._loading=was_loading
        self.refresh_saved()
