"""Fake forge adapter for tests."""
from typing import Any, Mapping, Sequence
from vash.core.interfaces import ForgeAdapter, IssueRef, BoardItem, PullRequestRef

class FakeForge(ForgeAdapter):
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.issues: list[IssueRef] = []
        self.board: list[BoardItem] = []
        self.prs: list[PullRequestRef] = []

    def create_issue(self, title: str, body: str, labels: Sequence[str]) -> IssueRef:
        ref = IssueRef(number=len(self.issues) + 1, title=title, url="fake", state="open", labels=tuple(labels))
        self.issues.append(ref)
        return ref

    def list_issues(self, state: str = "open", labels: Sequence[str] = ()) -> list[IssueRef]:
        res = [i for i in self.issues if i.state == state]
        if labels:
            res = [i for i in res if all(lbl in i.labels for lbl in labels)]
        return res

    def read_board(self, board: str) -> list[BoardItem]:
        return self.board

    def open_pr(self, head: str, base: str, title: str, body: str) -> PullRequestRef:
        ref = PullRequestRef(number=len(self.prs) + 1, url="fake", head=head, base=base, state="open")
        self.prs.append(ref)
        return ref

    def merge_pr(self, number: int, method: str = "squash") -> None:
        for idx, pr in enumerate(self.prs):
            if pr.number == number:
                self.prs[idx] = PullRequestRef(number=pr.number, url=pr.url, head=pr.head, base=pr.base, state="merged")
                return

    def export_status(self) -> dict[str, Any]:
        return {"open_issues": len([i for i in self.issues if i.state == "open"]), "open_prs": len([p for p in self.prs if p.state == "open"])}
