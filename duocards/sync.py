"""Offline-first card/deck sync; SQLite triggers also track imports and SRS edits."""
import ipaddress
import json
import os
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from duocards import db
from sync_server.service import CARD_FIELDS, DECK_FIELDS


class SyncError(Exception):
    pass


def normalize_url(value):
    value = value.strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        raise SyncError("Sunucu adresi https://sunucu.example veya http://192.168.1.10:8765 biçiminde olmalı.")
    local = parsed.hostname in {"localhost", "10.0.2.2"}
    try:
        address = ipaddress.ip_address(parsed.hostname)
        local = address.is_loopback or address in ipaddress.ip_network("10.0.0.0/8") or address in ipaddress.ip_network("172.16.0.0/12") or address in ipaddress.ip_network("192.168.0.0/16")
    except ValueError:
        pass
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise SyncError("İnternet sunucusu için HTTPS gerekir. HTTP yalnızca yerel ağda kullanılabilir.")
    try:
        parsed.port
    except ValueError:
        raise SyncError("Sunucu portu geçersiz.")
    return value


def init_sync_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sync_control (id INTEGER PRIMARY KEY, importing INTEGER NOT NULL DEFAULT 0);
        INSERT OR IGNORE INTO sync_control VALUES (1, 0);
        CREATE TABLE IF NOT EXISTS sync_config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sync_items (
            entity TEXT NOT NULL, local_id INTEGER NOT NULL, uuid TEXT NOT NULL UNIQUE,
            baseline TEXT NOT NULL DEFAULT '{}', revision INTEGER NOT NULL DEFAULT 0,
            dirty INTEGER NOT NULL DEFAULT 1, deleted INTEGER NOT NULL DEFAULT 0,
            generation INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(entity,local_id)
        );
        CREATE TABLE IF NOT EXISTS sync_recovery (
            id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT NOT NULL, entity TEXT NOT NULL,
            data TEXT NOT NULL, saved_at TEXT NOT NULL
        );
    """)
    for entity, table in (("deck", "decks"), ("card", "cards")):
        fields = DECK_FIELDS if entity == "deck" else (CARD_FIELDS - {"deck_uuid"}) | {"deck_id"}
        modified = " OR ".join(f"OLD.{field} IS NOT NEW.{field}" for field in sorted(fields))
        conn.executescript(f"""
            INSERT OR IGNORE INTO sync_items(entity,local_id,uuid)
                SELECT '{entity}',id,lower(hex(randomblob(16))) FROM {table};
            CREATE TRIGGER IF NOT EXISTS sync_{entity}_insert AFTER INSERT ON {table}
            WHEN (SELECT importing FROM sync_control WHERE id=1)=0 BEGIN
                INSERT INTO sync_items(entity,local_id,uuid) VALUES('{entity}',NEW.id,lower(hex(randomblob(16))));
            END;
            CREATE TRIGGER IF NOT EXISTS sync_{entity}_update AFTER UPDATE ON {table}
            WHEN (SELECT importing FROM sync_control WHERE id=1)=0 AND ({modified}) BEGIN
                UPDATE sync_items SET dirty=1,generation=generation+1 WHERE entity='{entity}' AND local_id=NEW.id;
            END;
            CREATE TRIGGER IF NOT EXISTS sync_{entity}_delete AFTER DELETE ON {table}
            WHEN (SELECT importing FROM sync_control WHERE id=1)=0 BEGIN
                UPDATE sync_items SET dirty=1,deleted=1,generation=generation+1 WHERE entity='{entity}' AND local_id=OLD.id;
            END;
        """)


def config(conn, key, default=""):
    row = conn.execute("SELECT value FROM sync_config WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_config(conn, key, value):
    conn.execute("INSERT INTO sync_config VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def payload(conn, item):
    if item["deleted"]:
        return {}
    table = "decks" if item["entity"] == "deck" else "cards"
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (item["local_id"],)).fetchone()
    if not row:
        return {}
    fields = DECK_FIELDS if item["entity"] == "deck" else CARD_FIELDS - {"deck_uuid"}
    data = {key: row[key] for key in fields}
    if item["entity"] == "card":
        deck = conn.execute("SELECT uuid FROM sync_items WHERE entity='deck' AND local_id=?", (row["deck_id"],)).fetchone()
        data["deck_uuid"] = deck[0]
    return data


class SyncClient:
    def __init__(self, session_path=None, transport=None, cloud_factory=None):
        from duocards.paths import CONFIG_DIR
        self.session_path = Path(session_path) if session_path is not None else CONFIG_DIR / "account.json"
        self.transport = transport or self._http
        self.lock = threading.Lock()
        self.cloud_factory = cloud_factory

    def _cloud(self):
        from duocards.cloud_account import FirebaseCloud
        return (self.cloud_factory or FirebaseCloud)()

    def login_google(self, cancel=None, lang='en'):
        from duocards.cloud_account import google_sign_in, load_config
        account = google_sign_in(load_config(), cancel=cancel, lang=lang)
        if cancel is not None and cancel.is_set():
            from duocards.cloud_account import CloudError
            raise CloudError('Google sign-in was canceled.')
        return self.bind_google_account(account)

    def bind_google_account(self, account):
        """Attach only the authenticated UID; migrate a legacy account of the same email."""
        if account.get('provider') != 'firebase' or not account.get('token') or not account.get('refresh_token'):
            raise SyncError('Google could not complete the request. Please try again.')
        binding = account['server'] + '|' + account['user_id']
        with self.lock, db.get_connection() as conn:
            bound = config(conn, 'account')
            old_email = config(conn, 'account_email') or self.session().get('email', '')
            migration = bool(bound and not bound.startswith('firebase:') and old_email
                             and old_email.casefold() == account['email'].casefold())
            if bound and bound != binding and not migration:
                raise SyncError('This library belongs to another Google account. Sign in with the original account.')
            if migration:
                set_config(conn, 'previous_account', bound)
                conn.execute("UPDATE sync_items SET baseline='{}',revision=0,dirty=1,generation=generation+1")
                set_config(conn, 'cursor', 0)
            self.save_session(account)
            set_config(conn, 'account', binding)
            set_config(conn, 'account_email', account['email'])
        return account

    def session(self):
        try:
            return json.loads(self.session_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_session(self, session):
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        fd, path = tempfile.mkstemp(dir=self.session_path.parent, prefix=".account-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(session, file, ensure_ascii=False)
            os.replace(path, self.session_path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @staticmethod
    def _http(url, path, body, token=""):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(url + path, json.dumps(body, ensure_ascii=False).encode(), headers)
        # Redirects can forward bearer tokens or downgrade HTTPS; never follow them.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args):
                return None
        opener = urllib.request.build_opener(NoRedirect())
        try:
            with opener.open(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                message = json.load(exc).get("error", "Sunucu isteği reddetti.")
            except (ValueError, OSError):
                message = "Sunucu isteği reddetti."
            raise SyncError(message) from exc
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise SyncError("Sunucuya ulaşılamadı. Değişiklikler cihazda saklandı; yeniden denenecek.") from exc

    def login(self, url, email, password, register=False):
        url = normalize_url(url)
        with self.lock:
            result = self.transport(url, "/v1/register" if register else "/v1/login", {"email": email, "password": password})
            binding = url + "|" + result["user_id"]
            with db.get_connection() as conn:
                bound = config(conn, "account")
                if bound and bound != binding:
                    # Do not leak this library into a different person's account.
                    try:
                        self.transport(url, "/v1/logout", {}, result["token"])
                    except Exception:
                        pass
                    raise SyncError("Bu kütüphane başka bir hesaba bağlı. Kelimelerini korumak için önce aynı hesap ve sunucu ile giriş yap.")
                set_config(conn, "account", binding)
                set_config(conn, "account_email", result['email'])
            self.save_session(dict(result, server=url))
            return result

    def logout(self):
        with self.lock:
            session = self.session()
            self.save_session({})  # Offline logout must immediately stop local synchronization.
            if session.get("token") and session.get('provider') != 'firebase':
                try:
                    self.transport(session["server"], "/v1/logout", {}, session["token"])
                except SyncError:
                    pass

    def pending_count(self):
        with db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM sync_items WHERE dirty=1").fetchone()[0]

    def sync(self):
        with self.lock:
            session = self.session()
            if not session.get("token"):
                return {"changed": False, "pending": self.pending_count()}
            if session.get('provider') == 'firebase':
                cloud = self._cloud()
                refreshed = cloud.refresh(session)
                if refreshed != session:
                    self.save_session(refreshed)
                    session = refreshed
                def exchange(body):
                    return cloud.exchange(session, body)
            else:
                normalize_url(session["server"])
                def exchange(body):
                    return self.transport(session['server'], '/v1/sync', body, session['token'])
            with db.get_connection() as conn:
                if config(conn, "account") != session["server"] + "|" + session["user_id"]:
                    raise SyncError("Oturum bu kütüphaneye ait değil. Yeniden giriş yapın.")
                cursor = int(config(conn, "cursor", "0"))
                rows = conn.execute("SELECT * FROM sync_items WHERE dirty=1 ORDER BY CASE entity WHEN 'deck' THEN 0 ELSE 1 END,local_id LIMIT 100").fetchall()
                sent, changes, size = {}, [], 0
                for row in rows:
                    full = payload(conn, row)
                    baseline = json.loads(row["baseline"])
                    patch = {k: v for k, v in full.items() if k not in baseline or baseline[k] != v}
                    change = {"entity": row["entity"], "uuid": row["uuid"], "deleted": bool(row["deleted"]), "data": patch}
                    size += len(json.dumps(change, ensure_ascii=False).encode())
                    if size > 1500000 and changes:
                        break
                    changes.append(change)
                    sent[row["uuid"]] = {"data": full, "generation": row["generation"]}
            response = exchange({"cursor": cursor, "changes": changes})
            records = {r["uuid"]: r for r in response["acknowledged"]}
            for _ in range(100):
                for record in response["records"]:
                    old = records.get(record["uuid"])
                    if not old or old["revision"] <= record["revision"]:
                        records[record["uuid"]] = record
                cursor = response["cursor"]
                if not response["has_more"]:
                    break
                response = exchange({"cursor": cursor, "changes": []})
            else:
                raise SyncError("Kütüphane çok büyük; eşitlemeyi yeniden dene.")
            with db.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("UPDATE sync_control SET importing=1 WHERE id=1")
                for record in sorted(records.values(), key=lambda r: (2 if r["entity"] == "deck" and r["deleted"] else 0 if r["entity"] == "deck" else 1, r["revision"])):
                    self._apply(conn, record, sent.get(record["uuid"]))
                conn.execute("UPDATE sync_control SET importing=0 WHERE id=1")
                set_config(conn, "cursor", cursor)
                set_config(conn, "last_sync", datetime.now().isoformat(timespec="seconds"))
            return {"changed": bool(records), "pending": self.pending_count()}

    @staticmethod
    def _apply(conn, record, sent):
        entity, uuid = record["entity"], record["uuid"]
        item = conn.execute("SELECT * FROM sync_items WHERE uuid=?", (uuid,)).fetchone()
        table = "decks" if entity == "deck" else "cards"
        remote = record["data"]
        local = payload(conn, item) if item else {}
        reference = sent["data"] if sent else json.loads(item["baseline"]) if item else {}
        pending = {k: v for k, v in local.items() if reference.get(k) != v or k not in reference} if item and item["dirty"] else {}
        dirty_delete = bool(item and item["deleted"] and (not sent or item["generation"] != sent["generation"]))
        if record["deleted"]:
            if local:
                conn.execute("INSERT INTO sync_recovery(uuid,entity,data,saved_at) VALUES(?,?,?,?)", (uuid, entity, json.dumps(local, ensure_ascii=False), datetime.now().isoformat()))
            if item:
                conn.execute(f"DELETE FROM {table} WHERE id=?", (item["local_id"],))
                # Deck deletion cascades cards; their metadata must stop being dirty as well.
                if entity == "deck":
                    conn.execute("UPDATE sync_items SET deleted=1,dirty=0 WHERE entity='card' AND local_id NOT IN (SELECT id FROM cards)")
                conn.execute("UPDATE sync_items SET baseline=?,revision=?,dirty=0,deleted=1 WHERE uuid=?", (json.dumps(remote, ensure_ascii=False), record["revision"], uuid))
            return
        if dirty_delete:
            conn.execute("UPDATE sync_items SET baseline=?,revision=? WHERE uuid=?", (json.dumps(remote, ensure_ascii=False), record["revision"], uuid))
            return
        data = dict(remote, **pending)
        fields = DECK_FIELDS if entity == "deck" else CARD_FIELDS - {"deck_uuid"}
        values = {k: data[k] for k in fields if k in data}
        if entity == "card":
            deck = conn.execute("SELECT local_id FROM sync_items WHERE entity='deck' AND uuid=? AND deleted=0", (data["deck_uuid"],)).fetchone()
            if not deck:
                raise SyncError("Kartın destesi alınamadı; eşitlemeyi tekrar dene.")
            values["deck_id"] = deck[0]
        else:
            duplicate = conn.execute("SELECT id FROM decks WHERE name=?", (values["name"],)).fetchone()
            if duplicate and (not item or duplicate[0] != item["local_id"]):
                values["name"] += " (" + uuid[-8:] + ")"
        if item:
            conn.execute(f"UPDATE {table} SET " + ",".join(k + "=?" for k in values) + " WHERE id=?", [*values.values(), item["local_id"]])
            conn.execute("UPDATE sync_items SET baseline=?,revision=?,dirty=?,deleted=0 WHERE uuid=?", (json.dumps(remote, ensure_ascii=False), record["revision"], int(bool(pending)), uuid))
        else:
            cur = conn.execute(f"INSERT INTO {table}(" + ",".join(values) + ") VALUES(" + ",".join("?" for _ in values) + ")", list(values.values()))
            conn.execute("INSERT INTO sync_items(entity,local_id,uuid,baseline,revision,dirty) VALUES(?,?,?,?,?,0)", (entity, cur.lastrowid, uuid, json.dumps(remote, ensure_ascii=False), record["revision"]))
