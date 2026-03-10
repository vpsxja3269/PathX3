from __future__ import annotations

import unittest

from source.core.models import (
    ExecutableVersionInfo,
    Finding,
    FindingSeverity,
    FindingType,
    FixActionType,
    PathPosition,
    PathScope,
    ToolSpec,
    ToolState,
    ToolStatus,
)
from source.core.planner import FixPlanner
from source.platform.win.env import WindowsPathSnapshot


def build_state(*, detected_paths=None, findings=None, status=ToolStatus.WARN) -> ToolState:
    spec = ToolSpec(
        id="python",
        display_name="Python",
        description="Python interpreter",
        executables=["python.exe"],
        candidate_paths=[],
        path_hints=[],
    )
    return ToolState(
        spec=spec,
        status=status,
        detected_paths=detected_paths or [],
        findings=findings or [],
        scanned=True,
    )


class FixPlannerTests(unittest.TestCase):
    def test_builds_path_add_for_detected_tool_missing_from_path(self) -> None:
        install_path = r"C:\Users\Test\AppData\Local\Programs\Python\Python311\python.exe"
        state = build_state(
            detected_paths=[install_path],
            findings=[
                Finding(
                    finding_type=FindingType.FOUND_NOT_IN_PATH,
                    severity=FindingSeverity.WARN,
                    message="Python is installed but is not registered in PATH.",
                    evidence=[install_path],
                )
            ],
        )

        plan = FixPlanner().build_plan(state, WindowsPathSnapshot())

        self.assertTrue(plan.is_actionable)
        self.assertEqual(1, len(plan.actions))
        action = plan.actions[0]
        self.assertEqual(FixActionType.PATH_ADD, action.action_type)
        self.assertEqual(PathScope.USER, action.scope)
        self.assertEqual(PathPosition.BACK, action.position)
        self.assertIn(r"C:\Users\Test\AppData\Local\Programs\Python\Python311", action.directory)

    def test_builds_user_path_remove_for_broken_entry(self) -> None:
        broken_entry = r"C:\Users\Test\AppData\Local\Programs\Python\Python39"
        state = build_state(
            findings=[
                Finding(
                    finding_type=FindingType.PATH_INVALID,
                    severity=FindingSeverity.WARN,
                    message="Python has stale or invalid PATH entries.",
                    evidence=[broken_entry],
                )
            ],
        )
        snapshot = WindowsPathSnapshot(user_entries=[broken_entry], system_entries=[])

        plan = FixPlanner().build_plan(state, snapshot)

        self.assertEqual(1, len(plan.actions))
        self.assertEqual(FixActionType.PATH_REMOVE, plan.actions[0].action_type)
        self.assertEqual(broken_entry, plan.actions[0].directory)

    def test_warns_for_system_path_entry_without_auto_fixing(self) -> None:
        broken_system_entry = r"C:\Program Files\Python39"
        state = build_state(
            findings=[
                Finding(
                    finding_type=FindingType.PATH_INVALID,
                    severity=FindingSeverity.WARN,
                    message="Python has stale or invalid PATH entries.",
                    evidence=[broken_system_entry],
                ),
                Finding(
                    finding_type=FindingType.MULTIPLE_FOUND,
                    severity=FindingSeverity.WARN,
                    message="Python has multiple candidates.",
                    evidence=[],
                ),
            ],
        )
        snapshot = WindowsPathSnapshot(user_entries=[], system_entries=[broken_system_entry])

        plan = FixPlanner().build_plan(state, snapshot)

        self.assertFalse(plan.is_actionable)
        self.assertTrue(any("시스템 PATH" in warning for warning in plan.warnings))
        self.assertTrue(any("후보가 여러 개" in warning for warning in plan.warnings))

    def test_moves_selected_version_to_front_when_user_chooses_different_path_match(self) -> None:
        current_path = r"C:\Python39\python.exe"
        selected_path = r"C:\Python311\python.exe"
        state = build_state(
            findings=[
                Finding(
                    finding_type=FindingType.MULTIPLE_FOUND,
                    severity=FindingSeverity.WARN,
                    message="Python has multiple candidates.",
                    evidence=[current_path, selected_path],
                )
            ],
        )
        state.path_matches = [current_path, selected_path]
        state.path_match_details = [
            ExecutableVersionInfo(
                executable_path=current_path,
                version_output="Python 3.9.13",
                version_check_ok=True,
                version_check_ran=True,
            ),
            ExecutableVersionInfo(
                executable_path=selected_path,
                version_output="Python 3.11.7",
                version_check_ok=True,
                version_check_ran=True,
            ),
        ]
        state.selected_path = selected_path

        snapshot = WindowsPathSnapshot(
            user_entries=[r"C:\Python39", r"C:\Python311"],
            system_entries=[],
        )
        plan = FixPlanner().build_plan(state, snapshot)

        self.assertTrue(plan.is_actionable)
        self.assertEqual(FixActionType.PATH_MOVE, plan.actions[0].action_type)
        self.assertEqual(PathPosition.FRONT, plan.actions[0].position)
        self.assertEqual(r"C:\Python311", plan.actions[0].directory)


if __name__ == "__main__":
    unittest.main()
