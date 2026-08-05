#!/usr/bin/env python3
"""Turn the `Law tech news tracker` news.md digest into the site's content.

The tracker writes entries shaped like:

    ## [Headline](https://example.com/story)
    **Date:** 2026-07-29 | **Rank:** 5/5

    Summary paragraph...

    ---

This script keeps the headline, link, date and summary, and drops the
rating entirely -- ratings must never reach the published site.

Output is paginated at PER_PAGE stories per page:

    content/_index.md          page 1            ->  /
    content/page/_index.md     not rendered
    content/page/2/_index.md   page 2            ->  /page/2/
    ...

Each generated section carries its own prev/next links in `[extra]`, which
templates/index.html turns into the Newer/Older navigation.

Usage:
    python3 scripts/import_news.py [path/to/news.md]

Defaults to ../news.md relative to the repository root.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PER_PAGE = 20

# The tracker job is instructed to write summaries of around 140 characters.
MAX_SUMMARY = 200

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO.parent / "news.md"
CONTENT = REPO / "content"
PAGES_DIR = CONTENT / "page"

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


def toml_str(value: str) -> str:
    """A TOML basic string. JSON escaping is a valid subset of TOML's."""
    return json.dumps(value)


def render_items(items: list[dict]) -> list[str]:
    """Markdown for one page's worth of stories, grouped by date."""
    out: list[str] = []
    current: object = object()  # sentinel: never equal to a real date or None
    for item in items:
        if item["date"] != current:
            current = item["date"]
            out += [f'## {pretty_date(current) if current else "Undated"}', ""]
        out += [
            f'### [{item["title"]}]({item["url"]})',
            "",
            f'<span class="news-item__source">{source_label(item["url"])}</span> '
            f'{item["summary"]}',
            "",
        ]
    return out


def page_path(number: int) -> str:
    """Root-relative URL of a page, for get_url()."""
    return "/" if number == 1 else f"/page/{number}/"


def render_page(items: list[dict], number: int, total_pages: int, total_items: int,
                newest: date | None) -> str:
    front = [
        "+++",
        'title = "Law & Tech News"',
    ]
    if number > 1:
        front.append('template = "index.html"')
    front += [
        "",
        "[extra]",
        f"page_num = {number}",
        f"page_count = {total_pages}",
        f'prev = {toml_str(page_path(number - 1) if number > 1 else "")}',
        f'next = {toml_str(page_path(number + 1) if number < total_pages else "")}',
        "+++",
        "",
    ]

    body: list[str] = []
    if number == 1:
        body += [
            f'<p class="news-intro">{total_items} stories on European law, technology '
            "regulation and digital rights"
            + (f", latest from {pretty_date(newest)}." if newest else ".")
            + " Every headline links to the original source.</p>",
            "",
        ]
    body += render_items(items)

    return "\n".join(front + body).rstrip() + "\n"


def write(path: Path, text: str) -> None:
    leak = RATING_LEAK.search(text)
    if leak:
        raise SystemExit(f"error: rating leaked into {path}: {leak.group(0)!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_file():
        print(f"error: cannot read {source}", file=sys.stderr)
        return 1

    items = parse(source.read_text(encoding="utf-8"))
    if not items:
        print(f"error: no news entries found in {source}", file=sys.stderr)
        return 1

    long_ones = [it for it in items if len(it["summary"]) > MAX_SUMMARY]
    for it in long_ones:
        print(f"warning: {len(it['summary'])} chars (max {MAX_SUMMARY}): {it['title'][:60]}...",
              file=sys.stderr)
    if long_ones:
        print(f"warning: {len(long_ones)} summary/summaries over {MAX_SUMMARY} characters; "
              "shorten them in news.md and re-run", file=sys.stderr)

    items.sort(key=lambda it: (it["date"] or date.min, it["title"].lower()), reverse=True)
    newest = items[0]["date"]

    chunks = [items[i:i + PER_PAGE] for i in range(0, len(items), PER_PAGE)]
    total_pages = len(chunks)

    # Start from a clean slate so a shorter digest cannot leave stale pages behind.
    if PAGES_DIR.exists():
        shutil.rmtree(PAGES_DIR)

    write(CONTENT / "_index.md",
          render_page(chunks[0], 1, total_pages, len(items), newest))

    if total_pages > 1:
        write(PAGES_DIR / "_index.md",
              '+++\ntitle = "Pages"\nrender = false\n+++\n')

    for number, chunk in enumerate(chunks[1:], start=2):
        write(PAGES_DIR / str(number) / "_index.md",
              render_page(chunk, number, total_pages, len(items), newest))

    lengths = [len(it["summary"]) for it in items]
    print(f"wrote {len(items)} items across {total_pages} pages "
          f"({PER_PAGE} per page) from {source}")
    print(f"summary length: mean {sum(lengths) // len(lengths)}, max {max(lengths)} "
          f"(limit {MAX_SUMMARY})")
    return 1 if long_ones else 0


if __name__ == "__main__":
    raise SystemExit(main())
