from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from source.core.models import ExecutionBatchResult, ExecutionStatus, FixPlan, PlanExecutionResult
from source.platform.common.logging import log_action
from source.platform.common.runtime_paths import ensure_runtime_directories
from source.platform.win.broadcast import broadcast_environment_change
from source.platform.win.path_ops import UserPathManager, apply_actions


class FixExecutor:
    def __init__(
        self,
        path_manager: UserPathManager | None = None,
        broadcaster=broadcast_environment_change,
    ) -> None:
        self.path_manager = path_manager or UserPathManager()
        self.broadcaster = broadcaster

    def execute_plans(self, plans: list[FixPlan]) -> ExecutionBatchResult:
        actionable_plans = [plan for plan in plans if plan.is_actionable]
        if not actionable_plans:
            return ExecutionBatchResult(
                status=ExecutionStatus.SKIPPED,
                message="안전하게 자동 적용할 수정안이 없습니다.",
            )

        snapshot = self.path_manager.read_snapshot()
        snapshot_path = self._save_snapshot(snapshot.user_entries, snapshot.system_entries, actionable_plans)
        working_entries = list(snapshot.user_entries)
        plan_results: list[PlanExecutionResult] = []

        try:
            for plan in actionable_plans:
                working_entries, messages, any_changed = apply_actions(working_entries, plan.actions)
                plan_results.append(
                    PlanExecutionResult(
                        tool_id=plan.tool_id,
                        tool_name=plan.tool_name,
                        status=ExecutionStatus.SUCCESS if any_changed else ExecutionStatus.SKIPPED,
                        messages=messages,
                    )
                )

            self.path_manager.write_user_entries(working_entries, snapshot.system_entries)
            broadcast_sent = self.broadcaster()
            message = f"{len(actionable_plans)}개의 수정 계획을 적용했습니다."
            log_action(message)
            return ExecutionBatchResult(
                status=ExecutionStatus.SUCCESS,
                snapshot_path=str(snapshot_path),
                plan_results=plan_results,
                message=message,
                broadcast_sent=broadcast_sent,
            )
        except Exception as exc:
            rollback_success = self._restore_entries(snapshot.user_entries, snapshot.system_entries)
            if plan_results:
                plan_results[-1].rolled_back = rollback_success
                plan_results[-1].error_message = str(exc)
                plan_results[-1].status = ExecutionStatus.FAILED

            message = f"수정 적용 중 오류가 발생했습니다: {exc}"
            if rollback_success:
                message += " 이전 사용자 PATH 스냅샷으로 복원했습니다."
            log_action(message)
            return ExecutionBatchResult(
                status=ExecutionStatus.FAILED,
                snapshot_path=str(snapshot_path),
                plan_results=plan_results,
                message=message,
            )

    def restore_snapshot(self, snapshot_path: str | Path) -> ExecutionBatchResult:
        try:
            payload = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            user_entries = [str(entry) for entry in payload.get("user_entries", [])]
            system_entries = [str(entry) for entry in payload.get("system_entries", [])]

            self.path_manager.write_user_entries(user_entries, system_entries)
            broadcast_sent = self.broadcaster()
            message = f"스냅샷으로 사용자 PATH를 복원했습니다: {Path(snapshot_path).name}"
            log_action(message)
            return ExecutionBatchResult(
                status=ExecutionStatus.SUCCESS,
                snapshot_path=str(snapshot_path),
                message=message,
                broadcast_sent=broadcast_sent,
            )
        except Exception as exc:
            message = f"스냅샷 복원에 실패했습니다: {exc}"
            log_action(message)
            return ExecutionBatchResult(
                status=ExecutionStatus.FAILED,
                snapshot_path=str(snapshot_path),
                message=message,
            )

    def restore_latest_snapshot(self) -> ExecutionBatchResult:
        snapshots_dir = Path(ensure_runtime_directories()["snapshots"])
        snapshot_files = sorted(
            snapshots_dir.glob("user_path_snapshot_*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )

        if not snapshot_files:
            return ExecutionBatchResult(
                status=ExecutionStatus.SKIPPED,
                message="복원할 PATH 스냅샷이 아직 없습니다.",
            )

        return self.restore_snapshot(snapshot_files[0])

    def _save_snapshot(
        self,
        user_entries: list[str],
        system_entries: list[str],
        plans: list[FixPlan],
    ) -> Path:
        runtime_paths = ensure_runtime_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_path = Path(runtime_paths["snapshots"]) / f"user_path_snapshot_{timestamp}.json"
        payload = {
            "schema_version": 1,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "user_entries": user_entries,
            "system_entries": system_entries,
            "plans": [
                {
                    "tool_id": plan.tool_id,
                    "tool_name": plan.tool_name,
                    "actions": [
                        {
                            "action_type": action.action_type.value,
                            "directory": action.directory,
                            "scope": action.scope.value,
                            "position": action.position.value if action.position else None,
                            "reason": action.reason,
                        }
                        for action in plan.actions
                    ],
                }
                for plan in plans
            ],
        }
        snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return snapshot_path

    def _restore_entries(self, user_entries: list[str], system_entries: list[str]) -> bool:
        try:
            self.path_manager.write_user_entries(user_entries, system_entries)
            self.broadcaster()
            return True
        except Exception as exc:  # pragma: no cover - defensive rollback branch
            log_action(f"되돌리기에 실패했습니다: {exc}")
            return False
