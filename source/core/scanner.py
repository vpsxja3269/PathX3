from __future__ import annotations

import glob
import os

from source.core.diagnoser import ToolDiagnoser
from source.core.models import ExecutableVersionInfo, ToolSpec, ToolState
from source.core.validator import ToolValidator
from source.platform.common.fs import unique_existing_paths
from source.platform.win.env import WindowsPathSnapshot, read_windows_path_snapshot


class ToolScanner:
    def __init__(
        self,
        validator: ToolValidator | None = None,
        diagnoser: ToolDiagnoser | None = None,
    ) -> None:
        self.validator = validator or ToolValidator()
        self.diagnoser = diagnoser or ToolDiagnoser()

    def scan(self, specs: list[ToolSpec]) -> list[ToolState]:
        path_snapshot = read_windows_path_snapshot()
        return [self.scan_one(spec, path_snapshot) for spec in specs]

    def scan_one(self, spec: ToolSpec, path_snapshot: WindowsPathSnapshot | None = None) -> ToolState:
        detected_paths = self._detect_candidates(spec)
        path_matches = self._resolve_path_matches(spec)
        path_match_details = self._read_executable_details(path_matches, spec.version_args)

        version_output = ""
        version_command: list[str] = []
        version_check_ok = False
        version_check_ran = False
        selected_path = path_matches[0] if path_matches else ""

        selected_detail = path_match_details[0] if path_match_details else None
        if selected_detail is not None:
            version_output = selected_detail.version_output
            version_command = selected_detail.version_command
            version_check_ran = selected_detail.version_check_ran
            version_check_ok = selected_detail.version_check_ok
        else:
            version_target = detected_paths[0] if detected_paths else ""
            if version_target:
                detail = self._read_executable_detail(version_target, spec.version_args)
                version_output = detail.version_output
                version_command = detail.version_command
                version_check_ran = detail.version_check_ran
                version_check_ok = detail.version_check_ok

        state = ToolState(
            spec=spec,
            detected_paths=detected_paths,
            path_matches=path_matches,
            path_match_details=path_match_details,
            version_output=version_output,
            version_command=version_command,
            version_check_ok=version_check_ok,
            version_check_ran=version_check_ran,
            selected_path=selected_path,
            scanned=True,
        )
        return self.diagnoser.diagnose(state, path_snapshot=path_snapshot)

    def _detect_candidates(self, spec: ToolSpec) -> list[str]:
        matches: list[str] = []
        for candidate_pattern in spec.candidate_paths:
            matches.extend(glob.glob(os.path.expandvars(candidate_pattern)))
        return unique_existing_paths(matches)

    def _resolve_path_matches(self, spec: ToolSpec) -> list[str]:
        matches: list[str] = []
        for executable_name in spec.executables:
            matches.extend(self.validator.locate_on_path(executable_name))
        return unique_existing_paths(matches)

    def _read_executable_details(
        self,
        executable_paths: list[str],
        version_args: list[str],
    ) -> list[ExecutableVersionInfo]:
        return [self._read_executable_detail(path, version_args) for path in executable_paths]

    def _read_executable_detail(
        self,
        executable_path: str,
        version_args: list[str],
    ) -> ExecutableVersionInfo:
        version_result = self.validator.read_version(executable_path, version_args)
        version_output = (version_result.stdout or version_result.stderr).strip()
        version_check_ok = version_result.return_code == 0 and not version_result.timed_out

        return ExecutableVersionInfo(
            executable_path=executable_path,
            version_output=version_output,
            version_command=version_result.command,
            version_check_ok=version_check_ok,
            version_check_ran=True,
        )
