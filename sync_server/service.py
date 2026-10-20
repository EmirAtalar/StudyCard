"""SQLite-backed account service. No desktop or Android dependencies."""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import date

DECK_FIELDS = {"name", "description", "icon", "color", "created_at"}
CARD_FIELDS = {
    "deck_uuid", "term", "definition", "part_of_speech", "example_sentence",
    "example_translation", "phonetic", "notes", "target_lang", "source_lang",
    "status", "is_favorite", "repetition_count", "interval_days", "ease_factor",
    "due_date", "last_reviewed", "created_at",
}
UUID_RE = re.compile(r"^[a-f0-9]{32}$")


class ServiceError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class Service:
    def __init__(self, path):
        self.path = str(path)
        with self.connection() as conn:
            conn.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    salt TEXT NOT NULL, password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    expires INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS records (
                    user_id TEXT NOT NULL, entity TEXT NOT NULL, uuid TEXT NOT NULL,
                    data TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL,
                    PRIMARY KEY(user_id, entity, uuid)
                );
                CREATE INDEX IF NOT EXISTS records_revision ON records(user_id, revision);
                CREATE TABLE IF NOT EXISTS history (
                    revision INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL, entity TEXT NOT NULL, uuid TEXT NOT NULL,
                    data TEXT NOT NULL, deleted INTEGER NOT NULL,
                    saved_at INTEGER NOT NULL
                );
            """)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=20)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt),
                              n=16384, r=8, p=1, dklen=32).hex()

    def authenticate(self, body, register=False):
        email, password = body.get("email", ""), body.get("password", "")
        if not isinstance(email, str) or not isinstance(password, str):
            raise ServiceError("E-posta ve şifre geçerli değil.")
        email = email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ServiceError("Geçerli bir e-posta adresi yazın.")
        if not 10 <= len(password) <= 128:
            raise ServiceError("Şifre 10–128 karakter olmalı.")
        with self.connection() as conn:
            if register:
                uid, salt = secrets.token_hex(16), secrets.token_hex(16)
                digest = self.password_hash(password, salt)
                try:
                    conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                                 (uid, email, salt, digest))
                except sqlite3.IntegrityError:
                    raise ServiceError("Bu e-posta ile hesap zaten var.", 409)
            else:
                user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                # Hash on failed lookup as well, avoiding a cheap account-existence probe.
                salt = user["salt"] if user else "00" * 16
                digest = self.password_hash(password, salt)
                if not user or not hmac.compare_digest(digest, user["password_hash"]):
                    raise ServiceError("E-posta veya şifre yanlış.", 401)
                uid = user["id"]
            token = secrets.token_urlsafe(32)
            expires = int(time.time()) + 30 * 86400
            conn.execute("DELETE FROM sessions WHERE expires <= ?", (int(time.time()),))
            conn.execute("INSERT INTO sessions VALUES (?, ?, ?)",
                         (hashlib.sha256(token.encode()).hexdigest(), uid, expires))
        return {"token": token, "user_id": uid, "email": email, "expires": expires}

    def user(self, conn, token):
        if not isinstance(token, str) or len(token) > 256:
            raise ServiceError("Oturum geçersiz. Yeniden giriş yapın.", 401)
        row = conn.execute("SELECT user_id FROM sessions WHERE token_hash=? AND expires>?",
                           (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if not row:
            raise ServiceError("Oturum süresi doldu. Yeniden giriş yapın.", 401)
        return row["user_id"]

    def logout(self, token):
        with self.connection() as conn:
            self.user(conn, token)
            conn.execute("DELETE FROM sessions WHERE token_hash=?",
                         (hashlib.sha256(token.encode()).hexdigest(),))
        return {"ok": True}

    @staticmethod
    def validate(entity, data, complete=False):
        fields = DECK_FIELDS if entity == "deck" else CARD_FIELDS
        if not isinstance(data, dict) or set(data) - fields:
            raise ServiceError("Kart/deste alanları geçerli değil.")
        for key, value in data.items():
            if key in {"is_favorite", "repetition_count", "interval_days", "ease_factor"}:
                if type(value) not in (int, float) or not 0 <= value <= 1000000:
                    raise ServiceError("Tekrar değeri geçersiz.")
                if key != "ease_factor" and type(value) is not int:
                    raise ServiceError("Tekrar sayıları tam sayı olmalı.")
                if key == "is_favorite" and value not in (0, 1):
                    raise ServiceError("Favori değeri geçersiz.")
            elif value is not None and (not isinstance(value, str) or len(value) > 16000):
                raise ServiceError("Metin çok uzun veya geçersiz.")
        if "status" in data and data["status"] not in {"new", "learning", "mastered"}:
            raise ServiceError("Kart durumu geçersiz.")
        if "deck_uuid" in data and (not isinstance(data["deck_uuid"], str) or
                                    not UUID_RE.fullmatch(data["deck_uuid"])):
            raise ServiceError("Deste kimliği geçersiz.")
        for key in ({"name"} if entity == "deck" else {"term", "definition", "deck_uuid"}):
            if (complete or key in data) and (not isinstance(data.get(key), str) or not data[key].strip()):
                raise ServiceError("Kelime, anlam ve deste boş olamaz.")
        if "due_date" in data:
            try:
                date.fromisoformat(data["due_date"])
            except (TypeError, ValueError):
                raise ServiceError("Tekrar tarihi geçersiz.")

    @staticmethod
    def save(conn, uid, entity, uuid, data, deleted):
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
        cur = conn.execute("INSERT INTO history(user_id,entity,uuid,data,deleted,saved_at) VALUES(?,?,?,?,?,?)",
                           (uid, entity, uuid, encoded, int(deleted), int(time.time())))
        conn.execute("""INSERT INTO records VALUES(?,?,?,?,?,?)
            ON CONFLICT(user_id,entity,uuid) DO UPDATE SET
            data=excluded.data,deleted=excluded.deleted,revision=excluded.revision""",
                     (uid, entity, uuid, encoded, int(deleted), cur.lastrowid))

    def sync(self, token, body):
        cursor, changes = body.get("cursor", 0), body.get("changes", [])
        if type(cursor) is not int or cursor < 0 or not isinstance(changes, list) or len(changes) > 500:
            raise ServiceError("Eşitleme isteği geçersiz (en çok 500 değişiklik).")
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            uid = self.user(conn, token)
            # Parents first, including when a client supplies an unordered batch.
            for change in sorted(changes, key=lambda c: 0 if isinstance(c, dict) and c.get("entity") == "deck" else 1):
                if not isinstance(change, dict):
                    raise ServiceError("Değişiklik geçersiz.")
                entity, uuid = change.get("entity"), change.get("uuid")
                deleted, patch = change.get("deleted", False), change.get("data", {})
                if entity not in {"deck", "card"} or not isinstance(uuid, str) or not UUID_RE.fullmatch(uuid):
                    raise ServiceError("Kayıt kimliği geçersiz.")
                if type(deleted) is not bool:
                    raise ServiceError("Silme durumu geçersiz.")
                collision = conn.execute("SELECT entity FROM records WHERE user_id=? AND uuid=? AND entity<>?", (uid, uuid, entity)).fetchone()
                if collision:
                    raise ServiceError("Kart ve deste kimlikleri farklı olmalı.")
                row = conn.execute("SELECT * FROM records WHERE user_id=? AND entity=? AND uuid=?",
                                   (uid, entity, uuid)).fetchone()
                # Deletion is permanent for this UUID; an offline client cannot resurrect it.
                if row and row["deleted"]:
                    continue
                self.validate(entity, patch)
                data = json.loads(row["data"]) if row else {}
                data.update(patch)
                if not deleted:
                    self.validate(entity, data, complete=True)
                if entity == "card" and not deleted:
                    parent = conn.execute("SELECT deleted FROM records WHERE user_id=? AND entity='deck' AND uuid=?",
                                          (uid, data["deck_uuid"])).fetchone()
                    if not parent:
                        raise ServiceError("Kartın destesi bu hesapta bulunamadı.")
                    if parent["deleted"]:
                        deleted = True
                if row and bool(row["deleted"]) == deleted and json.loads(row["data"]) == data:
                    continue  # Retries after a lost response are idempotent.
                self.save(conn, uid, entity, uuid, data, deleted)
                if entity == "deck" and deleted:
                    children = conn.execute("SELECT * FROM records WHERE user_id=? AND entity='card' AND deleted=0",
                                            (uid,)).fetchall()
                    for child in children:
                        child_data = json.loads(child["data"])
                        if child_data.get("deck_uuid") == uuid:
                            self.save(conn, uid, "card", child["uuid"], child_data, True)
            rows = conn.execute("SELECT * FROM records WHERE user_id=? AND revision>? ORDER BY revision LIMIT 501",
                                (uid, cursor)).fetchall()
            page = rows[:500]
            records = [{"entity": r["entity"], "uuid": r["uuid"], "data": json.loads(r["data"]),
                        "deleted": bool(r["deleted"]), "revision": r["revision"]} for r in page]
            # Pull every acknowledged UUID even when its revision precedes the caller's cursor.
            acknowledged = []
            for change in changes:
                r = conn.execute("SELECT * FROM records WHERE user_id=? AND entity=? AND uuid=?",
                                 (uid, change["entity"], change["uuid"])).fetchone()
                if r:
                    acknowledged.append({"entity": r["entity"], "uuid": r["uuid"],
                                         "data": json.loads(r["data"]), "deleted": bool(r["deleted"]),
                                         "revision": r["revision"]})
            return {"records": records, "acknowledged": acknowledged,
                    "cursor": page[-1]["revision"] if page else cursor, "has_more": len(rows) > 500}
