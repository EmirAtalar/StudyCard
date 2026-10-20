"""
Study Card - İçe / Dışa Aktar ve Toplu Ekleme Ekranı
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QTextEdit, QFrame,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from duocards.db import (
    export_to_csv, export_to_json, import_from_csv,
    get_all_decks, add_card
)
from duocards.i18n import t
from duocards.settings import settings
from duocards.ui_localization import ui_text, localize_tree, QLabel, QPushButton, QComboBox, QTextEdit
from duocards.card_transfer import import_file, import_cards, FIELDS
from duocards.languages import LANGUAGES_DATA
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QTextEdit, QComboBox

def get_languages(lang):
    return [(row.get(lang,row["en"]),row["code"]) for row in LANGUAGES_DATA]


class ImportExportView(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "tr")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(14)

        self.lbl_title = QLabel(t("import_title", self.lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("import_subtitle", self.lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)
        from duocards.widgets.device_backup_panel import DeviceBackupPanel
        self.backup_panel = DeviceBackupPanel(self.lang)
        layout.addWidget(self.backup_panel)

        languages = QHBoxLayout()
        self.lbl_source = QLabel(ui_text('Word language', self.lang))
        self.lbl_target = QLabel(ui_text('Meaning language', self.lang))
        self.cmb_source = QComboBox(); self.cmb_target = QComboBox()
        for name, code in get_languages(self.lang):
            self.cmb_source.addItem(name, code); self.cmb_target.addItem(name, code)
        self.cmb_source.setCurrentIndex(max(0,self.cmb_source.findData('en')))
        self.cmb_target.setCurrentIndex(max(0,self.cmb_target.findData('tr')))
        for item in (self.lbl_source,self.cmb_source,self.lbl_target,self.cmb_target):
            languages.addWidget(item)
        layout.addLayout(languages)
        self.lbl_fields = QLabel(ui_text('CSV / JSON keeps decks, both languages, usage examples, pronunciation, notes, favorites and review progress. Repeated words are skipped regardless of case.', self.lang))
        self.lbl_fields.setWordWrap(True)
        layout.addWidget(self.lbl_fields)
        self.tabs = QTabWidget()

        # ---------------- TAB 1: TOPLU YAPIŞTIRIP EKLE ----------------
        tab_bulk = QWidget()
        bulk_layout = QVBoxLayout(tab_bulk)
        bulk_layout.setContentsMargins(15, 15, 15, 15)
        bulk_layout.setSpacing(12)

        self.lbl_bulk_info = QLabel(t("bulk_desc", self.lang))
        self.lbl_bulk_info.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        bulk_layout.addWidget(self.lbl_bulk_info)

        deck_select_row = QHBoxLayout()
        self.lbl_bulk_deck_title = QLabel(t("target_deck", self.lang))
        deck_select_row.addWidget(self.lbl_bulk_deck_title)
        self.cmb_bulk_deck = QComboBox()
        self.cmb_bulk_deck.setMinimumWidth(250)
        deck_select_row.addWidget(self.cmb_bulk_deck)
        deck_select_row.addStretch()
        bulk_layout.addLayout(deck_select_row)

        self.txt_bulk_input = QTextEdit()
        self.txt_bulk_input.setPlaceholderText(ui_text('word - meaning\nphrase - meaning', self.lang))
        bulk_layout.addWidget(self.txt_bulk_input)

        self.btn_bulk_add = QPushButton(t("btn_bulk_add", self.lang))
        self.btn_bulk_add.setProperty("class", "btn-primary")
        self.btn_bulk_add.setFixedHeight(42)
        self.btn_bulk_add.clicked.connect(self._process_bulk_add)
        bulk_layout.addWidget(self.btn_bulk_add)

        self.tabs.addTab(tab_bulk, t("tab_bulk", self.lang))

        # ---------------- TAB 2: DOSYADAN AKTARIM ----------------
        tab_files = QWidget()
        file_layout = QVBoxLayout(tab_files)
        file_layout.setContentsMargins(15, 15, 15, 15)
        file_layout.setSpacing(16)

        # Dışa Aktarma Bölümü
        exp_frame = QFrame()
        exp_frame.setStyleSheet("background-color: #111827; border: none; border-radius: 14px; padding: 18px;")
        exp_layout = QVBoxLayout(exp_frame)
        exp_layout.setSpacing(10)

        self.lbl_exp = QLabel(t("btn_export_csv", self.lang))
        self.lbl_exp.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc; background: transparent;")
        exp_layout.addWidget(self.lbl_exp)

        exp_btns = QHBoxLayout()
        self.btn_exp_csv = QPushButton(t("btn_export_csv", self.lang))
        self.btn_exp_csv.setProperty("class", "btn-secondary")
        self.btn_exp_csv.clicked.connect(self._export_csv)

        self.btn_exp_json = QPushButton(t("btn_export_json", self.lang))
        self.btn_exp_json.setProperty("class", "btn-secondary")
        self.btn_exp_json.clicked.connect(self._export_json)

        exp_btns.addWidget(self.btn_exp_csv)
        exp_btns.addWidget(self.btn_exp_json)
        exp_layout.addLayout(exp_btns)

        file_layout.addWidget(exp_frame)

        # İçe Aktarma Bölümü
        imp_frame = QFrame()
        imp_frame.setStyleSheet("background-color: #111827; border: none; border-radius: 14px; padding: 18px;")
        imp_layout = QVBoxLayout(imp_frame)
        imp_layout.setSpacing(10)

        self.lbl_imp = QLabel(t("btn_import_csv", self.lang))
        self.lbl_imp.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc; background: transparent;")
        imp_layout.addWidget(self.lbl_imp)

        imp_deck_row = QHBoxLayout()
        self.lbl_imp_deck_title = QLabel(t("target_deck", self.lang))
        imp_deck_row.addWidget(self.lbl_imp_deck_title)
        self.cmb_imp_deck = QComboBox()
        self.cmb_imp_deck.setMinimumWidth(220)
        imp_deck_row.addWidget(self.cmb_imp_deck)
        imp_deck_row.addStretch()
        imp_layout.addLayout(imp_deck_row)

        self.btn_imp_csv = QPushButton(t("btn_import_csv", self.lang))
        self.btn_imp_csv.setProperty("class", "btn-primary")
        self.btn_imp_csv.clicked.connect(self._import_csv)
        imp_layout.addWidget(self.btn_imp_csv)
        self.btn_imp_json = QPushButton(ui_text('Import JSON backup', self.lang))
        self.btn_imp_json.clicked.connect(lambda:self._import_csv('json'))
        imp_layout.addWidget(self.btn_imp_json)

        file_layout.addWidget(imp_frame)
        file_layout.addStretch()

        self.tabs.addTab(tab_files, t("tab_files", self.lang))

        layout.addWidget(self.tabs)

    def update_language(self, lang: str):
        self.lang = lang
        self.backup_panel.update_language(lang)
        self.lbl_title.setText(t("import_title", lang))
        self.lbl_subtitle.setText(t("import_subtitle", lang))
        self.tabs.setTabText(0, t("tab_bulk", lang))
        self.tabs.setTabText(1, t("tab_files", lang))
        self.lbl_bulk_info.setText(t("bulk_desc", lang))
        self.lbl_bulk_deck_title.setText(t("target_deck", lang))
        self.btn_bulk_add.setText(t("btn_bulk_add", lang))
        self.lbl_exp.setText(t("btn_export_csv", lang))
        self.btn_exp_csv.setText(t("btn_export_csv", lang))
        self.btn_exp_json.setText(t("btn_export_json", lang))
        self.lbl_imp.setText(t("btn_import_csv", lang))
        self.lbl_imp_deck_title.setText(t("target_deck", lang))
        self.btn_imp_csv.setText(t("btn_import_csv", lang))
        for combo in (self.cmb_source,self.cmb_target):
            selected=combo.currentData()
            combo.clear()
            for name,code in get_languages(lang): combo.addItem(name,code)
            combo.setCurrentIndex(max(0,combo.findData(selected)))
        localize_tree(self,lang)

    def refresh_decks(self):
        decks = get_all_decks()
        for cmb in [self.cmb_bulk_deck, self.cmb_imp_deck]:
            cmb.clear()
            for d in decks:
                cmb.addItem(d['name'], d["id"])

    def _message(self, title, message, **values):
        QMessageBox.information(self, ui_text(title,self.lang),ui_text(message,self.lang,**values))

    def _process_bulk_add(self):
        deck_id=self.cmb_bulk_deck.currentData()
        if not deck_id:
            self._message('Error','Please select a deck.')
            return
        rows=[]; invalid=[]
        for line in self.txt_bulk_input.toPlainText().splitlines():
            if not line.strip(): continue
            delimiter=next((d for d in ('\t',' - ',';',' : ','-') if d in line),None)
            parts=line.split(delimiter,1) if delimiter else []
            if len(parts)==2 and all(part.strip() for part in parts):
                rows.append({'term':parts[0],'definition':parts[1]})
            else: invalid.append(line)
        report=import_cards(rows,deck_id,self.cmb_source.currentData(),self.cmb_target.currentData())
        report['invalid']+=len(invalid)
        self.txt_bulk_input.setPlainText('\n'.join(invalid))
        self._report(report)

    def _report(self, report):
        self._message('Import complete','Added: {added} · Already exists: {skipped} · Invalid: {invalid}',**report)
        self.data_changed.emit()

    def _export_csv(self): self._export('csv')
    def _export_json(self): self._export('json')
    def _export(self, format):
        path,_=QFileDialog.getSaveFileName(self,ui_text('Save card backup',self.lang),f'studycard.{format}',f'{format.upper()} (*.{format})')
        if path:
            try:
                (export_to_csv if format=='csv' else export_to_json)(path)
                self._message('Saved','Cards saved to {path}',path=path)
            except (OSError,ValueError) as exc:
                self._message('Error','Unable to save the file: {error}',error=exc)

    def _import_csv(self, format='csv'):
        # QPushButton.clicked supplies a boolean.
        format='json' if format=='json' else 'csv'
        deck_id=self.cmb_imp_deck.currentData()
        if not deck_id:
            self._message('Error','Please select a deck.')
            return
        path,_=QFileDialog.getOpenFileName(self,ui_text('Select card backup',self.lang),'',f'{format.upper()} (*.{format})')
        if path:
            try:
                self._report(import_file(path,deck_id,self.cmb_source.currentData(),self.cmb_target.currentData()))
            except (OSError,ValueError) as exc:
                self._message('Error','Unable to read the file: {error}',error=ui_text(str(exc),self.lang))
