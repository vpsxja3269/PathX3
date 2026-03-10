from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from source.core.diagnoser import ToolDiagnoser
from source.core.models import FindingType, ToolSpec, ToolState, ToolStatus
from source.platform.win.env import WindowsPathSnapshot


def build_tool_spec(path_hints: list[str] | None = None) -> ToolSpec:
    return ToolSpec(
        id="python",
        display_name="Python",
        description="Python interpreter",
        executables=["python.exe"],
        candidate_paths=[],
        path_hints=path_hints or [],
    )


class ToolDiagnoserTests(unittest.TestCase):
    def test_marks_detected_but_missing_path_as_warning(self) -> None:
        spec = build_tool_spec()
        state = ToolState(
            spec=spec,
            detected_paths=[r"C:\Users\Test\AppData\Local\Programs\Python\Python311\python.exe"],
            path_matches=[],
            scanned=True,
        )

        diagnosed = ToolDiagnoser().diagnose(state, WindowsPathSnapshot())
        finding_types = {finding.finding_type for finding in diagnosed.findings}

        self.assertEqual(ToolStatus.WARN, diagnosed.status)
        self.assertIn(FindingType.FOUND_NOT_IN_PATH, finding_types)

    def test_marks_stale_path_entries_as_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "Python311"
            install_dir.mkdir()
            executable_path = install_dir / "python.exe"
            executable_path.write_text("", encoding="utf-8")

            broken_dir = Path(temp_dir) / "Python39"
            spec = build_tool_spec(path_hints=[str(broken_dir)])
            state = ToolState(
                spec=spec,
                path_matches=[str(executable_path)],
                version_check_ran=True,
                version_check_ok=True,
                scanned=True,
            )
            snapshot = WindowsPathSnapshot(user_entries=[str(broken_dir)])

            diagnosed = ToolDiagnoser().diagnose(state, snapshot)
            findings = {finding.finding_type: finding for finding in diagnosed.findings}

            self.assertEqual(ToolStatus.WARN, diagnosed.status)
            self.assertIn(FindingType.PATH_INVALID, findings)
            self.assertIn(str(broken_dir), findings[FindingType.PATH_INVALID].evidence)

    def test_keeps_healthy_state_as_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "Python311"
            install_dir.mkdir()
            executable_path = install_dir / "python.exe"
            executable_path.write_text("", encoding="utf-8")

            spec = build_tool_spec(path_hints=[str(install_dir)])
            state = ToolState(
                spec=spec,
                path_matches=[str(executable_path)],
                version_check_ran=True,
                version_check_ok=True,
                scanned=True,
            )
            snapshot = WindowsPathSnapshot(user_entries=[str(install_dir)])

            diagnosed = ToolDiagnoser().diagnose(state, snapshot)

            self.assertEqual(ToolStatus.OK, diagnosed.status)
            self.assertEqual([], diagnosed.findings)


if __name__ == "__main__":
    unittest.main()
