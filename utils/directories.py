import os

BASE_DIR = r"C:\PathX3"
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

def ensure_directories() -> dict:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    return {
        "base": BASE_DIR,
        "backup": BACKUP_DIR,
        "logs": LOG_DIR,
        "settings": SETTINGS_PATH,
    }
