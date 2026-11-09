"""GitHub forge adapter over the REST and GraphQL APIs."""
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Mapping, Sequence
from vash.core.interfaces import ForgeAdapter, IssueRef, BoardItem, PullRequestRef
from vash.core.exceptions import VashError, RouteUnavailable

class Adapter(ForgeAdapter):
    """GitHub forge adapter."""
    def __init__(self, settings: Mapping[str, Any]):
        super().__init__(settings)
        self.repo = self.settings.get("repo", "")
        self.timeout_s = int(self.settings.get("timeout_s", 30))
        self.base_url = "https://api.github.com"
        if not self.repo or "/" not in self.repo:
            raise VashError(
                f"Invalid or missing repo setting: {self.repo}",
                "Set forge.settings.repo to 'owner/name'"
            )

    def _request(self, method: str, path: str, data: dict | None = None) -> Any:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise RouteUnavailable(
                "GITHUB_TOKEN environment variable is missing",
                "Set GITHUB_TOKEN to a valid personal access token"
            )
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "VASH-Engine"
        }
        req_data = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise VashError(
                f"GitHub API error {e.code}: {body}",
                "Check API limits or token permissions"
            )
        except (urllib.error.URLError, TimeoutError) as e:
            raise RouteUnavailable(
                f"GitHub connection failed: {e}",
                "Check network connection"
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise VashError(
                f"Invalid JSON response from GitHub: {e}",
                "The API may be degraded"
            )

    def _paginate(self, path: str) -> list[Any]:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise RouteUnavailable(
                "GITHUB_TOKEN environment variable is missing",
                "Set GITHUB_TOKEN to a valid personal access token"
            )
        results = []
        next_url = path
        while next_url:
            if next_url.startswith("https://"):
                req = urllib.request.Request(next_url)
            else:
                req = urllib.request.Request(f"{self.base_url}{next_url}")
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "VASH-Engine")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    results.extend(res)
                    link = response.headers.get("Link", "")
                    next_url = ""
                    if 'rel="next"' in link:
                        for part in link.split(","):
                            if 'rel="next"' in part:
                                next_url = part.split(";")[0].strip(" <>")
                                break
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                raise VashError(
                    f"GitHub API error {e.code}: {body}",
                    "Check API limits or token permissions"
                )
            except (urllib.error.URLError, TimeoutError) as e:
                raise RouteUnavailable(
                    f"GitHub connection failed: {e}",
                    "Check network connection"
                )
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                raise VashError(
                    f"Invalid JSON response from GitHub: {e}",
                    "The API may be degraded"
                )
        return results

    def create_issue(self, title: str, body: str, labels: Sequence[str]) -> IssueRef:
        data = {"title": title, "body": body, "labels": list(labels)}
        res = self._request("POST", f"/repos/{self.repo}/issues", data)
        return IssueRef(
            number=res["number"], title=res["title"], url=res["html_url"],
            state=res["state"], labels=tuple(lbl["name"] for lbl in res.get("labels", []))
        )

    def list_issues(self, state: str = "open", labels: Sequence[str] = ()) -> list[IssueRef]:
        params = {"state": state, "per_page": "100"}
        if labels:
            params["labels"] = ",".join(labels)
        path = f"/repos/{self.repo}/issues?{urllib.parse.urlencode(params)}"
        res = self._paginate(path)
        return [
            IssueRef(
                number=i["number"], title=i["title"], url=i["html_url"],
                state=i["state"], labels=tuple(lbl["name"] for lbl in i.get("labels", []))
            ) for i in res if "pull_request" not in i
        ]

    def read_board(self, board: str) -> list[BoardItem]:
        owner_type = self.settings.get("board_owner_type", "organization")
        owner = self.settings.get("board_owner", self.repo.split("/")[0])
        query = """
        query($owner: String!, $board: Int!, $after: String) {
          %s(login: $owner) {
            projectV2(number: $board) {
              items(first: 100, after: $after) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  content { ... on Issue { number title } }
                  fieldValues(first: 20) {
                    nodes { ... on ProjectV2ItemFieldSingleSelectValue { name } }
                  }
                }
              }
            }
          }
        }
        """ % ("user" if owner_type == "user" else "organization")

        result = []
        after = None
        while True:
            data = {"query": query, "variables": {"owner": owner, "board": int(board), "after": after}}
            res = self._request("POST", "/graphql", data)
            if not res or "errors" in res:
                raise VashError(f"GraphQL error: {res.get('errors') if res else 'Empty'}", "Check board permissions")
            try:
                items_obj = res["data"][owner_type if owner_type == "user" else "organization"]["projectV2"]["items"]
            except (KeyError, TypeError):
                raise VashError("Invalid GraphQL response format", "Check API version")
            for item in items_obj["nodes"]:
                status = "Unknown"
                for fv in item.get("fieldValues", {}).get("nodes", []):
                    if "name" in fv:
                        status = fv["name"]
                        break
                content = item.get("content") or {}
                result.append(BoardItem(
                    item_id=item["id"], title=content.get("title", ""),
                    status=status, issue_number=content.get("number")
                ))
            if not items_obj["pageInfo"]["hasNextPage"]:
                break
            after = items_obj["pageInfo"]["endCursor"]
        return result

    def open_pr(self, head: str, base: str, title: str, body: str) -> PullRequestRef:
        data = {"title": title, "body": body, "head": head, "base": base}
        res = self._request("POST", f"/repos/{self.repo}/pulls", data)
        return PullRequestRef(
            number=res["number"], url=res["html_url"], head=res["head"]["ref"],
            base=res["base"]["ref"], state=res["state"]
        )

    def merge_pr(self, number: int, method: str = "squash") -> None:
        data = {"merge_method": method}
        self._request("PUT", f"/repos/{self.repo}/pulls/{number}/merge", data)

    def export_status(self) -> dict[str, Any]:
        issues = self.list_issues("open")
        params = {"state": "open", "per_page": "100"}
        prs = self._paginate(f"/repos/{self.repo}/pulls?{urllib.parse.urlencode(params)}")
        return {
            "open_issues": len(issues),
            "open_prs": len(prs) if prs else 0
        }
