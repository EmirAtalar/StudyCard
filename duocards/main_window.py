"""
Study Card - Ana Uygulama Penceresi
Özel çerçeve, 3D animasyonlar, oyunlaştırma ses efektleri, çoklu dil desteği ve ayarlar.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QButtonGroup, QFrame, QApplication,
    QSystemTrayIcon, QMenu, QScrollArea, QScrollBar
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QTimer, QEvent
from PyQt6.QtGui import QCursor, QIcon

from duocards.db import init_db, get_stats
from duocards.styles import MAIN_STYLESHEET
from duocards.icons import get_icon
from duocards.widgets.title_bar import CustomTitleBar
from duocards.widgets.study_view import StudyView
from duocards.widgets.add_card_view import AddCardView
from duocards.widgets.library_view import LibraryView
from duocards.widgets.decks_view import DecksView
from duocards.widgets.stats_view import StatsView
from duocards.widgets.import_export_view import ImportExportView
from duocards.widgets.settings_view import SettingsView
from duocards.widgets.verbs_view import IrregularVerbsView
from duocards.widgets.timer_view import TimerView
from duocards.widgets.extensions_view import ExtensionsView, AVAILABLE_EXTENSIONS
from duocards.widgets.universal_module_view import UniversalLanguageModuleView
from duocards.widgets.match_game_view import MatchGameView
from duocards.widgets.dictation_view import DictationView
from duocards.widgets.cloze_view import ClozeView
from duocards.widgets.practice_view import PracticeView
from duocards.widgets.sentence_memory_view import SentenceMemoryView
from duocards.practice_menus import NEW_CORE_MENUS
from duocards.hotkey import global_hotkey, toggle_app_window, sync_system_shortcut
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.i18n import t
from duocards.widgets.steam_popup import show_steam_notification
from duocards.widgets.desktop_widget import DesktopMiniWidget
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 7

    def __init__(self):
        super().__init__()
        self._manual_resize = None
        self.setWindowTitle(ui_text('Study Card — Flashcards and vocabulary'))
        self.resize(1180, 760)
        self.setMinimumSize(900, 580)

        # Çerçevesiz pencere ve şeffaf zemin (köşe yuvarlatma ve özel çerçeve için)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._desktop_widget = None
        self.current_lang = settings.get("ui_language", "en")

        # Veritabanını hazırla
        init_db()

        # Tasarım temasını uygula
        self.setStyleSheet(MAIN_STYLESHEET)

        self._setup_ui()
        self._connect_signals()

        # Dil metinlerini ayarla
        self._apply_language(self.current_lang)

        # Aktif eklenti menü butonlarını göster/gizle
        self._update_extension_nav_buttons()

        # İlk veri yüklemesi
        self._on_data_updated()

        # İlk açılışta Çalış ekranını yükle
        self.nav_study.setChecked(True)
        self.switch_to_study(play_sound=False, allow_autoplay=False)
        opening = {'library': self.view_library, 'tables': self.view_tables, 'stats': self.view_stats, 'import': self.view_import, 'settings': self.view_settings}.get(settings.get('startup_page'))
        if opening is not None:
            self.content_stack.setCurrentWidget(opening)
            {'library': self.nav_library, 'tables': self.nav_tables, 'stats': self.nav_stats, 'import': self.nav_import, 'settings': self.nav_settings}[settings.get('startup_page')].setChecked(True)
            if opening is self.view_library:
                self.view_library.reload_cards()

        # Günlük bildirim arka plan kontrol zamanlayıcısı (Her 30 saniyede bir)
        self._last_notified_date = None
        self._notif_timer = QTimer(self)
        self._notif_timer.timeout.connect(self._check_daily_notification)
        self._notif_timer.start(30000)

        # Uygulama başlatma / öne getirme kısayolu
        self._app_shortcut_obj = None
        self._setup_app_shortcut()
        self._apply_preferences()

        # Sistem tepsisi (System Tray Icon) ve Arka Plan Çalışması
        self.tray_icon = None
        self._is_force_quitting = False
        self._setup_tray_icon()

    def _setup_ui(self):
        self.central_container = QWidget(self)
        self.central_container.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.central_container.installEventFilter(self)
        self.setCentralWidget(self.central_container)
        outer_layout = QVBoxLayout(self.central_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Uygulamanın özel kenarlıklı çerçevesi
        self.root_frame = QFrame()
        self.root_frame.setObjectName("windowRoot")
        self.root_frame.setMouseTracking(True)
        root_layout = QVBoxLayout(self.root_frame)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Özel Başlık Çubuğu
        self.title_bar = CustomTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # 2. Çalışma Alanı (Sidebar + Content Stack)
        workspace = QWidget()
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # ---------------- YAN MENÜ (SIDEBAR) ----------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 8)
        sidebar_layout.setSpacing(2)

        # Logo & Başlık Alanı
        header_widget = QWidget()
        header_widget.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(2)

        self.lbl_logo = QLabel(ui_text('Study Card', self.current_lang))
        self.lbl_logo.setObjectName("appLogoTitle")
        self.lbl_sub = QLabel(ui_text('Flashcards & Vocabulary', self.current_lang))
        self.lbl_sub.setObjectName("appSubtitle")

        header_layout.addWidget(self.lbl_logo)
        header_layout.addWidget(self.lbl_sub)
        sidebar_layout.addWidget(header_widget)

        # Menü Butonları (Tek renk yeşil minimalist ikonlar, taşmada sola yeşil çubuklu kaydırma alanı)
        nav_scroll_container = QWidget()
        nav_scroll_container.setStyleSheet("background: transparent; border: none;")
        nav_container_layout = QHBoxLayout(nav_scroll_container)
        nav_container_layout.setContentsMargins(0, 0, 0, 0)
        nav_container_layout.setSpacing(2)

        # Sola yeşil çubuk (QScrollBar)
        self.sidebar_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.sidebar_scrollbar.setFixedWidth(5)
        self.sidebar_scrollbar.setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
                margin: 0px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #10b981;
                min-height: 24px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #059669;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        self.sidebar_scrollbar.setVisible(False)
        nav_container_layout.addWidget(self.sidebar_scrollbar)

        # QScrollArea (İç scrollbar gizli, soldaki yeşil çubuk ile senkronize)
        self.sidebar_scroll_area = QScrollArea()
        self.sidebar_scroll_area.setWidgetResizable(True)
        self.sidebar_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll_area.setStyleSheet("background: transparent; border: none;")

        nav_content = QWidget()
        nav_content.setStyleSheet("background: transparent; border: none;")
        nav_inner_layout = QVBoxLayout(nav_content)
        nav_inner_layout.setContentsMargins(0, 0, 0, 0)
        nav_inner_layout.setSpacing(6)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        icon_size = QSize(20, 20)

        self.nav_study = QPushButton(f"  {t('nav_study', self.current_lang)}")
        self.nav_study.setIcon(get_icon("study", 20))
        self.nav_study.setIconSize(icon_size)
        self.nav_study.setProperty("class", "nav-btn")
        self.nav_study.setCheckable(True)
        self.nav_group.addButton(self.nav_study)
        nav_inner_layout.addWidget(self.nav_study)

        self.nav_add = QPushButton(f"  {t('nav_add', self.current_lang)}")
        self.nav_add.setIcon(get_icon("add", 20))
        self.nav_add.setIconSize(icon_size)
        self.nav_add.setProperty("class", "nav-btn")
        self.nav_add.setCheckable(True)
        self.nav_group.addButton(self.nav_add)
        nav_inner_layout.addWidget(self.nav_add)

        self.nav_library = QPushButton(f"  {t('nav_library', self.current_lang)}")
        self.nav_library.setIcon(get_icon("library", 20))
        self.nav_library.setIconSize(icon_size)
        self.nav_library.setProperty("class", "nav-btn")
        self.nav_library.setCheckable(True)
        self.nav_group.addButton(self.nav_library)
        nav_inner_layout.addWidget(self.nav_library)

        self.nav_decks = QPushButton(f"  {t('nav_decks', self.current_lang)}")
        self.nav_decks.setIcon(get_icon("decks", 20))
        self.nav_decks.setIconSize(icon_size)
        self.nav_decks.setProperty("class", "nav-btn")
        self.nav_decks.setCheckable(True)
        self.nav_group.addButton(self.nav_decks)
        nav_inner_layout.addWidget(self.nav_decks)

        self.nav_tables = QPushButton(ui_text('Create extension', self.current_lang))
        self.nav_tables.setIcon(get_icon('maker', 20))
        self.nav_tables.setIconSize(icon_size)
        self.nav_tables.setProperty('class', 'nav-btn')
        self.nav_tables.setCheckable(True)
        self.nav_group.addButton(self.nav_tables)
        nav_inner_layout.addWidget(self.nav_tables)

        self.nav_timer = QPushButton(f"  {t('nav_timer', self.current_lang)}")
        self.nav_timer.setIcon(get_icon("timer", 20))
        self.nav_timer.setIconSize(icon_size)
        self.nav_timer.setProperty("class", "nav-btn")
        self.nav_timer.setCheckable(True)
        self.nav_group.addButton(self.nav_timer)
        nav_inner_layout.addWidget(self.nav_timer)

        self.nav_stats = QPushButton(f"  {t('nav_stats', self.current_lang)}")
        self.nav_stats.setIcon(get_icon("stats", 20))
        self.nav_stats.setIconSize(icon_size)
        self.nav_stats.setProperty("class", "nav-btn")
        self.nav_stats.setCheckable(True)
        self.nav_group.addButton(self.nav_stats)
        nav_inner_layout.addWidget(self.nav_stats)

        self.nav_import = QPushButton(f"  {t('nav_import', self.current_lang)}")
        self.nav_import.setIcon(get_icon("import", 20))
        self.nav_import.setIconSize(icon_size)
        self.nav_import.setProperty("class", "nav-btn")
        self.nav_import.setCheckable(True)
        self.nav_group.addButton(self.nav_import)
        nav_inner_layout.addWidget(self.nav_import)

        # 5 Yeni İnteraktif Modül Menü Butonları
        self.nav_match = QPushButton(f"  {t('nav_match', self.current_lang)}")
        self.nav_match.setIcon(get_icon("match", 20))
        self.nav_match.setIconSize(icon_size)
        self.nav_match.setProperty("class", "nav-btn")
        self.nav_match.setCheckable(True)
        self.nav_group.addButton(self.nav_match)
        nav_inner_layout.addWidget(self.nav_match)

        self.nav_dictation = QPushButton(f"  {t('nav_dictation', self.current_lang)}")
        self.nav_dictation.setIcon(get_icon("dictation", 20))
        self.nav_dictation.setIconSize(icon_size)
        self.nav_dictation.setProperty("class", "nav-btn")
        self.nav_dictation.setCheckable(True)
        self.nav_group.addButton(self.nav_dictation)
        nav_inner_layout.addWidget(self.nav_dictation)

        self.nav_cloze = QPushButton(f"  {t('nav_cloze', self.current_lang)}")
        self.nav_cloze.setIcon(get_icon("cloze", 20))
        self.nav_cloze.setIconSize(icon_size)
        self.nav_cloze.setProperty("class", "nav-btn")
        self.nav_cloze.setCheckable(True)
        self.nav_group.addButton(self.nav_cloze)
        nav_inner_layout.addWidget(self.nav_cloze)

        # Eklentiler Menü Butonu
        self.practice_nav_btns = {}
        for menu in NEW_CORE_MENUS:
            btn = QPushButton("  " + menu['titles'].get(self.current_lang, menu['titles']['en']))
            btn.setIcon(get_icon(menu['icon'], 20))
            btn.setIconSize(icon_size)
            btn.setProperty('class', 'nav-btn')
            btn.setCheckable(True)
            self.nav_group.addButton(btn)
            nav_inner_layout.addWidget(btn)
            self.practice_nav_btns[menu['id']] = btn

        self.nav_extensions = QPushButton(f"  {t('nav_extensions', self.current_lang)}")
        self.nav_extensions.setIcon(get_icon("extensions", 20))
        self.nav_extensions.setIconSize(icon_size)
        self.nav_extensions.setProperty("class", "nav-btn")
        self.nav_extensions.setCheckable(True)
        self.nav_group.addButton(self.nav_extensions)
        nav_inner_layout.addWidget(self.nav_extensions)

        self.personal_nav_btns={}
        self.personal_nav_container=QWidget()
        self.personal_nav_layout=QVBoxLayout(self.personal_nav_container)
        self.personal_nav_layout.setContentsMargins(0,0,0,0)
        self.personal_nav_layout.setSpacing(6)
        nav_inner_layout.addWidget(self.personal_nav_container)

        # 15 Dil Modülü İçin Dinamik Butonlar (Tümü emojilerden arındırılmış, yeşil SVG ikonlu)
        self.extension_nav_btns = {}
        icon_map = {
            "en_verbs": "verbs",
            "de_articles": "articles",
            "fr_verbs": "verbs_fr",
            "es_verbs": "verbs_es",
            "it_verbs": "verbs",
            "pt_verbs": "verbs",
            "nl_articles": "articles",
            "sv_articles": "articles",
        }

        for ext in AVAILABLE_EXTENSIONS:
            ext_id = ext["id"]
            icon_key = ext.get("icon", icon_map.get(ext_id, "library"))
            btn = QPushButton(f"  {ext.get('nav_names', {}).get(self.current_lang, ext['nav_name'])}")
            btn.setIcon(get_icon(icon_key, 20))
            btn.setIconSize(icon_size)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            self.nav_group.addButton(btn)
            nav_inner_layout.addWidget(btn)
            self.extension_nav_btns[ext_id] = btn

        # Geriye dönük uyumluluk referansları
        self.nav_verbs = self.extension_nav_btns.get("en_verbs")
        self.nav_articles_de = self.extension_nav_btns.get("de_articles")
        self.nav_verbs_fr = self.extension_nav_btns.get("fr_verbs")
        self.nav_verbs_es = self.extension_nav_btns.get("es_verbs")

        self.nav_settings = QPushButton(f"  {t('nav_settings', self.current_lang)}")
        self.nav_settings.setIcon(get_icon("settings", 20))
        self.nav_settings.setIconSize(icon_size)
        self.nav_settings.setProperty("class", "nav-btn")
        self.nav_settings.setCheckable(True)
        self.nav_group.addButton(self.nav_settings)
        nav_inner_layout.addWidget(self.nav_settings)

        nav_inner_layout.addStretch()

        self.sidebar_scroll_area.setWidget(nav_content)
        nav_container_layout.addWidget(self.sidebar_scroll_area, 1)

        def _sync_sidebar_scroll(min_val, max_val):
            self.sidebar_scrollbar.setRange(min_val, max_val)
            self.sidebar_scrollbar.setVisible(max_val > 0)

        self.sidebar_scroll_area.verticalScrollBar().rangeChanged.connect(_sync_sidebar_scroll)
        self.sidebar_scroll_area.verticalScrollBar().valueChanged.connect(self.sidebar_scrollbar.setValue)
        self.sidebar_scrollbar.valueChanged.connect(self.sidebar_scroll_area.verticalScrollBar().setValue)

        sidebar_layout.addWidget(nav_scroll_container, 1)

        # Alt Bilgi / Günlük Sayaç Kartı (Üste doğru genişletilmiş, ferah görünüm)
        bottom_box = QFrame()
        bottom_box.setObjectName("sidebarBottomBox")
        bottom_box.setFixedHeight(74)
        bottom_box.setStyleSheet("""
            QFrame#sidebarBottomBox {
                background-color: #0d1527;
                border-radius: 10px;
                margin: 2px 10px 10px 10px;
                border: 1.2px solid #1e293b;
            }
        """)
        bottom_layout = QVBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(12, 10, 12, 10)
        bottom_layout.setSpacing(4)

        self.lbl_sidebar_due = QLabel("Bugün: 0 tekrar")
        self.lbl_sidebar_due.setStyleSheet("font-size: 12px; font-weight: 800; color: #10b981; background: transparent; border: none;")
        self.lbl_sidebar_total = QLabel("Toplam: 0 kart")
        self.lbl_sidebar_total.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8; background: transparent; border: none;")

        bottom_layout.addWidget(self.lbl_sidebar_due)
        bottom_layout.addWidget(self.lbl_sidebar_total)
        sidebar_layout.addWidget(bottom_box)

        workspace_layout.addWidget(sidebar)

        # ---------------- SAĞ: İÇERİK ALANI (STACK) ----------------
        self.content_stack = QStackedWidget()

        self.view_study = StudyView()
        self.view_add_card = AddCardView()
        self.view_library = LibraryView()
        self.view_decks = DecksView()
        self.view_stats = StatsView()
        self.view_import = ImportExportView()
        self.view_settings = SettingsView()
        self.view_timer = TimerView()
        self.view_extensions = ExtensionsView()
        self.view_match = MatchGameView()
        self.view_dictation = DictationView()
        self.view_cloze = ClozeView()
        from duocards.widgets.extension_builder import ExtensionBuilderView
        self.view_tables = ExtensionBuilderView()
        self.content_stack.addWidget(self.view_tables)

        self.content_stack.addWidget(self.view_study)         # 0
        self.content_stack.addWidget(self.view_add_card)      # 1
        self.content_stack.addWidget(self.view_library)       # 2
        self.content_stack.addWidget(self.view_decks)         # 3
        self.content_stack.addWidget(self.view_stats)         # 4
        self.content_stack.addWidget(self.view_import)        # 5
        self.content_stack.addWidget(self.view_settings)      # 6
        self.content_stack.addWidget(self.view_timer)         # 8
        self.content_stack.addWidget(self.view_extensions)    # 9
        self.content_stack.addWidget(self.view_match)         # 10
        self.content_stack.addWidget(self.view_dictation)     # 11
        self.content_stack.addWidget(self.view_cloze)         # 12

        self.practice_views = {}
        for menu in NEW_CORE_MENUS:
            view = SentenceMemoryView() if menu['id'] == 'sentence_memory' else PracticeView(menu['id'])
            self.practice_views[menu['id']] = view
            self.content_stack.addWidget(view)

        # 15 Dil Eklenti Modül Görünümleri (1000+ satırlık veri seti, responsif quiz, tam çok dilli)
        self.extension_views = {}
        for ext in AVAILABLE_EXTENSIONS:
            view = UniversalLanguageModuleView(
                module_id=ext["id"],
                title=ext["title"],
                lang_code=ext["lang_code"],
                dataset_file=ext["dataset_file"],
                term_col_name=ext["term_col"],
                attr_col_name=ext["attr_col"],
                extra_col_name=ext["extra_col"],
                filter_options=ext.get("filters", []),
                titles=ext.get("titles"),
                column_titles=ext.get("column_titles")
            )
            self.extension_views[ext["id"]] = view
            self.content_stack.addWidget(view)

        # Geriye dönük uyumluluk referansları
        self.view_verbs = self.extension_views.get("en_verbs")
        self.view_articles_de = self.extension_views.get("de_articles")
        self.view_verbs_fr = self.extension_views.get("fr_verbs")
        self.view_verbs_es = self.extension_views.get("es_verbs")

        workspace_layout.addWidget(self.content_stack, 1)

        root_layout.addWidget(workspace, 1)
        outer_layout.addWidget(self.root_frame)

    def _connect_signals(self):
        # Navigasyon
        self.nav_study.clicked.connect(self.switch_to_study)
        self.nav_add.clicked.connect(self.switch_to_add)
        self.nav_library.clicked.connect(self.switch_to_library)
        self.nav_decks.clicked.connect(self.switch_to_decks)
        self.nav_stats.clicked.connect(self.switch_to_stats)
        self.nav_import.clicked.connect(self.switch_to_import)
        self.nav_timer.clicked.connect(self.switch_to_timer)
        self.nav_match.clicked.connect(self.switch_to_match)
        self.nav_dictation.clicked.connect(self.switch_to_dictation)
        self.nav_cloze.clicked.connect(self.switch_to_cloze)
        self.nav_extensions.clicked.connect(self.switch_to_extensions)
        self.nav_settings.clicked.connect(self.switch_to_settings)
        self.nav_tables.clicked.connect(self.switch_to_tables)
        self.view_tables.open_extensions_requested.connect(self.switch_to_extensions)
        self.view_tables.data_changed.connect(self.view_extensions.reload_personal)
        self.view_tables.data_changed.connect(self._sync_personal_nav)

        for key, btn in self.practice_nav_btns.items():
            btn.clicked.connect(lambda checked, menu_id=key: self.switch_to_practice(menu_id))

        for ext_id, btn in self.extension_nav_btns.items():
            btn.clicked.connect(lambda checked, eid=ext_id: self.switch_to_extension(eid))

        # Eklentiler Görünümü Sinyalleri
        self.view_extensions.extension_toggled.connect(self._on_extension_toggled)
        self.view_extensions.menu_toggled.connect(self._on_menu_toggled)
        self.view_extensions.open_module_requested.connect(self._open_extension_module)
        self.view_extensions.personal_menu_toggled.connect(lambda route,active:self._sync_personal_nav())

        # Global Masaüstü Kısayolu Sinyali
        global_hotkey.triggered.connect(self._toggle_window_focus)

        # Kart Ekleme Ekranı Sinyalleri
        self.view_add_card.card_saved.connect(self._on_data_updated)
        self.view_add_card.open_library.connect(self.switch_to_library)
        self.view_add_card.edit_existing.connect(self._edit_card_from_study)

        # Kütüphane Sinyalleri
        self.view_library.card_updated.connect(self._on_data_updated)

        # Deste Ekranı Sinyalleri
        self.view_decks.request_study_deck.connect(self._study_specific_deck)
        self.view_decks.decks_changed.connect(self._on_data_updated)

        # Çalışma Ekranı Sinyalleri
        self.view_study.request_add_card.connect(self.switch_to_add)
        self.view_study.request_edit_card.connect(self._edit_card_from_study)

        # İçe Aktarma Sinyalleri
        self.view_import.data_changed.connect(self._on_data_updated)
        self.view_import.backup_panel.restored.connect(self._backup_restored)
        self.view_settings.backup_panel.restored.connect(self._backup_restored)
        for panel in (self.view_import.backup_panel, self.view_settings.backup_panel):
            panel.busy_changed.connect(self._backup_busy)

        for view in self.practice_views.values():
            view.data_changed.connect(self._on_data_updated)

        # Ayarlar Sinyalleri
        self.view_settings.language_changed.connect(self._apply_language)
        self.view_settings.open_widget_requested.connect(self._launch_desktop_widget)
        self.view_settings.settings_saved.connect(self._setup_app_shortcut)
        self.view_settings.settings_saved.connect(self._apply_preferences)

    def _apply_language(self, lang: str):
        self.current_lang = lang
        settings.set("ui_language", lang)
        self.setWindowTitle(ui_text('Study Card — Flashcards and vocabulary', lang))
        for action, key in getattr(self, '_tray_actions', ()):
            action.setText(ui_text(key, lang))
        self.nav_study.setText(f"  {t('nav_study', lang)}")
        self.nav_add.setText(f"  {t('nav_add', lang)}")
        self.nav_library.setText(f"  {t('nav_library', lang)}")
        self.nav_decks.setText(f"  {t('nav_decks', lang)}")
        self.nav_timer.setText(f"  {t('nav_timer', lang)}")
        self.nav_stats.setText(f"  {t('nav_stats', lang)}")
        self.nav_import.setText(f"  {t('nav_import', lang)}")
        self.nav_match.setText(f"  {t('nav_match', lang)}")
        self.nav_dictation.setText(f"  {t('nav_dictation', lang)}")
        self.nav_cloze.setText(f"  {t('nav_cloze', lang)}")
        self.nav_extensions.setText(f"  {t('nav_extensions', lang)}")
        self.nav_settings.setText(f"  {t('nav_settings', lang)}")
        self.lbl_sub.setText(t("app_subtitle", lang))
        for menu in NEW_CORE_MENUS:
            self.practice_nav_btns[menu["id"]].setText("  " + menu["titles"].get(lang, menu["titles"]["en"]))
        for view in self.practice_views.values():
            view.update_language(lang)

        # Alt ekranların dilini güncelle
        self.view_study.update_language(lang)
        self.view_add_card.update_language(lang)
        self.view_library.update_language(lang)
        self.view_decks.update_language(lang)
        self.view_timer.update_language(lang)
        self.view_stats.update_language(lang)
        self.view_import.update_language(lang)
        self.view_settings.update_language(lang)
        self.view_tables.update_language(lang)
        self.view_extensions.update_language(lang)
        self.view_match.update_language(lang)
        self.view_dictation.update_language(lang)
        self.view_cloze.update_language(lang)

        # 15 Dil Modülünün menü butonlarını ve görünümlerini arayüz diline göre güncelle
        for ext in AVAILABLE_EXTENSIONS:
            ext_id = ext["id"]
            btn = self.extension_nav_btns.get(ext_id)
            if btn:
                nav_name = ext.get("nav_names", {}).get(lang, ext.get("nav_name", ext_id))
                btn.setText(f"  {nav_name}")

        for view in self.extension_views.values():
            view.update_language(lang)

        if self._desktop_widget is not None:
            self._desktop_widget.update_language(lang)
        from duocards.ui_localization import localize_tree
        localize_tree(self, lang)
        self.view_add_card._refresh_duplicates()
        from duocards.widgets.mini_timer_popup import MiniTimerPopup
        if MiniTimerPopup._instance is not None:
            MiniTimerPopup._instance.update_language(lang)
        from duocards.widgets.steam_popup import SteamNotificationPopup
        popup = SteamNotificationPopup._current_instance
        if popup is not None:
            popup.lang = lang
            popup.setWindowTitle(ui_text('Study Card Notification', lang))
            localize_tree(popup, lang)

        self._update_sidebar_stats()

    def _update_sidebar_stats(self):
        stats = get_stats()
        lang = getattr(self, "current_lang", "en")
        due_prefix = ui_text('Today', lang)
        due_reps = t("deck_reps", lang, count=stats['due_cards'])
        total_prefix = ui_text('Total', lang)
        card_word = ui_text('cards', lang)
        self.lbl_sidebar_due.setText(f"{due_prefix}: {due_reps}")
        self.lbl_sidebar_total.setText(f"{total_prefix}: {stats['total_cards']} {card_word}")

    def _on_data_updated(self):
        self._update_sidebar_stats()
        self.view_study.refresh_decks_list()
        self.view_add_card.refresh_decks()
        if self.view_library.isVisible():
            self.view_library.refresh_filter_decks()
            self.view_library.reload_cards()
            self.view_library._needs_reload = False
        else:
            self.view_library._needs_reload = True
        self.view_decks.reload_decks()
        self.view_stats.reload_stats()
        self.view_import.refresh_decks()
        self.view_extensions.reload_personal()
        self._sync_personal_nav()

    def _sync_personal_nav(self):
        from duocards import personal_extensions
        documents=personal_extensions.documents()
        routes={kind+':'+doc['id'] for kind,doc in documents}
        for route in list(self.personal_nav_btns):
            if route not in routes:
                control=self.personal_nav_btns.pop(route)
                self.nav_group.removeButton(control)
                self.personal_nav_layout.removeWidget(control)
                control.deleteLater()
        any_active=False
        for kind,doc in documents:
            route=kind+':'+doc['id']
            control=self.personal_nav_btns.get(route)
            if control is None:
                control=QPushButton();control.setProperty('class','nav-btn')
                control.setCheckable(True);control.setIconSize(QSize(20,20))
                control.clicked.connect(lambda checked=False,key=route:self._open_extension_module(key))
                self.nav_group.addButton(control);self.personal_nav_layout.addWidget(control)
                self.personal_nav_btns[route]=control
            control.setText('  '+doc['name'])
            control.setToolTip(doc.get('description') or doc['name'])
            control.setIcon(get_icon(doc.get('icon','table_grid'),20))
            active=personal_extensions.in_menu(kind,doc['id'])
            control.setVisible(active);any_active=any_active or active
        self.personal_nav_container.setVisible(any_active)

    def switch_to_tables(self):
        sfx.play_click()
        self.nav_tables.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_tables)
        self.view_tables.open_home()

    def _backup_busy(self, busy):
        # Keep a backup snapshot consistent and prevent writes during restoration.
        if busy:
            self.view_tables.save()
            from duocards.audio import audio_player
            audio_player.stop()
        for button in self.nav_group.buttons():
            button.setEnabled(not busy)
        self.view_settings.setEnabled(not busy)
        self.view_import.setEnabled(not busy)
        self._backup_in_progress = busy

    def _backup_restored(self):
        for view in self.practice_views.values():
            if hasattr(view, 'invalidate_session'):
                view.invalidate_session()
            elif hasattr(view, '_signature'):
                view._signature = None
        self.view_study._session_initialized = False
        self.view_study.cards_queue = []
        self.view_study.repeat_queue = []
        self.view_study.current_card = None
        for view in (self.view_dictation, self.view_cloze):
            view.invalidate_session()
        self.view_tables.refresh()
        self.view_timer.refresh_goal_progress()
        self.view_library._needs_reload = True
        self._on_data_updated()
        self._apply_language(settings.get('ui_language', 'en'))
        self.view_settings.load_values()
        self._apply_preferences()

    def _apply_preferences(self):
        from duocards.styles import preference_stylesheet, transform_preferences
        style = preference_stylesheet()
        if self.styleSheet() != style:
            self.setStyleSheet(style)
        for widget in self.findChildren(QWidget):
            current = widget.styleSheet()
            if current != getattr(widget, '_preference_applied_style', None):
                widget._preference_original_style = current
            style = transform_preferences(getattr(widget, '_preference_original_style', current))
            if style != current:
                widget.setStyleSheet(style)
            widget._preference_applied_style = style
        self.view_study.card_widget._render_card_content()
        self._update_sidebar_stats()
        self.lbl_logo.setText(settings.get('profile_name', '').strip() or 'Study Card')
        for view in (self.view_dictation, self.practice_views.get('shadowing')):
            if view:
                view.chk_autoplay.setChecked(settings.get('practice_autoplay', True))

    def switch_to_study(self, play_sound=True, allow_autoplay=True):
        if play_sound:
            sfx.play_click()
        self.nav_study.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_study)
        self.view_study.refresh_decks_list()
        if not self.view_study._session_initialized or self.view_study.session_total_count == 0:
            self.view_study.reload_session(allow_autoplay=allow_autoplay)
        self._update_sidebar_stats()

    def _study_specific_deck(self, deck_id: int):
        sfx.play_click()
        self.nav_study.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_study)
        self.view_study.refresh_decks_list()
        self.view_study.reload_session(specific_deck_id=deck_id)
        self._update_sidebar_stats()

    def switch_to_add(self):
        sfx.play_click()
        self.nav_add.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_add_card)
        self.view_add_card.refresh_decks()
        self.view_add_card.input_term.setFocus()
        self._update_sidebar_stats()

    def switch_to_library(self):
        sfx.play_click()
        self.nav_library.setChecked(True)
        if getattr(self.view_library, "_needs_reload", True):
            self.view_library.refresh_filter_decks()
            self.view_library.reload_cards()
            self.view_library._needs_reload = False
        self.content_stack.setCurrentWidget(self.view_library)
        self._update_sidebar_stats()

    def switch_to_decks(self):
        sfx.play_click()
        self.nav_decks.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_decks)
        self.view_decks.reload_decks()
        self._update_sidebar_stats()

    def switch_to_stats(self):
        sfx.play_click()
        self.nav_stats.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_stats)
        self.view_stats.reload_stats()
        self._update_sidebar_stats()

    def switch_to_import(self):
        sfx.play_click()
        self.nav_import.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_import)
        self.view_import.refresh_decks()
        self._update_sidebar_stats()

    def switch_to_settings(self):
        sfx.play_click()
        self.nav_settings.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_settings)
        self.view_settings.load_values()
        self._update_sidebar_stats()

    def switch_to_timer(self):
        sfx.play_click()
        self.nav_timer.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_timer)
        self.view_timer.refresh_goal_progress()
        self._update_sidebar_stats()

    def switch_to_extensions(self):
        sfx.play_click()
        self.nav_extensions.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_extensions)
        self.view_extensions.reload_personal()
        self._update_sidebar_stats()

    def switch_to_extension(self, ext_id: str):
        sfx.play_click()
        btn = self.extension_nav_btns.get(ext_id)
        if btn:
            btn.setChecked(True)
        view = self.extension_views.get(ext_id)
        if view:
            self.content_stack.setCurrentWidget(view)
        self._update_sidebar_stats()

    def switch_to_verbs(self):
        self.switch_to_extension("en_verbs")

    def switch_to_articles_de(self):
        self.switch_to_extension("de_articles")

    def switch_to_verbs_fr(self):
        self.switch_to_extension("fr_verbs")

    def switch_to_verbs_es(self):
        self.switch_to_extension("es_verbs")

    def switch_to_practice(self, key):
        sfx.play_click()
        self.practice_nav_btns[key].setChecked(True)
        view = self.practice_views[key]
        self.content_stack.setCurrentWidget(view)
        view.reload_cards()
        self._update_sidebar_stats()

    def switch_to_match(self):
        sfx.play_click()
        self.nav_match.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_match)
        self.view_match.reload_cards()
        self._update_sidebar_stats()

    def switch_to_dictation(self):
        sfx.play_click()
        self.nav_dictation.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_dictation)
        self.view_dictation.reload_cards()
        self._update_sidebar_stats()

    def switch_to_cloze(self):
        sfx.play_click()
        self.nav_cloze.setChecked(True)
        self.content_stack.setCurrentWidget(self.view_cloze)
        self.view_cloze.reload_cards()
        self._update_sidebar_stats()

    def _update_extension_nav_buttons(self):
        """Kullanıcının Eklentiler menüsünden aktif ettiği ana menüleri ve 15 dili gösterir/gizler."""
        # Ana Menüler
        for menu in NEW_CORE_MENUS:
            self.practice_nav_btns[menu["id"]].setVisible(settings.get(menu["setting_key"], True))
        self.nav_study.setVisible(settings.get("menu_visible_study", True))
        self.nav_add.setVisible(settings.get("menu_visible_add", True))
        self.nav_library.setVisible(settings.get("menu_visible_library", True))
        self.nav_decks.setVisible(settings.get("menu_visible_decks", True))
        self.nav_tables.setVisible(settings.get('menu_visible_maker', True))
        self.nav_timer.setVisible(settings.get("menu_visible_timer", True))
        self.nav_stats.setVisible(settings.get("menu_visible_stats", True))
        self.nav_import.setVisible(settings.get("menu_visible_import", True))

        # Yeni İnteraktif Modüller
        self.nav_match.setVisible(settings.get("menu_visible_match", True))
        self.nav_dictation.setVisible(settings.get("menu_visible_dictation", True))
        self.nav_cloze.setVisible(settings.get("menu_visible_cloze", True))

        self.nav_settings.setVisible(settings.get("menu_visible_settings", True))

        # 15 Dil Eklenti modülleri
        for ext in AVAILABLE_EXTENSIONS:
            btn = self.extension_nav_btns.get(ext["id"])
            if btn:
                is_active = settings.get(ext["setting_key"], ext.get("default", False))
                btn.setVisible(is_active)
        self._sync_personal_nav()

    def _on_extension_toggled(self, ext_id: str, active: bool):
        self._update_extension_nav_buttons()

    def _on_menu_toggled(self, menu_id: str, active: bool):
        self._update_extension_nav_buttons()

    def _open_extension_module(self, view_name: str):
        if view_name.startswith(('table:', 'game:', 'edit-game:')):
            kind, ident = view_name.split(':',1)
            menu_route=('game' if kind=='edit-game' else kind)+':'+ident
            control=self.personal_nav_btns.get(menu_route)
            (control if control is not None and not control.isHidden() else self.nav_tables).setChecked(True)
            self.content_stack.setCurrentWidget(self.view_tables)
            {'table':self.view_tables.open_table,'game':self.view_tables.open_game,'edit-game':self.view_tables.open_game_editor}[kind](ident)
            return
        # 1. Ana menülerden birisi istendiyse
        core_switch_map = {
            'maker': self.switch_to_tables,
            "study": self.switch_to_study,
            "add": self.switch_to_add,
            "library": self.switch_to_library,
            "decks": self.switch_to_decks,
            "timer": self.switch_to_timer,
            "stats": self.switch_to_stats,
            "import": self.switch_to_import,
            "match": self.switch_to_match,
            "dictation": self.switch_to_dictation,
            "cloze": self.switch_to_cloze,
            "settings": self.switch_to_settings,
        }
        if view_name in self.practice_views:
            self.switch_to_practice(view_name)
            return
        if view_name in core_switch_map:
            core_switch_map[view_name]()
            return

        # 2. 15 Dil modüllerinden birisi istendiyse
        for ext in AVAILABLE_EXTENSIONS:
            if view_name in (ext["view_name"], ext["id"]):
                self.switch_to_extension(ext["id"])
                return

    def _launch_desktop_widget(self):
        if self._desktop_widget is None:
            self._desktop_widget = DesktopMiniWidget()
            self._desktop_widget.closed.connect(self._on_desktop_widget_closed)
        self._desktop_widget.reload_cards()
        self._desktop_widget.show()
        self._desktop_widget.raise_()
        self._desktop_widget.activateWindow()

    def _on_desktop_widget_closed(self):
        self._desktop_widget = None

    def _setup_app_shortcut(self):
        sc_seq = settings.get("app_shortcut", "Ctrl+Alt+S")
        if hasattr(self, "_app_shortcut_obj") and self._app_shortcut_obj:
            self._app_shortcut_obj.setEnabled(False)
            self._app_shortcut_obj.deleteLater()
            self._app_shortcut_obj = None

        if sc_seq:
            try:
                from PyQt6.QtGui import QKeySequence, QShortcut
                self._app_shortcut_obj = QShortcut(QKeySequence(sc_seq), self)
                self._app_shortcut_obj.activated.connect(self._toggle_window_focus)
            except Exception:
                pass
            global_hotkey.set_shortcut(sc_seq)
            sync_system_shortcut(sc_seq)
        else:
            global_hotkey.stop()
            sync_system_shortcut("")

    def _toggle_window_focus(self):
        toggle_app_window(self)

    def _check_daily_notification(self):
        if not settings.get("daily_notification_enabled", False):
            return
        from datetime import datetime
        now = datetime.now()
        now_time_str = now.strftime("%H:%M")
        target_time = settings.get("notification_time", "20:00")
        today_str = now.strftime("%Y-%m-%d")

        if now_time_str == target_time and self._last_notified_date != today_str:
            self._last_notified_date = today_str
            lang = getattr(self, "current_lang", "en")
            msg = (
                ui_text("Time to review today's flashcards! Take 5 minutes to keep your streak!", lang)
            )
            title = ui_text('DAILY STUDY TIME', lang)

            def _on_notif_click():
                self.showNormal()
                self.activateWindow()
                self.raise_()
                self.switch_to_study()

            # Steam tarzı sağ-alt pop-up bildirim
            show_steam_notification(title, msg, on_click=_on_notif_click)

    def _edit_card_from_study(self, card_id: int):
        self.view_library.open_edit_dialog(card_id)
        self.view_study.reload_session()

    # ---------------- ÖZEL ÇERÇEVE KENAR BOYUTLANDIRMASI ----------------
    def _get_resize_edges(self, global_pos: QPoint):
        if self.isMaximized():
            return Qt.Edge(0)

        pos = self.mapFromGlobal(global_pos)
        m = self.RESIZE_MARGIN
        w = self.width()
        h = self.height()

        if pos.x() < 0 or pos.x() > w or pos.y() < 0 or pos.y() > h:
            return Qt.Edge(0)

        edges = Qt.Edge(0)
        if pos.x() <= m:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= w - m:
            edges |= Qt.Edge.RightEdge

        if pos.y() <= m:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= h - m:
            edges |= Qt.Edge.BottomEdge

        return edges

    def mouseMoveEvent(self, event):
        if self._manual_resize is not None and event.buttons() & Qt.MouseButton.LeftButton:
            edges, start, original = self._manual_resize
            delta = event.globalPosition().toPoint() - start
            geometry = QRect(original)
            if edges & Qt.Edge.LeftEdge:
                geometry.setLeft(min(original.left() + delta.x(), original.right() - self.minimumWidth() + 1))
            if edges & Qt.Edge.RightEdge:
                geometry.setRight(max(original.right() + delta.x(), original.left() + self.minimumWidth() - 1))
            if edges & Qt.Edge.TopEdge:
                geometry.setTop(min(original.top() + delta.y(), original.bottom() - self.minimumHeight() + 1))
            if edges & Qt.Edge.BottomEdge:
                geometry.setBottom(max(original.bottom() + delta.y(), original.top() + self.minimumHeight() - 1))
            self.setGeometry(geometry)
            event.accept()
            return
        edges = self._get_resize_edges(event.globalPosition().toPoint())
        if edges:
            if (edges & Qt.Edge.LeftEdge and edges & Qt.Edge.TopEdge) or \
               (edges & Qt.Edge.RightEdge and edges & Qt.Edge.BottomEdge):
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
            elif (edges & Qt.Edge.RightEdge and edges & Qt.Edge.TopEdge) or \
                 (edges & Qt.Edge.LeftEdge and edges & Qt.Edge.BottomEdge):
                self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
            elif edges & Qt.Edge.LeftEdge or edges & Qt.Edge.RightEdge:
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            elif edges & Qt.Edge.TopEdge or edges & Qt.Edge.BottomEdge:
                self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def eventFilter(self, watched, event):
        if watched == self.central_container:
            if event.type() in (QEvent.Type.Enter, QEvent.Type.MouseMove):
                if self.testAttribute(Qt.WidgetAttribute.WA_SetCursor):
                    self.unsetCursor()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._get_resize_edges(event.globalPosition().toPoint())
            if edges:
                handle = self.windowHandle()
                if not (handle and handle.startSystemResize(edges)):
                    self._manual_resize = (edges, event.globalPosition().toPoint(), self.geometry())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._manual_resize = None
        super().mouseReleaseEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.isMaximized():
                self.root_frame.setObjectName("windowRootMaximized")
                self.title_bar.btn_max.setText("[ ]")
            else:
                self.root_frame.setObjectName("windowRoot")
                self.title_bar.btn_max.setText("□")
            self.root_frame.style().unpolish(self.root_frame)
            self.root_frame.style().polish(self.root_frame)
        super().changeEvent(event)

    def _setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        import os
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icon.png")
        tray_icon_obj = QIcon(icon_path) if os.path.exists(icon_path) else self.windowIcon()

        self.tray_icon = QSystemTrayIcon(tray_icon_obj, self)
        self.tray_icon.setToolTip(ui_text('Study Card', self.current_lang))

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #111827;
                color: #f1f5f9;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #10b981;
                color: #ffffff;
            }
        """)

        act_show = tray_menu.addAction(ui_text('Open Study Card', self.current_lang))
        act_show.triggered.connect(self._toggle_window_focus)

        act_timer = tray_menu.addAction(ui_text('Timer / Stopwatch', self.current_lang))
        act_timer.triggered.connect(self._open_timer_from_tray)

        tray_menu.addSeparator()

        act_quit = tray_menu.addAction(ui_text('Quit', self.current_lang))
        act_quit.triggered.connect(self.force_quit)
        self._tray_actions = ((act_show, 'Open Study Card'), (act_timer, 'Timer / Stopwatch'), (act_quit, 'Quit'))

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _open_timer_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.switch_to_timer()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._toggle_window_focus()

    def force_quit(self):
        self._is_force_quitting = True
        global_hotkey.stop()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if getattr(self, '_backup_in_progress', False):
            event.ignore()
            return
        self.view_tables.save()
        if getattr(self, "_is_force_quitting", False):
            event.accept()
            return

        # Arka planda başlatma / çalışma izni aktifse pencereyi gizle, arka planda çalışmaya devam et
        background_enabled = settings.get("autostart_enabled", False) or settings.get("run_in_background", False)
        if background_enabled and self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            return

        global_hotkey.stop()
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        super().closeEvent(event)

