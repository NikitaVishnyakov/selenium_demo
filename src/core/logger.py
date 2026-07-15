from datetime import datetime
import logging
from pathlib import Path

LOG_DIR = Path("reports/logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_CONFIGURED = False


def setup_logger(level=logging.INFO):
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"pytest_log_{ts}.log"

    formatter = logging.Formatter(LOG_FORMAT)

    file_h = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_h.setFormatter(formatter)
    root.addHandler(file_h)

    console_h = logging.StreamHandler()
    console_h.setFormatter(formatter)
    root.addHandler(console_h)
