from __future__ import annotations

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
                "User-Agent": "ai-tools-radar/1.0",
            }
        )
        token = token or os.getenv("GITHUB_TOKEN")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{API}{path}"
        for attempt in range(4):
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            if response.status_code in {403, 429}:
                retry_after = int(response.headers.get("Retry-After", "5"))
                time.sleep(min(retry_after * (attempt + 1), 30))
                continue
            response.raise_for_status()
        response.raise_for_status()
        return {}

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
