#!/usr/bin/env python3
"""Apply reviewed translation fixes to the localized HTML pages.

Input JSON, per language, either a bare list of segment pairs or a dict:

  {"de": {"segments": [["old", "new"], ...],
          "raw":      [["<h1>old markup</h1>", "<h1>new markup</h1>"], ...]}}

"segments" pairs are plain text: whitespace-collapsed, plain characters
("&", "—"). "raw" pairs are exact markup, for copy that a heading splits across
tags and which therefore cannot be edited one text node at a time.

"old" is written whitespace-collapsed and with plain characters ("&", "—"); the
matcher tolerates any run of whitespace between words and either the literal
character or its HTML entity, so a sentence that the page wraps across three
indented lines still matches. Replacement is a raw substring edit — the file is
never re-parsed or re-serialized, so nothing else in the markup moves.

Every pair must match at least once; unmatched pairs are reported as misses and
exit non-zero, so a typo in a fix list cannot silently do nothing.

  scripts/i18n-apply-fixes.py fixes.json [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Characters the pages sometimes write as entities instead of literally.
ENTITY_ALT = {
    "&": r"(?:&amp;|&)",
    "—": r"(?:&mdash;|—)",
    "–": r"(?:&ndash;|–)",
    "’": r"(?:&rsquo;|&#8217;|’)",
    "'": r"(?:&#39;|&apos;|')",
    '"': r"(?:&quot;|\")",
    "↓": r"(?:&darr;|↓)",
    " ": r"(?:&nbsp;| |\s)",
}


def build_pattern(old: str) -> re.Pattern[str]:
    parts = []
    for token in old.split():
        parts.append("".join(ENTITY_ALT.get(ch, re.escape(ch)) for ch in token))
    body = r"\s+".join(parts)
    # Anchor on word boundaries so a short replacement cannot fire inside a
    # longer word ("inicio" -> "Init" must not turn "reinicio" into "reInit").
    if old[:1].isalnum():
        body = r"\b" + body
    if old[-1:].isalnum():
        body = body + r"\b"
    return re.compile(body)


def check_new(new: str) -> str | None:
    if "<" in new or ">" in new:
        return "contains < or >"
    for m in re.finditer(r"&", new):
        tail = new[m.start() : m.start() + 10]
        if not re.match(r"&(?:amp|lt|gt|quot|apos|mdash|ndash|rsquo|darr|nbsp|#\d+);", tail):
            return "contains a bare '&' (write &amp;)"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixes")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    misses: list[tuple[str, str]] = []
    written: set[Path] = set()
    grand = 0

    for lang, pairs in fixes.items():
        if isinstance(pairs, dict):
            seg_pairs = pairs.get("segments", [])
            raw_pairs = pairs.get("raw", [])
        else:
            seg_pairs, raw_pairs = pairs, []

        seen: set[str] = set()
        compiled = []
        for old, new in seg_pairs:
            old_n = " ".join(old.split())
            if old_n in seen:
                sys.exit(f"{lang}: duplicate 'old' value {old_n[:60]!r}")
            seen.add(old_n)
            problem = check_new(new)
            if problem:
                sys.exit(f"{lang}: bad replacement ({problem}): {new[:60]!r}")
            compiled.append((old_n, new, build_pattern(old_n)))
        # Longest first, so a short pair cannot eat part of a longer one.
        compiled.sort(key=lambda t: -len(t[0]))

        hits: dict[str, int] = {}
        for path in sorted((ROOT / lang).rglob("*.html")):
            text = original = path.read_text(encoding="utf-8")
            for old, new in raw_pairs:
                n = text.count(old)
                if n:
                    text = text.replace(old, new)
                    hits[old] = hits.get(old, 0) + n
            for old_n, new, pat in compiled:
                text, n = pat.subn(lambda _m, _new=new: _new, text)
                if n:
                    hits[old_n] = hits.get(old_n, 0) + n
            if text != original:
                written.add(path)
                if not args.dry_run:
                    path.write_text(text, encoding="utf-8")
        total = sum(hits.values())
        grand += total
        print(f"{lang}: {len(hits)}/{len(compiled) + len(raw_pairs)} pairs matched, "
              f"{total} replacements")
        for old_n, _, _ in compiled:
            if old_n not in hits:
                misses.append((lang, old_n))
        for old, _ in raw_pairs:
            if old not in hits:
                misses.append((lang, old))

    print(f"\n{grand} replacements in {len(written)} files"
          f"{' (dry run)' if args.dry_run else ''}")
    if misses:
        print(f"\n{len(misses)} MISSES:")
        for lang, key in misses:
            print(f"  {lang}: {key[:110]!r}")
        sys.exit(1)


if __name__ == "__main__":
    main()
