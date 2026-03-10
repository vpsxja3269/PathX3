import sys

from PySide6.QtWidgets import QApplication

from source.platform.common.logging import log_action
from source.platform.common.runtime_paths import ensure_runtime_directories
from source.ui.main_window import PathXMainWindow
from source.ui.theme import apply_light_theme


def main() -> None:
    ensure_runtime_directories()
    log_action("Application started")

    app = QApplication(sys.argv)
    apply_light_theme(app)
    window = PathXMainWindow()
    window.show()
    sys.exit(app.exec())
