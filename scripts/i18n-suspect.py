#!/usr/bin/env python3
"""Surface segments whose translation looks broken, worst first.

Machine translation fails in recognisable ways: English function words left in
mid-sentence, a target much shorter than its source, doubled words. Long-form
pages are too large to reread line by line, so this ranks the segments most
likely to be wrong and shows them next to their English source.

  scripts/i18n-suspect.py de --group docs --limit 30
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("shared", HERE / "i18n-shared.py")
shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shared)
align = shared.align
from i18n_lib import ROOT, file_to_en_canon, localized_html_path  # noqa: E402

# English function words that should never survive a translation.
STRAY_EN = re.compile(
    r"\b(the|and|with|from|your|their|that|this|which|when|there|these|those|"
    r"into|over|about|been|being|will|would|should|could|must|because|while|"
    r"through|without|between|before|after|again|also|only|just|very|more|most)\b"
)
# Words the source shares with the target language, so they prove nothing.
SHARED_OK = {
    "de": re.compile(r"\b(will|also|man|kann|in|international|links)\b"),
    "fr": re.compile(r"\b(the|design|patch)\b"),
    "es": re.compile(r"\b(the)\b"),
    "pt": re.compile(r"\b(the|a|no|as|e|o)\b"),
    "it": re.compile(r"\b(the|non|come|e|a|in|di)\b"),
}
DOUBLED = re.compile(r"\b(\w{4,})\s+\1\b", re.I)


def score(en: str, tg: str, lang: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    points = 0
    strays = {m.group(0) for m in STRAY_EN.finditer(tg.lower())}
    ok = SHARED_OK.get(lang)
    if ok:
        strays = {w for w in strays if not ok.fullmatch(w)}
    if strays:
        points += 3 * len(strays)
        reasons.append("stray EN: " + ", ".join(sorted(strays)))
    if m := DOUBLED.search(tg):
        points += 4
        reasons.append(f"doubled: {m.group(0)!r}")
    en_w, tg_w = len(en.split()), len(tg.split())
    if en_w >= 8 and tg_w < en_w * 0.6:
        points += 3
        reasons.append(f"much shorter ({tg_w} vs {en_w} words)")
    if en_w >= 8 and tg_w > en_w * 1.8:
        points += 2
        reasons.append(f"much longer ({tg_w} vs {en_w} words)")
    return points, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang")
    ap.add_argument("--group", choices=sorted(shared.GROUPS), default="docs")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--min-words", type=int, default=6)
    args = ap.parse_args()

    rows = []
    for name in shared.GROUPS[args.group]():
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
            continue
        for (_, a), (_, b) in zip(en, tg):
            a_s, b_s = " ".join(a.split()), " ".join(b.split())
            if len(a_s.split()) < args.min_words:
                continue
            pts, why = score(a_s, b_s, args.lang)
            if pts >= args.min_score:
                rows.append((pts, why, a_s, b_s, en_file.name))

    rows.sort(key=lambda r: -r[0])
    seen: set[str] = set()
    shown = 0
    for pts, why, a_s, b_s, page in rows:
        if b_s in seen:
            continue
        seen.add(b_s)
        shown += 1
        if shown > args.limit:
            break
        print(f"--- score {pts} [{page}] {'; '.join(why)}")
        print(f"  EN: {a_s}")
        print(f"  {args.lang.upper()}: {b_s}")
    print(f"\n# {len(rows)} suspicious segments, {len(seen)} distinct", file=sys.stderr)


if __name__ == "__main__":
    main()
