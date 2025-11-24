import os
import datetime
from utils.directories import ensure_directories

paths = ensure_directories()
LOG_FILE = os.path.join(paths["logs"], "usage_log.txt")

def log_action(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
