#!/usr/bin/env python3
"""Tiny static download server for the coloring book (forces PDF/ZIP downloads)."""
import http.server
import os
import socketserver

DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8123


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        path = self.path.split("?")[0]
        if path.lower().endswith((".pdf", ".zip")):
            name = os.path.basename(path)
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[download-server] {self.address_string()} - {fmt % args}")


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Serving {DIR} on 0.0.0.0:{PORT}")
    ThreadedServer(("0.0.0.0", PORT), Handler).serve_forever()
