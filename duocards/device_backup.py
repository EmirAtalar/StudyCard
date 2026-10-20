"""Versioned offline backups with full SQLite history and atomic restoration."""
import json
import os
import sqlite3
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from duocards import db
from duocards.settings import settings, SETTINGS_FILE

MAX_SIZE = 256 * 1024 * 1024
EXCLUDED_SETTINGS = ('google_', 'firebase_', 'sync_', 'cloud_', 'ai_', 'ollama_')


@contextmanager
def _sqlite(path):
    connection = sqlite3.connect(path)
    try:
        yield connection
    finally:
        connection.close()


def validate_preferences(values):
    import re
    from duocards.settings import DEFAULT_SETTINGS
    for key, value in values.items():
        default = DEFAULT_SETTINGS.get(key)
        if default is not None and (type(default) is bool and type(value) is not bool or type(default) is str and not isinstance(value, str)):
            raise ValueError('Invalid backup preferences')
        if key.startswith(('personal_menu_','menu_visible_','plugin_')) and type(value) is not bool:
            raise ValueError('Invalid backup menu preferences')
    bounds = dict(text_scale=(90,130), speech_speed=(.5,2), speech_volume=(0,100), sfx_volume=(0,100), daily_goal=(5,100), session_size=(5,200), practice_advance_ms=(300,5000))
    for key, (low, high) in bounds.items():
        if key in values and (type(values[key]) not in ((int,float) if key == 'speech_speed' else (int,)) or not low <= values[key] <= high):
            raise ValueError('Invalid backup preferences')
    if 'notification_time' in values and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', values['notification_time']):
        raise ValueError('Invalid backup preferences')
    choices = dict(ui_language=('tr','en','de','es'), theme=('dark_slate','midnight','graphite'), startup_page=('study','library','tables','stats','import','settings'), pronounce_trigger=('flip','appear','both'), accent_color=('#10b981','#38bdf8','#a78bfa','#fbbf24','#fb7185'))
    for key, options in choices.items():
        if key in values and values[key] not in options:
            raise ValueError('Invalid backup preferences')


def portable_settings():
    return {k: v for k, v in settings.get_all().items() if not k.startswith(EXCLUDED_SETTINGS) and k not in ('autostart_enabled', 'app_shortcut')}


def export_backup(path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='studycard-backup-') as tmp:
        snapshot = Path(tmp) / 'library.sqlite'
        with db.get_connection() as source, _sqlite(snapshot) as target:
            source.backup(target)
        with _sqlite(snapshot) as conn:
            counts = {name: conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in ('cards', 'decks', 'study_logs', 'timer_sessions', 'practice_attempts')}
        manifest = dict(format='studycard-device-backup', version=1, created_at=datetime.now(timezone.utc).isoformat(), counts=counts)
        fd, temporary = tempfile.mkstemp(prefix='.studycard-', dir=destination.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot, 'library.sqlite')
                archive.writestr('manifest.json', json.dumps(manifest))
                archive.writestr('settings.json', json.dumps(portable_settings(), ensure_ascii=False))
            os.replace(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return manifest


def _extract(path, directory):
    try:
        with zipfile.ZipFile(path) as archive:
            if len(archive.infolist()) != 3 or set(archive.namelist()) != {'library.sqlite', 'settings.json', 'manifest.json'} or any(i.file_size > (MAX_SIZE if i.filename == 'library.sqlite' else 1024*1024) for i in archive.infolist()):
                raise ValueError('Invalid backup contents')
            manifest = json.loads(archive.read('manifest.json'))
            values = json.loads(archive.read('settings.json'))
            if not isinstance(manifest, dict) or manifest.get('format') != 'studycard-device-backup' or manifest.get('version') != 1 or not isinstance(values, dict):
                raise ValueError('Unsupported backup format')
            validate_preferences(values)
            database = Path(directory) / 'library.sqlite'
            database.write_bytes(archive.read('library.sqlite'))
        with _sqlite(database) as conn:
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Damaged backup database')
            schema = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'cards', 'decks', 'study_logs', 'timer_sessions', 'practice_attempts'}.issubset(schema):
                raise ValueError('Incomplete backup database')
            required = dict(cards={'id','deck_id','term','definition','part_of_speech','source_lang','target_lang','example_sentence','example_translation','phonetic','notes','status','is_favorite','repetition_count','interval_days','ease_factor','due_date','last_reviewed','created_at'},
                            decks={'id','name','description','icon','color','created_at'},
                            study_logs={'id','card_id','rating','reviewed_at'},
                            timer_sessions={'id','mode','duration_seconds','notes','created_at'},
                            practice_attempts={'id','card_id','mode','correct','answer','expected','practiced_at','day'})
            for name, expected in required.items():
                if not expected.issubset({r[1] for r in conn.execute(f'PRAGMA table_info({name})')}):
                    raise ValueError('Incomplete backup database')
            for name in ('cards', 'decks', 'study_logs', 'timer_sessions', 'practice_attempts'):
                if conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] != manifest['counts'][name]:
                    raise ValueError('Backup counts do not match')
            if 'custom_tables' in schema:
                from duocards.custom_tables import validate
                for row in conn.execute('SELECT data FROM custom_tables'):
                    validate(json.loads(row[0]))
            if 'custom_games' in schema:
                from duocards.custom_games import validate as validate_game
                for row in conn.execute('SELECT data FROM custom_games'):
                    validate_game(json.loads(row[0]))
        return manifest, values, database
    except (zipfile.BadZipFile, sqlite3.DatabaseError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid Studycard backup') from exc


def inspect_backup(path):
    with tempfile.TemporaryDirectory(prefix='studycard-check-') as tmp:
        return _extract(path, tmp)[0]


def restore_backup(path):
    """Validate before touching data; save a recovery archive before replacement."""
    with tempfile.TemporaryDirectory(prefix='studycard-restore-', dir=db.DB_DIR) as tmp:
        manifest, values, snapshot = _extract(path, tmp)
        from duocards.sentence_memory import invalidate_requests
        invalidate_requests()
        recovery = Path(db.DB_DIR) / 'backups' / ('before-restore-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.studycard')
        export_backup(recovery)
        original = settings.get_all()
        settings_path = Path(SETTINGS_FILE)
        original_bytes = settings_path.read_bytes() if settings_path.exists() else None
        try:
            for key in list(settings._settings):
                if key.startswith(('personal_menu_','menu_visible_','plugin_')):
                    settings._settings.pop(key)
            settings._settings.update({k: v for k, v in values.items() if not k.startswith(EXCLUDED_SETTINGS) and k not in ('autostart_enabled', 'app_shortcut')})
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            pending = Path(tmp) / 'settings.json'
            pending.write_text(json.dumps(settings.get_all(), ensure_ascii=False, indent=2), encoding='utf-8')
            with _sqlite(snapshot) as source, db.get_connection() as target:
                source.backup(target)
            os.replace(pending, settings_path)
        except Exception:
            with tempfile.TemporaryDirectory(dir=db.DB_DIR) as rollback:
                _, _, old_db = _extract(recovery, rollback)
                with _sqlite(old_db) as source, db.get_connection() as target:
                    source.backup(target)
            settings._settings = original
            if original_bytes is not None:
                settings_path.write_bytes(original_bytes)
            else:
                settings_path.unlink(missing_ok=True)
            raise
    return manifest, str(recovery)
