#!/usr/bin/env python3
"""List the translatable segments a group of pages shares, most repeated first.

The comparison pages are built from one template, so a handful of segments carry
most of the copy. Fixing those reaches every page at once — this shows which
they are, next to their English source.

  scripts/i18n-shared.py de --group compare
  scripts/i18n-shared.py fr --group guides --limit 40
"""
from __future__ import annotations

import argparse
import collections
import glob
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("align", HERE / "i18n-align.py")
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)
sys.path.insert(0, str(HERE))
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402

GROUPS = {
    "compare": lambda: sorted(glob.glob("en/alternative-to-*.html"))
    + ["en/alternatives.html", "en/best-laravel-forge-alternatives.html"],
    "guides": lambda: sorted(glob.glob("en/guides/*.html")),
    "docs": lambda: sorted(glob.glob("en/docs/*.html")),
    "misc": lambda: ["en/whats-new.html", "en/cipi-yml.html", "en/discovery.html"],
    "all": lambda: sorted(p.as_posix() for p in Path("en").rglob("*.html")),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("--group", choices=sorted(GROUPS), default="compare")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--min-words", type=int, default=3)
    ap.add_argument("--width", type=int, default=185)
    args = ap.parse_args()

    counts: collections.Counter[str] = collections.Counter()
    english: dict[str, str] = {}
    for name in GROUPS[args.group]():
        en_file = (ROOT / name).resolve()
        canon = file_to_en_canon(en_file)
        if canon is None:
            continue
        tgt = localized_html_path(canon, args.lang)
        if not tgt.exists():
            continue
        en = align.segments(en_file.read_text(encoding="utf-8"))
        tg = align.segments(tgt.read_text(encoding="utf-8"))
        if len(en) != len(tg):
            print(f"# unaligned, skipped: {en_file.name}", file=sys.stderr)
            continue
        for (_, a), (_, b) in zip(en, tg):
            a_s, b_s = " ".join(a.split()), " ".join(b.split())
            if len(b_s.split()) < args.min_words:
                continue
            counts[b_s] += 1
            english[b_s] = a_s

    rows = counts.most_common()[args.skip : args.skip + args.limit]
    for text, n in rows:
        print(f"[{n}x] EN: {english[text][:args.width]}")
        print(f"      {args.lang.upper()}: {text[:args.width]}")
    print(f"\n# {len(counts)} distinct shared segments in {args.group}", file=sys.stderr)


if __name__ == "__main__":
    main()
