"""Editable vocabulary tables with independently configured speech columns."""
import uuid
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog,
    QSpinBox, QDoubleSpinBox, QFormLayout, QMenu)
from duocards.ui_localization import QLabel, QPushButton, QComboBox, QCheckBox, ui_text, localize_tree
from duocards.languages import get_languages
from duocards import custom_tables
from duocards.settings import settings
from duocards.audio import audio_player
from duocards.widgets.practice_styles import PRACTICE_STYLES
from PyQt6.QtGui import QShortcut, QKeySequence
from duocards.icons import get_icon
from duocards.styles import transform_preferences
from duocards.widgets.studio_dialogs import (STUDIO_STYLES, StudioDialog,
    TextDialog, ConfirmDialog, TableDetailsDialog, apply_studio_style)


class TableGrid(QTableWidget):
    """Spreadsheet paste fills a rectangle instead of a single cell."""
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            from PyQt6.QtWidgets import QApplication
            owner = self.parentWidget()
            rows = QApplication.clipboard().text().replace('\r\n', '\n').rstrip('\n').split('\n')
            if not owner.document or len(rows) > 10000:
                return
            start_row, start_col = max(0, self.currentRow()), max(0, self.currentColumn())
            while len(owner.document['rows']) < min(10000, start_row + len(rows)):
                owner.document['rows'].append(dict(id=uuid.uuid4().hex, name=str(len(owner.document['rows'])+1), cells={}, muted=[]))
            for i, line in enumerate(rows):
                if start_row+i >= len(owner.document['rows']):
                    break
                for j, value in enumerate(line.split('\t')):
                    if start_col+j >= len(owner.document['columns']):
                        break
                    owner.document['rows'][start_row+i]['cells'][owner.document['columns'][start_col+j]['id']] = value
            owner.changed(True)
            return
        super().keyPressEvent(event)


class CustomTablesView(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get('ui_language', 'en')
        self.document = None
        self._dirty = False
        self._loading = False
        apply_studio_style(self)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self.save)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        title = QLabel(ui_text('Table editor', self.lang))
        title.setProperty('class', 'page-title')
        layout.addWidget(title)
        hint = QLabel(ui_text('Name your rows and columns. Double-click a heading to rename it. Set column languages and reading order in Speech settings; right-click a cell to mute it.', self.lang))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        bar = QHBoxLayout()
        self.selector = QComboBox()
        self.selector.setMinimumWidth(160)
        self.selector.currentIndexChanged.connect(self._select)
        bar.addWidget(self.selector, 1)
        self._button(bar, 'New table', self.create)
        self._button(bar, 'Duplicate', self.duplicate)
        self._button(bar, 'Delete table', self.delete)
        layout.addLayout(bar)
        tools = QHBoxLayout()
        self._button(tools, 'Table identity', self.rename)
        self._button(tools, 'Add row', self.add_row)
        self._button(tools, 'Add column', self.add_column)
        self._button(tools, 'Remove selected', self.remove_selected)
        self._button(tools, 'Save', self.save)
        layout.addLayout(tools)
        speech = QHBoxLayout()
        self._button(speech, 'Speech settings', self.configure)
        self._button(speech, 'Read table', self.read)
        self._button(speech, 'Read selected row', lambda: self.read(self.table.currentRow()))
        self._button(speech, 'Stop', audio_player.stop)
        layout.addLayout(speech)
        self.table = TableGrid(self)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setDefaultSectionSize(180)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.rename_column)
        self.table.verticalHeader().sectionDoubleClicked.connect(self.rename_row)
        self.table.itemChanged.connect(self._cell_changed)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=self.save)
        layout.addWidget(self.table, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.refresh()

    def _button(self, bar, text, callback):
        btn = QPushButton(ui_text(text, self.lang))
        btn.clicked.connect(lambda checked=False: callback())
        bar.addWidget(btn)
        return btn

    def refresh(self, selected=None):
        tables = custom_tables.list_tables()
        selected = selected or (self.document['id'] if self.document else None)
        self.selector.blockSignals(True)
        self.selector.clear()
        for table in tables:
            self.selector.addItem(get_icon(table.get('icon', 'table_grid')), table['name'], table)
        index = next((i for i, table in enumerate(tables) if table['id'] == selected), 0)
        self.selector.setCurrentIndex(index if tables else -1)
        self.selector.blockSignals(False)
        self.document = self.selector.currentData()
        self._dirty = False
        self._render()

    def _select(self):
        self.save()
        self.document = self.selector.currentData()
        self._dirty = False
        self._render()

    def _render(self):
        self._loading = True
        self.table.clear()
        doc = self.document
        self.table.setRowCount(len(doc['rows']) if doc else 0)
        self.table.setColumnCount(len(doc['columns']) + int(doc['speakers']) if doc else 0)
        if doc:
            self.table.setHorizontalHeaderLabels([c['name'] for c in doc['columns']] + ([str(ui_text('Listen', self.lang))] if doc['speakers'] else []))
            self.table.setVerticalHeaderLabels([r['name'] for r in doc['rows']])
            for i, row in enumerate(doc['rows']):
                for j, col in enumerate(doc['columns']):
                    item = QTableWidgetItem(row['cells'].get(col['id'], ''))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
                    if col['id'] in row['muted']:
                        item.setForeground(Qt.GlobalColor.gray)
                        item.setToolTip(str(ui_text('This cell is muted', self.lang)))
                    self.table.setItem(i, j, item)
                if doc['speakers']:
                    btn = QPushButton('▶')
                    btn.setToolTip(ui_text('Read selected row', self.lang))
                    btn.clicked.connect(lambda checked=False, index=i: self.read(index))
                    self.table.setCellWidget(i, len(doc['columns']), btn)
        self._loading = False
        self.status.setText(ui_text('Changes are saved automatically.', self.lang) if doc else ui_text('Create your first table to begin.', self.lang))

    def _cell_changed(self, item):
        if self._loading or not self.document or item.column() >= len(self.document['columns']):
            return
        row = self.document['rows'][item.row()]
        row['cells'][self.document['columns'][item.column()]['id']] = item.text()
        self.changed()

    def changed(self, render=False):
        self._dirty = True
        self._save_timer.start()
        if render:
            self._render()

    def save(self):
        self._save_timer.stop()
        if not self.document or not self._dirty:
            return
        try:
            custom_tables.save_table(self.document)
            self._dirty = False
            self.status.setText(ui_text('Saved', self.lang))
            self.data_changed.emit()
        except Exception as exc:
            self.status.setText(ui_text('Unable to save the file: {error}', self.lang, error=exc))

    def create(self):
        dialog = TableDetailsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.save()
            doc = custom_tables.new_table(dialog.name.text().strip(), dialog.template.currentData())
            doc.update(dialog.metadata())
            if dialog.template.currentData() == 'blank':
                count = dialog.columns.value()
                doc['columns'] = (doc['columns'] + [dict(id=uuid.uuid4().hex, name=str(ui_text('Column {number}', self.lang, number=i+1)), language='en', speech_order=0) for i in range(2, count)])[:count]
            for col in doc['columns']:
                col['name'] = str(ui_text(col['name'], self.lang))
            doc['rows'] = [dict(id=uuid.uuid4().hex, name=str(i+1), cells={}, muted=[]) for i in range(dialog.rows.value())]
            custom_tables.save_table(doc)
            self.refresh(doc['id'])
            self.data_changed.emit()
            dialog.deleteLater()
            return doc['id']
        dialog.deleteLater()

    def rename(self):
        if self.document:
            dialog = TableDetailsDialog(self, self.document)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.document.update(dialog.metadata())
                self.selector.setItemText(self.selector.currentIndex(), self.document['name'])
                self.selector.setItemIcon(self.selector.currentIndex(), get_icon(self.document['icon']))
                self.changed()
            dialog.deleteLater()

    def duplicate(self):
        if self.document:
            name, ok = TextDialog.get_text(self, 'Duplicate', 'Table name', self.document['name'] + ' (2)')
            if ok:
                self.save()
                copy = custom_tables.duplicate_table(self.document, name)
                self.refresh(copy['id'])
                self.data_changed.emit()

    def delete(self):
        if self.document and ConfirmDialog.ask(self, 'Delete table', 'Delete this table and all its rows?'):
            self._save_timer.stop()
            custom_tables.delete_table(self.document['id'])
            self.document = None
            self.refresh()
            self.data_changed.emit()

    def add_row(self):
        if self.document and len(self.document['rows']) < 10000:
            self.document['rows'].append(dict(id=uuid.uuid4().hex, name=str(len(self.document['rows'])+1), cells={}, muted=[]))
            self.changed(True)

    def add_column(self):
        if self.document and len(self.document['columns']) < 64:
            name, ok = TextDialog.get_text(self, 'Add column', 'Column name')
            if ok and name.strip():
                self.document['columns'].append(dict(id=uuid.uuid4().hex, name=name.strip(), language='en', speech_order=0))
                self.changed(True)

    def rename_column(self, index):
        if self.document and index < len(self.document['columns']):
            col = self.document['columns'][index]
            name, ok = TextDialog.get_text(self, 'Column name', 'Column name', col['name'])
            if ok and name.strip():
                col['name'] = name.strip()
                self.changed(True)

    def rename_row(self, index):
        if self.document:
            row = self.document['rows'][index]
            name, ok = TextDialog.get_text(self, 'Row name', 'Row name', row['name'])
            if ok and name.strip():
                row['name'] = name.strip()
                self.changed(True)

    def remove_selected(self):
        if not self.document:
            return
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if rows and ConfirmDialog.ask(self, 'Remove selected', 'Delete the selected rows?'):
            for index in rows:
                self.document['rows'].pop(index)
            self.changed(True)

    def context_menu(self, position):
        item = self.table.itemAt(position)
        if not item or not self.document:
            return
        row = self.document['rows'][item.row()]
        col = self.document['columns'][item.column()]
        menu = QMenu(self)
        menu.setStyleSheet(transform_preferences(STUDIO_STYLES))
        listen = menu.addAction(ui_text('Listen', self.lang))
        mute = menu.addAction(ui_text('Unmute cell' if col['id'] in row['muted'] else 'Mute cell', self.lang))
        remove = menu.addAction(ui_text('Delete column', self.lang))
        up = menu.addAction(ui_text('Move row up', self.lang))
        down = menu.addAction(ui_text('Move row down', self.lang))
        up.setEnabled(item.row() > 0)
        down.setEnabled(item.row()+1 < len(self.document['rows']))
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == listen:
            audio_player.play_pronunciation(item.text(), col['language'])
        elif action == mute:
            row['muted'].remove(col['id']) if col['id'] in row['muted'] else row['muted'].append(col['id'])
            self.changed(True)
        elif action == remove and len(self.document['columns']) > 1 and ConfirmDialog.ask(self, 'Delete column', 'Delete this column and its cells?'):
            self.document['columns'].remove(col)
            for r in self.document['rows']:
                r['cells'].pop(col['id'], None)
                if col['id'] in r['muted']:
                    r['muted'].remove(col['id'])
            self.changed(True)
        elif action in (up, down):
            old = item.row()
            new = old + (-1 if action == up else 1)
            self.document['rows'][old], self.document['rows'][new] = self.document['rows'][new], self.document['rows'][old]
            self.changed(True)

    def configure(self):
        if not self.document:
            return
        dialog = StudioDialog('Speech settings', 'Set 0 to skip a column. Other numbers define its reading order. Muted cells and empty cells are skipped.', self, 'audio', 700)
        layout = dialog.form
        config = QTableWidget(len(self.document['columns']), 3)
        config.setMinimumHeight(190)
        config.setHorizontalHeaderLabels([str(ui_text(k, self.lang)) for k in ('Column name', 'Language', 'Reading order')])
        config.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        controls = []
        for i, col in enumerate(self.document['columns']):
            item = QTableWidgetItem(col['name'])
            config.setItem(i, 0, item)
            language = QComboBox()
            for name, code in get_languages(self.lang):
                language.addItem(name, code)
            language.setCurrentIndex(max(0, language.findData(col['language'])))
            order = QSpinBox()
            order.setRange(0, 64)
            order.setSpecialValueText(ui_text('Silent', self.lang))
            order.setValue(col['speech_order'])
            config.setCellWidget(i, 1, language)
            config.setCellWidget(i, 2, order)
            controls.append((language, order))
        layout.addWidget(config)
        form = QFormLayout()
        reading = QComboBox()
        for text, key in [('By row', 'rows'), ('By column', 'columns')]:
            reading.addItem(ui_text(text, self.lang), key)
        reading.setCurrentIndex(reading.findData(self.document['reading_order']))
        speed = QDoubleSpinBox(); speed.setRange(.5, 2); speed.setSingleStep(.1); speed.setValue(self.document['speed'])
        pause = QSpinBox(); pause.setRange(0, 5000); pause.setSingleStep(100); pause.setValue(self.document['pause_ms']); pause.setSuffix(' ms')
        repeat = QSpinBox(); repeat.setRange(1, 10); repeat.setValue(self.document['repeat'])
        speakers = QCheckBox(); speakers.setChecked(self.document['speakers'])
        for text, control in [('Reading order', reading), ('Speech speed', speed), ('Pause between cells', pause), ('Repeat count', repeat), ('Show speaker buttons', speakers)]:
            form.addRow(str(ui_text(text, self.lang)), control)
        layout.addLayout(form)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for i, (language, order) in enumerate(controls):
                self.document['columns'][i].update(language=language.currentData(), speech_order=order.value(), name=config.item(i, 0).text().strip() or self.document['columns'][i]['name'])
            self.document.update(reading_order=reading.currentData(), speed=speed.value(), pause_ms=pause.value(), repeat=repeat.value(), speakers=speakers.isChecked())
            self.changed(True)

        dialog.deleteLater()

    def read(self, row=None):
        if self.document and (row is None or row >= 0):
            items = custom_tables.speech_items(self.document, row)
            if items:
                audio_player.play_sequence(items, self.document['speed'], self.document['pause_ms'])
            else:
                self.status.setText(ui_text('No cells are enabled for speech.', self.lang))

    def hideEvent(self, event):
        self.save()
        audio_player.stop()
        super().hideEvent(event)

    def update_language(self, lang):
        self.lang = lang
        localize_tree(self, lang)
        if self.document and self.document['speakers']:
            self.table.horizontalHeaderItem(len(self.document['columns'])).setText(ui_text('Listen', lang))
