"""Preferences with real application behavior, grouped into searchable cards."""
from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox
from duocards.ui_localization import QLineEdit, QComboBox, QCheckBox, ui_text

GROUPS = [
    ('Appearance and profile', 'Make Studycard feel like your own learning space.', 'settings', [
        ('profile_name', 'Display name', 'Shown at the top of the sidebar.', 'text', None),
        ('theme', 'Color theme', 'Choose a comfortable background.', 'choice', [('Slate', 'dark_slate'), ('Midnight blue', 'midnight'), ('Graphite', 'graphite')]),
        ('accent_color', 'Accent color', 'Personalize buttons, highlights and progress.', 'choice', [('Emerald', '#10b981'), ('Blue', '#38bdf8'), ('Violet', '#a78bfa'), ('Amber', '#fbbf24'), ('Coral', '#fb7185')]),
        ('text_scale', 'Text size', 'Increase text size for easier reading.', 'int', (90, 130, 5, '%')),
        ('reduced_motion', 'Reduce animations', 'Flip cards instantly and simplify study transitions.', 'bool', None),
        ('show_phonetics', 'Show pronunciation text', 'Show phonetic spelling on vocabulary cards.', 'bool', None),
        ('show_card_notes', 'Show card notes', 'Display your personal notes when studying.', 'bool', None),
    ]),
    ('Learning preferences', 'Choose the pace and shape of your study sessions.', 'target', [
        ('session_size', 'Cards per session', 'Applies when you start a new study session.', 'int', (5, 200, 5, '')),
        ('shuffle_cards', 'Shuffle study cards', 'Mix the selected cards in each new session.', 'bool', None),
        ('practice_auto_next', 'Advance after correct answers', 'Continue automatically in vocabulary practice.', 'bool', None),
        ('practice_advance_ms', 'Answer feedback duration', 'Time to read feedback before the next question.', 'int', (300, 5000, 100, ' ms')),
        ('practice_autoplay', 'Autoplay in listening and imitation', 'Play the question when it becomes visible.', 'bool', None),
    ]),
    ('Speech preferences', 'Tune pronunciation independently from sound effects.', 'audio', [
        ('speech_speed', 'Speech speed', 'Default speed for vocabulary pronunciation.', 'float', (.5, 2., .1, '×')),
        ('speech_volume', 'Speech volume', 'Volume of spoken words and sentences.', 'int', (0, 100, 5, '%')),
        ('audio_prefetch', 'Prepare upcoming audio', 'Cache upcoming pronunciation in the background.', 'bool', None),
    ]),
    ('Startup and desktop', 'Choose how the app opens and runs.', 'desktop', [
        ('startup_page', 'Opening page', 'Go directly to your preferred screen on launch.', 'choice', [('Study', 'study'), ('Library', 'library'), ('Create extension', 'tables'), ('Statistics', 'stats'), ('Import / export', 'import'), ('Settings', 'settings')]),
        ('run_in_background', 'Keep running when closed', 'Closing the window keeps Studycard in the system tray.', 'bool', None),
    ]),
]


def build_cards(view):
    view.extra_controls = {}
    for title, description, icon, entries in GROUPS:
        card, layout = view._create_card(icon)
        view._add_card_header(layout, icon, ui_text(title, view.lang), ui_text(description, view.lang))
        for index, (key, label, hint, kind, spec) in enumerate(entries):
            if index:
                view._add_separator(layout)
            if kind == 'bool':
                control = QCheckBox()
            elif kind == 'text':
                control = QLineEdit()
                control.setMaxLength(40)
                control.setMinimumWidth(180)
            elif kind == 'choice':
                control = QComboBox()
                for name, value in spec:
                    control.addItem(ui_text(name, view.lang), value)
            else:
                control = QDoubleSpinBox() if kind == 'float' else QSpinBox()
                low, high, step, suffix = spec
                control.setRange(low, high)
                control.setSingleStep(step)
                control.setSuffix(suffix)
            control.setMinimumWidth(120)
            view._add_row(layout, ui_text(label, view.lang), ui_text(hint, view.lang), control)
            view.extra_controls[key] = (control, kind)
        view.content_layout.addWidget(card)


def set_value(control, kind, value):
    if kind == 'bool':
        control.setChecked(bool(value))
    elif kind == 'text':
        control.setText(str(value))
    elif kind == 'choice':
        control.setCurrentIndex(max(0, control.findData(value)))
    else:
        control.setValue(value)


def get_value(control, kind):
    if kind == 'bool':
        return control.isChecked()
    if kind == 'text':
        return control.text().strip()
    if kind == 'choice':
        return control.currentData()
    return control.value()
