import socket
from datetime import datetime, timezone

from common.config import AppConfig
from common.logging_setup import get_logger

LOGGER = get_logger("udp_health.server")

class UDPHealthServer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self) -> None:
        self._sock.bind((self.config.host, self.config.udp_port))
        LOGGER.info("UDP health server listening on %s:%s", self.config.host, self.config.udp_port)

    def serve_forever(self, should_stop) -> None:
        while not should_stop():
            try:
                self._sock.settimeout(1.0)
                data, addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            payload = data.decode("utf-8", errors="ignore").strip().upper()
            if not payload:
                # Ignore empty datagrams (common with some nc variants)
                continue
            if payload == "PING":
                ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                msg = f"PONG {ts}\n".encode("utf-8")
                try:
                    self._sock.sendto(msg, addr)
                except Exception:
                    LOGGER.debug("Failed to send UDP response to %s", addr)
            else:
                # Ignore unknown messages to avoid noisy output
                continue

    def stop(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass
        LOGGER.info("UDP health server stopped")
