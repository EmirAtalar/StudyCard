"""One offline transfer panel shared by settings and import/export."""
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
from duocards.ui_localization import QLabel, QPushButton, ui_text, localize_tree
from duocards import device_backup


class BackupWorker(QThread):
    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, action, path, parent):
        super().__init__(parent)
        self.action, self.path = action, path

    def run(self):
        try:
            self.done.emit(self.action(self.path))
        except Exception as exc:
            self.failed.emit(str(exc))


class DeviceBackupPanel(QFrame):
    restored = pyqtSignal()
    busy_changed = pyqtSignal(bool)

    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        self._worker = None
        self.setProperty('panel', 'card')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        title = QLabel(ui_text('Device backup', lang))
        title.setStyleSheet('font-size:18px; font-weight:700;')
        layout.addWidget(title)
        description = QLabel(ui_text('Save your library, decks, statistics, practice history, sentence memory, custom tables and preferences in one file. Load it on this computer without an account.', lang))
        description.setWordWrap(True)
        layout.addWidget(description)
        buttons = QHBoxLayout()
        self.btn_export = QPushButton(ui_text('Export to device', lang))
        self.btn_import = QPushButton(ui_text('Load device backup', lang))
        self.btn_export.setProperty('class', 'btn-primary')
        self.btn_import.setProperty('class', 'btn-secondary')
        self.btn_export.clicked.connect(self.export)
        self.btn_import.clicked.connect(self.load)
        buttons.addWidget(self.btn_export)
        buttons.addWidget(self.btn_import)
        layout.addLayout(buttons)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, ui_text('Export to device', self.lang), 'studycard-' + datetime.now().strftime('%Y-%m-%d') + '.studycard', 'Studycard (*.studycard)')
        if path:
            self._start(device_backup.export_backup, path, False)

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, ui_text('Load device backup', self.lang), '', 'Studycard (*.studycard)')
        if not path:
            return
        self._start(device_backup.inspect_backup, path, None)

    def _start(self, action, path, restoring):
        if self._worker and self._worker.isRunning():
            return
        self.btn_export.setEnabled(False)
        self.btn_import.setEnabled(False)
        self.status.setText(ui_text('Preparing backup…', self.lang))
        self.busy_changed.emit(True)
        worker = BackupWorker(action, path, self)
        self._worker = worker
        worker.done.connect(lambda result: self._done(result, path, restoring))
        worker.failed.connect(self._error)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _done(self, result, path, restoring):
        self._worker = None
        self.btn_export.setEnabled(True)
        self.btn_import.setEnabled(True)
        self.busy_changed.emit(False)
        if restoring is None:
            counts = result['counts']
            message = ui_text('This backup contains {cards} cards and {decks} decks. Loading replaces your current library and history. A recovery copy of your current data is saved first. Continue?', self.lang, **counts)
            if QMessageBox.question(self, ui_text('Load device backup', self.lang), message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self._start(device_backup.restore_backup, path, True)
            else:
                self.status.clear()
            return
        if restoring:
            self.status.setText(ui_text('Backup loaded. Recovery copy: {path}', self.lang, path=result[1]))
            self.restored.emit()
        else:
            self.status.setText(ui_text('Backup saved: {path}', self.lang, path=path))

    def _error(self, message):
        self._worker = None
        self.btn_export.setEnabled(True)
        self.btn_import.setEnabled(True)
        self.busy_changed.emit(False)
        self.status.setText(ui_text('Backup failed: {error}', self.lang, error=message))

    def update_language(self, lang):
        self.lang = lang
        localize_tree(self, lang)
