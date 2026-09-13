from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def repo_score(repo: dict[str, Any], growth_24h: int | None, growth_7d: int | None) -> float:
    now = datetime.now(timezone.utc)
    stars = max(int(repo.get("stars", 0)), 0)
    pushed_at = parse_dt(repo["pushed_at"])
    created_at = parse_dt(repo["created_at"])

    freshness_days = max((now - pushed_at).total_seconds() / 86400, 0)
    age_days = max((now - created_at).total_seconds() / 86400, 1)

    star_component = min(math.log10(stars + 1) / 5.0, 1.0) * 35
    freshness_component = math.exp(-freshness_days / 35.0) * 25
    velocity = (growth_24h or 0) + (growth_7d or 0) / 7.0
    velocity_component = min(math.log1p(max(velocity, 0)) / math.log(501), 1.0) * 30
    newness_component = max(0.0, 1.0 - age_days / 365.0) * 10

    return round(star_component + freshness_component + velocity_component + newness_component, 1)


def growth_for_window(history: list[dict[str, Any]], current_stars: int, hours: int) -> int | None:
    if not history:
        return None

    now = datetime.now(timezone.utc)
    threshold = now.timestamp() - hours * 3600
    candidates: list[tuple[float, int]] = []
    for item in history:
        try:
            ts = parse_dt(item["ts"]).timestamp()
            if ts <= threshold:
                candidates.append((ts, int(item["stars"])))
        except (KeyError, ValueError, TypeError):
            continue

    if not candidates:
        return None
    _, stars_then = max(candidates, key=lambda x: x[0])
    return max(0, current_stars - stars_then)
