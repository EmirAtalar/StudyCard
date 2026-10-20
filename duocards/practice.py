"""Pratik için kesin yanıt eşleştirme, güvenli boşluk ve kalıcı sonuç kaydı."""
import re
import unicodedata
from datetime import date
from duocards import db
from duocards.sentence_memory import card_language, term_pattern


def normalize_answer(value, lang=None):
    # Aksanları korur: ano/año ve schon/schön farklı sözcüklerdir.
    value = unicodedata.normalize('NFC', value)
    if lang == 'tr':
        value = value.replace('I', 'ı').replace('İ', 'i')
    # İ.casefold() görünmez birleşen nokta üretir; İnto ve into eşleşmeli.
    value = value.casefold().replace('i\u0307', 'i').replace('’', "'")
    return ' '.join(value.strip().strip(' .!?。！？').split())


def accepted_answers(value, lang=None):
    answers = [normalize_answer(value, lang)]
    answers += [normalize_answer(part, lang) for part in re.split(r'[,;/]', value)]
    return {answer for answer in answers if answer}


def make_cloze(card, sentence):
    term = card.get('term', '').strip()
    if not term:
        return None
    match = term_pattern(term, card_language(card)).search(sentence)
    if not match:
        return None
    # Gerçekte silinen biçim cevap olur; HTML ayrı olarak oluşturulur.
    return sentence[:match.start()], sentence[match.start():match.end()], sentence[match.end():]


def init_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS practice_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,
        mode TEXT NOT NULL, correct INTEGER NOT NULL,
        answer TEXT NOT NULL, expected TEXT NOT NULL,
        practiced_at TEXT NOT NULL, day TEXT NOT NULL)''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_practice_day ON practice_attempts(day,mode)')


def record_attempt(card, mode, answer, expected, correct):
    from datetime import datetime
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('INSERT INTO practice_attempts(card_id,mode,correct,answer,expected,practiced_at,day) VALUES(?,?,?,?,?,?,?)',
                     (card['id'], mode, int(correct), answer, expected, datetime.now().isoformat(), date.today().isoformat()))
        if not correct:
            db._ensure_quiz_mistakes_table(conn.cursor())
            conn.execute('''INSERT INTO quiz_mistakes(card_id,term,definition,wrong_count,last_mistake_at)
                            VALUES(?,?,?,1,CURRENT_TIMESTAMP)
                            ON CONFLICT(term) DO UPDATE SET
                            wrong_count=wrong_count+1,last_mistake_at=CURRENT_TIMESTAMP''',
                         (card['id'],card['term'],card['definition']))


def mistake_ids():
    with db.get_connection() as conn:
        init_tables(conn)
        rows = conn.execute('''SELECT card_id FROM practice_attempts WHERE correct=0 AND card_id IS NOT NULL
                               UNION SELECT card_id FROM quiz_mistakes WHERE card_id IS NOT NULL''').fetchall()
        return {row['card_id'] for row in rows}


def daily_results():
    with db.get_connection() as conn:
        init_tables(conn)
        return [dict(row) for row in conn.execute('SELECT * FROM practice_attempts WHERE day=? AND mode=? ORDER BY id',
                                                (date.today().isoformat(), 'challenge'))]


def challenge_cards(cards, filter_key):
    import json
    import random
    today=date.today().isoformat()
    by_id={c['id']:c for c in cards}
    with db.get_connection() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS daily_challenges(day TEXT, filter_key TEXT, card_ids TEXT, PRIMARY KEY(day,filter_key))')
        row=conn.execute('SELECT card_ids FROM daily_challenges WHERE day=? AND filter_key=?',(today,filter_key)).fetchone()
        if row:
            ids=json.loads(row['card_ids'])
        else:
            ids=sorted(by_id)
            random.Random(today+filter_key).shuffle(ids)
            ids=ids[:10]
            conn.execute('INSERT INTO daily_challenges VALUES(?,?,?)',(today,filter_key,json.dumps(ids)))
    return [by_id[i] for i in ids if i in by_id]
