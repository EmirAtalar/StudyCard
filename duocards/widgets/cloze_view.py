"""Gerçek hedef kelimeyi silen, şıklı veya yazılı cümle pratiği."""
from duocards.widgets.practice_view import PracticeView


class ClozeView(PracticeView):
    def __init__(self, parent=None):
        super().__init__('cloze', parent)
