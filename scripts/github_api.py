from __future__ import annotations

import base64
import os
import time
from typing import Any

import requests

API = "https://api.github.com"


class GitHubAPI:
    def __init__(self, token: str | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "github-ai-radar/2.0",
            }
        )
        token = token or os.getenv("GITHUB_TOKEN")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _request(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        url = f"{API}{path}"
        last: requests.Response | None = None
        for attempt in range(4):
            response = self.session.get(url, params=params, timeout=30)
            last = response
            if response.status_code in {200, 404}:
                return response
            if response.status_code in {403, 429}:
                retry_after = int(response.headers.get("Retry-After", "5"))
                time.sleep(min(retry_after * (attempt + 1), 30))
                continue
            response.raise_for_status()
        assert last is not None
        last.raise_for_status()
        return last

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._request(path, params)
        if response.status_code == 404:
            return {}
        return response.json()

    def search_repositories(
        self,
        query: str,
        *,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        payload = self._get(
            "/search/repositories",
            {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": max(1, min(per_page, 100)),
                "page": 1,
            },
        )
        return payload.get("items", [])

    def get_readme_text(self, owner: str, repo: str) -> str:
        payload = self._get(f"/repos/{owner}/{repo}/readme")
        content = payload.get("content") or ""
        if content and payload.get("encoding") == "base64":
            try:
                return base64.b64decode(content).decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return ""
