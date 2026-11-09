"""VASH adapter interfaces (C-03)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Mapping, Any


@dataclass(frozen=True)
class IssueRef:
    number: int
    title: str
    url: str
    state: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class BoardItem:
    item_id: str
    title: str
    status: str
    issue_number: int | None


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    url: str
    head: str
    base: str
    state: str


@dataclass(frozen=True)
class RunRef:
    run_id: str
    url: str


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    conclusion: str | None
    url: str


@dataclass(frozen=True)
class CloudPlan:
    environment: str
    summary: str
    changes: int


@dataclass(frozen=True)
class VersionCheck:
    tool: str
    expected: str
    found: str | None
    ok: bool


@dataclass(frozen=True)
class RouteSettings:
    name: str
    adapter: str
    model: str
    vendor: str
    base_url: str | None
    key_env: str | None
    timeout_s: int


@dataclass(frozen=True)
class LLMReply:
    text: str
    route: str
    model: str
    degraded: bool
    usage: Mapping[str, int]


class ForgeAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def create_issue(self, title: str, body: str, labels: Sequence[str]) -> IssueRef: pass
    @abstractmethod
    def list_issues(self, state: str = "open", labels: Sequence[str] = ()) -> list[IssueRef]: pass
    @abstractmethod
    def read_board(self, board: str) -> list[BoardItem]: pass
    @abstractmethod
    def open_pr(self, head: str, base: str, title: str, body: str) -> PullRequestRef: pass
    @abstractmethod
    def merge_pr(self, number: int, method: str = "squash") -> None: pass
    @abstractmethod
    def export_status(self) -> dict[str, Any]: pass


class CIAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def start_run(self, workflow: str, ref: str, inputs: Mapping[str, str]) -> RunRef: pass
    @abstractmethod
    def get_run(self, run_id: str) -> RunResult: pass
    @abstractmethod
    def register_runner(self, labels: Sequence[str]) -> str | None: pass
    @abstractmethod
    def install_hooks(self, repo_root: Path) -> list[Path]: pass


class CloudAdapter(ABC):
    """Cloud adapter.

    apply() and destroy() raise FreezeInvalid with a fix text when
    approved is False (C-03).
    """
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def plan(self, environment: str) -> CloudPlan: pass
    @abstractmethod
    def apply(self, environment: str, approved: bool) -> dict[str, Any]: pass
    @abstractmethod
    def destroy(self, environment: str, approved: bool) -> None: pass
    @abstractmethod
    def outputs(self, environment: str) -> dict[str, Any]: pass


class LLMAdapter(ABC):
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def reply(self, prompt: str, route: RouteSettings) -> LLMReply: pass


class StackPack(ABC):
    """Stack pack (C-03)."""
    def __init__(self, settings: Mapping[str, Any]):
        self.settings = settings

    @abstractmethod
    def manifest(self) -> dict[str, Any]: pass
    @abstractmethod
    def check_versions(self) -> list[VersionCheck]: pass
    @abstractmethod
    def outputs_layout(self) -> list[str]: pass


CATEGORY_INTERFACES = {
    "forge": ForgeAdapter,
    "ci": CIAdapter,
    "cloud": CloudAdapter,
    "llm": LLMAdapter,
}
