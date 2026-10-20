"""User-owned tables; stable column IDs keep speech settings attached to cells."""
import copy
import json
import uuid
from duocards import db


def init_tables(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS custom_tables (id TEXT PRIMARY KEY, name TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)')


def new_table(name='My table', template='blank'):
    names = {'blank': ['Word', 'Meaning'], 'verbs': ['Infinitive', 'Past simple', 'Past participle', 'Meaning'], 'phrases': ['Phrase', 'Example sentence', 'Meaning']}[template]
    columns = [dict(id=uuid.uuid4().hex, name=n, language='tr' if n == 'Meaning' else 'en', speech_order=0 if n == 'Meaning' else i+1) for i, n in enumerate(names)]
    return dict(id=uuid.uuid4().hex, name=name, description='', icon='table_grid', columns=columns,
                rows=[dict(id=uuid.uuid4().hex, name='1', cells={}, muted=[])],
                speakers=True, reading_order='rows', speed=1.0, pause_ms=500, repeat=1)


def validate(table):
    if not isinstance(table, dict) or not isinstance(table.get('id'), str) or not table['id'] or not isinstance(table.get('name'), str) or not table['name'].strip():
        raise ValueError('Invalid table')
    from duocards.icons import PERSONAL_ICONS
    if not isinstance(table.get('description', ''), str) or table.get('icon', 'table_grid') not in PERSONAL_ICONS:
        raise ValueError('Invalid table identity')
    cols, rows = table.get('columns'), table.get('rows')
    if not isinstance(cols, list) or not 1 <= len(cols) <= 64 or not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError('Invalid table size')
    ids = set()
    for col in cols:
        if not isinstance(col, dict) or not isinstance(col.get('id'), str) or col['id'] in ids or not isinstance(col.get('name'), str) or not col['name'].strip():
            raise ValueError('Invalid column')
        ids.add(col['id'])
        if not isinstance(col.get('language'), str) or type(col.get('speech_order')) is not int or not 0 <= col['speech_order'] <= 64:
            raise ValueError('Invalid speech settings')
    row_ids = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or row['id'] in row_ids or not isinstance(row.get('name'), str):
            raise ValueError('Invalid row')
        row_ids.add(row['id'])
        if not isinstance(row.get('cells'), dict) or not all(k in ids and isinstance(v, str) for k, v in row['cells'].items()):
            raise ValueError('Invalid cells')
        if not isinstance(row.get('muted'), list) or not all(k in ids for k in row['muted']):
            raise ValueError('Invalid muted cells')
    if table.get('reading_order') not in ('rows', 'columns') or type(table.get('speakers')) is not bool:
        raise ValueError('Invalid reading order')
    if not isinstance(table.get('speed'), (int, float)) or not .5 <= table['speed'] <= 2 or type(table.get('repeat')) is not int or not 1 <= table['repeat'] <= 10 or type(table.get('pause_ms')) is not int or not 0 <= table['pause_ms'] <= 5000:
        raise ValueError('Invalid playback settings')
    return table


def save_table(table):
    validate(table)
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('INSERT INTO custom_tables(id,name,data) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,data=excluded.data,updated_at=CURRENT_TIMESTAMP',
                     (table['id'], table['name'].strip(), json.dumps(table, ensure_ascii=False)))


def list_tables():
    with db.get_connection() as conn:
        init_tables(conn)
        return [json.loads(r['data']) for r in conn.execute('SELECT data FROM custom_tables ORDER BY name COLLATE NOCASE')]


def delete_table(ident):
    with db.get_connection() as conn:
        init_tables(conn)
        conn.execute('DELETE FROM custom_tables WHERE id=?', (ident,))


def duplicate_table(table, name):
    result = copy.deepcopy(table)
    result.update(id=uuid.uuid4().hex, name=name)
    save_table(result)
    return result


def speech_items(table, row_index=None):
    columns = sorted((c for c in table['columns'] if c['speech_order'] > 0), key=lambda c: c['speech_order'])
    rows = table['rows'] if row_index is None else table['rows'][row_index:row_index+1]
    pairs = ((r, c) for r in rows for c in columns) if table['reading_order'] == 'rows' else ((r, c) for c in columns for r in rows)
    items = [(r['cells'].get(c['id'], '').strip(), c['language']) for r, c in pairs if c['id'] not in r['muted'] and r['cells'].get(c['id'], '').strip()]
    return items * table['repeat']
