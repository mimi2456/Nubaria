from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlsplit
import os


ROOT = Path(__file__).resolve().parent
ROUTES = {"/hlasovani", "/tym", "/banlist", "/vip"}


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path.rstrip("/") or "/"
        if path.startswith("/.dev/") or path == "/.dev":
            self.send_error(404)
            return
        if path == "/banlist-data.php":
            try:
                with urlopen("https://mcnubaria.eu/banlist-data.php", timeout=10) as result:
                    body = result.read()
                    self.send_response(result.status)
                    self.send_header("Content-Type", result.headers.get("Content-Type", "application/json"))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            except (OSError, URLError):
                fallback = ROOT / ".dev" / "banlist-preview.json"
                if fallback.is_file():
                    body = fallback.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Banlist-Source", "preview-cache")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(502, "Banlist není dostupný.")
            return
        if path in ROUTES:
            self.path = "/index.html"
        super().do_GET()


port = int(os.environ.get("PORT", "4173"))
server = ThreadingHTTPServer(("0.0.0.0", port), partial(SiteHandler))
print(f"Nubaria běží na http://localhost:{port}")
server.serve_forever()