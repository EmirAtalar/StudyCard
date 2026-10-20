"""Kelime, anlam ve cümle diktesi; yalnız seçili kullanıcı kartlarını kullanır."""
from duocards.widgets.practice_view import PracticeView


class DictationView(PracticeView):
    def __init__(self, parent=None):
        super().__init__('dictation', parent)
