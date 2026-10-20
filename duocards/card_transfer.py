"""Versioned, platform-neutral card backup and validated, duplicate-aware imports."""
import csv
import io
import json
from datetime import date, datetime
from pathlib import Path
from duocards.content_rules import term_key
from duocards.languages import get_language_code

FIELDS = ['deck_name', 'term', 'definition', 'part_of_speech', 'source_lang', 'target_lang',
          'example_sentence', 'example_translation', 'phonetic', 'notes', 'is_favorite',
          'status', 'ease_factor', 'interval_days', 'repetition_count', 'due_date', 'last_reviewed']
ALIASES = dict(zip(['deste','kelime/kalıp','anlamı','kelime türü','örnek cümle', 'örnek çevirisi','fonetik','notlar','durum'],
                   ['deck_name','term','definition','part_of_speech','example_sentence','example_translation','phonetic','notes','status']))
ALIASES.update({'word':'term','meaning':'definition','kelime':'term','anlam':'definition', 'deck':'deck_name'})

def export_cards(path, format='json', deck_id=None):
    from duocards import db
    cards = db.get_all_cards(deck_id)
    rows = [{key: card.get(key, '') for key in FIELDS} for card in cards]
    if format == 'csv':
        with open(path, 'w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    else:
        decks = db.get_all_decks()
        if deck_id is not None:
            decks = [deck for deck in decks if deck['id'] == deck_id]
        Path(path).write_text(json.dumps({'version':2,'exported_at':datetime.now().isoformat(),
            'decks': [{key: d.get(key, '') for key in ('name','description','icon','color')} for d in decks],
            'cards':rows}, ensure_ascii=False, indent=2), encoding='utf-8')

def read_csv(text):
    text = text.lstrip('\ufeff')
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        return []
    headers = [ALIASES.get(term_key(value), term_key(value)) for value in rows[0]]
    has_header = 'term' in headers and 'definition' in headers
    if not has_header:
        headers = ['term','definition','example_sentence'] if len(rows[0]) <= 3 else [
            'deck_name','term','definition','part_of_speech','example_sentence','example_translation','phonetic','notes','status']
    return [dict(zip(headers, row)) for row in rows[1 if has_header else 0:] if any(row)]

def import_cards(rows, default_deck_id, source_lang='en', target_lang='tr', decks=()):
    from duocards import db
    report = {'added':0,'skipped':0,'invalid':0}
    with db.get_connection() as conn:
        if not conn.execute('SELECT 1 FROM decks WHERE id=?', (default_deck_id,)).fetchone():
            raise ValueError('Please select a deck.')
        known = {(term_key(r['term']), get_language_code(r['source_lang']), get_language_code(r['target_lang']))
                 for r in conn.execute('SELECT term,source_lang,target_lang FROM cards')}
        deck_map = {r['name']:r['id'] for r in conn.execute('SELECT id,name FROM decks')}
        definitions = {d.get('name'):d for d in decks if isinstance(d, dict)}
        for name, info in definitions.items():
            if isinstance(name,str) and name.strip() and name not in deck_map:
                cur=conn.execute('INSERT INTO decks(name,description,icon,color) VALUES (?,?,?,?)',
                    (name, str(info.get('description') or ''), str(info.get('icon') or ''), str(info.get('color') or '#10b981')))
                deck_map[name]=cur.lastrowid
        for row in rows:
            if not isinstance(row, dict):
                report['invalid'] += 1
                continue
            def value(key, fallback=''):
                raw = row.get(key, fallback)
                return str(raw if raw is not None else fallback).strip()
            term, definition = value('term'), value('definition')
            src, tgt = get_language_code((value('source_lang') or source_lang)), get_language_code((value('target_lang') or target_lang))
            if not term or not definition or len(term)>500 or len(definition)>5000:
                report['invalid'] += 1
                continue
            key = (term_key(term),src,tgt)
            if key in known:
                report['skipped'] += 1
                continue
            try:
                ease = max(1.3, min(5.,float(value('ease_factor') or 2.5)))
                interval = max(0,int(value('interval_days') or 0))
                reps = max(0,int(value('repetition_count') or 0))
                due = value('due_date') or date.today().isoformat()
                date.fromisoformat(due)
                favorite = int(value('is_favorite').lower() in ('1','true','yes'))
                status = value('status') or 'new'
                if status not in ('new','learning','mastered'):
                    raise ValueError('status')
            except (ValueError, OverflowError):
                report['invalid'] += 1
                continue
            deck_name = value('deck_name')
            if deck_name and deck_name not in deck_map:
                info = definitions.get(deck_name,{})
                cur = conn.execute('INSERT INTO decks(name,description,icon,color) VALUES (?,?,?,?)',
                    (deck_name, info.get('description',''), info.get('icon',''),info.get('color','#10b981')))
                deck_map[deck_name] = cur.lastrowid
            fields = FIELDS[1:]
            data = {f:value(f) for f in fields}
            data.update(source_lang=src,target_lang=tgt,status=status,ease_factor=ease,interval_days=interval,
                        repetition_count=reps,due_date=due,is_favorite=favorite,part_of_speech=value('part_of_speech') or 'word')
            conn.execute('INSERT INTO cards(deck_id,'+','.join(fields)+') VALUES ('+','.join('?' for _ in range(len(fields)+1))+')',
                         [deck_map.get(deck_name,default_deck_id)]+[data[f] for f in fields])
            known.add(key)
            report['added'] += 1
        conn.commit()
    return report

def import_file(path, default_deck_id, source_lang='en', target_lang='tr'):
    text = Path(path).read_text(encoding='utf-8-sig')
    if Path(path).suffix.lower() == '.json':
        data = json.loads(text)
        if not isinstance(data, dict) or data.get('version',1) not in (1,2) or not isinstance(data.get('cards'),list):
            raise ValueError('Unsupported card backup.')
        deck_names = {d.get('id'):d.get('name','') for d in data.get('decks',[]) if isinstance(d,dict)}
        rows = [dict(row, deck_name=row.get('deck_name',deck_names.get(row.get('deck_id'),''))) if isinstance(row,dict) else row for row in data['cards']]
        return import_cards(rows,default_deck_id,source_lang,target_lang,data.get('decks',[]))
    return import_cards(read_csv(text),default_deck_id,source_lang,target_lang)
