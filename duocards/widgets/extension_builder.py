"""Creation hub, table editor, game studio and saved-game player."""
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QScrollArea
from duocards.ui_localization import QLabel, ui_text, localize_tree
from duocards.widgets.studio_dialogs import STUDIO_STYLES, label, button, apply_studio_style
from duocards.widgets.custom_tables_view import CustomTablesView
from duocards.widgets.game_studio import GameStudio
from duocards.widgets.game_player import GamePlayer
from duocards.styles import transform_preferences
from duocards.icons import get_icon
from duocards.settings import settings
from duocards import custom_tables, custom_games


class ExtensionBuilderView(QWidget):
    data_changed = pyqtSignal()
    open_extensions_requested = pyqtSignal()

    def __init__(self,parent=None):
        super().__init__(parent)
        self.lang=settings.get('ui_language','en')
        apply_studio_style(self)
        layout=QVBoxLayout(self);layout.setContentsMargins(24,20,24,20);layout.setSpacing(16)
        navigation=QHBoxLayout()
        self.home_button=button('Create extension',self.lang,self.open_home,'maker')
        self.tables_button=button('Tables',self.lang,self.open_tables,'table_grid')
        self.games_button=button('Game studio',self.lang,self.open_studio,'gamepad')
        for control in (self.home_button,self.tables_button,self.games_button):navigation.addWidget(control)
        navigation.addStretch();navigation.addWidget(button('Extensions',self.lang,self.open_extensions_requested.emit,'extensions'))
        layout.addLayout(navigation)
        self.stack=QStackedWidget();layout.addWidget(self.stack,1)
        home_scroll=QScrollArea();home_scroll.setWidgetResizable(True)
        self.home=QWidget();home_scroll.setWidget(self.home);self.stack.addWidget(home_scroll);self.home_page=home_scroll
        home_layout=QVBoxLayout(self.home);home_layout.setContentsMargins(0,4,0,4);home_layout.setSpacing(18)
        hero=QFrame();hero.setProperty('studioPanel',True);hero_layout=QVBoxLayout(hero);hero_layout.setContentsMargins(28,26,28,26);hero_layout.setSpacing(12)
        hero_top=QHBoxLayout();emblem=QLabel();emblem.setPixmap(get_icon('maker',42).pixmap(42,42));hero_top.addWidget(emblem);hero_top.addWidget(label('YOUR LEARNING WORKSHOP',self.lang,'eyebrow'),1);hero_layout.addLayout(hero_top)
        hero_layout.addWidget(label('Create extension',self.lang,'heading'))
        hero_layout.addWidget(label('Turn your own words into a table or a game. Choose the details; Studycard takes care of the rest.',self.lang,'muted'))
        home_layout.addWidget(hero)
        self.table_card=self._creation_card('table_grid','Build a table','Your rows, your columns, your reading order. Start blank or use a template.','New table',self.create_table)
        self.game_card=self._creation_card('gamepad','Design a game','Choose a game style, connect your content and try it live. Save it straight to Extensions.','Design a game',self.open_studio)
        home_layout.addWidget(self.table_card);home_layout.addWidget(self.game_card)
        collection=QFrame();collection.setProperty('studioPanel',True);collection_layout=QHBoxLayout(collection);collection_layout.setContentsMargins(20,18,20,18)
        self.summary=label('',self.lang,'muted');collection_layout.addWidget(self.summary,1);collection_layout.addWidget(button('Open my extensions',self.lang,self.open_extensions_requested.emit,'extensions'))
        home_layout.addWidget(collection);home_layout.addStretch()
        self.editor=CustomTablesView();self.stack.addWidget(self.editor)
        self.studio=GameStudio(self.lang);self.stack.addWidget(self.studio)
        self.player_page=QWidget();player_layout=QVBoxLayout(self.player_page);player_layout.setContentsMargins(0,0,0,0)
        player_bar=QHBoxLayout();self.play_error=label('',self.lang,'error');player_bar.addWidget(self.play_error,1);self.edit_game_button=button('Edit game',self.lang,self.edit_current_game,'settings');player_bar.addWidget(self.edit_game_button);player_layout.addLayout(player_bar)
        self.player=GamePlayer(self.lang);player_layout.addWidget(self.player,1);self.stack.addWidget(self.player_page)
        self.editor.data_changed.connect(self._changed);self.studio.data_changed.connect(self._changed);self.player.finished.connect(self.data_changed.emit)
        self._current_game=None
        self.open_home()

    @property
    def document(self):
        return self.editor.document

    @property
    def table(self):
        return self.editor.table

    def _creation_card(self,icon,title,description,action,callback):
        card=QFrame();card.setProperty('studioPanel',True);body=QHBoxLayout(card);body.setContentsMargins(24,22,24,22);body.setSpacing(18)
        emblem=QLabel();emblem.setPixmap(get_icon(icon,34).pixmap(34,34));body.addWidget(emblem)
        copy=QVBoxLayout();copy.addWidget(label(title,self.lang,'heading'));copy.addWidget(label(description,self.lang,'muted'));body.addLayout(copy,1)
        cta=button(action,self.lang,callback,icon,'primary');body.addWidget(cta);return card

    def _select(self,page):
        self.stack.setCurrentWidget(page)
        for control,target in [(self.home_button,self.home_page),(self.tables_button,self.editor),(self.games_button,self.studio)]:
            control.setCheckable(True);control.setChecked(page is target)

    def _changed(self):
        self._summary();self.data_changed.emit()

    def _summary(self):
        self.summary.setText(ui_text('{tables} tables · {games} games. Everything you create is in Extensions.',self.lang,tables=len(custom_tables.list_tables()),games=len(custom_games.list_games())))

    def open_home(self):
        self._summary();self._select(self.home_page)

    def create_table(self):
        ident=self.editor.create()
        if ident:self.open_table(ident)

    def open_tables(self):
        self._select(self.editor)

    def open_table(self,ident):
        self.editor.save();self.editor.refresh(ident);self._select(self.editor)

    def open_studio(self):
        self.studio.refresh_saved();self._select(self.studio)

    def open_game_editor(self,ident):
        game=custom_games.get_game(ident)
        if game and self.studio.load(game):self._select(self.studio)

    def open_game(self,ident):
        game=custom_games.get_game(ident)
        if not game:return
        self._current_game=ident;self.play_error.clear();self._select(self.player_page)
        try:self.player.start(game)
        except ValueError as exc:
            self.player.placeholder();self.play_error.setText(ui_text(str(exc),self.lang))

    def edit_current_game(self):
        if self._current_game:self.open_game_editor(self._current_game)

    def save(self):
        self.editor.save()

    def refresh(self,selected=None):
        self.editor.refresh(selected);self.studio.load(custom_games.new_game(),force=True);self.player.placeholder();self._summary()

    def update_language(self,lang):
        self.lang=lang;localize_tree(self,lang);self.editor.update_language(lang);self.studio.update_language(lang);self.player.update_language(lang);self._summary()

    def hideEvent(self,event):
        self.editor.save();super().hideEvent(event)
