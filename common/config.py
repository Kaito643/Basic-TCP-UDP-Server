import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    host: str = "0.0.0.0"
    tcp_port: int = 8080
    udp_port: int = 9999
    read_timeout_seconds: int = 5
    max_request_line_bytes: int = 4096
    max_header_bytes: int = 16 * 1024
    static_dir: str = "static"

def load_config_from_env() -> AppConfig:
    host = os.getenv("HOST", "0.0.0.0")
    tcp_port = int(os.getenv("TCP_PORT", "8080"))
    udp_port = int(os.getenv("UDP_PORT", "9999"))
    read_timeout_seconds = int(os.getenv("READ_TIMEOUT", "5"))
    max_request_line_bytes = int(os.getenv("MAX_REQUEST_LINE_BYTES", "4096"))
    max_header_bytes = int(os.getenv("MAX_HEADER_BYTES", str(16 * 1024)))
    static_dir = os.getenv("STATIC_DIR", "static")
    return AppConfig(
        host=host,
        tcp_port=tcp_port,
        udp_port=udp_port,
        read_timeout_seconds=read_timeout_seconds,
        max_request_line_bytes=max_request_line_bytes,
        max_header_bytes=max_header_bytes,
        static_dir=static_dir,
    )
