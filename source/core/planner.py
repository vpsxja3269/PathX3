from __future__ import annotations

from pathlib import Path

from source.core.models import (
    FixAction,
    FixActionType,
    FixPlan,
    FindingType,
    PathPosition,
    PathScope,
    ToolState,
)
from source.platform.common.normalize import normalize_windows_path
from source.platform.win.env import WindowsPathSnapshot, read_windows_path_snapshot


class FixPlanner:
    def build_plans(
        self,
        states: list[ToolState],
        path_snapshot: WindowsPathSnapshot | None = None,
    ) -> list[FixPlan]:
        snapshot = path_snapshot or read_windows_path_snapshot()
        return [self.build_plan(state, snapshot) for state in states if state.scanned and state.findings]

    def build_plan(
        self,
        state: ToolState,
        path_snapshot: WindowsPathSnapshot | None = None,
    ) -> FixPlan:
        snapshot = path_snapshot or read_windows_path_snapshot()
        plan = FixPlan(
            tool_id=state.spec.id,
            tool_name=state.spec.display_name,
            rollback_summary="적용 전 저장한 사용자 PATH 스냅샷으로 되돌릴 수 있습니다.",
        )
        normalized_user_entries = {
            normalize_windows_path(entry): entry for entry in snapshot.user_entries
        }
        normalized_system_entries = {
            normalize_windows_path(entry): entry for entry in snapshot.system_entries
        }

        plan.preview_lines.extend(
            [
                f"[{state.spec.display_name}]",
                f"상태: {self._status_text(state.status)}",
                f"요약: {state.summary}",
            ]
        )
        if len(state.path_match_details) > 1 and state.selected_path_detail is not None:
            selected_detail = state.selected_path_detail
            plan.preview_lines.append(
                f"선택 버전: {selected_detail.display_version} ({selected_detail.executable_path})"
            )

        for finding in state.findings:
            if finding.finding_type == FindingType.FOUND_NOT_IN_PATH:
                preferred_directory = state.preferred_path_directory
                normalized_preferred = normalize_windows_path(preferred_directory)

                if not preferred_directory:
                    plan.warnings.append("자동으로 선택할 설치 경로를 결정하지 못했습니다.")
                    continue

                if normalized_preferred in normalized_user_entries:
                    continue

                if normalized_preferred in normalized_system_entries:
                    plan.warnings.append(
                        f"{preferred_directory} 경로는 이미 시스템 PATH에 있습니다. 수동 검토가 더 안전합니다."
                    )
                    continue

                plan.actions.append(
                    FixAction(
                        action_type=FixActionType.PATH_ADD,
                        directory=preferred_directory,
                        scope=PathScope.USER,
                        position=PathPosition.BACK,
                        reason="탐지된 설치 경로가 사용자 PATH에 없습니다.",
                    )
                )

            if finding.finding_type == FindingType.PATH_INVALID:
                for broken_entry in finding.evidence:
                    normalized_entry = normalize_windows_path(broken_entry)
                    if normalized_entry in normalized_user_entries:
                        plan.actions.append(
                            FixAction(
                                action_type=FixActionType.PATH_REMOVE,
                                directory=normalized_user_entries[normalized_entry],
                                scope=PathScope.USER,
                                reason="잘못된 PATH 항목이 존재하지 않는 폴더 또는 실행 파일을 가리킵니다.",
                            )
                        )
                    elif normalized_entry in normalized_system_entries:
                        plan.warnings.append(
                            f"{broken_entry} 경로는 잘못되었지만 시스템 PATH에 있으므로 v1에서는 자동 수정하지 않습니다."
                        )

            if finding.finding_type == FindingType.MULTIPLE_FOUND:
                current_directory = str(Path(state.path_matches[0]).parent) if state.path_matches else ""
                selected_directory = state.preferred_path_directory
                normalized_current = normalize_windows_path(current_directory)
                normalized_selected = normalize_windows_path(selected_directory)

                if (
                    selected_directory
                    and normalized_selected
                    and normalized_selected != normalized_current
                ):
                    if normalized_selected in normalized_user_entries:
                        plan.actions.append(
                            FixAction(
                                action_type=FixActionType.PATH_MOVE,
                                directory=normalized_user_entries[normalized_selected],
                                scope=PathScope.USER,
                                position=PathPosition.FRONT,
                                reason="선택한 버전이 먼저 실행되도록 사용자 PATH 앞쪽으로 이동합니다.",
                            )
                        )
                    elif normalized_selected in normalized_system_entries:
                        plan.warnings.append(
                            f"{selected_directory} 경로는 시스템 PATH에 있으므로 v1에서는 자동으로 우선순위를 바꾸지 않습니다."
                        )
                    else:
                        plan.actions.append(
                            FixAction(
                                action_type=FixActionType.PATH_ADD,
                                directory=selected_directory,
                                scope=PathScope.USER,
                                position=PathPosition.FRONT,
                                reason="선택한 버전이 먼저 실행되도록 사용자 PATH 앞쪽에 추가합니다.",
                            )
                        )
                else:
                    plan.warnings.append(
                        "후보가 여러 개이므로 PATH 순서를 바꾸기 전에 수동 검토를 권장합니다."
                    )

        if plan.actions:
            plan.preview_lines.append("예정된 작업:")
            for action in plan.actions:
                if action.action_type == FixActionType.PATH_ADD:
                    plan.preview_lines.append(
                        f"- 사용자 PATH {self._position_text(action.position)} 추가: {action.directory}"
                    )
                elif action.action_type == FixActionType.PATH_REMOVE:
                    plan.preview_lines.append(f"- 사용자 PATH에서 제거: {action.directory}")
                elif action.action_type == FixActionType.PATH_MOVE:
                    plan.preview_lines.append(
                        f"- 사용자 PATH {self._position_text(action.position)} 이동: {action.directory}"
                    )
        else:
            plan.preview_lines.append("예정된 작업: 안전하게 자동 적용할 수정안이 없습니다.")

        if plan.warnings:
            plan.preview_lines.append("주의 사항:")
            for warning in plan.warnings:
                plan.preview_lines.append(f"- {warning}")

        plan.preview_lines.append(f"되돌리기: {plan.rollback_summary}")
        return plan

    def _status_text(self, status) -> str:
        status_map = {
            "OK": "정상",
            "WARN": "주의",
            "ERR": "오류",
            "UNKNOWN": "대기",
        }
        return status_map.get(status.value, status.value)

    def _position_text(self, position: PathPosition | None) -> str:
        if position == PathPosition.FRONT:
            return "앞쪽에"
        return "뒤쪽에"
