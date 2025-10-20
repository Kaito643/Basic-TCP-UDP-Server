import signal
import threading

class ShutdownFlag:
    def __init__(self) -> None:
        self._event = threading.Event()

    def set(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

def install_signal_handlers(flag: ShutdownFlag) -> None:
    def handler(_signum, _frame):
        flag.set()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handler)
