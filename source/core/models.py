from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ToolStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    OK = "OK"
    WARN = "WARN"
    ERR = "ERR"


class FindingSeverity(str, Enum):
    OK = "OK"
    WARN = "WARN"
    ERR = "ERR"


class FindingType(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    FOUND_NOT_IN_PATH = "FOUND_NOT_IN_PATH"
    PATH_INVALID = "PATH_INVALID"
    MULTIPLE_FOUND = "MULTIPLE_FOUND"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class PathScope(str, Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class FixActionType(str, Enum):
    PATH_ADD = "PATH_ADD"
    PATH_REMOVE = "PATH_REMOVE"
    PATH_MOVE = "PATH_MOVE"


class PathPosition(str, Enum):
    FRONT = "FRONT"
    BACK = "BACK"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(slots=True)
class ToolSpec:
    id: str
    display_name: str
    description: str
    executables: list[str]
    version_args: list[str] = field(default_factory=lambda: ["--version"])
    candidate_paths: list[str] = field(default_factory=list)
    path_hints: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Finding:
    finding_type: FindingType
    severity: FindingSeverity
    message: str
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExecutableVersionInfo:
    executable_path: str
    version_output: str = ""
    version_command: list[str] = field(default_factory=list)
    version_check_ok: bool = False
    version_check_ran: bool = False

    @property
    def directory(self) -> str:
        return str(Path(self.executable_path).parent)

    @property
    def display_version(self) -> str:
        if self.version_output:
            return self.version_output
        if self.version_check_ran and not self.version_check_ok:
            return "버전 확인 실패"
        return "-"


@dataclass(slots=True)
class FixAction:
    action_type: FixActionType
    directory: str
    scope: PathScope = PathScope.USER
    position: PathPosition | None = None
    reason: str = ""


@dataclass(slots=True)
class FixPlan:
    tool_id: str
    tool_name: str
    scope: PathScope = PathScope.USER
    actions: list[FixAction] = field(default_factory=list)
    preview_lines: list[str] = field(default_factory=list)
    rollback_summary: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        return bool(self.actions)


@dataclass(slots=True)
class PlanExecutionResult:
    tool_id: str
    tool_name: str
    status: ExecutionStatus = ExecutionStatus.SKIPPED
    messages: list[str] = field(default_factory=list)
    error_message: str = ""
    rolled_back: bool = False


@dataclass(slots=True)
class ExecutionBatchResult:
    status: ExecutionStatus = ExecutionStatus.SKIPPED
    snapshot_path: str = ""
    plan_results: list[PlanExecutionResult] = field(default_factory=list)
    message: str = ""
    broadcast_sent: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS


@dataclass(slots=True)
class ToolState:
    spec: ToolSpec
    status: ToolStatus = ToolStatus.UNKNOWN
    detected_paths: list[str] = field(default_factory=list)
    path_matches: list[str] = field(default_factory=list)
    path_match_details: list[ExecutableVersionInfo] = field(default_factory=list)
    version_output: str = ""
    version_command: list[str] = field(default_factory=list)
    version_check_ok: bool = False
    version_check_ran: bool = False
    selected_path: str = ""
    findings: list[Finding] = field(default_factory=list)
    scanned: bool = False

    @property
    def summary(self) -> str:
        if not self.findings:
            return "문제가 발견되지 않았습니다. 정상 상태로 보입니다."
        return " / ".join(finding.message for finding in self.findings)

    @property
    def candidate_directories(self) -> list[str]:
        directories: list[str] = []
        seen: set[str] = set()

        for raw_path in [*self.path_matches, *self.detected_paths]:
            directory = str(Path(raw_path).parent)
            normalized = directory.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            directories.append(directory)

        return directories

    @property
    def preferred_path_directory(self) -> str:
        selected_detail = self.selected_path_detail
        if selected_detail is not None:
            return selected_detail.directory

        directories = self.candidate_directories
        return directories[0] if directories else ""

    @property
    def selected_path_detail(self) -> ExecutableVersionInfo | None:
        if not self.path_match_details:
            return None

        if self.selected_path:
            selected_key = self.selected_path.casefold()
            for detail in self.path_match_details:
                if detail.executable_path.casefold() == selected_key:
                    return detail

        return self.path_match_details[0]

    @property
    def displayed_version_output(self) -> str:
        selected_detail = self.selected_path_detail
        if selected_detail is not None:
            return selected_detail.display_version
        return self.version_output or "-"
