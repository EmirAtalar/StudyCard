"""
Study Card - İstatistikler ve Öğrenme Analitiği Ekranı
Sınır çizgisiz soft zeminler, 3 renkli segmentli kart dağılımı çubuğu,
haftalık çalışma aktivitesi grafiği, tekrar performansı, gelecek tekrar takvimi
ve odaklanılması gereken kartlar paneli.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from duocards.db import (
    get_stats, get_weekly_review_counts, get_review_performance,
    get_upcoming_forecast, get_difficult_cards
)
from duocards.i18n import t
from duocards.settings import settings
from duocards.ui_localization import ui_text, localize_tree , QLabel


class StatBox(QFrame):
    def __init__(self, title: str, value: str, color: str = "#10b981", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            StatBox {
                background-color: #162032;
                border: none;
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; background: transparent;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {color}; background: transparent;")
        layout.addWidget(self.lbl_value)

    def set_title(self, title: str):
        self.lbl_title.setText(title)


class SegmentedDistributionBar(QFrame):
    """
    Tüm kartların (Ezberlendi, Öğreniliyor, Yeni) oransal dağılımını
    aynı bar üzerinde 3 farklı renkte kesintisiz gösteren özel görsel bileşen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setStyleSheet("""
            SegmentedDistributionBar {
                background-color: #111827;
                border: none;
                border-radius: 9px;
            }
        """)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        # 1. Ezberlendi (Yeşil #10b981)
        self.seg_mastered = QFrame()
        self.seg_mastered.setStyleSheet("background-color: #10b981; border: none; border-radius: 8px;")
        
        # 2. Öğreniliyor (Turuncu #f59e0b)
        self.seg_learning = QFrame()
        self.seg_learning.setStyleSheet("background-color: #f59e0b; border: none; border-radius: 8px;")

        # 3. Yeni Kartlar (Mavi #38bdf8)
        self.seg_new = QFrame()
        self.seg_new.setStyleSheet("background-color: #38bdf8; border: none; border-radius: 8px;")

        self.layout.addWidget(self.seg_mastered, 1)
        self.layout.addWidget(self.seg_learning, 1)
        self.layout.addWidget(self.seg_new, 1)

    def set_distribution(self, mastered: int, learning: int, new: int):
        total = mastered + learning + new
        if total <= 0:
            self.layout.setStretch(0, 0)
            self.layout.setStretch(1, 0)
            self.layout.setStretch(2, 1)
            self.seg_mastered.setVisible(False)
            self.seg_learning.setVisible(False)
            self.seg_new.setVisible(True)
            return

        self.seg_mastered.setVisible(mastered > 0)
        self.seg_learning.setVisible(learning > 0)
        self.seg_new.setVisible(new > 0)

        # Orantılı flex stretch
        self.layout.setStretch(0, max(0, mastered))
        self.layout.setStretch(1, max(0, learning))
        self.layout.setStretch(2, max(0, new))


class WeeklyActivityWidget(QFrame):
    """
    Son 7 günün çalışma aktivitesini dikey sütun grafiği olarak çizer.
    """
    def __init__(self, lang: str = "tr", parent=None):
        super().__init__(parent)
        self.lang = lang
        self.setStyleSheet("""
            WeeklyActivityWidget {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        self.lbl_title = QLabel(ui_text('Last 7 Days Study Activity', lang))
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        layout.addWidget(self.lbl_title)

        self.bars_row = QHBoxLayout()
        self.bars_row.setSpacing(12)
        self.bars_row.setAlignment(Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(self.bars_row)

        self.day_cols = []
        for _ in range(7):
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
            col.setSpacing(4)

            lbl_val = QLabel("0")
            lbl_val.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700; background: transparent;")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bar = QFrame()
            bar.setFixedWidth(24)
            bar.setFixedHeight(8)
            bar.setStyleSheet("background-color: #1e293b; border-radius: 4px; border: none;")

            lbl_day = QLabel("Pzt")
            lbl_day.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; background: transparent;")
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)

            col.addWidget(lbl_val, 0, Qt.AlignmentFlag.AlignCenter)
            col.addWidget(bar, 0, Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl_day, 0, Qt.AlignmentFlag.AlignCenter)

            self.bars_row.addLayout(col)
            self.day_cols.append((lbl_val, bar, lbl_day))

    def update_data(self, weekly_data: list):
        day_names_tr = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_names = {"tr":day_names_tr,"en":day_names_en,"de":["Mo","Di","Mi","Do","Fr","Sa","So"],"es":["lun","mar","mié","jue","vie","sáb","dom"]}.get(self.lang,day_names_en)

        max_val = max([cnt for _, cnt in weekly_data] + [10])

        for idx, (date_str, cnt) in enumerate(weekly_data[:7]):
            lbl_val, bar, lbl_day = self.day_cols[idx]
            lbl_val.setText(str(cnt))

            # Yükseklik hesapla (min: 8px, max: 70px)
            height = 8 + int((cnt / max_val) * 62) if max_val > 0 else 8
            bar.setFixedHeight(height)

            if cnt > 0:
                bar.setStyleSheet("background-color: #10b981; border-radius: 4px; border: none;")
                lbl_val.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 800; background: transparent;")
            else:
                bar.setStyleSheet("background-color: #1e293b; border-radius: 4px; border: none;")
                lbl_val.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; background: transparent;")

            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                weekday = dt.weekday()
                lbl_day.setText(day_names[weekday])
            except Exception:
                lbl_day.setText(f"D{idx+1}")


class StatsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = settings.get("ui_language", "en")
        self._setup_ui()
        self.reload_stats()

    def showEvent(self, event):
        super().showEvent(event)
        self.reload_stats()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Kaydırılabilir alan
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(16)

        # 1. Başlık
        self.lbl_title = QLabel(t("stats_title", self.lang))
        self.lbl_title.setProperty("class", "page-title")
        self.lbl_subtitle = QLabel(t("stats_subtitle", self.lang))
        self.lbl_subtitle.setProperty("class", "page-subtitle")
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)

        # 2. Üst Sayaç Kutuları Grid
        self.grid = QGridLayout()
        self.grid.setSpacing(12)

        self.box_total = StatBox(t("box_total", self.lang), "0", "#38bdf8")
        self.box_mastered = StatBox(t("box_mastered", self.lang), "0", "#10b981")
        self.box_learning = StatBox(t("box_learning", self.lang), "0", "#f59e0b")
        self.box_new = StatBox(t("box_new", self.lang), "0", "#818cf8")
        self.box_today = StatBox(t("box_today", self.lang), "0", "#34d399")
        self.box_active = StatBox(t("box_active", self.lang), "0", "#06b6d4")

        self.grid.addWidget(self.box_total, 0, 0)
        self.grid.addWidget(self.box_mastered, 0, 1)
        self.grid.addWidget(self.box_learning, 0, 2)
        self.grid.addWidget(self.box_new, 1, 0)
        self.grid.addWidget(self.box_today, 1, 1)
        self.grid.addWidget(self.box_active, 1, 2)

        layout.addLayout(self.grid)

        # 3. ORTA ALAN: Kart Dağılımı ve İlerleme Paneli
        dist_panel = QFrame()
        dist_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        dist_layout = QVBoxLayout(dist_panel)
        dist_layout.setContentsMargins(18, 16, 18, 16)
        dist_layout.setSpacing(12)

        dist_header = QHBoxLayout()
        self.lbl_bar_title = QLabel(ui_text('Learning Progress & Card Distribution', self.lang))
        self.lbl_bar_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #f8fafc; background: transparent;")
        
        self.lbl_mastery_pct = QLabel("%0 Ezberlendi")
        self.lbl_mastery_pct.setStyleSheet("font-size: 13px; font-weight: 800; color: #10b981; background: transparent;")

        dist_header.addWidget(self.lbl_bar_title)
        dist_header.addStretch()
        dist_header.addWidget(self.lbl_mastery_pct)
        dist_layout.addLayout(dist_header)

        # 3 Renkli Kesintisiz Segment Bar
        self.distribution_bar = SegmentedDistributionBar()
        dist_layout.addWidget(self.distribution_bar)

        # Dağılım Rozetleri / Açıklamaları
        legends_row = QHBoxLayout()
        legends_row.setSpacing(14)

        self.lbl_leg_mastered = QLabel("Ezberlenen: 0 (%0)")
        self.lbl_leg_mastered.setStyleSheet("""
            color: #10b981;
            font-size: 11px;
            font-weight: 700;
            background-color: rgba(16, 185, 129, 0.12);
            padding: 4px 10px;
            border-radius: 8px;
        """)

        self.lbl_leg_learning = QLabel(ui_text('Learning: 0 (0%)', self.lang))
        self.lbl_leg_learning.setStyleSheet("""
            color: #f59e0b;
            font-size: 11px;
            font-weight: 700;
            background-color: rgba(245, 158, 11, 0.12);
            padding: 4px 10px;
            border-radius: 8px;
        """)

        self.lbl_leg_new = QLabel("Yeni: 0 (%0)")
        self.lbl_leg_new.setStyleSheet("""
            color: #38bdf8;
            font-size: 11px;
            font-weight: 700;
            background-color: rgba(56, 189, 248, 0.12);
            padding: 4px 10px;
            border-radius: 8px;
        """)

        legends_row.addWidget(self.lbl_leg_mastered)
        legends_row.addWidget(self.lbl_leg_learning)
        legends_row.addWidget(self.lbl_leg_new)
        legends_row.addStretch()
        dist_layout.addLayout(legends_row)

        layout.addWidget(dist_panel)

        # 4. ORTA ALAN: Haftalık Çalışma Aktivitesi Çizelgesi
        self.weekly_chart = WeeklyActivityWidget(lang=self.lang)
        layout.addWidget(self.weekly_chart)

        # 5. YENİ ANALİTİK PANEL: Tekrar Performansı & Gelecek Tekrar Takvimi
        perf_forecast_row = QHBoxLayout()
        perf_forecast_row.setSpacing(12)

        # 5A: Tekrar Performansı ve Yanıt Dağılımı (Kolay, Zor, Tekrar)
        self.perf_panel = QFrame()
        self.perf_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        perf_layout = QVBoxLayout(self.perf_panel)
        perf_layout.setContentsMargins(18, 16, 18, 16)
        perf_layout.setSpacing(12)

        perf_header = QHBoxLayout()
        self.lbl_perf_title = QLabel(t("stats_performance_title", self.lang))
        self.lbl_perf_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        
        self.lbl_accuracy_badge = QLabel(ui_text('0% Accuracy', self.lang))
        self.lbl_accuracy_badge.setStyleSheet("""
            color: #34d399;
            font-size: 11px;
            font-weight: 800;
            background-color: rgba(16, 185, 129, 0.15);
            padding: 3px 8px;
            border-radius: 6px;
        """)
        perf_header.addWidget(self.lbl_perf_title)
        perf_header.addStretch()
        perf_header.addWidget(self.lbl_accuracy_badge)
        perf_layout.addLayout(perf_header)

        self.lbl_total_reviews = QLabel("Toplam Tekrar: 0")
        self.lbl_total_reviews.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; background: transparent;")
        perf_layout.addWidget(self.lbl_total_reviews)

        # 3 Yanıt Rozeti (Kolay, Zor, Tekrar)
        ratings_box = QHBoxLayout()
        ratings_box.setSpacing(8)

        self.badge_easy = QLabel("Kolay: 0 (%0)")
        self.badge_easy.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700; background-color: rgba(16, 185, 129, 0.12); padding: 6px 10px; border-radius: 8px;")
        
        self.badge_hard = QLabel("Zor: 0 (%0)")
        self.badge_hard.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 700; background-color: rgba(245, 158, 11, 0.12); padding: 6px 10px; border-radius: 8px;")

        self.badge_again = QLabel("Tekrar: 0 (%0)")
        self.badge_again.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 700; background-color: rgba(239, 68, 68, 0.12); padding: 6px 10px; border-radius: 8px;")

        ratings_box.addWidget(self.badge_easy)
        ratings_box.addWidget(self.badge_hard)
        ratings_box.addWidget(self.badge_again)
        perf_layout.addLayout(ratings_box)

        perf_forecast_row.addWidget(self.perf_panel, 1)

        # 5B: Gelecek Tekrar Takvimi (Bugün, Yarın, 3 Gün, 7 Gün)
        self.forecast_panel = QFrame()
        self.forecast_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        forecast_layout = QVBoxLayout(self.forecast_panel)
        forecast_layout.setContentsMargins(18, 16, 18, 16)
        forecast_layout.setSpacing(10)

        self.lbl_fc_title = QLabel(t("stats_forecast_title", self.lang))
        self.lbl_fc_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        forecast_layout.addWidget(self.lbl_fc_title)

        fc_grid = QGridLayout()
        fc_grid.setSpacing(8)

        self.fc_box_today = StatBox(t("stats_due_today", self.lang), "0", "#38bdf8")
        self.fc_box_tomorrow = StatBox(t("stats_due_tomorrow", self.lang), "0", "#10b981")
        self.fc_box_3days = StatBox(t("stats_due_3days", self.lang), "0", "#f59e0b")
        self.fc_box_7days = StatBox(t("stats_due_7days", self.lang), "0", "#818cf8")

        # Daha kompakt stat kutusu stilleri
        for b in [self.fc_box_today, self.fc_box_tomorrow, self.fc_box_3days, self.fc_box_7days]:
            b.setStyleSheet("background-color: #111827; border: none; border-radius: 12px;")
            b.lbl_value.setStyleSheet(b.lbl_value.styleSheet().replace("32px", "20px"))
            b.layout().setContentsMargins(12, 10, 12, 10)

        fc_grid.addWidget(self.fc_box_today, 0, 0)
        fc_grid.addWidget(self.fc_box_tomorrow, 0, 1)
        fc_grid.addWidget(self.fc_box_3days, 1, 0)
        fc_grid.addWidget(self.fc_box_7days, 1, 1)
        forecast_layout.addLayout(fc_grid)

        perf_forecast_row.addWidget(self.forecast_panel, 1)
        layout.addLayout(perf_forecast_row)

        # 6. YENİ ANALİTİK PANEL: Odaklanılması Gereken Kartlar (Zorlanılan / En Çok Tekrar Edilen)
        self.focus_panel = QFrame()
        self.focus_panel.setStyleSheet("""
            QFrame {
                background-color: #162032;
                border: none;
                border-radius: 16px;
                padding: 18px;
            }
        """)
        self.focus_layout = QVBoxLayout(self.focus_panel)
        self.focus_layout.setContentsMargins(18, 16, 18, 16)
        self.focus_layout.setSpacing(10)

        self.lbl_focus_title = QLabel(t("stats_focus_title", self.lang))
        self.lbl_focus_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #f8fafc; background: transparent;")
        self.focus_layout.addWidget(self.lbl_focus_title)

        self.focus_cards_container = QVBoxLayout()
        self.focus_cards_container.setSpacing(6)
        self.focus_layout.addLayout(self.focus_cards_container)

        layout.addWidget(self.focus_panel)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def update_language(self, lang: str):
        self.lang = lang
        self.lbl_title.setText(t("stats_title", lang))
        self.lbl_subtitle.setText(t("stats_subtitle", lang))
        self.box_total.set_title(t("box_total", lang))
        self.box_mastered.set_title(t("box_mastered", lang))
        self.box_learning.set_title(t("box_learning", lang))
        self.box_new.set_title(t("box_new", lang))
        self.box_today.set_title(t("box_today", lang))
        self.box_active.set_title(t("box_active", lang))
        self.lbl_bar_title.setText(ui_text('Learning Progress & Card Distribution', lang))
        self.weekly_chart.lang = lang
        self.weekly_chart.lbl_title.setText(ui_text('Last 7 Days Study Activity', lang))
        
        self.lbl_perf_title.setText(t("stats_performance_title", lang))
        self.lbl_fc_title.setText(t("stats_forecast_title", lang))
        self.lbl_focus_title.setText(t("stats_focus_title", lang))

        self.fc_box_today.set_title(t("stats_due_today", lang))
        self.fc_box_tomorrow.set_title(t("stats_due_tomorrow", lang))
        self.fc_box_3days.set_title(t("stats_due_3days", lang))
        self.fc_box_7days.set_title(t("stats_due_7days", lang))

        self.reload_stats()
        localize_tree(self,lang)

    def reload_stats(self):
        stats = get_stats()
        self.box_total.lbl_value.setText(str(stats["total_cards"]))
        self.box_mastered.lbl_value.setText(str(stats["mastered_cards"]))
        self.box_learning.lbl_value.setText(str(stats["learning_cards"]))
        self.box_new.lbl_value.setText(str(stats["new_cards"]))
        self.box_today.lbl_value.setText(str(stats["today_reviews"]))
        self.box_active.lbl_value.setText(str(stats["active_days"]))

        total = stats["total_cards"]
        mastered = stats["mastered_cards"]
        learning = stats["learning_cards"]
        new_c = stats["new_cards"]

        m_pct = int((mastered / total * 100)) if total > 0 else 0
        l_pct = int((learning / total * 100)) if total > 0 else 0
        n_pct = int((new_c / total * 100)) if total > 0 else 0

        self.lbl_mastery_pct.setText(ui_text('{m_pct}% Mastered ({mastered} / {total})', self.lang, **{'m_pct': m_pct, 'mastered': mastered, 'total': total}))
        self.distribution_bar.set_distribution(mastered, learning, new_c)

        self.lbl_leg_mastered.setText(ui_text('Mastered: {mastered} ({m_pct}%)', self.lang, **{'mastered': mastered, 'm_pct': m_pct}))
        self.lbl_leg_learning.setText(ui_text('Learning: {learning} ({l_pct}%)', self.lang, **{'learning': learning, 'l_pct': l_pct}))
        self.lbl_leg_new.setText(ui_text('New: {new_c} ({n_pct}%)', self.lang, **{'new_c': new_c, 'n_pct': n_pct}))

        # 1. Haftalık aktivite grafiğini güncelle
        try:
            weekly = get_weekly_review_counts()
            self.weekly_chart.update_data(weekly)
        except Exception:
            pass

        # 2. Tekrar Performansı ve Yanıt Dağılımını güncelle
        try:
            perf = get_review_performance()
            self.lbl_accuracy_badge.setText(f"%{perf['accuracy_pct']} {t('stats_accuracy', self.lang)}")
            self.lbl_total_reviews.setText(f"{t('stats_total_reviews', self.lang)} {perf['total_reviews']}")

            self.badge_easy.setText(f"{t('stats_rating_easy', self.lang)}: {perf['easy_count']} (%{perf['easy_pct']})")
            self.badge_hard.setText(f"{t('stats_rating_hard', self.lang)}: {perf['hard_count']} (%{perf['hard_pct']})")
            self.badge_again.setText(f"{t('stats_rating_again', self.lang)}: {perf['again_count']} (%{perf['again_pct']})")
        except Exception:
            pass

        # 3. Gelecek Tekrar Takvimini güncelle
        try:
            fc = get_upcoming_forecast()
            self.fc_box_today.lbl_value.setText(str(fc["due_today"]))
            self.fc_box_tomorrow.lbl_value.setText(str(fc["due_tomorrow"]))
            self.fc_box_3days.lbl_value.setText(str(fc["due_3days"]))
            self.fc_box_7days.lbl_value.setText(str(fc["due_7days"]))
        except Exception:
            pass

        # 4. Odaklanılması Gereken Kartları güncelle
        try:
            # Önce eski kart etiketlerini temizle
            while self.focus_cards_container.count() > 0:
                item = self.focus_cards_container.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()

            diff_cards = get_difficult_cards(limit=4)
            if not diff_cards:
                lbl_empty = QLabel(t("stats_no_focus_cards", self.lang))
                lbl_empty.setStyleSheet("""
                    color: #10b981;
                    font-size: 12px;
                    font-weight: 600;
                    background-color: rgba(16, 185, 129, 0.1);
                    padding: 10px 14px;
                    border-radius: 10px;
                """)
                self.focus_cards_container.addWidget(lbl_empty)
            else:
                for c in diff_cards:
                    row_frame = QFrame()
                    row_frame.setStyleSheet("""
                        QFrame {
                            background-color: #111827;
                            border: none;
                            border-radius: 10px;
                            padding: 8px 12px;
                        }
                    """)
                    r_layout = QHBoxLayout(row_frame)
                    r_layout.setContentsMargins(10, 8, 10, 8)
                    r_layout.setSpacing(12)

                    lbl_term = QLabel(c.get("term", ""))
                    lbl_term.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 800; background: transparent;")
                    
                    if c.get("deck_name"):
                        lbl_deck = QLabel(c.get("deck_name", ""))
                        lbl_deck.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600; background: transparent;")
                        r_layout.addWidget(lbl_term)
                        r_layout.addWidget(lbl_deck)
                    else:
                        r_layout.addWidget(lbl_term)

                    r_layout.addStretch()

                    lbl_def = QLabel(c.get("definition", ""))
                    lbl_def.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 600; background: transparent;")
                    r_layout.addWidget(lbl_def)

                    r_layout.addStretch()

                    reps = c.get("repetition_count", 0)
                    lbl_badge = QLabel(f"{reps} {t('stats_reps', self.lang)}")
                    lbl_badge.setStyleSheet("""
                        color: #f59e0b;
                        font-size: 10px;
                        font-weight: 700;
                        background-color: rgba(245, 158, 11, 0.15);
                        padding: 3px 8px;
                        border-radius: 6px;
                    """)
                    r_layout.addWidget(lbl_badge)

                    self.focus_cards_container.addWidget(row_frame)
        except Exception:
            pass
