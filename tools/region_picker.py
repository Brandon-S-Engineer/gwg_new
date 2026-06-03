"""Launcher del editor de coordenadas (web local).

    python3 tools/region_picker.py

Endpoints:
  GET  /                          → HTML
  GET  /resolutions               → ["3840x2160", "1920x1080", ...]
  POST /resolutions               → crea una nueva (body: {"wxh": "1920x1080"})
  GET  /coords/<wxh>              → coords JSON de esa resolución
  POST /coords/<wxh>              → escribe coords JSON
  GET  /image/<wxh>/<filename>    → screenshot de calibración
  POST /capture/<wxh>             → captura pantalla → calibration/<wxh>/<filename>
  POST /capture-item/<wxh>        → captura, recorta por rect, guarda en assets/items/<wxh>/

Para parar: Ctrl+C.
"""

from __future__ import annotations

import http.server
import json
import re
import socket
import threading
import urllib.parse
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
HTML_PATH = TOOLS_DIR / "region_picker.html"
COORDS_DIR = ROOT / "bot" / "coords"
CALIB_DIR = TOOLS_DIR / "calibration"
ITEMS_ASSETS_DIR = ROOT / "bot" / "assets" / "items"

RES_RE = re.compile(r"^\d{2,5}x\d{2,5}$")


def safe_filename(name: str) -> bool:
    return bool(name) and "/" not in name and "\\" not in name and not name.startswith(".")


def safe_res(wxh: str) -> bool:
    return bool(RES_RE.match(wxh or ""))


def _empty_coords_from(reference: dict) -> dict:
    """Devuelve una copia de la estructura con todos los valores en 0."""
    out = {"reference_resolution": reference.get("reference_resolution", [0, 0]),
           "types": {}}
    for key, t in reference.get("types", {}).items():
        copied = {
            "description": t.get("description", ""),
            "image": t.get("image", f"{key}.png"),
            "regions": [{"name": r["name"], "x": 0, "y": 0, "w": 0, "h": 0}
                        for r in t.get("regions", [])],
            "points":  [{"name": p["name"], "x": 0, "y": 0}
                        for p in t.get("points", [])],
        }
        if "items" in t:
            copied["items"] = [{"name": it["name"], "image": it["image"]}
                               for it in t["items"]]
        out["types"][key] = copied
    return out


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencio
        pass

    # HEAD reusa el routing de GET. _send_file omite el body cuando
    # command == 'HEAD'. Se usa desde el frontend para chequear si un PNG
    # de item existe sin descargarlo.
    def do_HEAD(self):
        self.do_GET()

    # ------------------------------------------------------------- GET
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ("/", "/index.html"):
            return self._send_file(HTML_PATH, "text/html; charset=utf-8")

        if path == "/resolutions":
            res = sorted([f.stem for f in COORDS_DIR.glob("*.json")])
            return self._send_json(res)

        m = re.match(r"^/coords/(\d+x\d+)$", path)
        if m:
            wxh = m.group(1)
            target = COORDS_DIR / f"{wxh}.json"
            if not target.exists():
                return self.send_error(404)
            return self._send_file(target, "application/json; charset=utf-8")

        m = re.match(r"^/image/(\d+x\d+)/(.+)$", path)
        if m:
            return self._serve_image_under(CALIB_DIR, m.group(1),
                                           urllib.parse.unquote(m.group(2)))

        m = re.match(r"^/item/(\d+x\d+)/(.+)$", path)
        if m:
            return self._serve_image_under(ITEMS_ASSETS_DIR, m.group(1),
                                           urllib.parse.unquote(m.group(2)))

        self.send_error(404)

    def _serve_image_under(self, root: Path, wxh: str, name: str):
        if not safe_filename(name):
            return self.send_error(403)
        target = (root / wxh / name).resolve()
        base = (root / wxh).resolve()
        if base not in target.parents and target != base:
            return self.send_error(403)
        if not target.exists():
            return self.send_error(404)
        ct = "image/png" if target.suffix.lower() == ".png" else "image/jpeg"
        return self._send_file(target, ct)

    # ------------------------------------------------------------- POST
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        # Guardar PNG del item: el body son los bytes del PNG, no JSON.
        m = re.match(r"^/save-item/(\d+x\d+)/(.+)$", path)
        if m:
            wxh = m.group(1)
            filename = urllib.parse.unquote(m.group(2))
            if not safe_filename(filename):
                return self.send_error(400, "filename inválido")
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length) if length else b""
            if not data:
                return self.send_error(400, "body vacío")
            out_dir = ITEMS_ASSETS_DIR / wxh
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / filename).write_bytes(data)
            return self._send_json({"ok": True, "bytes": len(data)})

        body = self._read_body()

        if path == "/resolutions":
            wxh = (body.get("wxh") or "").strip()
            if not safe_res(wxh):
                return self.send_error(400, "resolución inválida (ej: 1920x1080)")
            target = COORDS_DIR / f"{wxh}.json"
            if target.exists():
                return self.send_error(409, "ya existe")
            # plantilla = el primer JSON existente
            existing = sorted(COORDS_DIR.glob("*.json"))
            if not existing:
                return self.send_error(500, "no hay coords base para clonar la estructura")
            reference = json.loads(existing[0].read_text(encoding="utf-8"))
            new = _empty_coords_from(reference)
            w, h = map(int, wxh.split("x"))
            new["reference_resolution"] = [w, h]
            target.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
            (CALIB_DIR / wxh).mkdir(parents=True, exist_ok=True)
            (ITEMS_ASSETS_DIR / wxh).mkdir(parents=True, exist_ok=True)
            return self._send_json({"ok": True, "wxh": wxh})

        m = re.match(r"^/coords/(\d+x\d+)$", path)
        if m:
            wxh = m.group(1)
            target = COORDS_DIR / f"{wxh}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
            return self._send_json({"ok": True})

        m = re.match(r"^/capture/(\d+x\d+)$", path)
        if m:
            wxh = m.group(1)
            filename = (body.get("filename") or "").strip()
            if not safe_filename(filename):
                return self.send_error(400, "filename inválido")
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
            except Exception as e:
                return self.send_error(500, f"no se pudo capturar: {e}")
            out_dir = CALIB_DIR / wxh
            out_dir.mkdir(parents=True, exist_ok=True)
            img.save(out_dir / filename, "PNG")
            return self._send_json({"ok": True, "width": img.width, "height": img.height})

        self.send_error(404)

    # ------------------------------------------------------------- helpers
    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _send_file(self, path: Path, content_type: str):
        if not Path(path).exists():
            return self.send_error(404)
        data = Path(path).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _send_json(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _find_free_port(start: int = 5173) -> int:
    for p in range(start, start + 100):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("no hay puerto libre")


def main() -> None:
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}/"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"Region Picker corriendo en {url}  (Ctrl+C para parar)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye.")
        server.server_close()


if __name__ == "__main__":
    main()
