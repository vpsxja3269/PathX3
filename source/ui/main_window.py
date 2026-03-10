from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from source.core.executor import FixExecutor
from source.core.models import ExecutionBatchResult, ToolState, ToolStatus
from source.core.planner import FixPlanner
from source.core.scanner import ToolScanner
from source.core.tool_registry import ToolRegistry
from source.platform.common.logging import log_action
from source.ui.widgets.fix_preview_dialog import FixPreviewDialog
from source.ui.widgets.version_selection_dialog import VersionSelectionDialog


class PathXMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.registry = ToolRegistry()
        self.scanner = ToolScanner()
        self.planner = FixPlanner()
        self.executor = FixExecutor()
        self.tool_states: list[ToolState] = []

        self.setWindowTitle("PathX3")
        self.resize(1080, 700)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)

        self.scan_button = QPushButton("도구 검사")
        self.scan_button.clicked.connect(self.on_scan_clicked)
        self.scan_button.setToolTip("설정된 개발 도구를 검사하고 결과를 새로 고칩니다.")

        self.reload_button = QPushButton("초기화")
        self.reload_button.clicked.connect(self.on_reload_clicked)
        self.reload_button.setToolTip("프로그램의 도구 탐지 규칙을 다시 읽어 초기 상태로 정리합니다.")

        self.preview_button = QPushButton("수정 계획 미리보기")
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.preview_button.setToolTip("적용 전에 사용자 PATH 변경 내용을 먼저 확인합니다.")

        self.select_version_button = QPushButton("버전 선택")
        self.select_version_button.clicked.connect(self.on_select_version_clicked)
        self.select_version_button.setToolTip("PATH 검색 결과가 여러 개이면 사용할 버전을 직접 고릅니다.")

        self.apply_button = QPushButton("수정 적용")
        self.apply_button.clicked.connect(self.on_apply_clicked)
        self.apply_button.setToolTip("스냅샷을 만든 뒤 안전한 사용자 PATH 수정안을 적용합니다.")

        self.undo_button = QPushButton("마지막 수정 되돌리기")
        self.undo_button.clicked.connect(self.on_undo_clicked)
        self.undo_button.setToolTip("가장 최근 사용자 PATH 스냅샷으로 복원합니다.")

        for button in (
            self.scan_button,
            self.reload_button,
            self.preview_button,
            self.select_version_button,
            self.apply_button,
            self.undo_button,
        ):
            button.setMinimumHeight(42)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["도구", "상태", "탐지된 경로", "PATH 검색 결과", "버전", "진단 결과"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.ElideRight)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("실행 로그가 여기에 표시됩니다.")

        action_layout = QHBoxLayout()
        action_layout.addWidget(
            self._build_action_group(
                "1. 설정 및 검사",
                "도구 규칙이 바뀌었거나 현재 PC 상태를 다시 확인하고 싶을 때 여기서 시작합니다.",
                [self.scan_button, self.reload_button],
            )
        )
        action_layout.addWidget(
            self._build_action_group(
                "2. 검토",
                "사용자 PATH를 바꾸기 전에 어떤 수정이 예정되어 있는지 먼저 확인합니다.",
                [self.preview_button, self.select_version_button],
            )
        )
        action_layout.addWidget(
            self._build_action_group(
                "3. 적용 및 복구",
                "스냅샷을 만든 뒤 안전한 수정안을 적용하거나, 필요하면 가장 최근 상태로 되돌립니다.",
                [self.apply_button, self.undo_button],
            )
        )

        layout = QVBoxLayout()
        layout.addLayout(action_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.log_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._load_tool_catalog(clear_status=True)

    def on_reload_clicked(self) -> None:
        self._load_tool_catalog(clear_status=True)
        message = "프로그램을 초기화하였습니다. 도구 검사를 다시 진행하여주세요."
        self._set_status_message(message)
        self.append_log(message)
        log_action(message)

    def on_scan_clicked(self) -> None:
        try:
            specs = self.registry.load()
            self.tool_states = self.scanner.scan(specs)
        except Exception as exc:  # pragma: no cover - UI safety branch
            message = f"검사 중 오류가 발생했습니다: {exc}"
            self._set_status_message(message)
            self.append_log(message)
            log_action(message)
            return

        self._render_states(self.tool_states)
        ok_count = sum(1 for state in self.tool_states if state.status == ToolStatus.OK)
        warn_count = sum(1 for state in self.tool_states if state.status == ToolStatus.WARN)
        err_count = sum(1 for state in self.tool_states if state.status == ToolStatus.ERR)
        status_message = f"검사가 완료되었습니다. 정상: {ok_count}, 주의: {warn_count}, 오류: {err_count}"
        self._set_status_message(status_message)
        self.append_log(status_message)
        log_action(status_message)

    def on_preview_clicked(self) -> None:
        scanned_states = [state for state in self.tool_states if state.scanned]
        if not scanned_states:
            message = "수정 계획을 보려면 먼저 도구 검사를 실행해 주세요."
            self._set_status_message(message)
            self.append_log(message)
            log_action(message)
            return

        plans = self.planner.build_plans(scanned_states)
        if not plans:
            message = "미리보기가 필요한 진단 결과가 없습니다."
            self._set_status_message(message)
            self.append_log(message)
            log_action(message)
            return

        actionable_count = sum(1 for plan in plans if plan.is_actionable)
        dialog = FixPreviewDialog(plans, self)
        dialog.exec()

        message = f"수정 계획 {len(plans)}개를 만들었습니다. 바로 적용 가능한 계획은 {actionable_count}개입니다."
        self._set_status_message(message)
        self.append_log(message)
        log_action(message)

    def on_select_version_clicked(self) -> None:
        selected_row = self.table.currentRow()
        state = self._selected_tool_state()
        if state is None:
            message = "버전을 선택하려면 먼저 표에서 도구 한 개를 선택하여주세요."
            self.append_log(message)
            log_action(message)
            return

        if len(state.path_match_details) < 2:
            message = f"{state.spec.display_name}은(는) 선택할 PATH 검색 결과가 2개 이상일 때만 버전을 고를 수 있습니다."
            self.append_log(message)
            log_action(message)
            return

        dialog = VersionSelectionDialog(state, self)
        if dialog.exec() != VersionSelectionDialog.Accepted:
            return

        selected_path = dialog.selected_path()
        if not selected_path:
            return

        state.selected_path = selected_path
        selected_detail = state.selected_path_detail
        if selected_detail is not None:
            state.version_output = selected_detail.version_output
            state.version_command = selected_detail.version_command
            state.version_check_ok = selected_detail.version_check_ok
            state.version_check_ran = selected_detail.version_check_ran

        self._render_states(self.tool_states)
        if selected_row >= 0:
            self.table.selectRow(selected_row)

        if selected_detail is not None:
            message = (
                f"{state.spec.display_name} 우선 버전을 선택했습니다: "
                f"{selected_detail.display_version} ({selected_detail.executable_path})"
            )
            self.append_log(message)
            log_action(message)

    def on_apply_clicked(self) -> None:
        scanned_states = [state for state in self.tool_states if state.scanned]
        if not scanned_states:
            message = "수정을 적용하기 전에 먼저 도구 검사를 실행해 주세요."
            self._set_status_message(message)
            self.append_log(message)
            log_action(message)
            return

        plans = self.planner.build_plans(scanned_states)
        actionable_plans = [plan for plan in plans if plan.is_actionable]
        if not actionable_plans:
            message = "현재 검사 결과에서는 안전하게 자동 적용할 수 있는 수정안이 없습니다."
            self._set_status_message(message)
            self.append_log(message)
            log_action(message)
            return

        answer = QMessageBox.question(
            self,
            "수정 적용",
            (
                f"사용자 PATH에 수정 계획 {len(actionable_plans)}개를 적용하시겠습니까?\n\n"
                "실제 변경 전에 스냅샷을 먼저 저장합니다."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        result = self.executor.execute_plans(actionable_plans)
        self._handle_execution_result(result)

        if result.succeeded:
            self.on_scan_clicked()

    def on_undo_clicked(self) -> None:
        answer = QMessageBox.question(
            self,
            "마지막 수정 되돌리기",
            "가장 최근 사용자 PATH 스냅샷으로 복원하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        result = self.executor.restore_latest_snapshot()
        self._handle_execution_result(result)

        if result.succeeded:
            self.on_scan_clicked()

    def _load_tool_catalog(self, clear_status: bool = False) -> None:
        specs = self.registry.load()
        self.tool_states = [ToolState(spec=spec) for spec in specs]
        self._render_states(self.tool_states)

        if clear_status:
            self._set_status_message("")

    def _render_states(self, states: list[ToolState]) -> None:
        self.table.setRowCount(0)

        for state in states:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._set_table_item(row, 0, state.spec.display_name)
            self._set_table_item(row, 1, self._tool_status_text(state.status))
            self._set_table_item(
                row,
                2,
                "\n".join(state.detected_paths) if state.detected_paths else "-",
            )
            self._set_table_item(
                row,
                3,
                self._path_matches_cell_text(state),
                self._path_matches_tooltip_text(state),
            )
            self._set_table_item(
                row,
                4,
                self._version_cell_text(state),
                self._version_tooltip_text(state),
            )

            findings_text = "아직 검사를 실행하지 않았습니다."
            if state.scanned:
                findings_text = state.summary
            self._set_table_item(row, 5, findings_text)

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _set_status_message(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message.strip()))

    def _set_table_item(self, row: int, column: int, text: str, tooltip: str | None = None) -> None:
        item = QTableWidgetItem(text)
        item.setToolTip(tooltip or text)
        self.table.setItem(row, column, item)

    def _selected_tool_state(self) -> ToolState | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.tool_states):
            return None
        return self.tool_states[row]

    def _path_matches_cell_text(self, state: ToolState) -> str:
        if not state.path_match_details:
            return "-"

        selected_detail = state.selected_path_detail
        lines: list[str] = []
        for detail in state.path_match_details:
            prefix = "[선택] " if selected_detail and detail.executable_path == selected_detail.executable_path else ""
            lines.append(f"{prefix}{detail.executable_path}")
        return "\n".join(lines)

    def _path_matches_tooltip_text(self, state: ToolState) -> str:
        if not state.path_match_details:
            return "-"

        selected_detail = state.selected_path_detail
        lines: list[str] = []
        for detail in state.path_match_details:
            selected_label = "선택됨" if selected_detail and detail.executable_path == selected_detail.executable_path else "후보"
            lines.append(f"[{selected_label}] {detail.display_version}")
            lines.append(detail.executable_path)
        return "\n".join(lines)

    def _version_cell_text(self, state: ToolState) -> str:
        version_text = state.displayed_version_output
        if len(state.path_match_details) > 1:
            return f"{version_text} (후보 {len(state.path_match_details)}개)"
        return version_text

    def _version_tooltip_text(self, state: ToolState) -> str:
        if not state.path_match_details:
            return state.displayed_version_output

        selected_detail = state.selected_path_detail
        lines: list[str] = []
        for detail in state.path_match_details:
            selected_label = "선택됨" if selected_detail and detail.executable_path == selected_detail.executable_path else "후보"
            lines.append(f"[{selected_label}] {detail.display_version}")
            lines.append(detail.executable_path)
        return "\n".join(lines)

    def _tool_status_text(self, status: ToolStatus) -> str:
        status_map = {
            ToolStatus.UNKNOWN: "대기",
            ToolStatus.OK: "정상",
            ToolStatus.WARN: "주의",
            ToolStatus.ERR: "오류",
        }
        return status_map.get(status, status.value)

    def _build_action_group(
        self,
        title: str,
        description: str,
        buttons: list[QPushButton],
    ) -> QGroupBox:
        group = QGroupBox(title)

        description_label = QLabel(description)
        description_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(description_label)
        for button in buttons:
            layout.addWidget(button)
        layout.addStretch(1)

        group.setLayout(layout)
        return group

    def _handle_execution_result(self, result: ExecutionBatchResult) -> None:
        self._set_status_message(result.message)
        self.append_log(result.message)
        log_action(result.message)

        if result.snapshot_path:
            self.append_log(f"스냅샷: {result.snapshot_path}")

        for plan_result in result.plan_results:
            self.append_log(f"[{plan_result.status.value}] {plan_result.tool_name}")
            for line in plan_result.messages:
                self.append_log(f"  {line}")
            if plan_result.error_message:
                self.append_log(f"  오류: {plan_result.error_message}")
            if plan_result.rolled_back:
                self.append_log("  되돌리기: 이전 사용자 PATH를 복원했습니다.")

        if result.succeeded:
            QMessageBox.information(self, "작업 완료", result.message)
        elif result.plan_results:
            QMessageBox.warning(self, "작업 결과 확인", result.message)
