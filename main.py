# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui import DevPathHelperGUI
from logger import log_action
from utils.directories import ensure_directories

def main():
    ensure_directories()
    log_action("Application started")

    app = QApplication(sys.argv)
    window = DevPathHelperGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
