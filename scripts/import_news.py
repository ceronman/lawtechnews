#!/usr/bin/env python3
"""Turn the `Law tech news tracker` news.md digest into content/_index.md.

The tracker writes entries shaped like:

    ## [Headline](https://example.com/story)
    **Date:** 2026-07-29 | **Rank:** 5/5

    Summary paragraph...

    ---

This script keeps the headline, link, date and summary, and drops the
rating entirely -- ratings must never reach the published site.

Usage:
    python3 scripts/import_news.py [path/to/news.md]

Defaults to ../news.md relative to the repository root.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO.parent / "news.md"
OUTPUT = REPO / "content" / "_index.md"

HEADING = re.compile(r"^## \[(?P<title>.+)\]\((?P<url>\S+)\)\s*$")
META = re.compile(
    r"^\*\*Date:\*\*\s*(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:\s*\|\s*\*\*Rank:\*\*\s*\d+/\d+)?\s*$"
)
RATING_LEAK = re.compile(r"\*\*Rank:\*\*|\bRank:\s*\d|\b\d/5\b")


def parse(text: str) -> list[dict]:
    items: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        heading = HEADING.match(lines[i])
        if not heading:
            i += 1
            continue

        item = {
            "title": heading["title"].strip(),
            "url": heading["url"].strip(),
            "date": None,
            "summary": "",
        }
        i += 1

        meta = META.match(lines[i]) if i < len(lines) else None
        if meta:
            item["date"] = date.fromisoformat(meta["date"])
            i += 1

        body: list[str] = []
        while i < len(lines) and not lines[i].startswith("## "):
            line = lines[i]
            if line.strip() == "---":
                i += 1
                break
            body.append(line)
            i += 1

        item["summary"] = " ".join(b.strip() for b in body if b.strip())
        items.append(item)

    return items


def source_label(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def pretty_date(value: date) -> str:
    return f"{value.day} {value:%B %Y}"


def render(items: list[dict]) -> str:
    items = sorted(
        items,
        key=lambda it: (it["date"] or date.min, it["title"].lower()),
        reverse=True,
    )
    newest = items[0]["date"] if items and items[0]["date"] else None

    out = [
        "+++",
        'title = "Law & Tech News"',
        "+++",
        "",
        f'<p class="news-intro">{len(items)} stories on European law, technology '
        "regulation and digital rights"
        + (f", latest from {pretty_date(newest)}." if newest else ".")
        + " Every headline links to the original source.</p>",
        "",
    ]

    current: object = object()  # sentinel: never equal to a real date or None
    for item in items:
        if item["date"] != current:
            current = item["date"]
            label = pretty_date(current) if current else "Undated"
            out += [f"## {label}", ""]

        out += [
            f'### [{item["title"]}]({item["url"]})',
            "",
            f'<span class="news-item__source">{source_label(item["url"])}</span> '
            f'{item["summary"]}',
            "",
        ]

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_file():
        print(f"error: cannot read {source}", file=sys.stderr)
        return 1

    items = parse(source.read_text(encoding="utf-8"))
    if not items:
        print(f"error: no news entries found in {source}", file=sys.stderr)
        return 1

    page = render(items)

    leak = RATING_LEAK.search(page)
    if leak:
        print(f"error: rating leaked into output: {leak.group(0)!r}", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)} ({len(items)} items) from {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
