#!/usr/bin/env python3
"""Translate the JSON-LD structured data from the page's own visible copy.

Every page repeats its description and FAQ answers inside a JSON-LD block for
search engines, but the generator never translated those — so a German page
hands Google English answers. The strings are the same sentences that appear in
the visible page, so this looks each one up in the English→target map built from
the aligned pages and substitutes the translation that is already published.

Replacement is a JSON-escaped substring edit inside the block, and every block
is re-parsed afterwards; a block that would stop being valid JSON is left alone.

  scripts/i18n-translate-jsonld.py --dry-run
  scripts/i18n-translate-jsonld.py --lang de
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("align", HERE / "i18n-align.py")
align = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(align)
sys.path.insert(0, str(HERE))
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402

LD_RE = re.compile(r'(<script[^>]*type\s*=\s*"application/ld\+json"[^>]*>)(.*?)(</script>)',
                   re.S | re.I)
PROSE_KEYS = {"description", "text", "name", "headline", "articleBody",
              "alternateName", "about"}
LANGS = ("de", "fr", "es", "pt", "it")


def norm(s: str) -> str:
    return " ".join(s.split())


# Block elements whose whole text (inline <code> included) forms one sentence.
BLOCK_TAGS = ("p", "li", "td", "th", "dd", "dt", "h1", "h2", "h3", "h4", "figcaption")


def block_texts(html: str) -> list[str]:
    """Full text of each block element, in document order."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tag in soup.find_all(BLOCK_TAGS):
        out.append(" ".join(tag.get_text(" ", strip=True).split()))
    return out


def build_map(lang: str) -> dict[str, str]:
    """English visible text → its published translation, for this language."""
    table: dict[str, str] = {}
    for en_file in sorted((ROOT / "en").rglob("*.html")):
        canon = file_to_en_canon(en_file)
        if canon is None:
            continue
        tgt = localized_html_path(canon, lang)
        if not tgt.exists():
            continue
        en = align.segments(en_file.read_text(encoding="utf-8"))
        tg = align.segments(tgt.read_text(encoding="utf-8"))
        if len(en) != len(tg):
            continue
        for (_, a), (_, b) in zip(en, tg):
            a_n, b_n = norm(a), norm(b)
            if a_n and b_n and a_n != b_n:
                table.setdefault(a_n, b_n)
        # A JSON-LD sentence is often one visible paragraph broken up by inline
        # <code>, so match whole blocks too, not just single text nodes.
        en_blocks = block_texts(en_file.read_text(encoding="utf-8"))
        tg_blocks = block_texts(tgt.read_text(encoding="utf-8"))
        if len(en_blocks) == len(tg_blocks):
            for a, b in zip(en_blocks, tg_blocks):
                if a and b and a != b:
                    table.setdefault(a, b)
    return table


def lookup(table: dict[str, str], src: str) -> str | None:
    """Find the published translation, tolerating trailing punctuation.

    JSON-LD drops the full stop that the visible heading or step carries (and
    sometimes adds one), so an exact match misses translations that exist.
    """
    key = norm(src)
    if key in table:
        return table[key]
    bare = key.rstrip(" .:;\u2014-")
    for candidate in (bare, bare + ".", bare + ":"):
        if candidate in table:
            got = table[candidate]
            # Carry the source's own ending, so a heading stays a heading.
            tail = key[len(bare):]
            return got.rstrip(" .:;\u2014-") + tail
    return None


def prose_strings(obj: object, out: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and key in PROSE_KEYS:
                out.append(value)
            else:
                prose_strings(value, out)
    elif isinstance(obj, list):
        for value in obj:
            prose_strings(value, out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", choices=LANGS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-words", type=int, default=4)
    args = ap.parse_args()

    for lang in args.lang or LANGS:
        table = build_map(lang)
        hits = misses = blocks_kept = 0
        files = 0
        for tgt in sorted((ROOT / lang).rglob("*.html")):
            original = tgt.read_text(encoding="utf-8")
            text = original

            def fix(m: re.Match[str]) -> str:
                nonlocal hits, misses, blocks_kept
                body = m.group(2)
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    return m.group(0)
                found: list[str] = []
                prose_strings(data, found)
                new_body = body
                for src in found:
                    if len(src.split()) < args.min_words:
                        continue
                    dst = lookup(table, src)
                    if not dst:
                        misses += 1
                        continue
                    needle = json.dumps(src, ensure_ascii=False)[1:-1]
                    repl = json.dumps(dst, ensure_ascii=False)[1:-1]
                    if needle not in new_body:
                        continue
                    new_body = new_body.replace(needle, repl)
                    hits += 1
                try:
                    json.loads(new_body)
                except json.JSONDecodeError:
                    blocks_kept += 1  # refuse to write invalid JSON
                    return m.group(0)
                return m.group(1) + new_body + m.group(3)

            text = LD_RE.sub(fix, text)
            if text != original:
                files += 1
                if not args.dry_run:
                    tgt.write_text(text, encoding="utf-8")
        print(f"{lang}: {hits} strings translated, {misses} without a match, "
              f"{files} files {'would change' if args.dry_run else 'written'}"
              + (f", {blocks_kept} blocks skipped (would break JSON)" if blocks_kept else ""))


if __name__ == "__main__":
    main()
