#!/usr/bin/env python3
"""Extract aligned (EN, target) translatable segments for review.

Walks the English source and its localized twin in parallel and prints the
segment pairs, so translations can be reviewed in context instead of blind.

  scripts/i18n-align.py de index.html            # one page
  scripts/i18n-align.py de index.html --prose    # skip code/short tokens
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402

SKIP_TAGS = {"script", "style", "pre", "code", "svg", "path", "meta"}
TRANSLATABLE_ATTRS = ("title", "alt", "aria-label", "placeholder")
META_TRANSLATE = {"description", "keywords", "twitter:title", "twitter:description",
                  "og:title", "og:description"}


def should_skip_text(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    if s.startswith(("http://", "https://", "/", "#", "$", "curl ", "ssh ", "git ", "cipi ")):
        return True
    if re.fullmatch(r"[\d\s\W]+", s):
        return True
    if len(s) <= 2 and s.isupper():
        return True
    return False


def in_lang_switch(node: NavigableString) -> bool:
    parent = node.parent
    while parent and isinstance(parent, Tag):
        classes = parent.get("class") or []
        if "lang-switch" in classes or "lang-menu" in classes:
            return True
        parent = parent.parent
    return False


def segments(html: str) -> list[tuple[str, str]]:
    """(kind, text) for every translatable string, in document order."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[tuple[str, str]] = []

    if soup.title and soup.title.string:
        out.append(("title", str(soup.title.string)))
    for meta in soup.find_all("meta"):
        key = meta.get("property") or meta.get("name") or ""
        if key in META_TRANSLATE and meta.get("content"):
            out.append((f"meta:{key}", meta["content"]))
    for tag in soup.find_all(True):
        if tag.name in SKIP_TAGS:
            continue
        for attr in TRANSLATABLE_ATTRS:
            if tag.has_attr(attr) and not should_skip_text(tag[attr]):
                out.append((f"attr:{attr}", tag[attr]))
    for node in soup.strings:
        parent = node.parent
        if not parent or not isinstance(parent, Tag):
            continue
        if parent.name in SKIP_TAGS or in_lang_switch(node):
            continue
        if should_skip_text(str(node)):
            continue
        out.append((f"text:{parent.name}", str(node)))
    return out


def is_prose(s: str) -> bool:
    s = s.strip()
    if len(s.split()) < 2:
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]{3,}\s+[A-Za-zÀ-ÿ]", s))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("page", help="path relative to en/, e.g. index.html or docs/deploy.html")
    ap.add_argument("--prose", action="store_true", help="only multi-word prose segments")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=10**9)
    args = ap.parse_args()

    en_file = ROOT / "en" / args.page
    if not en_file.exists():
        sys.exit(f"missing {en_file}")
    canon = file_to_en_canon(en_file)
    tgt_file = localized_html_path(canon, args.lang)
    if not tgt_file.exists():
        sys.exit(f"missing {tgt_file}")

    en = segments(en_file.read_text(encoding="utf-8"))
    tg = segments(tgt_file.read_text(encoding="utf-8"))
    print(f"# {en_file.relative_to(ROOT)}  ({len(en)} segs)")
    print(f"# {tgt_file.relative_to(ROOT)}  ({len(tg)} segs)")
    if len(en) != len(tg):
        print(f"# WARNING: segment count differs ({len(en)} vs {len(tg)}) — alignment may drift")
    print()
    for i, ((ka, a), (kb, b)) in enumerate(zip(en, tg)):
        if i < args.start or i >= args.end:
            continue
        a_s, b_s = re.sub(r"\s+", " ", a).strip(), re.sub(r"\s+", " ", b).strip()
        if args.prose and not (is_prose(a_s) or is_prose(b_s)):
            continue
        print(f"[{i}] {ka}")
        print(f"  EN: {a_s}")
        print(f"  {args.lang.upper()}: {b_s}")
    print()


if __name__ == "__main__":
    main()
