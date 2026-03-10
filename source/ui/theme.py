from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_light_theme(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f5f7fb"))
    palette.setColor(QPalette.WindowText, QColor("#1f2937"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#eef2f7"))
    palette.setColor(QPalette.ToolTipBase, QColor("#fffce8"))
    palette.setColor(QPalette.ToolTipText, QColor("#1f2937"))
    palette.setColor(QPalette.Text, QColor("#111827"))
    palette.setColor(QPalette.Button, QColor("#e9eef5"))
    palette.setColor(QPalette.ButtonText, QColor("#111827"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor("#6b7280"))
    palette.setColor(QPalette.Light, QColor("#ffffff"))
    palette.setColor(QPalette.Midlight, QColor("#d7dee8"))
    palette.setColor(QPalette.Mid, QColor("#b8c2cf"))
    palette.setColor(QPalette.Dark, QColor("#8a94a3"))
    palette.setColor(QPalette.Shadow, QColor("#5f6b7a"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            background-color: #f5f7fb;
            color: #111827;
            font-size: 10pt;
        }
        QMainWindow, QDialog {
            background-color: #f5f7fb;
        }
        QLabel {
            color: #111827;
        }
        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #d7dee8;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: #1f2937;
        }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #c9d4e2;
            border-radius: 8px;
            padding: 10px 14px;
            color: #111827;
        }
        QPushButton:hover {
            background-color: #f0f6ff;
            border-color: #8cb4ff;
        }
        QPushButton:pressed {
            background-color: #dbeafe;
        }
        QTableWidget, QPlainTextEdit {
            background-color: #ffffff;
            alternate-background-color: #f7f9fc;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            gridline-color: #e5e7eb;
        }
        QHeaderView::section {
            background-color: #edf2f7;
            color: #1f2937;
            border: none;
            border-right: 1px solid #d7dee8;
            border-bottom: 1px solid #d7dee8;
            padding: 8px;
            font-weight: 600;
        }
        QTableWidget::item:selected {
            background-color: #dbeafe;
            color: #111827;
        }
        QScrollBar:vertical, QScrollBar:horizontal {
            background: #eef2f7;
            border-radius: 6px;
            margin: 0;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #c4cfdd;
            border-radius: 6px;
            min-height: 24px;
            min-width: 24px;
        }
        QToolTip {
            background-color: #fffce8;
            color: #111827;
            border: 1px solid #e5d96f;
            padding: 6px;
        }
        """
    )

    app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
