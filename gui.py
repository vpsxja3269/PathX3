# gui.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView
)

from logger import log_action

class DevPathHelperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DevPATH Helper")
        self.resize(800, 500)

        self.status_label = QLabel("아직 스캔하지 않았습니다.")

        self.scan_button = QPushButton("도구 스캔")
        self.scan_button.clicked.connect(self.on_scan_clicked)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Tool", "Status", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.scan_button)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_scan_clicked(self):
        # 아직은 더미 데이터
        dummy_data = [
            ("Python", "✅ Installed (PATH OK)", r"C:\Python39\python.exe"),
            ("Git", "❌ Installed (PATH Missing)", r"C:\Program Files\Git\cmd\git.exe"),
        ]

        self.table.setRowCount(0)
        for name, status, path in dummy_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(status))
            self.table.setItem(row, 2, QTableWidgetItem(path))

        self.status_label.setText("더미 스캔 결과를 표시했습니다.")
        log_action("Dummy scan executed")
