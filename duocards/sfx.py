"""Play bundled WAV effects through Qt's native audio backend."""

from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtMultimedia import QSoundEffect

from duocards.settings import settings

SOUNDS_DIR = Path(__file__).resolve().parents[1] / "assets" / "sounds"


class SFXPlayer(QObject):
    _play_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._effects = {}
        self._play_requested.connect(self._play_sound)

    def _play_file(self, filename: str):
        if QCoreApplication.instance() is not None:
            self._play_requested.emit(filename)

    @pyqtSlot(str)
    def _play_sound(self, filename: str):
        if not settings.get("sfx_enabled", True):
            return

        filepath = SOUNDS_DIR / filename
        if not filepath.is_file():
            return

        effect = self._effects.get(filename)
        if effect is None:
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(filepath)))
            effect.setLoopCount(1)
            self._effects[filename] = effect

        volume = max(0, min(100, settings.get("sfx_volume", 80))) / 100.0
        effect.setVolume(volume)
        effect.stop()
        effect.play()

    def play_flip(self):
        self._play_file("flip.wav")

    def play_correct(self):
        self._play_file("correct.wav")

    def play_wrong(self):
        self._play_file("wrong.wav")

    def play_complete(self):
        self._play_file("complete.wav")

    def play_click(self):
        self._play_file("click.wav")

    def play_alert_soft(self):
        self._play_file("alert_soft.wav")


sfx = SFXPlayer()
