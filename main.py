import argparse
import threading
import time

from common.config import load_config_from_env, AppConfig
from common.logging_setup import setup_logging, get_logger
from common.signals import ShutdownFlag, install_signal_handlers
from tcp_http.server import ThreadedHTTPServer
from udp_health.server import UDPHealthServer

LOGGER = get_logger("main")

def parse_args():
    p = argparse.ArgumentParser(description="TCP HTTP + UDP Health servers (stdlib)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--tcp", action="store_true", help="Run only TCP HTTP server")
    mode.add_argument("--udp", action="store_true", help="Run only UDP health server")
    mode.add_argument("--both", action="store_true", help="Run both servers")
    p.add_argument("--host", default=None)
    p.add_argument("--tcp-port", type=int, default=None)
    p.add_argument("--udp-port", type=int, default=None)
    p.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR")
    return p.parse_args()

def build_config(args) -> AppConfig:
    env = load_config_from_env()
    return AppConfig(
        host=args.host or env.host,
        tcp_port=args.tcp_port or env.tcp_port,
        udp_port=args.udp_port or env.udp_port,
        read_timeout_seconds=env.read_timeout_seconds,
        max_request_line_bytes=env.max_request_line_bytes,
        max_header_bytes=env.max_header_bytes,
        static_dir=env.static_dir,
    )

def main():
    args = parse_args()
    setup_logging(args.log_level)
    config = build_config(args)

    flag = ShutdownFlag()
    install_signal_handlers(flag)

    run_tcp = args.tcp or args.both or (not args.tcp and not args.udp and not args.both)
    run_udp = args.udp or args.both or (not args.tcp and not args.udp and not args.both)

    threads: list[threading.Thread] = []
    http_server = None
    udp_server = None

    if run_tcp:
        http_server = ThreadedHTTPServer(config)
        http_server.start()

    if run_udp:
        udp_server = UDPHealthServer(config)
        udp_server.start()
        t = threading.Thread(target=udp_server.serve_forever, args=(flag.is_set,), daemon=True)
        t.start()
        threads.append(t)

    LOGGER.info("Servers up. Press Ctrl+C to stop.")
    try:
        while not flag.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        flag.set()

    if http_server:
        http_server.stop()
    if udp_server:
        udp_server.stop()
    for t in threads:
        if t.is_alive():
            t.join(timeout=1.0)
    LOGGER.info("Exited cleanly")

if __name__ == "__main__":
    main()
