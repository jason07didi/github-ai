from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from categorizer import categorize, technical_tags
from covers import choose_readme_cover
from github_api import GitHubAPI
from scoring import growth_for_window, repo_score
from translator import LocalTranslator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PROJECTS_PATH = DATA / "projects.json"
HISTORY_PATH = DATA / "history.json"
STATUS_PATH = DATA / "status.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(repo: dict[str, Any], discovered_at: str) -> dict[str, Any]:
    license_obj = repo.get("license") or {}
    owner_obj = repo.get("owner") or {}
    return {
        "repo": repo["full_name"],
        "owner": owner_obj.get("login") or "",
        "owner_avatar": owner_obj.get("avatar_url") or "",
        "name": repo["name"],
        "default_branch": repo.get("default_branch") or "main",
        "url": repo["html_url"],
        "homepage": repo.get("homepage") or "",
        "description_en": repo.get("description") or "",
        "description_zh": "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "language": repo.get("language") or "Unknown",
        "topics": repo.get("topics") or [],
        "license": license_obj.get("spdx_id") or "Unknown",
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "pushed_at": repo["pushed_at"],
        "discovered_at": discovered_at,
        "category": "其他实用 AI",
        "tech_tags": [],
        "cover_image": "",
        "cover_checked_at": "",
        "growth_24h": None,
        "growth_7d": None,
        "score": 0.0,
    }


def should_retry_cover(item: dict[str, Any], now: datetime) -> bool:
    if item.get("cover_image"):
        return False
    checked = item.get("cover_checked_at") or ""
    if not checked:
        return True
    try:
        ts = datetime.fromisoformat(checked.replace("Z", "+00:00"))
        return now - ts >= timedelta(days=int(CONFIG.get("cover_retry_days", 7)))
    except Exception:
        return True


def balance_categories(records: list[dict[str, Any]], limit: int, max_per_category: int) -> list[dict[str, Any]]:
    # First pass keeps the page diverse; second pass fills any unused capacity by score.
    selected: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for item in records:
        category = item.get("category") or "其他实用 AI"
        if counts.get(category, 0) < max_per_category:
            selected.append(item)
            counts[category] = counts.get(category, 0) + 1
        else:
            remaining.append(item)
        if len(selected) >= limit:
            return selected[:limit]
    for item in remaining:
        if len(selected) >= limit:
            break
        selected.append(item)
    return selected[:limit]


def main() -> None:
    now = datetime.now(timezone.utc)
    now_iso = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    existing_list = load_json(PROJECTS_PATH, [])
    existing = {p["repo"].lower(): p for p in existing_list if "repo" in p}
    history: dict[str, list[dict[str, Any]]] = load_json(HISTORY_PATH, {})

    api = GitHubAPI()
    candidates: dict[str, dict[str, Any]] = {}
    queries = list(CONFIG["queries"])
    since = (now - timedelta(days=int(CONFIG.get("new_repo_days", 60)))).date().isoformat()
    queries.extend(
        [
            f"topic:artificial-intelligence created:>{since} stars:>20",
            f"topic:llm created:>{since} stars:>20",
            f"topic:ai-agent created:>{since} stars:>20",
            f"topic:generative-ai created:>{since} stars:>20",
            f"topic:geospatial created:>{since} stars:>10",
        ]
    )

    for raw_query in queries:
        query = f"{raw_query} archived:false fork:false"
        try:
            repos = api.search_repositories(
                query,
                sort="stars",
                order="desc",
                per_page=int(CONFIG.get("search_per_query", 25)),
            )
        except Exception as exc:
            print(f"[warn] query failed: {query!r}: {exc}")
            continue
        for repo in repos:
            candidates[repo["full_name"].lower()] = repo

    min_stars = int(CONFIG.get("min_stars", 20))
    records: list[dict[str, Any]] = []
    needs_translation: list[tuple[int, str]] = []

    for key, raw in candidates.items():
        if raw.get("stargazers_count", 0) < min_stars or raw.get("archived") or raw.get("fork"):
            continue

        old = existing.get(key)
        discovered_at = old.get("discovered_at", now_iso) if old else now_iso
        item = normalize(raw, discovered_at)
        if old:
            if old.get("description_en") == item["description_en"]:
                item["description_zh"] = old.get("description_zh", "")
            item["cover_image"] = old.get("cover_image", "")
            item["cover_checked_at"] = old.get("cover_checked_at", "")

        item["category"] = categorize(item["name"], item["description_en"], item["topics"])
        item["tech_tags"] = technical_tags(item["name"], item["description_en"], item["topics"])
        records.append(item)
        if item["description_en"] and not item["description_zh"]:
            needs_translation.append((len(records) - 1, item["description_en"]))

    if needs_translation:
        print(f"Translating {len(needs_translation)} new/changed descriptions...")
        translator = LocalTranslator(CONFIG["translation_model"])
        try:
            translated = translator.translate_many([text for _, text in needs_translation])
        except Exception as exc:
            print(f"[warn] translation unavailable: {exc}")
            translated = [text for _, text in needs_translation]
        for (idx, _), zh in zip(needs_translation, translated):
            records[idx]["description_zh"] = zh

    cutoff = now - timedelta(days=15)
    for item in records:
        key = item["repo"].lower()
        snapshots = history.get(key, [])
        cleaned: list[dict[str, Any]] = []
        for snap in snapshots:
            try:
                ts = datetime.fromisoformat(snap["ts"].replace("Z", "+00:00"))
                if ts >= cutoff:
                    cleaned.append(snap)
            except Exception:
                pass
        cleaned.append({"ts": now_iso, "stars": item["stars"]})
        history[key] = cleaned[-800:]
        item["growth_24h"] = growth_for_window(cleaned, item["stars"], 24)
        item["growth_7d"] = growth_for_window(cleaned, item["stars"], 24 * 7)
        item["score"] = repo_score(item, item["growth_24h"], item["growth_7d"])

    records.sort(key=lambda x: (x["score"], x["stars"]), reverse=True)
    records = balance_categories(
        records,
        int(CONFIG.get("max_projects", 160)),
        int(CONFIG.get("max_per_category", 16)),
    )

    # Fetch one representative README image. Existing successful covers are cached in projects.json.
    cover_fetches = 0
    for item in records:
        if not should_retry_cover(item, now):
            continue
        try:
            readme = api.get_readme_text(item["owner"], item["name"])
            item["cover_image"] = choose_readme_cover(
                readme,
                item["owner"],
                item["name"],
                item.get("default_branch") or "main",
            )
            item["cover_checked_at"] = now_iso
            cover_fetches += 1
        except Exception as exc:
            print(f"[warn] cover lookup failed for {item['repo']}: {exc}")
            item["cover_checked_at"] = now_iso

    active = {p["repo"].lower() for p in records}
    history = {key: value for key, value in history.items() if key in active}
    dump_json(PROJECTS_PATH, records)
    dump_json(HISTORY_PATH, history)
    dump_json(
        STATUS_PATH,
        {
            "last_updated": now_iso,
            "project_count": len(records),
            "translated_this_run": len(needs_translation),
            "cover_fetches_this_run": cover_fetches,
            "query_count": len(queries),
            "translation_engine": CONFIG["translation_model"],
        },
    )
    print(f"Updated {len(records)} projects at {now_iso}; cover lookups: {cover_fetches}")


if __name__ == "__main__":
    main()
