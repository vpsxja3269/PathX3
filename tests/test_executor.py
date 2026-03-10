from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source.core.executor import FixExecutor
from source.core.models import ExecutionStatus, FixAction, FixActionType, FixPlan, PathPosition, PathScope
from source.platform.win.env import WindowsPathSnapshot


class FakePathManager:
    def __init__(self) -> None:
        self.snapshot = WindowsPathSnapshot(
            user_entries=[r"C:\BrokenPython39", r"C:\Tools\Git\cmd"],
            system_entries=[r"C:\Windows\System32"],
            process_entries=[],
        )
        self.write_history: list[list[str]] = []

    def read_snapshot(self) -> WindowsPathSnapshot:
        return self.snapshot

    def write_user_entries(self, entries: list[str], system_entries: list[str] | None = None) -> None:
        self.write_history.append(list(entries))
        self.snapshot = WindowsPathSnapshot(
            user_entries=list(entries),
            system_entries=list(system_entries or self.snapshot.system_entries),
            process_entries=[],
        )


class FixExecutorTests(unittest.TestCase):
    def test_execute_plans_saves_snapshot_and_applies_changes(self) -> None:
        manager = FakePathManager()
        executor = FixExecutor(path_manager=manager, broadcaster=lambda: True)
        plan = FixPlan(
            tool_id="python",
            tool_name="Python",
            actions=[
                FixAction(
                    action_type=FixActionType.PATH_REMOVE,
                    directory=r"C:\BrokenPython39",
                    scope=PathScope.USER,
                ),
                FixAction(
                    action_type=FixActionType.PATH_ADD,
                    directory=r"C:\Users\Test\AppData\Local\Programs\Python\Python311",
                    scope=PathScope.USER,
                    position=PathPosition.BACK,
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_paths = {"snapshots": temp_dir}
            with patch("source.core.executor.ensure_runtime_directories", return_value=runtime_paths):
                with patch("source.core.executor.log_action"):
                    result = executor.execute_plans([plan])

            self.assertEqual(ExecutionStatus.SUCCESS, result.status)
            self.assertTrue(Path(result.snapshot_path).exists())
            self.assertEqual(
                [r"C:\Tools\Git\cmd", r"C:\Users\Test\AppData\Local\Programs\Python\Python311"],
                manager.snapshot.user_entries,
            )

            payload = json.loads(Path(result.snapshot_path).read_text(encoding="utf-8"))
            self.assertEqual([r"C:\BrokenPython39", r"C:\Tools\Git\cmd"], payload["user_entries"])
            self.assertEqual("python", payload["plans"][0]["tool_id"])

    def test_restore_latest_snapshot_restores_previous_user_path(self) -> None:
        manager = FakePathManager()
        executor = FixExecutor(path_manager=manager, broadcaster=lambda: True)
        plan = FixPlan(
            tool_id="python",
            tool_name="Python",
            actions=[
                FixAction(
                    action_type=FixActionType.PATH_REMOVE,
                    directory=r"C:\BrokenPython39",
                    scope=PathScope.USER,
                )
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_paths = {"snapshots": temp_dir}
            with patch("source.core.executor.ensure_runtime_directories", return_value=runtime_paths):
                with patch("source.core.executor.log_action"):
                    execute_result = executor.execute_plans([plan])
                    self.assertEqual(ExecutionStatus.SUCCESS, execute_result.status)
                    self.assertEqual([r"C:\Tools\Git\cmd"], manager.snapshot.user_entries)

                    restore_result = executor.restore_latest_snapshot()

        self.assertEqual(ExecutionStatus.SUCCESS, restore_result.status)
        self.assertEqual([r"C:\BrokenPython39", r"C:\Tools\Git\cmd"], manager.snapshot.user_entries)

    def test_skips_when_no_actionable_plan_exists(self) -> None:
        executor = FixExecutor(path_manager=FakePathManager(), broadcaster=lambda: True)
        plan = FixPlan(tool_id="git", tool_name="Git", actions=[])

        with patch("source.core.executor.log_action"):
            result = executor.execute_plans([plan])

        self.assertEqual(ExecutionStatus.SKIPPED, result.status)


if __name__ == "__main__":
    unittest.main()
