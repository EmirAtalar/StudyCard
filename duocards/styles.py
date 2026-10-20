"""
Study Card - QSS Stylesheet & Visual Theme
Modern, minimalist, soft 3D dokulu butonlar ve pürüzsüz geçişler.
"""

MAIN_STYLESHEET = """
/* Pencere Kök Çerçevesi */
#windowRoot {
    background-color: #0c121e;
    border: 1.5px solid #243550;
    border-radius: 14px;
}

#windowRootMaximized {
    background-color: #0c121e;
    border: none;
    border-radius: 0px;
}

/* Özel Başlık Çubuğu */
#customTitleBar {
    background-color: #111827;
    border-bottom: 1px solid #1f2937;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

/* Ana Taşıyıcı ve Zeminler */
QMainWindow, #centralWidget, QDialog {
    background-color: #0c121e;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Ubuntu', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Tüm Etiketler Şeffaf */
QLabel {
    background-color: transparent;
    color: #f1f5f9;
}

QFrame {
    background-color: transparent;
}

/* Yan Menü (Sidebar) */
#sidebar {
    background-color: #111827;
    border-right: 1px solid #1f2937;
    border-bottom-left-radius: 14px;
    min-width: 220px;
    max-width: 240px;
}

#sidebarHeader {
    padding: 16px 14px;
    border-bottom: 1px solid #1f2937;
    background-color: transparent;
}

#appLogoTitle {
    font-size: 20px;
    font-weight: 900;
    color: #10b981;
    letter-spacing: -0.5px;
    background: transparent;
}

#appSubtitle {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
    background: transparent;
}

/* Menü Butonları */
QPushButton.nav-btn {
    text-align: left;
    padding: 8px 14px;
    margin: 1px 8px;
    border-radius: 10px;
    border: none;
    background-color: transparent;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 700;
}

QPushButton.nav-btn:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QPushButton.nav-btn:checked {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 800;
}

/* Başlıklar */
QLabel.page-title {
    font-size: 22px;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 2px;
    background: transparent;
}

QLabel.page-subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 12px;
    background: transparent;
}

/* Kart Panelleri - Sınır Çizgisiz Soft Minimalist Zemin */
.card-panel {
    background-color: #162032;
    border: none;
    border-radius: 16px;
    padding: 22px;
}

/* Flashcard Büyük Çalışma Kartı */
#studyFlashcard {
    background-color: #162032;
    border: none;
    border-radius: 24px;
    padding: 24px;
}

#studyFlashcard:hover {
    background-color: #19263a;
}

/* Giriş Kutuları (Inputs) */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #111827;
    border: 1.5px solid #283548;
    border-radius: 10px;
    padding: 10px 14px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #10b981;
    background-color: #131d2e;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #64748b;
}

/* Modern Soft ComboBox */
QComboBox {
    background-color: #162032;
    border: 1.5px solid #283548;
    border-radius: 10px;
    padding: 8px 14px;
    color: #f8fafc;
    font-size: 13px;
    font-weight: 600;
    min-height: 24px;
}

QComboBox:hover {
    border-color: #3b82f6;
    background-color: #1b263b;
}

QComboBox:focus {
    border-color: #10b981;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #162032;
    border: 1px solid #283548;
    selection-background-color: #10b981;
    color: #f8fafc;
    border-radius: 8px;
    padding: 6px;
}

/* Modern 3D Basılabilir Butonlar */
QPushButton.btn-primary {
    background-color: #10b981;
    color: #ffffff;
    border: none;
    border-bottom: 4px solid #047857;
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 800;
}

QPushButton.btn-primary:hover {
    background-color: #34d399;
}

QPushButton.btn-primary:pressed {
    border-bottom: 1px solid #047857;
    margin-top: 3px;
}

QPushButton.btn-secondary {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-bottom: 3px solid #0f172a;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton.btn-secondary:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton.btn-secondary:pressed {
    border-bottom: 1px solid #0f172a;
    margin-top: 2px;
}

/* 3D Çalışma Butonları (Rating) */
QPushButton#btnFlip {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-bottom: 4px solid #4338ca;
    border-radius: 12px;
    padding: 12px 28px;
    font-size: 15px;
    font-weight: 800;
    min-width: 240px;
}

QPushButton#btnFlip:hover {
    background-color: #818cf8;
}

QPushButton#btnFlip:pressed {
    border-bottom: 1px solid #4338ca;
    margin-top: 3px;
}

QPushButton#btnRepeat {
    background-color: #ef4444;
    color: #ffffff;
    border: none;
    border-bottom: 4px solid #b91c1c;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 800;
    min-width: 130px;
}

QPushButton#btnRepeat:hover {
    background-color: #f87171;
}

QPushButton#btnRepeat:pressed {
    border-bottom: 1px solid #b91c1c;
    margin-top: 3px;
}

QPushButton#btnHard {
    background-color: #f59e0b;
    color: #ffffff;
    border: none;
    border-bottom: 4px solid #b45309;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 800;
    min-width: 120px;
}

QPushButton#btnHard:hover {
    background-color: #fbbf24;
}

QPushButton#btnHard:pressed {
    border-bottom: 1px solid #b45309;
    margin-top: 3px;
}

QPushButton#btnEasy {
    background-color: #10b981;
    color: #ffffff;
    border: none;
    border-bottom: 4px solid #047857;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 800;
    min-width: 140px;
}

QPushButton#btnEasy:hover {
    background-color: #34d399;
}

QPushButton#btnEasy:pressed {
    border-bottom: 1px solid #047857;
    margin-top: 3px;
}

/* Seçenek Hap Butonları (Pill Chips) */
QPushButton.pill-chip {
    background-color: #162032;
    color: #94a3b8;
    border: 1.5px solid #243550;
    border-radius: 10px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
}

QPushButton.pill-chip:hover {
    background-color: #1e293b;
    color: #f1f5f9;
    border-color: #3b82f6;
}

QPushButton.pill-chip:checked {
    background-color: #10b981;
    color: #ffffff;
    border-color: #34d399;
    font-weight: 800;
}

/* Tablo */
QTableWidget {
    background-color: #111827;
    border: 1px solid #243550;
    border-radius: 12px;
    gridline-color: #1e293b;
    selection-background-color: #1e293b;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 2px 8px;
    border-bottom: 1px solid #1e293b;
    background-color: transparent;
}

QHeaderView::section {
    background-color: #162032;
    color: #94a3b8;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #283548;
    font-weight: 800;
    text-align: left;
}

/* İlerleme Çubuğu - Sınır Çizgisiz Soft */
QProgressBar {
    background-color: #111827;
    border: none;
    border-radius: 8px;
    height: 10px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
    border-radius: 7px;
}

/* Sekmeler (QTabWidget & QTabBar) - Asla kahverengi olmaz, temiz koyu slate */
QTabWidget {
    background: transparent;
    border: none;
}

QTabWidget::pane {
    background-color: #162032;
    border: none;
    border-radius: 16px;
    padding: 16px;
}

QTabBar::tab {
    background-color: #111827;
    color: #94a3b8;
    padding: 10px 22px;
    margin-right: 8px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 700;
    font-size: 13px;
    border: none;
}

QTabBar::tab:hover {
    color: #f1f5f9;
    background-color: #192538;
}

QTabBar::tab:selected {
    background-color: #162032;
    color: #10b981;
}

/* QCheckBox */
QCheckBox {
    color: #f1f5f9;
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #334155;
    background-color: #111827;
}

QCheckBox::indicator:checked {
    background-color: #10b981;
    border-color: #34d399;
}

/* QTimeEdit */
QTimeEdit {
    background-color: #111827;
    border: 1.5px solid #334155;
    border-radius: 10px;
    padding: 6px 12px;
    color: #f8fafc;
    font-size: 13px;
    font-weight: 700;
}

QTimeEdit:focus {
    border-color: #06b6d4;
    background-color: #162032;
}

QTimeEdit::up-button, QTimeEdit::down-button {
    background-color: #1e293b;
    border-radius: 4px;
    margin: 1px;
    width: 16px;
}

QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
    background-color: #334155;
}

/* QSlider */
QSlider::groove:horizontal {
    border: none;
    height: 8px;
    background: #1e293b;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa);
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #60a5fa;
    border: 2px solid #ffffff;
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #93c5fd;
    border-color: #60a5fa;
}

/* AI Chat Baloncukları */
#aiBubbleBox {
    background-color: #1e293b;
    border: none;
    border-radius: 14px;
}

/* Özel İnce Zümrüt Yeşili Kaydırma Çubuğu (Custom Thin Emerald Green Scrollbar) */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 2px 0 2px 0;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background-color: #10b981;
    min-height: 28px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: #34d399;
}

QScrollBar::handle:vertical:pressed {
    background-color: #059669;
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 0px;
    width: 0px;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background: none;
    width: 0px;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0 2px 0 2px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background-color: #10b981;
    min-width: 28px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #34d399;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #059669;
}

QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
    border: none;
    background: none;
    width: 0px;
    height: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""

def transform_preferences(style):
    import re
    from duocards.settings import settings
    accent = settings.get('accent_color', '#10b981')
    accents = {} if accent == '#10b981' else {'#10b981': accent, '#059669': accent, '#34d399': accent, '#6ee7b7': accent}
    backgrounds = {
        'midnight': {'#0c121e': '#080f24', '#0d121c': '#080f24', '#121824': '#101a32', '#111827': '#111c36', '#0f172a': '#0a1530', '#1e293b': '#233455'},
        'graphite': {'#0c121e': '#141416', '#0d121c': '#141416', '#121824': '#1c1c20', '#111827': '#202024', '#0f172a': '#17171c', '#1e293b': '#33333b'},
    }.get(settings.get('theme'), {})
    for old, new in {**accents, **backgrounds}.items():
        style = style.replace(old, new)
    scale = settings.get('text_scale', 100) / 100
    if scale != 1:
        style = re.sub(r'(font-size:\s*)(\d+(?:\.\d+)?)(px|pt)', lambda m: m[1]+str(round(float(m[2])*scale, 1))+m[3], style)
    return style


def preference_stylesheet():
    return transform_preferences(MAIN_STYLESHEET)

