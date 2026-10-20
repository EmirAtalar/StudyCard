"""Exercise real SQLite/service sync with independent PC and phone libraries."""
import json
import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from duocards import db
from duocards.sync import SyncClient, SyncError, normalize_url, set_config
from sync_server.service import Service, ServiceError
from sync_server.__main__ import make_handler


class AccountSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.service = Service(self.folder / "server.db")
        self.accounts = {}
        self.clients = {}
        for name in ("pc", "phone"):
            self.clients[name] = SyncClient(self.folder / (name + "-session.json"), self.transport)
            with self.device(name):
                db.init_db()
        with self.device("pc"):
            self.clients["pc"].login("http://127.0.0.1:8765", "learner@example.com", "strong-password", True)
        with self.device("phone"):
            self.clients["phone"].login("http://127.0.0.1:8765", "learner@example.com", "strong-password")

    @contextmanager
    def device(self, name):
        with patch.object(db, "DB_DIR", str(self.folder)), patch.object(db, "DB_PATH", str(self.folder / (name + ".db"))), patch("duocards.sentence_memory.request_examples"):
            yield

    def transport(self, url, path, body, token=""):
        try:
            if path == "/v1/register":
                return self.service.authenticate(body, True)
            if path == "/v1/login":
                return self.service.authenticate(body)
            if path == "/v1/logout":
                return self.service.logout(token)
            return self.service.sync(token, body)
        except ServiceError as exc:
            raise SyncError(str(exc)) from exc

    def sync(self, name):
        with self.device(name):
            return self.clients[name].sync()

    def card(self, name, term):
        with self.device(name):
            return next(c for c in db.get_all_cards() if c["term"] == term)

    def add(self, name, term="phone-word"):
        with self.device(name):
            return db.add_card(db.get_all_decks()[0]["id"], term, "Telefondan eklendi", notes="ilk not")

    def edit(self, name, term, **fields):
        card = self.card(name, term)
        with self.device(name), db.get_connection() as conn:
            conn.execute("UPDATE cards SET " + ",".join(k + "=?" for k in fields) + " WHERE id=?", [*fields.values(), card["id"]])

    def pair(self):
        self.sync("pc"); self.sync("phone"); self.sync("pc")

    def test_phone_added_word_arrives_on_pc_and_pc_edits_arrive_on_phone(self):
        self.add("phone"); self.pair()
        self.assertEqual(self.card("pc", "phone-word")["definition"], "Telefondan eklendi")
        self.edit("pc", "phone-word", definition="PC’de düzeltildi")
        self.sync("pc"); self.sync("phone")
        self.assertEqual(self.card("phone", "phone-word")["definition"], "PC’de düzeltildi")
        with self.device("phone"):
            self.assertEqual(self.clients["phone"].pending_count(), 0)

    def test_offline_change_survives_failure_and_restart(self):
        self.add("phone")
        with self.device("phone"), patch.object(self.clients["phone"], "transport", side_effect=SyncError("offline")):
            with self.assertRaises(SyncError): self.clients["phone"].sync()
            self.assertGreater(self.clients["phone"].pending_count(), 0)
            restarted = SyncClient(self.folder / "phone-session.json", self.transport)
            restarted.sync()
        self.sync("pc")
        self.assertEqual(self.card("pc", "phone-word")["notes"], "ilk not")

    def test_lost_response_retry_is_idempotent(self):
        self.add("phone")
        def lost(url, path, body, token=""):
            self.transport(url, path, body, token)
            raise SyncError("connection lost")
        with self.device("phone"), patch.object(self.clients["phone"], "transport", side_effect=lost):
            with self.assertRaises(SyncError): self.clients["phone"].sync()
        with self.service.connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        self.sync("phone")
        with self.service.connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM history").fetchone()[0], count)

    def test_independent_offline_fields_merge(self):
        self.add("phone"); self.pair()
        self.edit("pc", "phone-word", definition="yeni anlam")
        self.edit("phone", "phone-word", notes="telefondaki not")
        self.sync("pc"); self.sync("phone"); self.sync("pc")
        for name in ("pc", "phone"):
            card = self.card(name, "phone-word")
            self.assertEqual(card["definition"], "yeni anlam")
            self.assertEqual(card["notes"], "telefondaki not")

    def test_edit_during_request_is_not_acknowledged_or_overwritten(self):
        self.add("phone")
        transport = self.clients["phone"].transport
        def during(url, path, body, token=""):
            response = transport(url, path, body, token)
            if path == "/v1/sync" and body["changes"]:
                self.edit("phone", "phone-word", notes="istek sırasında yazıldı")
            return response
        with self.device("phone"), patch.object(self.clients["phone"], "transport", side_effect=during):
            self.clients["phone"].sync()
            self.assertEqual(db.get_card(self.card("phone", "phone-word")["id"])["notes"], "istek sırasında yazıldı")
            self.assertEqual(self.clients["phone"].pending_count(), 1)
        self.sync("phone"); self.sync("pc")
        self.assertEqual(self.card("pc", "phone-word")["notes"], "istek sırasında yazıldı")

    def test_deletion_wins_over_stale_phone_edit_and_is_backed_up(self):
        self.add("phone"); self.pair()
        self.edit("phone", "phone-word", notes="çevrimdışı not")
        card = self.card("pc", "phone-word")
        with self.device("pc"): db.delete_card(card["id"])
        self.sync("pc"); self.sync("phone")
        with self.device("phone"), db.get_connection() as conn:
            self.assertFalse(any(c["term"] == "phone-word" for c in db.get_all_cards()))
            recovered = json.loads(conn.execute("SELECT data FROM sync_recovery ORDER BY id DESC LIMIT 1").fetchone()[0])
            self.assertEqual(recovered["notes"], "çevrimdışı not")
            self.assertEqual(self.clients["phone"].pending_count(), 0)

    def test_deck_deletion_cascades_and_survives_restart(self):
        self.add("phone"); self.pair()
        card = self.card("pc", "phone-word")
        with self.device("pc"): db.delete_deck(card["deck_id"])
        self.sync("pc"); self.sync("phone")
        with self.device("phone"):
            self.assertFalse(any(c["term"] == "phone-word" for c in db.get_all_cards()))
            db.init_db()
            self.assertEqual(self.clients["phone"].pending_count(), 0)

    def test_reviews_and_favorites_are_synced(self):
        self.add("phone"); self.pair()
        card = self.card("phone", "phone-word")
        with self.device("phone"):
            db.toggle_card_favorite(card["id"])
            for _ in range(3): db.record_study_result(card["id"], 3)
        self.sync("phone"); self.sync("pc")
        card = self.card("pc", "phone-word")
        self.assertEqual((card["is_favorite"], card["repetition_count"], card["status"]), (1, 3, "mastered"))

    def test_bound_library_cannot_upload_to_another_account(self):
        with self.device("phone"):
            with self.assertRaises(SyncError):
                self.clients["phone"].login("http://127.0.0.1:8765", "other@example.com", "other-password", True)
            self.assertEqual(self.clients["phone"].session()["email"], "learner@example.com")
        other = self.service.authenticate({"email":"other@example.com", "password":"other-password"})
        self.pair()
        self.assertEqual(self.service.sync(other["token"], {"cursor":0,"changes":[]})["records"], [])

    def test_account_tokens_are_revoked_on_logout(self):
        token = self.clients["phone"].session()["token"]
        self.clients["phone"].logout()
        self.assertFalse(self.clients["phone"].session())
        with self.assertRaises(ServiceError): self.service.sync(token,{"cursor":0,"changes":[]})
        self.assertEqual(os.stat(self.folder / "phone-session.json").st_mode & 0o777, 0o600)

    def test_server_rejects_foreign_deck_and_rolls_back_entire_batch(self):
        other = self.service.authenticate({"email":"other@example.com", "password":"other-password"}, True)
        uid = "a" * 32
        with self.assertRaises(ServiceError):
            self.service.sync(other["token"], {"changes":[{"entity":"deck","uuid":"b"*32,"data":{"name":"valid"}}, {"entity":"card","uuid":uid,"data":{"deck_uuid":"c"*32,"term":"invalid","definition":"no deck"}}]})
        self.assertEqual(self.service.sync(other["token"], {})["records"], [])

    def test_pagination_fetches_parent_updated_after_child(self):
        self.add("phone"); self.sync("phone")
        phone_token = self.clients["phone"].session()["token"]
        changes = [{"entity":"deck","uuid":f"{n:032x}","data":{"name":f"Deck {n}"}} for n in range(1,551)]
        self.service.sync(phone_token,{"changes":changes[:500]})
        self.service.sync(phone_token,{"changes":changes[500:]})
        # Put the phone word's parent after the first pull page.
        with self.device("phone"), db.get_connection() as conn:
            card = next(c for c in db.get_all_cards() if c["term"] == "phone-word")
            deck_uuid = conn.execute("SELECT uuid FROM sync_items WHERE entity='deck' AND local_id=?",(card["deck_id"],)).fetchone()[0]
        self.service.sync(phone_token,{"changes":[{"entity":"deck","uuid":deck_uuid,"data":{"name":"Latest parent"}}]})
        self.sync("pc")
        self.assertEqual(self.card("pc", "phone-word")["deck_name"], "Latest parent")

    def test_protocol_accepts_android_card_json(self):
        token = self.clients["phone"].session()["token"]
        data = {"deck_uuid":"a"*32,"term":"resilient 📚","definition":"dirençli","source_lang":"İngilizce","target_lang":"Türkçe","status":"new","is_favorite":0,"repetition_count":0,"interval_days":1,"ease_factor":2.5,"due_date":"2026-10-12","last_reviewed":None,"created_at":"2026-10-12T15:30:00"}
        self.service.sync(token,{"changes":[{"entity":"deck","uuid":"a"*32,"deleted":False,"data":{"name":"Android"}},{"entity":"card","uuid":"b"*32,"deleted":False,"data":data}]})
        self.sync("pc")
        self.assertEqual(self.card("pc", "resilient 📚")["source_lang"], "İngilizce")

    def test_duplicate_deck_names_do_not_drop_cards(self):
        self.add("phone"); self.pair()
        with self.device("pc"):
            self.assertEqual(len(db.get_all_decks()), 6)
            self.assertEqual(len({d["name"] for d in db.get_all_decks()}), 6)
            self.assertEqual(len(db.get_all_cards()), 11)

    def test_deleting_all_decks_does_not_reseed_after_restart(self):
        self.pair()
        with self.device("phone"):
            for deck in db.get_all_decks(): db.delete_deck(deck["id"])
        self.sync("phone"); self.sync("pc")
        for name in ("pc", "phone"):
            with self.device(name):
                db.init_db()
                self.assertEqual(db.get_all_decks(), [])
                self.assertEqual(self.clients[name].pending_count(), 0)


class ServerValidationTests(unittest.TestCase):
    def test_urls_require_https_except_lan(self):
        for url in ("https://study.example/", "http://192.168.1.2:8765", "http://127.0.0.1:8765", "http://10.0.2.2:8765"):
            self.assertTrue(normalize_url(url))
        for url in ("http://study.example", "http://8.8.8.8", "http://169.254.169.254", "https://user:secret@study.example", "https://study.example/path", "https://study.example?token=secret", "https://study.example:99999"):
            with self.assertRaises(SyncError): normalize_url(url)

    def test_invalid_record_values_are_rejected(self):
        for data in ({"status":"bogus"},{"is_favorite":4},{"interval_days":1.2},{"ease_factor":float("nan")},{"due_date":"oops"},{"term":""},{"deck_uuid":"not-id"},{"unknown":"data"}):
            with self.assertRaises(ServiceError): Service.validate("card",data)


class AccountHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.handler = make_handler(Service(Path(self.tmp.name) / "server.db"))

    def request(self, path, body=None, token="", content_type="application/json"):
        encoded = json.dumps(body).encode() if body is not None else b""
        method = "POST" if body is not None else "GET"
        request = (f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\nContent-Type: {content_type}\r\nContent-Length: {len(encoded)}\r\nAuthorization: Bearer {token}\r\n\r\n").encode() + encoded
        class Socket:
            def __init__(self): self.output = io.BytesIO()
            def makefile(self, *args): return io.BytesIO(request)
            def settimeout(self, value): pass
            def sendall(self, value): self.output.write(value)
        socket = Socket()
        self.handler(socket, ("127.0.0.1", 1234), object())
        header, response = socket.output.getvalue().split(b"\r\n\r\n", 1)
        return int(header.split(b" ")[1]), json.loads(response)

    def test_http_register_login_sync_and_logout(self):
        body = {"email":"http@example.com", "password":"http-password"}
        status, account = self.request("/v1/register", body)
        self.assertEqual(status, 200)
        status, _ = self.request("/v1/login", body)
        self.assertEqual(status, 200)
        status, result = self.request("/v1/sync", {"changes":[{"entity":"deck","uuid":"a"*32,"data":{"name":"HTTP deste"}}]}, account["token"])
        self.assertEqual(status, 200)
        self.assertEqual(result["records"][0]["data"]["name"], "HTTP deste")
        self.assertEqual(self.request("/v1/logout", {}, account["token"])[0], 200)
        self.assertEqual(self.request("/v1/sync", {}, account["token"])[0], 401)

    def test_http_enforces_json_and_auth(self):
        self.assertEqual(self.request("/health")[0], 200)
        self.assertEqual(self.request("/v1/sync", {})[0], 401)
        self.assertEqual(self.request("/v1/login", {}, content_type="text/plain")[0], 415)
        self.assertEqual(self.request("/missing", {})[0], 404)

    def test_http_rate_limits_failed_logins(self):
        body = {"email":"http@example.com", "password":"wrong-password"}
        for _ in range(10): self.assertEqual(self.request("/v1/login", body)[0], 401)
        self.assertEqual(self.request("/v1/login", body)[0], 429)


if __name__ == "__main__":
    unittest.main()
