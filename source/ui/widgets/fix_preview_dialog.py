from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPlainTextEdit, QPushButton, QVBoxLayout

from source.core.models import FixPlan


class FixPreviewDialog(QDialog):
    def __init__(self, plans: list[FixPlan], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("수정 계획 미리보기")
        self.resize(860, 620)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlainText(self._format_plans(plans))

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.preview)
        layout.addWidget(close_button)
        self.setLayout(layout)

    def _format_plans(self, plans: list[FixPlan]) -> str:
        if not plans:
            return "아직 검사 결과가 없습니다."

        rendered_sections: list[str] = []
        for plan in plans:
            rendered_sections.append("\n".join(plan.preview_lines))

        return "\n\n".join(rendered_sections)
