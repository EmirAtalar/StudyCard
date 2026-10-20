"""Kalıcı cümle hafızası ve kaynaklı, çeşitli kullanım örnekleri; AI kullanmaz."""
import json
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
import socket
from pathlib import Path
from duocards.languages import get_language_code, detect_card_term_language
from duocards.sentence_templates import TEMPLATES
from duocards.offline_examples import examples as offline_examples, canonical
from duocards.content_rules import useful_sentence

ISO3 = dict(zip(
    'en tr de fr es it pt ru ja ko zh ar hi nl sv el pl uk fa he cs ro hu da fi no bg sr hr sk sl ca eu gl ga cy is lt lv et ka hy mn sq mk bs sw af la th vi id ms bn ur ta te mr gu kn ml ne si km lo my am zu xh yo ig ha so eo'.split(),
    'eng tur deu fra spa ita por rus jpn kor cmn ara hin nld swe ell pol ukr pes heb ces ron hun dan fin nob bul srp hrv slk slv cat eus glg gle cym isl lit lav est kat hye mon sqi mkd bos swa afr lat tha vie ind msa ben urd tam tel mar guj kan mal nep sin khm lao mya amh zul xho yor ibo hau som epo'.split()))
ISO3.update({'zh-tw':'cmn','tl':'tgl','az':'aze','kk':'kaz','uz':'uzb','ky':'kir','tk':'tuk','tt':'tat','yi':'yid'})
_PUNCTUATION = str.maketrans({'’':"'",'‘':"'",'ʼ':"'",'‐':'-','‑':'-','–':'-'})
_pending = set()
_guard = threading.Lock()
_slots = threading.Semaphore(2)
_local = None
_request_generation = 0


def invalidate_requests():
    global _request_generation
    with _guard:
        _request_generation += 1


def word_key(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def card_language(card):
    return get_language_code(card['source_lang']) if card.get('source_lang') else detect_card_term_language(card)


def term_pattern(term, lang='en'):
    # CJK metinlerinde sözcükler boşlukla ayrılmayabilir.
    term=canonical(term,lang)
    chunks=re.split(r'\s*(?:\.{2,}|…|\[.*?\])\s*',term)
    def escape(token):
        return re.escape(token.translate(_PUNCTUATION)).replace("'", "['’‘ʼ]").replace(r'\-', '[-‐‑–]')
    escaped=r'.{1,100}?'.join(r'\s+'.join(escape(p) for p in chunk.split()) for chunk in chunks)
    if lang in ('zh', 'zh-tw', 'ja'):
        return re.compile(escaped, re.IGNORECASE)
    return re.compile(r'(?<!\w)' + escaped + r'(?!\w)', re.IGNORECASE)


def _connection():
    from duocards.db import get_connection
    return get_connection()


def init_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS sentence_memory (
        lang TEXT NOT NULL, term_key TEXT NOT NULL, position INTEGER NOT NULL,
        text TEXT NOT NULL, translations TEXT NOT NULL DEFAULT '{}',
        kind TEXT NOT NULL, source TEXT NOT NULL, url TEXT NOT NULL DEFAULT '',
        author TEXT NOT NULL DEFAULT '', license TEXT NOT NULL DEFAULT '',
        PRIMARY KEY(lang, term_key, position))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sentence_fetches (
        lang TEXT NOT NULL, term_key TEXT NOT NULL, attempted REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'local', error TEXT NOT NULL DEFAULT '',
        PRIMARY KEY(lang, term_key))''')


def _local_index():
    global _local
    with _guard:
        if _local is not None:
            return _local
        index = {}
        from duocards.authentic_sentences import AUTHENTIC_SENTENCES_MAP
        from duocards.word_data import FULL_200_WORDS
        def add(lang, term, text, translations):
            if useful_sentence(term, text, lang):
                index.setdefault((lang, word_key(term)), []).append(dict(
                    text=text, translations=translations, kind='example', source='local'))
        for term, (text, tr) in AUTHENTIC_SENTENCES_MAP.items():
            add('en', term, text, {'tr': tr})
        for item in FULL_200_WORDS:
            add('en', item[0], item[3], {'tr': item[4]})
        for path in sorted((Path(__file__).parent/'data').glob('*.json')):
            if path.name in ('offline_usage.json','ui_catalog.json'):
                continue
            lang = path.name.split('_')[0]
            try:
                items=json.loads(path.read_text())
                if not isinstance(items,list): continue
                for item in items:
                    if not isinstance(item,dict): continue
                    # Paket çevirileri kelimeye aittir, cümle çevirisi değildir.
                    add(lang, item.get('term', ''), item.get('example', ''), {})
            except (ValueError, TypeError, KeyError):
                continue
        _local = index
        return index


def _read(conn, lang, term):
    rows = conn.execute('SELECT * FROM sentence_memory WHERE lang=? AND term_key=? ORDER BY position',
                        (lang, word_key(term))).fetchall()
    return [dict(row, translations=json.loads(row['translations'])) for row in rows
            if row['kind'] == 'example' and useful_sentence(term, row['text'], lang)]


def available_examples(cards, cancelled):
    """Read a practice pool in one connection, without writes or network requests."""
    with _connection() as conn:
        for card in cards:
            if cancelled.is_set():
                return
            term, lang = card['term'], card_language(card)
            manual = (card.get('example_sentence') or '').strip()
            if manual and useful_sentence(term, manual, lang):
                yield card, [dict(text=manual, translations={get_language_code(card.get('target_lang', 'tr')): card.get('example_translation') or ''}, kind='example')]
                continue
            rows = _read(conn, lang, term)
            if not rows:
                rows = _local_index().get((lang, word_key(term)), []) + offline_examples(term, lang)
            yield card, [r for r in rows if r.get('kind') == 'example' and useful_sentence(term, r['text'], lang)]


def _store(conn, lang, term, candidates):
    seen, selected = set(), []
    for item in candidates:
        key = word_key(item['text'])
        if key in seen or item.get('kind', 'example') != 'example' or not useful_sentence(term, item['text'], lang):
            continue
        seen.add(key)
        selected.append(item)
        if len(selected) == 10:
            break
    conn.execute('DELETE FROM sentence_memory WHERE lang=? AND term_key=?', (lang, word_key(term)))
    for pos, item in enumerate(selected):
        conn.execute('INSERT INTO sentence_memory VALUES (?,?,?,?,?,?,?,?,?,?)',
            (lang, word_key(term), pos, item['text'], json.dumps(item.get('translations', {}), ensure_ascii=False),
             item.get('kind', 'example'), item.get('source', 'local'), item.get('url', ''),
             item.get('author', ''), item.get('license', '')))
    return selected


def ensure_examples(card):
    term = (card.get('term') or '').strip()
    if not term:
        return []
    lang = card_language(card)
    candidates = []
    manual = (card.get('example_sentence') or '').strip()
    if manual and term_pattern(term, lang).search(manual):
        translation = (card.get('example_translation') or '').strip()
        candidates.append(dict(text=manual, translations={get_language_code(card.get('target_lang', 'tr')): translation}
                               if translation else {}, kind='example', source='user'))
    local_candidates = _local_index().get((lang, word_key(term)), [])
    generated=offline_examples(term,lang)
    conn = _connection()
    try:
        init_tables(conn)
        conn.execute("BEGIN IMMEDIATE")
        existing = _read(conn, lang, term)
        if len(existing) == 10 and (not generated or (all(row['kind']=='example' for row in existing) and all(row['source']!='offline_example' or row['text'] in {r['text'] for r in generated} for row in existing))) and (not candidates or any(row["text"] == candidates[0]["text"] and row["translations"] == candidates[0]["translations"] for row in existing)):
            conn.rollback()
            return existing
        candidates += [row for row in existing if row['kind'] == 'example' and (row['source']!='offline_example' or not generated)]
        candidates += local_candidates
        candidates += generated
        candidates += [row for row in existing if row['kind'] == 'practice']
        candidates += [dict(text=template.format(word=term), translations={}, kind='practice', source='practice')
                       for template in TEMPLATES.get(lang, '').split('|') if template]
        result = _store(conn, lang, term, candidates)
        conn.commit()
        return result
    finally:
        conn.close()


def _load_json(url):
    req=urllib.request.Request(url, headers={
        'User-Agent':'StudyCard/3.0 (Desktop vocabulary learning application)',
        'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=8) as response:
        payload=response.read(2_000_001)
    if len(payload)>2_000_000:
        raise ValueError('response_too_large')
    data=json.loads(payload)
    if not isinstance(data,(dict,list)):
        raise ValueError('invalid_provider_response')
    if isinstance(data,dict) and data.get('error'):
        raise ValueError('provider_error')
    return data


def _tatoeba_rows(items,term,lang,target,legacy=False):
    rows=[]
    pattern=term_pattern(term,lang)
    if not isinstance(items,list):
        return rows
    for item in items or []:
        if not isinstance(item,dict):
            continue
        sentence=item.get('text')
        if not isinstance(sentence,str):
            continue
        sentence=sentence.strip()
        if (item.get('lang')!=ISO3[lang] or not 3<=len(sentence)<=500
            or item.get('is_unapproved') or not pattern.search(sentence)):
            continue
        try:
            ident=int(item['id'])
        except (KeyError,TypeError,ValueError):
            continue
        translations={}
        credits=[]
        for group in item.get('translations') or []:
            for tr in (group if isinstance(group,list) else [group]):
                if not isinstance(tr,dict) or tr.get('lang')!=ISO3.get(target) or not isinstance(tr.get('text'),str) or not tr['text'].strip() or tr.get('is_unapproved'):
                    continue
                if target in translations:
                    continue
                translations[target]=tr['text'].strip()
                translator=tr.get('owner') or tr.get('user') or ''
                if isinstance(translator,dict):
                    translator=translator.get('username','')
                if translator:
                    credits.append(str(translator)+' · '+str(tr.get('license') or '')+' · https://tatoeba.org/en/sentences/show/'+str(tr.get('id','')))
        owner=item.get('owner') or item.get('user') or ''
        if isinstance(owner,dict):
            owner=owner.get('username','')
        author='; '.join([str(owner)]+credits).strip('; ')
        rows.append(dict(text=sentence,translations=translations,kind='example',source='tatoeba',
                         url=f'https://tatoeba.org/en/sentences/show/{ident}',author=author,
                         license=item.get('license') or ''))
    return rows


def _query_chunks(term,lang):
    clean=canonical(term,lang).translate(_PUNCTUATION)
    return [c.strip() for c in re.split(r'\.{2,}|…|\[.*?\]',clean) if c.strip()]


def _fetch_tatoeba(term, lang, target='tr'):
    if lang not in ISO3:
        return []
    chunks=_query_chunks(term,lang)
    if not chunks:
        return []
    query=' '.join(chr(34)+c.replace(chr(92),chr(92)*2).replace(chr(34),chr(92)+chr(34))+chr(34) for c in chunks)
    params={'q':query,'sort':'relevance','lang':ISO3[lang],'limit':50,
            'is_unapproved':'no','is_orphan':'no'}
    if target in ISO3:
        params['showtrans:lang']=ISO3[target]
    # Relevance sorts exact matches by shortest first. Gather context before
    # relaxing length; never require a translation, which excludes rare words.
    contextual=dict(params,word_count='12-80' if lang in ('zh','zh-tw','ja') else '8-35')
    simple=dict(params,q=' '.join(chunks))
    rows=[]
    seen=set()
    visited=set()
    errors=[]
    succeeded=False
    retry_simple=False
    for variant in (contextual,params,simple):
        if retry_simple and variant is params:
            continue
        url='https://api.tatoeba.org/v1/sentences?'+urllib.parse.urlencode(variant)
        pages=0
        # Reserve requests for both relaxed queries even if the first search
        # returns many pages that fail the exact-word validation.
        page_limit=2 if variant is contextual else 1
        while url and url not in visited and len(visited)<4 and pages<page_limit:
            visited.add(url)
            pages+=1
            try:
                data=_load_json(url)
                if not isinstance(data,dict) or not isinstance(data.get('data'),list):
                    raise ValueError('invalid_provider_response')
            except urllib.error.HTTPError as exc:
                errors.append(exc)
                code=exc.code
                exc.close()
                if code==400:
                    retry_simple=True
                    break  # Retry with fewer query constraints.
                if rows:
                    return rows
                raise
            except Exception:
                if rows:
                    return rows
                raise
            succeeded=True
            for row in _tatoeba_rows(data['data'],term,lang,target):
                key=word_key(row['text'])
                if key not in seen:
                    rows.append(row)
                    seen.add(key)
            if len(rows)>=40:
                return rows
            paging=data.get('paging') or {}
            next_url=paging.get('next') if isinstance(paging,dict) else None
            if not isinstance(next_url,str) or not next_url:
                break
            candidate=urllib.parse.urljoin(url,next_url)
            parsed=urllib.parse.urlparse(candidate)
            if parsed.scheme!='https' or parsed.netloc!='api.tatoeba.org' or parsed.path!='/v1/sentences':
                break
            url=candidate
        if len(rows)>=10 or len(visited)>=4:
            break
    if not succeeded and errors:
        raise errors[0]
    return rows


def _fetch_legacy(term, lang, target):
    # Deprecated endpoint: compatibility fallback only, without requiring a translation.
    params={'from':ISO3[lang],'query':canonical(term,lang),'to':'und'}
    data=_load_json('https://tatoeba.org/en/api_v0/search?'+urllib.parse.urlencode(params))
    if not isinstance(data,dict) or not isinstance(data.get('results'),list):
        raise ValueError('invalid_provider_response')
    return _tatoeba_rows(data.get('results',[]),term,lang,target,legacy=True)


def _fetch_wikipedia(term,lang,target='tr'):
    """Use complete same-language article sentences if teaching corpora are sparse."""
    wiki_lang={'zh-tw':'zh','he':'he','yi':'yi'}.get(lang,lang)
    if not re.fullmatch(r'[a-z]{2,3}',wiki_lang):
        return []
    params={'action':'query','generator':'search','gsrsearch':' '.join('"'+c.replace('"','')+'"' for c in _query_chunks(term,lang)),
            'gsrnamespace':0,'gsrlimit':10,'prop':'extracts|info','inprop':'url',
            'explaintext':1,'exintro':1,'exlimit':10,'exchars':1200,
            'format':'json','formatversion':2,'maxlag':5}
    data=_load_json(f'https://{wiki_lang}.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params))
    if not isinstance(data,dict):
        raise ValueError('invalid_provider_response')
    rows=[]
    for page in (data.get('query') or {}).get('pages',[]):
        if not isinstance(page,dict) or page.get('missing') or not page.get('extract'):
            continue
        # Extract complete sentences only; exclude truncated last sentences and headings.
        for paragraph in page['extract'].splitlines():
            for sentence in re.findall(r'[^.!?。！？]+[.!?。！？]+',paragraph):
                sentence=sentence.strip()
                if not 15<=len(sentence)<=500 or sentence.endswith(('…','...')) or not term_pattern(term,lang).search(sentence):
                    continue
                # TextExtracts can split common abbreviations; avoid tiny fragments.
                if lang not in ('zh','zh-tw','ja') and len(sentence.split())<4:
                    continue
                source_url=page.get('fullurl') or f'https://{wiki_lang}.wikipedia.org/?curid={int(page["pageid"])}'
                rows.append(dict(text=sentence,translations={},kind='example',source='wikipedia',
                                 url=source_url,author=page.get('title','')+' · Wikipedia contributors',
                                 license='CC BY-SA 4.0 · https://creativecommons.org/licenses/by-sa/4.0/'))
    return rows


def _fetch_dictionary(term):
    url='https://api.dictionaryapi.dev/api/v2/entries/en/'+urllib.parse.quote(canonical(term,'en'),safe='')
    data=_load_json(url)
    rows=[]
    if not isinstance(data,list):
        return rows
    for entry in data:
        for meaning in entry.get('meanings',[]):
            for definition in meaning.get('definitions',[]):
                sentence=definition.get('example','').strip()
                if sentence and term_pattern(term,'en').search(sentence):
                    license_info=entry.get('license') or {}
                    rows.append(dict(text=sentence,translations={},kind='example',source='dictionary',
                                     url=url,author='Free Dictionary API',license=license_info.get('name','')))
    return rows


def _example_score(row,lang,target):
    text=row['text']
    count=len(text) if lang in ('zh','zh-tw','ja') else len(text.split())
    low,high=(12,80) if lang in ('zh','zh-tw','ja') else (8,35)
    if count<low:
        score=max(-6,8-(low-count)*2)
    elif count>high:
        score=max(-6,8-(count-high)*.4)
    else:
        score=8
    if row.get('translations',{}).get(target):
        score+=3
    if row.get('source') in ('tatoeba','dictionary'):
        score+=1
    if text.endswith(('…','...')):
        score-=8
    return score


def _select_online_examples(rows,term,lang,target='tr',limit=10):
    """Prefer readable context and translations, then reduce repeated wording.

    Similar examples remain available when a rare term has few matches. Exact
    duplicates merge their translations instead of losing useful metadata.
    """
    pattern=term_pattern(term,lang)
    unique={}
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('text'),str):
            continue
        text=' '.join(row['text'].split())
        if not useful_sentence(term, text, lang):
            continue
        key=word_key(text).translate(_PUNCTUATION).rstrip('.!?。！？')
        translations=row.get('translations') or {}
        translations={k:v for k,v in translations.items() if isinstance(v,str) and v.strip()} if isinstance(translations,dict) else {}
        candidate=dict(row,text=text,translations=translations)
        if key in unique:
            old=unique[key]
            merged={**translations,**old['translations']}
            if _example_score(candidate,lang,target)>_example_score(old,lang,target):
                unique[key]=candidate
            unique[key]['translations']=merged
        else:
            unique[key]=candidate
    candidates=list(unique.values())
    # Removing the target word prevents its presence from inflating similarity.
    def features(row):
        context=word_key(pattern.sub(' ',row['text']))
        if lang in ('zh','zh-tw','ja'):
            return {context[i:i+2] for i in range(len(context)-1)}
        return set(re.findall(r'[^\W\d_]+',context))
    tokens={id(row):features(row) for row in candidates}
    selected=[]
    def score(row):
        words=tokens[id(row)]
        similarity=max((2*len(words & tokens[id(other)])/max(1,len(words)+len(tokens[id(other)])) for other in selected),default=0)
        return _example_score(row,lang,target)-8*similarity
    while candidates and len(selected)<limit:
        best=max(candidates,key=score)
        selected.append(best)
        candidates.remove(best)
    return selected


def fetch_corpus(term, lang, target='tr'):
    if lang not in ISO3:
        raise ValueError('unsupported_language')
    errors=[]
    succeeded=False
    collected=[]
    providers=[lambda:_fetch_tatoeba(term,lang,target)]
    if lang=='en':
        providers.append(lambda:_fetch_dictionary(term))
    providers.extend((lambda:_fetch_wikipedia(term,lang,target),lambda:_fetch_legacy(term,lang,target)))
    for fetch in providers:
        try:
            collected.extend(fetch())
            succeeded=True
            selected=_select_online_examples(collected,term,lang,target)
            if len(selected)==10 and all(_example_score(row,lang,target)>=8 for row in selected):
                return selected
        except urllib.error.HTTPError as exc:
            # A dictionary 404 is an absent entry; corpus outages still remain errors.
            errors.append(exc)
        except Exception as exc:
            errors.append(exc)
    if collected or succeeded:
        return _select_online_examples(collected,term,lang,target)
    if errors:
        raise errors[0]
    return []


def _error_code(exc):
    if isinstance(exc,urllib.error.HTTPError):
        return 'http_'+str(exc.code)
    reason=getattr(exc,'reason',exc)
    if isinstance(reason,socket.gaierror):
        return 'dns'
    if isinstance(reason,(TimeoutError,socket.timeout)):
        return 'timeout'
    if str(exc)=='unsupported_language':
        return 'unsupported'
    if isinstance(exc,urllib.error.URLError):
        return 'connection'
    return 'service'


def is_usage_example(row):
    return row.get('kind')=='example' and row.get('source') not in ('offline_example','practice')


def _sync_card_examples(conn, lang, term, rows):
    """Replace blank/trivial examples on cards still matching this word and language.

    Re-read cards inside the transaction: users may edit/delete a card while an
    online request is running. Contextual manual examples and SRS state are preserved.
    """
    usable=[r for r in rows if is_usage_example(r) and useful_sentence(term, r['text'], lang)]
    if not usable:
        return
    for stored in conn.execute("SELECT id,term,source_lang,target_lang,example_sentence FROM cards ").fetchall():
        card=dict(stored)
        if canonical(card['term'],card_language(card))!=canonical(term,lang) or card_language(card)!=lang:
            continue
        previous=card.get('example_sentence') or ''
        if useful_sentence(term,previous,lang): continue
        target=get_language_code(card.get('target_lang') or 'tr')
        example=next((r for r in usable if r.get('translations',{}).get(target)),usable[0])
        conn.execute("UPDATE cards SET example_sentence=?,example_translation=? WHERE id=? AND COALESCE(example_sentence,'')=?",
                     (example['text'],example.get('translations',{}).get(target,''),card['id'],previous))

def request_examples(card, force=False):
    """UI'yi bekletmeden örnekleri zenginleştirir; aynı kelime için tek iş."""
    card=dict(card)
    rows = ensure_examples(card)
    lang, term = card_language(card), card.get('term', '').strip()
    with _connection() as conn:
        _sync_card_examples(conn,lang,term,rows)
    if not term or (sum(is_usage_example(row) for row in rows) >= 10 and not force):
        return rows
    from duocards.db import DB_PATH
    key = (DB_PATH, lang, word_key(term))
    generation = _request_generation
    conn = _connection()
    try:
        status = conn.execute('SELECT attempted,status FROM sentence_fetches WHERE lang=? AND term_key=?',
                              (lang, word_key(term))).fetchone()
        if status and status['status'] != 'loading' and time.time() - status['attempted'] < (60 if status['status'] == 'offline' else 86400) and not force:
            return rows
        with _guard:
            if key in _pending:
                return rows
            if len(_pending) >= 64:
                conn.execute('INSERT OR REPLACE INTO sentence_fetches VALUES (?,?,?,?,?)',
                             (lang,word_key(term),time.time(),'offline','busy'))
                conn.commit()
                return rows
            _pending.add(key)
        conn.execute('INSERT OR REPLACE INTO sentence_fetches VALUES (?,?,?,?,?)',
                     (lang, word_key(term), time.time(), 'loading', ''))
        conn.commit()
    except Exception:
        with _guard:
            _pending.discard(key)
        raise
    finally:
        conn.close()
    # Sabit veritabanı yolu: test/çalışma alanı değişiminde başka veriyi etkilemez.
    def worker():
        import sqlite3
        try:
            with _slots:
                if generation != _request_generation:
                    return
                candidates = fetch_corpus(term, lang, get_language_code(card.get('target_lang', 'tr')))
            if generation != _request_generation:
                return
            connection = sqlite3.connect(DB_PATH, timeout=10)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("BEGIN IMMEDIATE")
                if generation != _request_generation:
                    return
                existing = _read(connection, lang, term)
                online = _select_online_examples(candidates + [r for r in existing if r['source'] in ('tatoeba','dictionary','wikipedia')],
                                                 term,lang,get_language_code(card.get('target_lang') or 'tr'))
                ordered = ([r for r in existing if r['source'] == 'user'] + online +
                           [r for r in existing if r['kind'] == 'example' and r['source'] not in ('user','tatoeba','dictionary','wikipedia')] +
                           [r for r in existing if r['kind'] == 'practice'])
                selected = _store(connection, lang, term, ordered)
                _sync_card_examples(connection,lang,term,selected)
                state = 'ready' if sum(is_usage_example(r) for r in selected) == 10 else 'partial'
                connection.execute('UPDATE sentence_fetches SET status=?,error=? WHERE lang=? AND term_key=?',
                                   (state, '', lang, word_key(term)))
                connection.commit()
            finally:
                connection.close()
        except Exception as exc:
            connection=None
            try:
                if generation != _request_generation:
                    return
                connection = sqlite3.connect(DB_PATH, timeout=10)
                connection.execute('UPDATE sentence_fetches SET status=?,error=? WHERE lang=? AND term_key=?',
                                   ('offline', _error_code(exc), lang, word_key(term)))
                connection.commit()
            except Exception:
                pass
            finally:
                if connection is not None:
                    connection.close()
        finally:
            with _guard:
                _pending.discard(key)
    try:
        threading.Thread(target=worker, daemon=True).start()
    except RuntimeError:
        with _guard:
            _pending.discard(key)
        with _connection() as conn:
            conn.execute('UPDATE sentence_fetches SET status=?,error=? WHERE lang=? AND term_key=?',
                         ('offline','busy',lang,word_key(term)))
        raise
    return rows


def fetch_status(card):
    conn = _connection()
    try:
        init_tables(conn)
        row = conn.execute('SELECT status FROM sentence_fetches WHERE lang=? AND term_key=?',
                           (card_language(card), word_key(card.get('term', '')))).fetchone()
        return row['status'] if row else 'local'
    finally:
        conn.close()



def fetch_error(card):
    with _connection() as conn:
        init_tables(conn)
        row=conn.execute('SELECT error FROM sentence_fetches WHERE lang=? AND term_key=?',
                         (card_language(card),word_key(card.get('term','')))).fetchone()
        return row['error'] if row else ''

def read_examples(card):
    conn=_connection()
    try:
        init_tables(conn)
        rows=_read(conn,card_language(card),card.get('term',''))
    finally:
        conn.close()
    return rows or ensure_examples(card)


def add_example(card, sentence, translation=''):
    sentence=sentence.strip()
    lang=card_language(card)
    if not useful_sentence(card['term'],sentence,lang):
        raise ValueError('usage_sentence_too_short')
    ensure_examples(card)
    row=dict(text=sentence,translations={get_language_code(card.get('target_lang','tr')):translation}
             if translation.strip() else {},kind='example',source='user')
    conn=_connection()
    try:
        conn.execute('BEGIN IMMEDIATE')
        rows=_read(conn,lang,card['term'])
        _store(conn,lang,card['term'],[row]+rows)
        conn.commit()
    finally:
        conn.close()
