"""Local game recipes, unambiguous question pools and persistent play results."""
import copy
import json
import random
import uuid
from datetime import datetime
from duocards import db, custom_tables
from duocards.practice import normalize_answer, accepted_answers
from duocards.languages import get_language_code
from duocards.icons import PERSONAL_ICONS

MODES = ('quiz', 'matching', 'typing', 'audio_dictation', 'audio_translation', 'audio_quiz', 'memory', 'word_builder')
BOARD_MODES = frozenset(('matching', 'memory'))
CHOICE_MODES = frozenset(('quiz', 'audio_quiz'))
AUDIO_MODES = frozenset(('audio_dictation', 'audio_translation', 'audio_quiz'))
PROMPT_ANSWER_MODES = frozenset(('audio_dictation', 'word_builder'))


def expected_answer(game,row):
    if game['mode'] in PROMPT_ANSWER_MODES:
        return row['prompt'],row.get('language','en')
    return row['answer'],row.get('answer_language','tr')


def init_tables(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS custom_games (id TEXT PRIMARY KEY, name TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    conn.execute('CREATE TABLE IF NOT EXISTS custom_game_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, game_id TEXT NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL, duration_seconds REAL NOT NULL, played_at TEXT NOT NULL)')


def new_game():
    return dict(id=uuid.uuid4().hex, name='', description='', icon='gamepad', mode='quiz',
                source='manual', source_id='', prompt_column='term', answer_column='definition',
                question_count=10, time_limit=0, shuffle=True, hints=True, sound=True,
                manual_pairs=[], language='en', answer_language='tr')


def validate(game):
    if not isinstance(game, dict) or not isinstance(game.get('id'), str) or not game['id'] or not isinstance(game.get('name'), str) or not game['name'].strip():
        raise ValueError('Please enter a game name.')
    if game.get('icon') not in PERSONAL_ICONS or not isinstance(game.get('description'), str):
        raise ValueError('Invalid game identity.')
    if game.get('mode') not in MODES or game.get('source') not in ('manual', 'library', 'table'):
        raise ValueError('Invalid game recipe.')
    for key, low, high in [('question_count',1,100),('time_limit',0,300)]:
        if type(game.get(key)) is not int or not low <= game[key] <= high:
            raise ValueError('Invalid game rules.')
    for key in ('shuffle','hints','sound'):
        if type(game.get(key)) is not bool:
            raise ValueError('Invalid game rules.')
    for key in ('source_id','prompt_column','answer_column','language'):
        if not isinstance(game.get(key), str):
            raise ValueError('Invalid game recipe.')
    if not isinstance(game.get('answer_language','tr'),str):
        raise ValueError('Invalid game recipe.')
    if not isinstance(game.get('manual_pairs'), list) or len(game['manual_pairs']) > 10000:
        raise ValueError('Invalid question pairs.')
    for pair in game['manual_pairs']:
        if not isinstance(pair, dict) or any(not isinstance(pair.get(k), str) for k in ('prompt', 'answer')):
            raise ValueError('Invalid question pairs.')
    return game


def save_game(game):
    validate(game)
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('INSERT INTO custom_games(id,name,data) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,data=excluded.data,updated_at=CURRENT_TIMESTAMP', (game['id'], game['name'].strip(), json.dumps(game, ensure_ascii=False)))


def list_games():
    with db.get_connection() as conn:
        init_tables(conn)
        return [json.loads(r['data']) for r in conn.execute('SELECT data FROM custom_games ORDER BY name COLLATE NOCASE')]


def get_game(ident):
    return next((game for game in list_games() if game['id'] == ident), None)


def delete_game(ident):
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('DELETE FROM custom_games WHERE id=?', (ident,))
        conn.execute('DELETE FROM custom_game_runs WHERE game_id=?', (ident,))


def questions(game):
    """Resolve live sources; reject ambiguous prompts rather than marking right answers wrong."""
    validate(game)
    pool = []
    if game['source'] == 'manual':
        pool = [dict(pair, language=game['language'], answer_language=game.get('answer_language','tr')) for pair in game['manual_pairs']]
    elif game['source'] == 'library':
        needs_answer=game['mode']!='audio_dictation'
        if game['prompt_column'] not in ('term', 'definition') or needs_answer and (game['answer_column'] not in ('term', 'definition') or game['prompt_column'] == game['answer_column']):
            raise ValueError('Choose two different columns.')
        deck = int(game['source_id']) if game['source_id'] else None
        for card in db.get_all_cards(deck):
            pool.append(dict(prompt=card[game['prompt_column']], answer=card.get(game['answer_column'],'') or '', language=get_language_code(card.get('source_lang') or 'en') if game['prompt_column']=='term' else get_language_code(card.get('target_lang') or 'tr'), answer_language=get_language_code(card.get('target_lang') or 'tr') if game['answer_column']=='definition' else get_language_code(card.get('source_lang') or 'en')))
    else:
        table = next((t for t in custom_tables.list_tables() if t['id']==game['source_id']), None)
        if not table:
            raise ValueError('The source table is unavailable. Choose another source in the studio.')
        columns = {c['id']: c for c in table['columns']}
        needs_answer=game['mode']!='audio_dictation'
        if game['prompt_column'] not in columns or needs_answer and (game['answer_column'] not in columns or game['prompt_column']==game['answer_column']):
            raise ValueError('Choose two different columns.')
        pool = [dict(prompt=row['cells'].get(game['prompt_column'],''), answer=row['cells'].get(game['answer_column'],''), language=columns[game['prompt_column']]['language'], answer_language=columns.get(game['answer_column'],columns[game['prompt_column']])['language']) for row in table['rows']]
    result, prompts = [], {}
    for row in pool:
        prompt, answer = row['prompt'].strip(), row['answer'].strip()
        if not prompt or not answer and game['mode']!='audio_dictation':
            continue
        if not answer:
            answer=prompt
        if game['mode']=='word_builder' and len(prompt)>60:
            raise ValueError('Word builder supports words or short phrases up to 60 characters.')
        prompt_key = normalize_answer(prompt, row.get('language'))
        answer_key = normalize_answer(answer, row.get('answer_language'))
        if prompt_key in prompts:
            if prompts[prompt_key] != answer_key and game['mode']!='audio_dictation':
                raise ValueError('Some questions have multiple answers. Edit the source pairs to make each question unique.')
            continue
        prompts[prompt_key] = answer_key
        result.append(dict(row, prompt=prompt, answer=answer))
    unique_answers = {normalize_answer(r['answer'], r.get('answer_language')) for r in result}
    if not result:
        raise ValueError('Add complete question and answer pairs to start.')
    if game['mode'] in CHOICE_MODES | BOARD_MODES and len(unique_answers) < 2:
        raise ValueError('This game needs at least two different answers.')
    if game['mode'] in BOARD_MODES and len(unique_answers) != len(result):
        raise ValueError('Matching needs a different answer for every question. Edit the source pairs.')
    return result


class GameSession:
    def __init__(self, game, pool=None, rng=None):
        self.game = copy.deepcopy(game)
        self.pool = questions(game) if pool is None else copy.deepcopy(pool)
        self.rng = rng or random.Random()
        self.items = list(self.pool)
        if game['shuffle']:
            self.rng.shuffle(self.items)
        self.items = self.items[:min(game['question_count'], 8 if game['mode'] in BOARD_MODES else 100)]
        self.index = self.correct = self.mistakes = 0
        self.locked = False
        self.matched = set()

    @property
    def complete(self):
        return len(self.matched) == len(self.items) if self.game['mode'] in BOARD_MODES else self.index >= len(self.items)

    def choices(self):
        current = self.items[self.index]
        expected = normalize_answer(current['answer'], current.get('answer_language'))
        alternatives, seen = [], {expected}
        for row in self.pool:
            key = normalize_answer(row['answer'], current.get('answer_language'))
            if key not in seen:
                seen.add(key); alternatives.append(row['answer'])
        self.rng.shuffle(alternatives)
        choices = [current['answer']] + alternatives[:3]
        self.rng.shuffle(choices)
        return choices

    def answer(self, value):
        if self.complete or self.locked:
            return None
        row = self.items[self.index]
        answer,language=expected_answer(self.game,row)
        response = normalize_answer(value, language)
        expected = accepted_answers(answer, language) if self.game['mode'] in ('typing','audio_translation') else {normalize_answer(answer,language)}
        correct = response in expected
        self.locked = True
        self.correct += int(correct)
        self.mistakes += int(not correct)
        return correct

    def advance(self):
        if self.locked and not self.complete:
            self.index += 1; self.locked = False

    def match(self, left, right):
        if not (0 <= left < len(self.items) and 0 <= right < len(self.items)):
            return None
        if left in self.matched or right in self.matched:
            return None
        if left == right:
            self.matched.add(left); self.correct += 1; return True
        self.mistakes += 1; return False


def record_run(ident, correct, total, duration):
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('INSERT INTO custom_game_runs(game_id,correct,total,duration_seconds,played_at) VALUES(?,?,?,?,?)', (ident,correct,total,max(0,duration),datetime.now().isoformat()))


def game_stats(ident):
    with db.get_connection() as conn:
        init_tables(conn)
        row = conn.execute('SELECT COUNT(*) plays, MAX(CASE WHEN total>0 THEN ROUND(100.0*correct/total) ELSE 0 END) best FROM custom_game_runs WHERE game_id=?', (ident,)).fetchone()
        return dict(row)
