import io
from typing import Dict, Tuple

CRLF = b"\r\n"

class HTTPParseError(Exception):
    pass

def parse_http_request(stream: io.BufferedReader, max_request_line: int, max_headers: int, read_timeout: int) -> Tuple[str, str, str, Dict[str, str]]:
    stream.peek(1)
    request_line = stream.readline(max_request_line + 1)
    if not request_line:
        raise HTTPParseError("Empty request")
    if len(request_line) > max_request_line:
        raise HTTPParseError("Request line too long")

    try:
        request_line_str = request_line.decode("iso-8859-1").rstrip("\r\n")
        method, path, version = request_line_str.split(" ", 2)
    except Exception as exc:
        raise HTTPParseError(f"Bad request line: {request_line!r}") from exc

    headers_bytes = bytearray()
    while True:
        line = stream.readline(max_headers + 1)
        if not line:
            break
        headers_bytes += line
        if line in (b"\r\n", b"\n"):
            break
        if len(headers_bytes) > max_headers:
            raise HTTPParseError("Headers too large")

    headers: Dict[str, str] = {}
    for raw in headers_bytes.splitlines():
        if not raw:
            continue
        try:
            key, value = raw.decode("iso-8859-1").split(":", 1)
            headers[key.strip().lower()] = value.strip()
        except ValueError:
            continue

    return method.upper(), path, version, headers

def build_response(status_code: int, reason: str, headers: Dict[str, str], body: bytes) -> bytes:
    status_line = f"HTTP/1.1 {status_code} {reason}".encode("ascii") + CRLF
    if "Content-Length" not in headers and "content-length" not in {k.lower(): v for k, v in headers.items()}:
        headers["Content-Length"] = str(len(body))
    if "Connection" not in headers:
        headers["Connection"] = "close"

    header_lines = b"".join(f"{k}: {v}".encode("ascii") + CRLF for k, v in headers.items())
    return status_line + header_lines + CRLF + body
