"""SQLite storage for decks, cards, spaced repetition and study history."""

import sqlite3
import os
from datetime import datetime, date, timedelta
import json
import csv
from duocards.content_rules import term_key
from duocards.paths import DATA_DIR
from typing import List, Dict, Any, Optional, Tuple

DB_DIR = str(DATA_DIR)
DB_PATH = os.path.join(DB_DIR, "cards.db")
MAX_REVIEW_INTERVAL_DAYS = 36500


def get_db_path() -> str:
    os.makedirs(DB_DIR, exist_ok=True)
    return DB_PATH


class _ManagedConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=10, factory=_ManagedConnection)
    conn.row_factory = sqlite3.Row
    conn.create_function('term_key', 1, term_key, deterministic=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Veritabanı tablolarını oluşturur ve ilk örnek verileri yükler."""
    os.makedirs(DB_DIR, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()

        from duocards.sentence_memory import init_tables as init_sentence_tables
        init_sentence_tables(conn)

        # Desteler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT DEFAULT '',
                color TEXT DEFAULT '#10b981',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kartlar tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
                term TEXT NOT NULL,
                definition TEXT NOT NULL,
                part_of_speech TEXT DEFAULT 'Kelime',
                example_sentence TEXT,
                example_translation TEXT,
                phonetic TEXT,
                notes TEXT,
                status TEXT DEFAULT 'new', -- 'new', 'learning', 'mastered'
                is_favorite INTEGER DEFAULT 0,
                repetition_count INTEGER DEFAULT 0,
                interval_days INTEGER DEFAULT 1,
                ease_factor REAL DEFAULT 2.5,
                due_date DATE DEFAULT CURRENT_DATE,
                last_reviewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Çalışma logları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL, -- 1: Tekrar, 2: Zor, 3: Kolay
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Zamanlayıcı ve kronometre oturum logları (1000 saat hedef takibi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timer_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL, -- 'stopwatch' veya 'timer'
                duration_seconds INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kütüphane testi yanlış yapılan kelimeler istatistik tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,
                term TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                wrong_count INTEGER DEFAULT 1,
                last_mistake_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        from duocards.practice import init_tables as init_practice_tables
        init_practice_tables(conn)

        # İndeksler
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_deck ON cards(deck_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_created ON timer_sessions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_mistakes_count ON quiz_mistakes(wrong_count DESC)")

        # cards tablosunda target_lang ve source_lang kolonları yoksa otomatik ekle
        cursor.execute("PRAGMA table_info(cards)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "target_lang" not in columns:
            cursor.execute("ALTER TABLE cards ADD COLUMN target_lang TEXT DEFAULT 'Türkçe'")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_lang ON cards(target_lang)")
        if "source_lang" not in columns:
            cursor.execute("ALTER TABLE cards ADD COLUMN source_lang TEXT DEFAULT 'İngilizce'")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_src_lang ON cards(source_lang)")
        if "is_favorite" not in columns:
            cursor.execute("ALTER TABLE cards ADD COLUMN is_favorite INTEGER DEFAULT 0")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_fav ON cards(is_favorite)")

        # Varsayılan desteler var mı kontrol et
        cursor.execute("SELECT COUNT(*) as count FROM decks")
        previously_initialized = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sync_items'").fetchone()
        if cursor.fetchone()["count"] == 0 and not previously_initialized:
            _seed_default_data(cursor)
        else:
            # Mevcut destelerdeki emoji ikonları sadeleştir
            cursor.execute("UPDATE decks SET icon = '' WHERE icon IS NOT NULL AND length(icon) > 0")

        from duocards.sync import init_sync_tables
        init_sync_tables(conn)
        conn.commit()


def _seed_default_data(cursor: sqlite3.Cursor):
    """Kullanıcının hemen denemesi için varsayılan örnek desteler ve kartlar ekler."""
    default_decks = [
        ("Günlük İngilizce & Kalıplar", "Günlük hayatta sık kullanılan kalıplar ve ifadeler", "", "#10b981"),
        ("İş & Profesyonel İngilizce", "Toplantılarda, maillerde ve iş dünyasında kullanılan tabirler", "", "#3b82f6"),
        ("Deyimler & Phrasal Verbs", "Sıkça karşılaşılan deyimsel ifadeler ve fiil öbekleri", "", "#8b5cf6")
    ]

    for name, desc, icon, color in default_decks:
        cursor.execute("INSERT INTO decks (name, description, icon, color) VALUES (?, ?, ?, ?)", (name, desc, icon, color))

    # Günlük Deste ID
    cursor.execute("SELECT id FROM decks WHERE name = 'Günlük İngilizce & Kalıplar'")
    deck_daily = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM decks WHERE name = 'Deyimler & Phrasal Verbs'")
    deck_idioms = cursor.fetchone()["id"]

    sample_cards = [
        (deck_daily, "on second thought", "düşündüm de / fikrimi değiştirdim", "Kalıp İfade",
         "On second thought, I think I'll have tea instead of coffee.", "Düşündüm de, kahve yerine çay alayım bence.",
         "/ɒn ˈsek.ənd θɔːt/", "Fikrini değiştirdiğinde kullanılır."),
        (deck_daily, "out of the blue", "aniden / hiç beklenmedik anda / damdan düşer gibi", "Deyim",
         "She called me out of the blue after five years.", "Beş yıl sonra hiç beklenmedik bir anda beni aradı.",
         "/aʊt əv ðə bluː/", "Sürpriz durumlar için çok yaygındır."),
        (deck_daily, "resilient", "dirençli / zorluklara karşı güçlü duran", "Sıfat",
         "Children are often remarkably resilient in difficult circumstances.", "Çocuklar zor koşullarda genellikle şaşırtıcı derecede dirençlidir.",
         "/rɪˈzɪl.jənt/", "Karakter veya malzeme dayanıklılığı."),
        (deck_idioms, "call it a day", "bugünlük bu kadar yeter / paydos etmek", "Deyim",
         "We've made great progress, let's call it a day.", "Harika ilerleme kaydettik, bugünlük bu kadar yeter.",
         "/kɔːl ɪt ə deɪ/", "İş veya çalışma bittiğinde söylenir."),
        (deck_idioms, "come up with", "ortaya bir fikir/çözüm atmak / bulmak", "Phrasal Verb",
         "He always comes up with brilliant solutions.", "O her zaman parlak çözümlerle ortaya çıkar.",
         "/kʌm ʌp wɪð/", "Yeni bir fikir üretmek anlamında.")
    ]

    for card in sample_cards:
        cursor.execute("""
            INSERT INTO cards (deck_id, term, definition, part_of_speech, example_sentence, example_translation, phonetic, notes, status, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', CURRENT_DATE)
        """, card)


# --- Deste İşlemleri ---

def get_all_decks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, 
                   COUNT(c.id) as total_cards,
                   SUM(CASE WHEN c.status = 'mastered' THEN 1 ELSE 0 END) as mastered_cards,
                   SUM(CASE WHEN c.due_date <= CURRENT_DATE THEN 1 ELSE 0 END) as due_cards
            FROM decks d
            LEFT JOIN cards c ON d.id = c.deck_id
            GROUP BY d.id
            ORDER BY d.name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_deck(deck_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_deck(name: str, description: str = "", icon: str = "", color: str = "#10b981") -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO decks (name, description, icon, color) VALUES (?, ?, ?, ?)",
                       (name.strip(), description.strip(), icon, color))
        conn.commit()
        return cursor.lastrowid


def update_deck(deck_id: int, name: str, description: str = "", icon: str = "", color: str = "#10b981"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE decks SET name = ?, description = ?, icon = ?, color = ? WHERE id = ?",
                       (name.strip(), description.strip(), icon, color, deck_id))
        conn.commit()


def delete_deck(deck_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        conn.commit()


# --- Kart İşlemleri ---

def find_existing_cards(term, source_lang=None, target_lang=None, exclude_id=None):
    """Unicode-aware, case-insensitive matches across all decks."""
    from duocards.languages import get_language_code
    with get_connection() as conn:
        rows = conn.execute("SELECT c.*,d.name AS deck_name FROM cards c JOIN decks d ON d.id=c.deck_id WHERE term_key(c.term)=? ORDER BY c.id", (term_key(term),)).fetchall() if term_key(term) else []
    return [dict(row) for row in rows if row['id'] != exclude_id
            and (source_lang is None or get_language_code(row['source_lang']) == get_language_code(source_lang))
            and (target_lang is None or get_language_code(row['target_lang']) == get_language_code(target_lang))]

def add_card(deck_id: int, term: str, definition: str, part_of_speech: str = "Kelime",
             example_sentence: str = "", example_translation: str = "",
             phonetic: str = "", notes: str = "", target_lang: str = "Türkçe",
             source_lang: str = "İngilizce") -> int:
    """Yeni kart ekler."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cards (
                deck_id, term, definition, part_of_speech, 
                example_sentence, example_translation, phonetic, notes, 
                target_lang, source_lang, status, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', CURRENT_DATE)
        """, (deck_id, term.strip(), definition.strip(), part_of_speech.strip(),
              example_sentence.strip(), example_translation.strip(),
              phonetic.strip(), notes.strip(), (target_lang or "Türkçe").strip(),
              (source_lang or "İngilizce").strip()))
        conn.commit()
        card_id = cursor.lastrowid
    from duocards.sentence_memory import request_examples
    request_examples(get_card(card_id))
    return card_id


def update_card(card_id: int, deck_id: int, term: str, definition: str,
                part_of_speech: str, example_sentence: str, example_translation: str,
                phonetic: str, notes: str, target_lang: Optional[str] = None,
                source_lang: Optional[str] = None):
    """Mevcut kartı günceller."""
    with get_connection() as conn:
        cursor = conn.cursor()
        fields = [
            ("deck_id", deck_id),
            ("term", term.strip()),
            ("definition", definition.strip()),
            ("part_of_speech", part_of_speech.strip()),
            ("example_sentence", example_sentence.strip()),
            ("example_translation", example_translation.strip()),
            ("phonetic", phonetic.strip()),
            ("notes", notes.strip()),
        ]
        if target_lang is not None:
            fields.append(("target_lang", target_lang.strip()))
        if source_lang is not None:
            fields.append(("source_lang", source_lang.strip()))

        set_clause = ", ".join(f"{f[0]} = ?" for f in fields)
        params = [f[1] for f in fields]
        params.append(card_id)
        cursor.execute(f"UPDATE cards SET {set_clause} WHERE id = ?", params)
        conn.commit()

    from duocards.sentence_memory import request_examples
    card = get_card(card_id)
    if card:
        request_examples(card)


def delete_card(card_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.commit()


def get_card(card_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, d.name as deck_name, d.icon as deck_icon, d.color as deck_color
            FROM cards c
            JOIN decks d ON c.deck_id = d.id
            WHERE c.id = ?
        """, (card_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_cards(deck_id: Optional[int] = None, search_query: str = "", status: str = "",
                  target_lang: Optional[str] = None, source_lang: Optional[str] = None) -> List[Dict[str, Any]]:
    """Kütüphane listesi için kartları filtreleyerek getirir."""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.*, d.name as deck_name, d.icon as deck_icon, d.color as deck_color
            FROM cards c
            JOIN decks d ON c.deck_id = d.id
            WHERE 1=1
        """
        params = []

        if deck_id is not None and deck_id > 0:
            query += " AND c.deck_id = ?"
            params.append(deck_id)

        if status:
            query += " AND c.status = ?"
            params.append(status)

        if target_lang and target_lang.strip() and target_lang.strip().lower() not in ("all", "tümü", "tüm diller", "tüm dillerde anlam"):
            clean_tgt = target_lang.strip()
            if clean_tgt.lower() in ("türkçe", "turkish", "tr"):
                query += " AND (c.target_lang = ? OR c.target_lang IS NULL OR c.target_lang = '')"
            else:
                query += " AND c.target_lang = ?"
            params.append(clean_tgt)

        if source_lang and source_lang.strip() and source_lang.strip().lower() not in ("all", "tümü", "tüm diller"):
            clean_src = source_lang.strip()
            if clean_src.lower() in ("ingilizce", "english", "en"):
                query += " AND (c.source_lang = ? OR c.source_lang IS NULL OR c.source_lang = '')"
            else:
                query += " AND c.source_lang = ?"
            params.append(clean_src)

        if search_query:
            query += " AND (c.term LIKE ? OR c.definition LIKE ? OR c.example_sentence LIKE ?)"
            term_wildcard = f"%{search_query.strip()}%"
            params.extend([term_wildcard, term_wildcard, term_wildcard])

        query += " ORDER BY c.id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


get_cards = get_all_cards


def get_distinct_target_languages() -> List[str]:
    """Kayıtlı kartlardaki farklı hedef dilleri alfabetik sırada döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT target_lang FROM cards WHERE target_lang IS NOT NULL AND trim(target_lang) != ''")
        langs = set()
        for r in cursor.fetchall():
            val = r["target_lang"].strip()
            if val:
                langs.add(val)
        langs.add("Türkçe")
        return sorted(list(langs))


def get_distinct_source_languages() -> List[str]:
    """Kayıtlı kartlardaki farklı kaynak dilleri alfabetik sırada döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source_lang FROM cards WHERE source_lang IS NOT NULL AND trim(source_lang) != ''")
        langs = set()
        for r in cursor.fetchall():
            val = r["source_lang"].strip()
            if val:
                langs.add(val)
        langs.add("İngilizce")
        return sorted(list(langs))


# --- Çalışma & Aralıklı Tekrar (SRS) İşlemleri ---

def get_study_cards(deck_id: Optional[int] = None, limit: int = 50, practice_mode: bool = False,
                    target_lang: Optional[str] = None, study_mode: str = "smart") -> List[Dict[str, Any]]:
    """
    Akıllı hata öncelikli aralıklı tekrar kartlarını getirir.
    study_mode:
        - 'smart': Hata yapılanlar ve zorlanılan kartlar daha yüksek öncelikle öne çıkar, ardından vadesi gelenler ve yeniler gelir.
        - 'mistakes': Sadece daha önce hata yapılmış, düşük ease_factor'lü veya tekrar gereken kartlar.
        - 'favorites': Sadece yıldızlı / favorilere eklenmiş kartlar.
        - 'new': Sadece henüz çalışılmamış yeni kartlar.
        - 'all': Vadeye bakılmaksızın tüm kartlar.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.*, d.name as deck_name, d.icon as deck_icon, d.color as deck_color,
                   (COALESCE(s.fail_count, 0) + COALESCE(qm.wrong_count, 0)) as mistake_count,
                   COALESCE(s.recent_fails, 0) as recent_fails
            FROM cards c
            JOIN decks d ON c.deck_id = d.id
            LEFT JOIN (
                SELECT card_id, 
                       SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as fail_count,
                       SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as recent_fails
                FROM study_logs
                GROUP BY card_id
            ) s ON s.card_id = c.id
            LEFT JOIN quiz_mistakes qm ON (qm.card_id = c.id OR qm.term = c.term)
        """
        params = []
        conditions = []

        if study_mode == "favorites":
            conditions.append("c.is_favorite = 1")
        elif study_mode == "mistakes":
            conditions.append("(COALESCE(s.fail_count, 0) > 0 OR COALESCE(qm.wrong_count, 0) > 0 OR c.status = 'learning' OR c.ease_factor < 2.3)")
        elif not practice_mode and study_mode != "all":
            if study_mode == "new":
                conditions.append("c.status = 'new'")
            elif study_mode == "due":
                conditions.append("c.due_date <= CURRENT_DATE")
            else:
                # smart default: vadesi gelenler, yeni eklenenler veya son zamanlarda hata yapılanlar
                conditions.append("(c.due_date <= CURRENT_DATE OR c.status = 'new' OR COALESCE(s.fail_count, 0) > 0 OR COALESCE(qm.wrong_count, 0) > 0)")

        if deck_id is not None and deck_id > 0:
            conditions.append("c.deck_id = ?")
            params.append(deck_id)

        if target_lang and target_lang.strip() and target_lang.strip().lower() not in ("all", "tümü", "tüm diller"):
            clean_lang = target_lang.strip()
            if clean_lang.lower() in ("türkçe", "turkish", "tr"):
                conditions.append("(c.target_lang = ? OR c.target_lang IS NULL OR c.target_lang = '')")
                params.append(clean_lang)
            else:
                conditions.append("c.target_lang = ?")
                params.append(clean_lang)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Hata sayısı yüksek olanları ve zorlanılanları en başa getir (Akıllı Ezberleme Artırıcı)
        if study_mode in ("smart", "mistakes", "favorites"):
            query += """
                ORDER BY 
                    (COALESCE(s.fail_count, 0) + COALESCE(qm.wrong_count, 0) * 2) DESC,
                    (CASE WHEN c.status = 'learning' THEN 0 WHEN c.status = 'new' THEN 1 ELSE 2 END) ASC,
                    c.ease_factor ASC,
                    c.due_date ASC
                LIMIT ?
            """
        elif practice_mode or study_mode == "all":
            query += " ORDER BY c.last_reviewed ASC, c.id ASC LIMIT ?"
        else:
            query += " ORDER BY (CASE WHEN c.status = 'new' THEN 1 ELSE 0 END) ASC, c.due_date ASC LIMIT ?"

        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def toggle_card_favorite(card_id: int) -> bool:
    """Kartın favori/yıldız durumunu tersine çevirir ve güncel durumu (True/False) döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_favorite FROM cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row["is_favorite"] else 1
        cursor.execute("UPDATE cards SET is_favorite = ? WHERE id = ?", (new_val, card_id))
        conn.commit()
        return bool(new_val)


def get_daily_streak() -> int:
    """
    Kullanıcının ardışık aktif çalışma gün sayısını hesaplar.
    Bugün çalışılmışsa bugünden geriye; henüz çalışılmamışsa dünden geriye ardışık günleri sayar.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT DATE(reviewed_at) as review_date FROM study_logs ORDER BY review_date DESC")
        rows = [r["review_date"] for r in cursor.fetchall()]
        if not rows:
            return 0

        today = date.today()
        yesterday = today - timedelta(days=1)

        dates_set = set(rows)
        if today.isoformat() in dates_set:
            curr = today
        elif yesterday.isoformat() in dates_set:
            curr = yesterday
        else:
            return 0

        streak = 0
        while curr.isoformat() in dates_set:
            streak += 1
            curr -= timedelta(days=1)
        return streak


def get_today_review_count() -> int:
    """Bugün çalışılan toplam kart sayısını döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE DATE(reviewed_at) = CURRENT_DATE")
        row = cursor.fetchone()
        return int(row["count"]) if row else 0


def calculate_review_interval(card: Dict[str, Any], rating: int, today: Optional[date] = None) -> int:
    """Tekrar aralığını hesaplar; büyüyen veya aktarılan değerleri güvenle sınırlar."""
    today = today if today is not None else date.today()
    maximum = min(MAX_REVIEW_INTERVAL_DAYS, (date.max - today).days)
    interval = card["interval_days"]
    reps = card["repetition_count"] + 1
    if rating == 1 or (rating != 2 and reps == 1):
        interval = 1
    elif rating == 2:
        interval = max(1, interval * 1.2)
    elif reps == 2:
        interval = 3
    else:
        interval = max(interval * card["ease_factor"], interval + 1)
    # Sınırı int dönüşümünden önce uygula; çarpım sonsuz olsa da taşma olmaz.
    return int(max(0, min(maximum, interval)))


def record_study_result(card_id: int, rating: int):
    """
    Kart çalışma sonucunu kaydeder ve bir sonraki tekrar tarihini hesaplar.
    Hata yapılan kartları anında hata takip tablolarıyla senkronize eder.
    rating:
        1 = Tekrar Et (Unlearned / Forgot)
        2 = Zor (Hard)
        3 = Biliyorum / Kolay (Easy / Mastered)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        card = cursor.fetchone()
        if not card:
            return

        card = dict(card)
        reps = card["repetition_count"]
        ease = card["ease_factor"]

        today = date.today()
        interval = calculate_review_interval(card, rating, today)

        if rating == 1:
            # Tekrar Et (Unlearned)
            reps = 0
            interval = 1
            new_status = 'learning'
            due = today  # bugün oturumda tekrar karşına çıkar veya yarın
            # Hata yapılan kelimeyi quiz_mistakes tablosunda da güncelle
            try:
                cursor.execute("""
                    INSERT INTO quiz_mistakes (card_id, term, definition, wrong_count, last_mistake_at)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(term) DO UPDATE SET
                        wrong_count = quiz_mistakes.wrong_count + 1,
                        last_mistake_at = CURRENT_TIMESTAMP
                """, (card_id, card["term"], card["definition"]))
            except Exception:
                pass
        elif rating == 2:
            # Zor
            reps += 1
            ease = max(1.3, ease - 0.15)
            new_status = 'learning'
            due = today + timedelta(days=interval)
        else:
            # Kolay / Biliyorum (3)
            reps += 1
            ease = ease + 0.1
            if reps >= 3 or interval >= 7:
                new_status = 'mastered'
            else:
                new_status = 'learning'
            due = today + timedelta(days=interval)

            # Başarıyla pekiştirildiyse hata sayısını hafiflet
            try:
                cursor.execute("""
                    UPDATE quiz_mistakes SET wrong_count = MAX(0, wrong_count - 1)
                    WHERE card_id = ? OR term = ?
                """, (card_id, card["term"]))
            except Exception:
                pass

        cursor.execute("""
            UPDATE cards SET
                repetition_count = ?,
                interval_days = ?,
                ease_factor = ?,
                status = ?,
                due_date = ?,
                last_reviewed = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reps, interval, ease, new_status, due.isoformat(), card_id))

        cursor.execute("""
            INSERT INTO study_logs (card_id, rating) VALUES (?, ?)
        """, (card_id, rating))

        conn.commit()


# --- İstatistikler ---

def get_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM cards")
        total_cards = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM cards WHERE status = 'mastered'")
        mastered_cards = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM cards WHERE status = 'learning'")
        learning_cards = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM cards WHERE status = 'new'")
        new_cards = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM cards WHERE due_date <= CURRENT_DATE")
        due_cards = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE DATE(reviewed_at) = CURRENT_DATE")
        today_reviews = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(DISTINCT DATE(reviewed_at)) as active_days FROM study_logs")
        active_days = cursor.fetchone()["active_days"]

        return {
            "total_cards": total_cards,
            "mastered_cards": mastered_cards,
            "learning_cards": learning_cards,
            "new_cards": new_cards,
            "due_cards": due_cards,
            "today_reviews": today_reviews,
            "active_days": active_days
        }


def get_weekly_review_counts() -> List[Tuple[str, int]]:
    """Son 7 günün gün adı ve çalışma kart sayısını döner."""
    from datetime import date, timedelta
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    result = []
    with get_connection() as conn:
        cursor = conn.cursor()
        for d in days:
            d_str = d.isoformat()
            cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE DATE(reviewed_at) = ?", (d_str,))
            cnt = cursor.fetchone()["count"]
            result.append((d_str, cnt))
    return result


def get_review_performance() -> Dict[str, Any]:
    """Çalışma loglarından genel başarı oranı ve cevap dağılımını hesaplar."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM study_logs")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE rating = 3")
        easy_cnt = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE rating = 2")
        hard_cnt = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM study_logs WHERE rating = 1")
        again_cnt = cursor.fetchone()["count"]

        success_cnt = easy_cnt + hard_cnt
        accuracy_pct = int((success_cnt / total) * 100) if total > 0 else 0

        return {
            "total_reviews": total,
            "easy_count": easy_cnt,
            "hard_count": hard_cnt,
            "again_count": again_cnt,
            "accuracy_pct": accuracy_pct,
            "easy_pct": int((easy_cnt / total) * 100) if total > 0 else 0,
            "hard_pct": int((hard_cnt / total) * 100) if total > 0 else 0,
            "again_pct": int((again_cnt / total) * 100) if total > 0 else 0,
        }


def get_upcoming_forecast() -> Dict[str, int]:
    """Bugün, yarın ve önümüzdeki günlerde tekrar bekleyen kart sayılarını döner."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    in_3days = today + timedelta(days=3)
    in_7days = today + timedelta(days=7)

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM cards WHERE due_date <= ?", (today.isoformat(),))
        due_today = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM cards WHERE due_date = ?", (tomorrow.isoformat(),))
        due_tomorrow = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM cards WHERE due_date > ? AND due_date <= ?", (today.isoformat(), in_3days.isoformat()))
        due_3days = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM cards WHERE due_date > ? AND due_date <= ?", (today.isoformat(), in_7days.isoformat()))
        due_7days = cursor.fetchone()["cnt"]

        return {
            "due_today": due_today,
            "due_tomorrow": due_tomorrow,
            "due_3days": due_3days,
            "due_7days": due_7days
        }


def get_difficult_cards(limit: int = 5) -> List[Dict[str, Any]]:
    """En çok tekrar edilen veya zorlanılan kartları döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.term, c.definition, c.repetition_count, c.ease_factor, c.status, d.name as deck_name
            FROM cards c
            LEFT JOIN decks d ON c.deck_id = d.id
            WHERE c.repetition_count > 0 OR c.status = 'learning'
            ORDER BY c.ease_factor ASC, c.repetition_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# --- Zamanlayıcı & Kronometre (1000 Saat Hedef Takibi) ---

def add_timer_session(mode: str, duration_seconds: int, notes: str = "") -> int:
    """Tamamlanan kronometre veya zamanlayıcı oturumunu kaydeder."""
    if duration_seconds <= 0:
        return 0
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO timer_sessions (mode, duration_seconds, notes)
            VALUES (?, ?, ?)
        """, (mode, int(duration_seconds), notes))
        conn.commit()
        return cursor.lastrowid or 0


def get_total_study_time_seconds() -> int:
    """Veritabanında kayıtlı tüm çalışma oturumlarının toplam saniyesini döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(duration_seconds), 0) as total FROM timer_sessions")
        row = cursor.fetchone()
        return int(row["total"]) if row else 0


def get_recent_timer_sessions(limit: int = 15) -> List[Dict[str, Any]]:
    """Son kaydedilen kronometre ve zamanlayıcı oturumlarını döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, mode, duration_seconds, notes, created_at
            FROM timer_sessions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def delete_timer_session(session_id: int):
    """Belirtilen oturum kaydını siler."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timer_sessions WHERE id = ?", (session_id,))
        conn.commit()


def clear_timer_sessions():
    """Tüm oturum kayıtlarını temizler."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timer_sessions")
        conn.commit()


# --- İçe / Dışa Aktarma ---

def export_to_json(filepath: str):
    from duocards.card_transfer import export_cards
    export_cards(filepath, 'json')


def export_to_csv(filepath: str, deck_id: Optional[int] = None):
    from duocards.card_transfer import export_cards
    export_cards(filepath, 'csv', deck_id)


def import_from_csv(filepath: str, default_deck_id: int) -> int:
    from duocards.card_transfer import import_file
    return import_file(filepath, default_deck_id)['added']


# --- Kütüphane Testi Yanlış Kelime İstatistikleri ---

def _ensure_quiz_mistakes_table(cursor: sqlite3.Cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,
            term TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            wrong_count INTEGER DEFAULT 1,
            last_mistake_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def record_quiz_mistake(term: str, definition: str, card_id: Optional[int] = None):
    """Kütüphane testinde yanlış yapılan kelimeyi ve hata sayısını kaydeder/günceller."""
    clean_t = term.strip()
    clean_d = definition.strip()
    if not clean_t:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_quiz_mistakes_table(cursor)
        cursor.execute("""
            INSERT INTO quiz_mistakes (card_id, term, definition, wrong_count, last_mistake_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(term) DO UPDATE SET
                wrong_count = wrong_count + 1,
                definition = excluded.definition,
                last_mistake_at = CURRENT_TIMESTAMP
        """, (card_id, clean_t, clean_d))
        conn.commit()


def get_top_quiz_mistakes(limit: int = 40) -> List[Dict[str, Any]]:
    """En çok yanlış yapılan kelimeleri azalan sırayla döner."""
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_quiz_mistakes_table(cursor)
        cursor.execute("""
            SELECT qm.*, c.source_lang, c.target_lang, d.name as deck_name
            FROM quiz_mistakes qm
            LEFT JOIN cards c ON qm.card_id = c.id
            LEFT JOIN decks d ON c.deck_id = d.id
            ORDER BY qm.wrong_count DESC, qm.last_mistake_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def clear_quiz_mistakes():
    """Tüm kütüphane test hata istatistiklerini sıfırlar."""
    with get_connection() as conn:
        cursor = conn.cursor()
        _ensure_quiz_mistakes_table(cursor)
        cursor.execute("DELETE FROM quiz_mistakes")
        conn.commit()

