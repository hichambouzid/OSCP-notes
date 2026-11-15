#!/usr/bin/env python3
"""Local-only practice: loopback HTTP, permissions, checksums, and evidence."""
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import build_opener, ProxyHandler
from urllib.error import HTTPError

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        responses = {"/": (200, b"OSCP local practice\n"), "/private": (403, b"Forbidden\n"), "/login": (401, b"Authentication required\n")}
        status, body = responses.get(self.path, (404, b"Not found\n"))
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        if status == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="local-demo"')
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_args):
        pass

def main():
    with TemporaryDirectory(prefix="oscp-local-") as directory:
        sample = Path(directory) / "evidence.txt"
        sample.write_text("hello\n", encoding="utf-8")
        original = hashlib.sha256(sample.read_bytes()).hexdigest()
        print("Original SHA-256:", original)
        sample.write_text("hello!\n", encoding="utf-8")
        changed = hashlib.sha256(sample.read_bytes()).hexdigest()
        assert original != changed
        print("Changed checksum differs: PASS")
        if os.name == "posix":
            sample.chmod(0o600)
            assert sample.stat().st_mode & 0o777 == 0o600
            print("File mode 0600: PASS")
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            opener = build_opener(ProxyHandler({}))
            try:
                for path, expected in [("/",200),("/login",401),("/private",403),("/missing",404)]:
                    url = f"http://127.0.0.1:{server.server_port}{path}"
                    try:
                        with opener.open(url, timeout=3) as response:
                            status = response.status
                            response.read()
                    except HTTPError as error:
                        status = error.code
                        error.close()
                    assert status == expected, (path, status, expected)
                    print(f"GET {path} -> {status}: PASS")
            finally:
                server.shutdown()
                thread.join()
    print("All local drills passed; temporary files and server cleaned up.")

if __name__ == "__main__":
    main()
