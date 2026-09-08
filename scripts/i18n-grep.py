#!/usr/bin/env python3
"""Grep the whole site for translated segments matching a pattern, aligned with English.

Walks every English page and its localized twin in parallel and prints the
(EN, target) pairs whose target text matches the regex — the fastest way to see
every place one bad term was used, in context, before fixing it.

  scripts/i18n-grep.py de 'Bereitstellung'
  scripts/i18n-grep.py de 'Protokoll|Dokumente' --files
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "align", Path(__file__).resolve().parent / "i18n-align.py"
)
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("pattern")
    ap.add_argument("--files", action="store_true", help="also print which page each pair is on")
    ap.add_argument("--limit", type=int, default=10**9)
    args = ap.parse_args()

    rx = re.compile(args.pattern)
    seen: dict[str, tuple[str, str]] = {}
    for en_file in sorted((ROOT / "en").rglob("*.html")):
        canon = file_to_en_canon(en_file)
        if canon is None:
            continue
        tgt_file = localized_html_path(canon, args.lang)
        if not tgt_file.exists():
            continue
        en = align.segments(en_file.read_text(encoding="utf-8"))
        tg = align.segments(tgt_file.read_text(encoding="utf-8"))
        aligned = len(en) == len(tg)
        if not aligned:
            # Hand-edited page: the English counterpart cannot be trusted by
            # position, so show the target segment alone rather than hide it.
            print(f"# unaligned {en_file.name}: {len(en)} vs {len(tg)}", file=sys.stderr)
            pairs = [("(unaligned — English counterpart unknown)", b) for _, b in tg]
        else:
            pairs = [(a, b) for (_, a), (_, b) in zip(en, tg)]
        for a, b in pairs:
            a_s, b_s = " ".join(a.split()), " ".join(b.split())
            if b_s in seen or not rx.search(b_s):
                continue
            seen[b_s] = (a_s, en_file.relative_to(ROOT).as_posix())

    for i, (b_s, (a_s, page)) in enumerate(seen.items()):
        if i >= args.limit:
            print(f"... {len(seen) - args.limit} more")
            break
        if args.files:
            print(f"# {page}")
        print(f"  EN: {a_s}")
        print(f"  {args.lang.upper()}: {b_s}")
    print(f"\n# {len(seen)} unique matching segments", file=sys.stderr)


if __name__ == "__main__":
    main()
