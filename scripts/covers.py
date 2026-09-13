from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

# Markdown images and HTML <img> tags are both common in GitHub READMEs.
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\((?:<)?([^\s)>]+)(?:>)?(?:\s+[\"'][^\"']*[\"'])?\)", re.I)
_HTML_IMAGE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)

_BAD_HINTS = (
    "shields.io", "badge", "badgen", "codecov", "coveralls", "github.com/actions/workflows",
    "img.shields", "license.svg", "stars.svg", "forks.svg", "npm.svg", "pypi.svg", "build.svg",
    "discord", "visitor", "counter", "sponsor", "buymeacoffee",
)
_GOOD_HINTS = (
    "screenshot", "screen-shot", "preview", "demo", "hero", "banner", "cover", "interface", "ui",
    "example", "overview", "showcase", "dashboard", "workflow", "architecture",
)


def _clean_url(value: str) -> str:
    value = (value or "").strip().strip("'\"")
    # GitHub Markdown may contain query fragments and HTML entities.
    return value.replace("&amp;", "&")


def _resolve_image(src: str, owner: str, repo: str, branch: str) -> str:
    src = _clean_url(src)
    if not src or src.startswith("data:"):
        return ""
    if src.startswith("//"):
        return "https:" + src
    parsed = urlparse(src)
    if parsed.scheme in {"http", "https"}:
        return src
    if src.startswith("/"):
        # A root-relative link in a README usually points to the repository tree.
        src = src.lstrip("/")
    while src.startswith("./"):
        src = src[2:]
    if src.startswith("../"):
        return ""
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{src}"


def _image_score(url: str, order: int) -> int:
    low = url.lower()
    if any(hint in low for hint in _BAD_HINTS):
        return -1000
    score = max(0, 30 - order)  # prefer images near the top of the README
    if any(hint in low for hint in _GOOD_HINTS):
        score += 50
    if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
        score += 12
    elif low.endswith(".gif"):
        score += 8
    elif low.endswith(".svg"):
        score -= 6  # often a logo; still usable as a fallback
    return score


def choose_readme_cover(readme_text: str, owner: str, repo: str, branch: str) -> str:
    if not readme_text:
        return ""
    candidates = _MD_IMAGE.findall(readme_text) + _HTML_IMAGE.findall(readme_text)
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for order, raw in enumerate(candidates[:30]):
        url = _resolve_image(raw, owner, repo, branch)
        if not url or url in seen:
            continue
        seen.add(url)
        score = _image_score(url, order)
        if score > -100:
            ranked.append((score, url))
    if not ranked:
        return ""
    ranked.sort(reverse=True, key=lambda x: x[0])
    return ranked[0][1]
