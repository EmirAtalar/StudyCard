"""Pratik ekranları için uygulamanın koyu temasına uygun ortak görünüm."""
PRACTICE_STYLES = '''
QWidget#practicePage, QWidget#practiceContent, QWidget#sentenceMemoryPage, QWidget#practiceViewport {
    background: #0c121e;
    color: #e2e8f0;
}
QWidget { background: transparent; border: none; }
QLabel { color: #ffffff; background: transparent; border: none; }
QLabel[class="page-title"] { color: #f8fafc; font-size: 24px; font-weight: 800; }
QPushButton {
    background: #10b981; color: #ffffff; border: none;
    border-radius: 9px; padding: 0 14px; min-height: 36px; font-weight: 600;
}
QPushButton:hover { background: #059669; border: none; }
QPushButton:disabled { background: #147d62; color: #ffffff; border: none; }
QPushButton[class="btn-primary"] { background: #10b981; color: #ffffff; border: none; }
QPushButton[class="btn-primary"]:hover { background: #059669; }
QPushButton[class="btn-primary"]:disabled { background: #145343; color: #ffffff; }
QLineEdit, QComboBox {
    background: #162032; color: #ffffff; border: 1px solid #243550;
    border-radius: 9px; min-height: 36px; padding: 0 12px;
}
QLineEdit:focus, QComboBox:focus { border-color: #10b981; }
QLineEdit:disabled { color: #ffffff; }
QComboBox QAbstractItemView { background: #111827; color: #e2e8f0; selection-background-color: #243550; }
QCheckBox { color: #ffffff; spacing: 7px; background: transparent; }
QProgressBar { background: #1e293b; border: none; border-radius: 4px; }
QProgressBar::chunk { background: #10b981; border-radius: 4px; }
QScrollArea { border: none; background: #0c121e; }
QListWidget {
    background: #111827; color: #e2e8f0; border: 1px solid #1e293b;
    border-radius: 10px; padding: 6px; outline: none;
}
QListWidget::item { padding: 12px 8px; border-radius: 6px; }
QListWidget::item:selected { background: #243550; color: #ffffff; }
QListWidget::item:hover { background: #1e293b; }
QTableWidget {
    background: #111827; alternate-background-color: #162032; color: #e2e8f0;
    gridline-color: transparent; border: none; border-radius: 10px;
    selection-background-color: #243550; selection-color: #e2e8f0;
}
QTableWidget::item { padding: 8px; color: #e2e8f0; }
QHeaderView::section {
    background: #1e293b; color: #ffffff; border: none; padding: 10px 6px; font-weight: 600;
}
QTableCornerButton::section { background: #1e293b; border: none; }
QSplitter::handle { background: transparent; width: 6px; }
'''

PRACTICE_STYLES += """
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #10b981; min-height: 30px; border-radius: 4px; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: #10b981; min-width: 30px; border-radius: 4px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; background: transparent; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""
