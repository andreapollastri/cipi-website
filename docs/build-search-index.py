#!/usr/bin/env python3
"""Regenerate docs/search-index.js from HTML doc sections.

Usage:
  python3 docs/build-search-index.py           # legacy: docs/*.html -> docs/search-index.js
  python3 docs/build-search-index.py en       # en/docs -> en/docs/search-index.js
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE_TITLES_EN = {
    "index": "Docs",
    "getting-started": "Getting Started",
    "agent": "Cipi Agent",
    "apps": "Apps",
    "deploy": "Deploy & CI/CD",
    "infrastructure": "Infrastructure",
    "cli-client": "CLI Client",
    "gui": "Control Panel (GUI)",
    "advanced": "Advanced",
    "about": "About Cipi",
}

def strip_tags(s: str) -> str:
    s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<style[^>]*>.*?</style>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<pre[^>]*>.*?</pre>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def page_chapter(content: str, page: str, titles: dict[str, str]) -> str:
    match = re.search(r'class="doc-section-label"[^>]*>([^<]+)', content)
    if match:
        return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
    return titles.get(page, page.replace("-", " ").title())


def extract_entries(docs_dir: str, titles: dict[str, str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for filepath in sorted(glob.glob(os.path.join(docs_dir, "*.html"))):
        page = os.path.basename(filepath).replace(".html", "")
        with open(filepath, encoding="utf-8") as handle:
            content = handle.read()

        chapter = page_chapter(content, page, titles)
        main_match = re.search(
            r'<main class="docs-content"[^>]*>(.*)</main>', content, re.DOTALL
        )
        if not main_match:
            continue

        parts = re.split(r'<div class="doc-section" id="([^"]+)">', main_match.group(1))
        index = 1
        while index < len(parts) - 1:
            section_id = parts[index]
            body = parts[index + 1]
            body = re.split(r'<div class="(?:doc-section|page-nav)"', body)[0]

            h = re.search(r"<h[12][^>]*>(.*?)</h[12]>", body, re.DOTALL)
            heading = strip_tags(h.group(1)) if h else section_id
            text = strip_tags(body)
            blob = f"{chapter} {heading} {text}"
            if len(blob) > 4000:
                blob = blob[:4000]

            entries.append(
                {
                    "p": page,
                    "c": chapter,
                    "id": section_id,
                    "h": heading,
                    "t": blob,
                }
            )
            index += 2

    return entries


def write_index(lang: str | None) -> None:
    if lang is None:
        docs_dir = os.path.join(ROOT, "docs")
        out = os.path.join(docs_dir, "search-index.js")
        titles = PAGE_TITLES_EN
    else:
        docs_dir = os.path.join(ROOT, lang, "docs")
        out = os.path.join(docs_dir, "search-index.js")
        titles = PAGE_TITLES_EN

    if not os.path.isdir(docs_dir):
        sys.exit(f"docs dir missing: {docs_dir}")

    entries = extract_entries(docs_dir, titles)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("window.CIPI_DOCS = ")
        json.dump(entries, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write(";\n")
    print(f"Wrote {len(entries)} entries to {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", nargs="?", choices=["en"], default="en")
    args = ap.parse_args()
    write_index(args.lang)


if __name__ == "__main__":
    main()
