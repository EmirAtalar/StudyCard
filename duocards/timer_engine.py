"""
Study Card - Zamanlayıcı & Kronometre Çekirdek Motoru (TimerEngine).
time.monotonic() tabanlı yüksek hassasiyetli zaman takibi;
1000+ saatlik uzun odaklanma çalışmalarında 1 milisaniye bile sapmaz.
Ana pencere ve Masaüstü Mini Widget arasında tekil (Singleton) senkronizasyon sağlar.
"""

import time
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from duocards.db import (
    add_timer_session, get_total_study_time_seconds, get_recent_timer_sessions
)
from duocards.settings import settings
from duocards.sfx import sfx
from duocards.widgets.steam_popup import show_steam_notification


class TimerEngine(QObject):
    """
    Kronometre ve Geri Sayım Zamanlayıcısını yöneten merkezi motor.
    """
    tick = pyqtSignal()
    timer_finished = pyqtSignal()
    session_saved = pyqtSignal(int)
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = "stopwatch"  # "stopwatch" veya "timer"

        # --- Kronometre (1000 Saat Hedefi İçin Sapıtmayan Tasarım) ---
        self._sw_running: bool = False
        self._sw_start_mono: float = 0.0
        self._sw_accumulated: float = 0.0
        self._laps: List[Dict[str, Any]] = []

        # --- Geri Sayım Zamanlayıcısı ---
        self._tm_running: bool = False
        self._tm_duration_seconds: int = 25 * 60  # Varsayılan 25 dk Pomodoro
        self._tm_remaining: float = float(25 * 60)
        self._tm_target_mono: float = 0.0

        # Ana Güncelleme Zamanlayıcısı (33ms hassasiyet / ~30 FPS akıcı centisecond) - Lazy başlatılır
        self._clock_timer: Optional[QTimer] = None

    def _ensure_timer(self):
        if self._clock_timer is None:
            from PyQt6.QtWidgets import QApplication
            if QApplication.instance() is not None:
                self._clock_timer = QTimer(self)
                self._clock_timer.setInterval(33)
                self._clock_timer.timeout.connect(self._on_tick)
                self._clock_timer.start()
        elif not self._clock_timer.isActive():
            self._clock_timer.start(33)

    def set_mode(self, mode: str):
        if mode in ("stopwatch", "timer") and self.mode != mode:
            self.mode = mode
            self.mode_changed.emit(mode)

    # ---------------- KRONOMETRE METOTLARI ----------------

    @property
    def is_stopwatch_running(self) -> bool:
        return self._sw_running

    def get_stopwatch_elapsed(self) -> float:
        """Geçen toplam süreyi saniye cinsinden döner (float)."""
        if self._sw_running:
            return self._sw_accumulated + (time.monotonic() - self._sw_start_mono)
        return self._sw_accumulated

    def start_stopwatch(self):
        if not self._sw_running:
            self._ensure_timer()
            self._sw_running = True
            self._sw_start_mono = time.monotonic()
            self.tick.emit()

    def pause_stopwatch(self):
        if self._sw_running:
            self._sw_accumulated += (time.monotonic() - self._sw_start_mono)
            self._sw_running = False
            self.tick.emit()

    stop_stopwatch = pause_stopwatch

    def toggle_stopwatch(self):
        if self._sw_running:
            self.pause_stopwatch()
        else:
            self.start_stopwatch()

    def reset_stopwatch(self):
        self._sw_running = False
        self._sw_accumulated = 0.0
        self._sw_start_mono = 0.0
        self._laps.clear()
        self.tick.emit()

    def add_lap(self) -> Optional[Dict[str, Any]]:
        """Mevcut süreyi tur (lap) olarak kaydeder."""
        elapsed = self.get_stopwatch_elapsed()
        if elapsed <= 0:
            return None
        lap_no = len(self._laps) + 1
        last_lap_total = self._laps[-1]["total"] if self._laps else 0.0
        lap_split = elapsed - last_lap_total
        lap_info = {
            "lap_no": lap_no,
            "split": lap_split,
            "total": elapsed,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self._laps.append(lap_info)
        return lap_info

    def get_laps(self) -> List[Dict[str, Any]]:
        return list(self._laps)

    def save_stopwatch_session(self, notes: str = "") -> int:
        """Mevcut kronometre süresini veritabanına ve 1000 saat hedefine ekler."""
        elapsed = int(self.get_stopwatch_elapsed())
        if elapsed < 5:
            # 5 saniyeden kısa testleri kaydetme
            return 0
        
        session_id = add_timer_session("stopwatch", elapsed, notes)
        self.reset_stopwatch()
        self.session_saved.emit(session_id)
        return session_id

    # ---------------- 1000 SAAT HEDEF İLERLEMESİ ----------------

    def get_target_hours(self) -> int:
        return settings.get("stopwatch_target_hours", 1000)

    def set_target_hours(self, hours: int):
        settings.set("stopwatch_target_hours", max(1, hours))
        self.tick.emit()

    def get_1000h_progress(self) -> Dict[str, Any]:
        """1000 saatlik hedef ilerleme istatistiklerini hesaplar."""
        db_total_sec = get_total_study_time_seconds()
        current_sw_sec = int(self.get_stopwatch_elapsed()) if self._sw_running or self._sw_accumulated > 0 else 0
        total_seconds = db_total_sec + current_sw_sec

        target_hours = self.get_target_hours()
        total_hours = total_seconds / 3600.0
        progress_pct = min(100.0, (total_hours / target_hours) * 100.0) if target_hours > 0 else 0.0
        remaining_seconds = max(0, (target_hours * 3600) - total_seconds)

        return {
            "total_seconds": total_seconds,
            "total_hours": total_hours,
            "target_hours": target_hours,
            "progress_pct": progress_pct,
            "remaining_seconds": remaining_seconds,
            "remaining_hours": remaining_seconds / 3600.0,
            "total_h": int(total_seconds // 3600),
            "total_m": int((total_seconds % 3600) // 60),
            "total_s": int(total_seconds % 60),
            "rem_h": int(remaining_seconds // 3600),
            "rem_m": int((remaining_seconds % 3600) // 60),
        }

    # ---------------- GERİ SAYIM ZAMANLAYICISI METOTLARI ----------------

    @property
    def is_timer_running(self) -> bool:
        return self._tm_running

    def get_timer_remaining(self) -> float:
        if self._tm_running:
            rem = self._tm_target_mono - time.monotonic()
            return max(0.0, rem)
        return self._tm_remaining

    def get_timer_duration(self) -> int:
        return self._tm_duration_seconds

    def set_timer_duration(self, seconds: int):
        self.pause_timer()
        self._tm_duration_seconds = max(5, seconds)
        self._tm_remaining = float(self._tm_duration_seconds)
        self.tick.emit()

    def start_timer(self):
        if not self._tm_running and self._tm_remaining > 0:
            self._ensure_timer()
            self._tm_running = True
            self._tm_target_mono = time.monotonic() + self._tm_remaining
            self.tick.emit()

    def pause_timer(self):
        if self._tm_running:
            self._tm_remaining = max(0.0, self._tm_target_mono - time.monotonic())
            self._tm_running = False
            self.tick.emit()

    stop_timer = pause_timer

    def toggle_timer(self):
        if self._tm_running:
            self.pause_timer()
        else:
            self.start_timer()

    def reset_timer(self):
        self._tm_running = False
        self._tm_remaining = float(self._tm_duration_seconds)
        self.tick.emit()

    # ---------------- ÇEKİRDEK TICK MOTORU ----------------

    def _on_tick(self):
        # Kronometre çalışıyorsa tick yay
        if self._sw_running:
            self.tick.emit()

        # Geri sayım çalışıyorsa kontrol et
        if self._tm_running:
            rem = self._tm_target_mono - time.monotonic()
            if rem <= 0:
                self._tm_running = False
                self._tm_remaining = 0.0
                self._handle_timer_completed()
            self.tick.emit()

    def _handle_timer_completed(self):
        """Geri sayım bittiğinde bildirim, ses ve veritabanı kaydı yapar."""
        try:
            sfx.play_complete()
        except Exception:
            pass

        # Veritabanına kaydet
        try:
            add_timer_session("timer", self._tm_duration_seconds, "Zamanlayıcı Odaklanma")
        except Exception:
            pass

        # Yeşil neon pop-up bildirim göster ("Süre bitti")
        try:
            lang = settings.get("ui_language", "tr")
            notif_title = "Süre bitti" if lang == "tr" else "Time's up"
            notif_msg = "Geri sayım zamanlayıcınız tamamlandı!" if lang == "tr" else "Your countdown timer has completed!"
            show_steam_notification(notif_title, notif_msg)
        except Exception:
            pass

        self.timer_finished.emit()


# Global Singleton Engine
timer_engine = TimerEngine()
