#!/usr/bin/env python3
"""Local preview server for dist/ that mimics Vercel's cleanUrls behavior.

Usage: python3 serve.py [port]
"""
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "dist"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        path = self.path.split("?")[0].split("#")[0]
        if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
            candidate = ROOT / (path.lstrip("/") + ".html")
            if candidate.exists():
                self.path = path + ".html"
            elif not (ROOT / path.lstrip("/")).exists():
                self.path = "/404.html"
        return super().send_head()


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("", PORT), CleanURLHandler) as srv:
        print(f"Serving dist/ with clean URLs at http://localhost:{PORT}")
        srv.serve_forever()
