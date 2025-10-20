import socket
import threading
from typing import Tuple

from common.config import AppConfig
from common.logging_setup import get_logger
from tcp_http.http_utils import parse_http_request, build_response
from tcp_http.handlers import route_request, headify

LOGGER = get_logger("tcp_http.server")

class ThreadedHTTPServer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._threads: list[threading.Thread] = []
        self._closing = threading.Event()

    def start(self) -> None:
        self._sock.bind((self.config.host, self.config.tcp_port))
        self._sock.listen(128)
        LOGGER.info("HTTP server listening on %s:%s", self.config.host, self.config.tcp_port)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self) -> None:
        while not self._closing.is_set():
            try:
                client, addr = self._sock.accept()
                t = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
                t.start()
                self._threads.append(t)
            except OSError:
                break

    def _handle_client(self, client: socket.socket, addr: Tuple[str, int]) -> None:
        client.settimeout(self.config.read_timeout_seconds)
        try:
            buf = client.makefile("rb")
            method, path, _version, _headers = parse_http_request(
                stream=buf,
                max_request_line=self.config.max_request_line_bytes,
                max_headers=self.config.max_header_bytes,
                read_timeout=self.config.read_timeout_seconds,
            )

            if method not in ("GET", "HEAD"):
                body = b"Method Not Allowed"
                resp = build_response(
                    405,
                    "Method Not Allowed",
                    {"Content-Type": "text/plain; charset=utf-8"},
                    body,
                )
                client.sendall(resp)
                return

            response = route_request(method, path, self.config)
            if method == "HEAD":
                response = headify(response)

            status, reason, content_type, body = response
            headers = {"Content-Type": content_type}
            if method == "HEAD":
                headers["Content-Length"] = str(len(route_request("GET", path, self.config)[3]))
            resp = build_response(status, reason, headers, body)
            client.sendall(resp)
        except Exception as exc:
            LOGGER.warning("Client error from %s: %s", addr, exc)
            try:
                resp = build_response(
                    400, "Bad Request",
                    {"Content-Type": "text/plain; charset=utf-8"},
                    b"Bad Request",
                )
                client.sendall(resp)
            except Exception:
                pass
        finally:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            client.close()

    def stop(self) -> None:
        self._closing.set()
        try:
            self._sock.close()
        except Exception:
            pass
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=1.0)
        LOGGER.info("HTTP server stopped")
