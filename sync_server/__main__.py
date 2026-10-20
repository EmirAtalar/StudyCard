"""Run with python3 -m sync_server. Put Caddy/HTTPS in front for public access."""
import argparse
import json
import logging
import os
import ssl
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .service import Service, ServiceError

log = logging.getLogger("studycard.server")


class RateLimiter:
    def __init__(self):
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            count, started = self.entries.pop(key, (0, now))
            if now - started > 60:
                count, started = 0, now
            self.entries[key] = (count + 1, started)
            while len(self.entries) > 10000:
                self.entries.popitem(last=False)
            return count < 10


def make_handler(service):
    limiter = RateLimiter()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(20)

        def respond(self, status, body):
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.respond(200, {"ok": True, "service": "study-card", "protocol": 1}) if self.path == "/health" else self.respond(404, {"error": "Adres bulunamadı."})

        def do_POST(self):
            try:
                if self.path not in {"/v1/register", "/v1/login", "/v1/logout", "/v1/sync"}:
                    raise ServiceError("Adres bulunamadı.", 404)
                if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                    raise ServiceError("JSON gerekli.", 415)
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2 * 1024 * 1024:
                    raise ServiceError("İstek çok büyük veya boş.", 413)
                body = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                if not isinstance(body, dict):
                    raise ServiceError("JSON nesnesi gerekli.")
                if self.path in {"/v1/register", "/v1/login"}:
                    # Do not trust client-controlled forwarding headers.
                    if not limiter.allow(self.client_address[0]) or not limiter.allow(str(body.get("email", "")).lower()[:254]):
                        raise ServiceError("Çok fazla giriş denemesi. Bir dakika bekleyin.", 429)
                    result = service.authenticate(body, self.path == "/v1/register")
                else:
                    auth = self.headers.get("Authorization", "")
                    if not auth.startswith("Bearer "):
                        raise ServiceError("Giriş yapın.", 401)
                    token = auth[7:]
                    result = service.logout(token) if self.path == "/v1/logout" else service.sync(token, body)
                self.respond(200, result)
            except ServiceError as exc:
                self.respond(exc.status, {"error": str(exc)})
            except (ValueError, UnicodeDecodeError):
                self.respond(400, {"error": "Geçersiz JSON isteği."})
            except (ConnectionError, TimeoutError):
                pass
            except Exception:
                log.exception("Request failed")
                self.respond(500, {"error": "Sunucu hatası. Tekrar deneyin."})

        def log_message(self, fmt, *args):
            # Never log passwords, tokens, request bodies or email addresses.
            log.info("%s", fmt % args)

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Study Card hesap ve eşitleme sunucusu")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default=os.path.expanduser("~/.local/share/study-card-server"))
    parser.add_argument("--cert")
    parser.add_argument("--key")
    args = parser.parse_args()
    folder = Path(args.data_dir)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(folder, 0o700)
    logging.basicConfig(level=logging.INFO)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(Service(folder / "accounts.db")))
    if args.cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.cert, args.key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    log.info("Study Card listening on %s:%s", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
