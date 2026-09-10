#!/usr/bin/env python3
"""Local preview server for dist/ that mimics Vercel's cleanUrls behavior.

Usage: python3 serve.py [port]
"""
import json
import http.server
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "dist"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123


def download_redirect(path):
    """Match /a/downloads redirects from vercel.json the same way production does."""
    cfg_path = Path(__file__).parent / "vercel.json"
    if not cfg_path.exists() or not path.startswith("/a/downloads"):
        return None
    redirects = json.loads(cfg_path.read_text()).get("redirects", [])
    for rule in redirects:
        source = rule.get("source", "")
        dest = rule.get("destination")
        if source == path:
            return dest
        if source.endswith("/:token*") and path.startswith(source[: -len("/:token*")] + "/"):
            return dest
        if source.endswith("/:path*"):
            prefix = source[: -len("/:path*")]
            if path == prefix or path.startswith(prefix + "/"):
                return dest
    return None


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _redirect_downloads(self):
        path = self.path.split("?")[0].split("#")[0]
        dest = download_redirect(path)
        if dest:
            self.send_response(302)
            self.send_header("Location", dest)
            self.end_headers()
            return True
        return False

    def do_GET(self):
        if self._redirect_downloads():
            return
        super().do_GET()

    def do_HEAD(self):
        if self._redirect_downloads():
            return
        super().do_HEAD()

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
