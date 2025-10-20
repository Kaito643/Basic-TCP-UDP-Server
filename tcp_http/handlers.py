import json
import os
from datetime import datetime, timezone
from typing import Tuple, Optional

from common.config import AppConfig

# Minimal content-type mapping for common extensions
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}

def _read_file_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None

def route_request(method: str, path: str, config: AppConfig) -> Tuple[int, str, str, bytes]:
    # Strip query string and map root to our static index
    if "?" in path:
        path = path.split("?", 1)[0]
    if path == "/":
        path = "/static/index.html"

    if path == "/health":
        payload = {
            "status": "ok",
            "time": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(payload).encode("utf-8")
        return 200, "OK", "application/json; charset=utf-8", body

    if path.startswith("/static/"):
        rel = path.removeprefix("/static/")
        # Crude directory traversal protection
        safe_rel = rel.replace("..", "")
        file_path = os.path.join(config.static_dir, safe_rel)
        data = _read_file_bytes(file_path)
        if data is None:
            return 404, "Not Found", "text/plain; charset=utf-8", b"Not Found"
        ext = os.path.splitext(file_path)[1].lower()
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        return 200, "OK", ctype, data

    return 404, "Not Found", "text/plain; charset=utf-8", b"Not Found"

def headify(response: Tuple[int, str, str, bytes]) -> Tuple[int, str, str, bytes]:
    # For HEAD we reuse headers but drop the body
    status, reason, content_type, _body = response
    return status, reason, content_type, b""
