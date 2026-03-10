from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from source.core.models import ToolState


class VersionSelectionDialog(QDialog):
    def __init__(self, state: ToolState, parent=None) -> None:
        super().__init__(parent)
        self._state = state
        self.setWindowTitle(f"{state.spec.display_name} 버전 선택")
        self.resize(820, 420)

        description_label = QLabel(
            "PATH 검색 결과가 여러 개 발견되었습니다. 우선해서 사용할 버전을 하나 선택하여주세요."
        )
        description_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self._populate_items()

        choose_button = QPushButton("선택")
        choose_button.clicked.connect(self.accept)

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(choose_button)
        button_layout.addWidget(close_button)

        layout = QVBoxLayout()
        layout.addWidget(description_label)
        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def selected_path(self) -> str:
        current_item = self.list_widget.currentItem()
        if current_item is None:
            return ""
        return str(current_item.data(Qt.ItemDataRole.UserRole) or "")

    def _populate_items(self) -> None:
        selected_detail = self._state.selected_path_detail

        for detail in self._state.path_match_details:
            item = QListWidgetItem(
                f"{detail.display_version}\n{detail.executable_path}"
            )
            item.setData(Qt.ItemDataRole.UserRole, detail.executable_path)
            item.setToolTip(f"{detail.display_version}\n{detail.executable_path}")
            self.list_widget.addItem(item)

            if selected_detail and detail.executable_path == selected_detail.executable_path:
                self.list_widget.setCurrentItem(item)

        if self.list_widget.count() and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)
