from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path, PureWindowsPath

from source.core.models import Finding, FindingSeverity, FindingType, ToolState, ToolStatus
from source.platform.common.normalize import normalize_windows_path
from source.platform.win.env import WindowsPathSnapshot, read_windows_path_snapshot


class ToolDiagnoser:
    def diagnose(
        self,
        state: ToolState,
        path_snapshot: WindowsPathSnapshot | None = None,
    ) -> ToolState:
        snapshot = path_snapshot or read_windows_path_snapshot()
        findings: list[Finding] = []

        if not state.detected_paths and not state.path_matches:
            findings.append(
                Finding(
                    finding_type=FindingType.NOT_FOUND,
                    severity=FindingSeverity.ERR,
                    message=(
                        f"{state.spec.display_name}을(를) 일반적인 설치 경로와 PATH에서 찾지 못했습니다."
                    ),
                    evidence=state.spec.executables,
                )
            )

        if state.detected_paths and not state.path_matches:
            findings.append(
                Finding(
                    finding_type=FindingType.FOUND_NOT_IN_PATH,
                    severity=FindingSeverity.WARN,
                    message=f"{state.spec.display_name}은(는) 설치되어 있지만 PATH에 등록되어 있지 않습니다.",
                    evidence=state.detected_paths,
                )
            )

        invalid_entries = self._find_invalid_path_entries(state, snapshot)
        if invalid_entries:
            findings.append(
                Finding(
                    finding_type=FindingType.PATH_INVALID,
                    severity=FindingSeverity.WARN,
                    message=f"{state.spec.display_name} 관련 PATH 항목에 오래되었거나 잘못된 경로가 있습니다.",
                    evidence=invalid_entries,
                )
            )

        if len(state.detected_paths) > 1 or len(state.path_matches) > 1:
            findings.append(
                Finding(
                    finding_type=FindingType.MULTIPLE_FOUND,
                    severity=FindingSeverity.WARN,
                    message=f"{state.spec.display_name} 후보가 여러 개 발견되었습니다.",
                    evidence=[*state.detected_paths, *state.path_matches],
                )
            )

        if state.version_check_ran and not state.version_check_ok:
            findings.append(
                Finding(
                    finding_type=FindingType.EXECUTION_FAILED,
                    severity=FindingSeverity.WARN,
                    message=(
                        f"{state.spec.display_name}은(는) 찾았지만 버전 확인 명령이 정상적으로 끝나지 않았습니다."
                    ),
                    evidence=[" ".join(state.version_command)] if state.version_command else [],
                )
            )

        state.findings = findings
        state.status = self._derive_status(findings)
        return state

    def _derive_status(self, findings: list[Finding]) -> ToolStatus:
        if not findings:
            return ToolStatus.OK
        if any(finding.severity == FindingSeverity.ERR for finding in findings):
            return ToolStatus.ERR
        if any(finding.severity == FindingSeverity.WARN for finding in findings):
            return ToolStatus.WARN
        return ToolStatus.OK

    def _find_invalid_path_entries(
        self,
        state: ToolState,
        snapshot: WindowsPathSnapshot,
    ) -> list[str]:
        invalid_entries: list[str] = []
        hint_patterns = [normalize_windows_path(hint) for hint in state.spec.path_hints]

        for entry in snapshot.combined_entries:
            normalized_entry = normalize_windows_path(entry)
            if hint_patterns and not any(
                self._matches_hint(normalized_entry, pattern) for pattern in hint_patterns
            ):
                continue

            entry_path = Path(entry)
            if not entry_path.exists():
                invalid_entries.append(entry)
                continue

            if not any((entry_path / executable_name).exists() for executable_name in state.spec.executables):
                invalid_entries.append(entry)

        return self._unique_case_insensitive(invalid_entries)

    def _matches_hint(self, normalized_entry: str, pattern: str) -> bool:
        if not fnmatch(normalized_entry, pattern):
            return False

        return len(PureWindowsPath(normalized_entry).parts) == len(PureWindowsPath(pattern).parts)

    def _unique_case_insensitive(self, paths: list[str]) -> list[str]:
        unique_paths: list[str] = []
        seen: set[str] = set()

        for raw_path in paths:
            normalized = normalize_windows_path(raw_path)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(str(Path(raw_path)))

        return unique_paths
