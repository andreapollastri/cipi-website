#!/usr/bin/env python3
"""Keep code-block language labels identical to the English source.

The label above each snippet ("bash", "json", "env") is a token, not prose, but
the generator fed it to the translator — so localized pages ended up labelling
shell snippets "coup", "fiesta" and "festa". Labels appear in the same order on
a page and its translation, so they can be copied across positionally.

  scripts/i18n-sync-code-labels.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402

LABEL_RE = re.compile(r'(<span class="code-block-lang">)([^<]*)(</span>)')
LANGS = ("de", "fr", "es", "pt", "it")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = fixed = 0
    mismatched: list[str] = []
    for en_file in sorted((ROOT / "en").rglob("*.html")):
        canon = file_to_en_canon(en_file)
        if canon is None:
            continue
        en_labels = [m.group(2) for m in LABEL_RE.finditer(en_file.read_text(encoding="utf-8"))]
        if not en_labels:
            continue
        for lang in LANGS:
            tgt = localized_html_path(canon, lang)
            if not tgt.exists():
                continue
            text = tgt.read_text(encoding="utf-8")
            found = LABEL_RE.findall(text)
            if len(found) != len(en_labels):
                mismatched.append(
                    f"{tgt.relative_to(ROOT)} ({len(found)} labels vs {len(en_labels)})"
                )
                continue
            wanted = iter(en_labels)
            local = 0

            def replace(m: re.Match[str]) -> str:
                nonlocal local
                value = next(wanted)
                if m.group(2) != value:
                    local += 1
                return m.group(1) + value + m.group(3)

            updated = LABEL_RE.sub(replace, text)
            if updated != text:
                changed += 1
                fixed += local
                if not args.dry_run:
                    tgt.write_text(updated, encoding="utf-8")

    print(f"{fixed} labels {'would be' if args.dry_run else ''} restored in {changed} files")
    for line in mismatched:
        print(f"  skipped, label count differs: {line}")


if __name__ == "__main__":
    main()
