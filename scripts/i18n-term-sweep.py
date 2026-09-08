#!/usr/bin/env python3
"""Sweep a terminology fix across a language's pages, text nodes only.

Word-level translation errors ("Stapel" for a software stack, "Fisch" for the
fish shell) repeat hundreds of times across the corpus, so listing whole
sentences for each is impractical. This applies regex rules to the *text* of the
pages while leaving markup, attributes, URLs and anything inside
<code>/<pre>/<script>/<style> byte-for-byte untouched.

Rules JSON: {"de": [["regex", "replacement"], ...]}

  scripts/i18n-term-sweep.py rules.json --dry-run   # show every distinct match
  scripts/i18n-term-sweep.py rules.json             # apply
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_TAGS = ("script", "style", "pre", "code", "svg", "textarea")
# JSON-LD carries the page copy again for search engines, so it needs the same
# terminology as the visible text even though it lives inside a <script>.
LD_JSON_RE = re.compile(
    r'(<script[^>]*type\s*=\s*"application/ld\+json"[^>]*>)(.*?)(</script>)', re.S | re.I
)
TAG_RE = re.compile(r"<[^>]*>", re.S)
# Attribute values that hold prose and therefore need sweeping too.
ATTR_RE = re.compile(r'\b(title|alt|aria-label|placeholder|content)\s*=\s*"([^"]*)"')
META_TRANSLATE = {"description", "keywords", "twitter:title", "twitter:description",
                  "og:title", "og:description"}


def attr_spans(tag: str, offset: int) -> list[tuple[int, int]]:
    """Ranges of prose-bearing attribute values inside one tag."""
    name = re.match(r"<\s*([A-Za-z0-9-]+)", tag)
    tag_name = name.group(1).lower() if name else ""
    spans: list[tuple[int, int]] = []
    for m in ATTR_RE.finditer(tag):
        attr = m.group(1).lower()
        if attr == "content":
            # Only the metas whose content is user-facing prose.
            if tag_name != "meta":
                continue
            key = re.search(r'\b(?:name|property)\s*=\s*"([^"]*)"', tag)
            if not key or key.group(1) not in META_TRANSLATE:
                continue
        elif tag_name in ("link", "html"):
            continue
        spans.append((offset + m.start(2), offset + m.end(2)))
    return spans


def text_spans(html: str) -> list[tuple[int, int]]:
    """Ranges of page prose: text outside skip elements, plus prose attributes."""
    spans: list[tuple[int, int]] = []
    depth = 0
    pos = 0
    for m in TAG_RE.finditer(html):
        if depth == 0 and m.start() > pos:
            spans.append((pos, m.start()))
        tag = m.group(0)
        name = re.match(r"</?\s*([A-Za-z0-9-]+)", tag)
        if not tag.startswith("</"):
            spans.extend(attr_spans(tag, m.start()))
        if name and name.group(1).lower() in SKIP_TAGS and not tag.endswith("/>"):
            depth += 1 if not tag.startswith("</") else -1
            depth = max(depth, 0)
        pos = m.end()
    if depth == 0 and pos < len(html):
        spans.append((pos, len(html)))
    for m in LD_JSON_RE.finditer(html):
        spans.append((m.start(2), m.end(2)))
    spans.sort()
    return spans


def apply_rules(html: str, rules: list[tuple[re.Pattern[str], str]],
                samples: dict[str, collections.Counter]) -> str:
    out: list[str] = []
    last = 0
    for start, end in text_spans(html):
        out.append(html[last:start])
        chunk = html[start:end]
        for pat, repl in rules:
            def record(m: re.Match[str], _p=pat, _r=repl) -> str:
                new = m.expand(_r)
                samples[_p.pattern][f"{m.group(0)}  ->  {new}"] += 1
                return new
            chunk = pat.sub(record, chunk)
        out.append(chunk)
        last = end
    out.append(html[last:])
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rules")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-samples", type=int, default=12)
    args = ap.parse_args()

    spec = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    exit_code = 0

    for lang, raw_rules in spec.items():
        rules = [(re.compile(p), r) for p, r in raw_rules]
        samples: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        changed = 0
        for path in sorted((ROOT / lang).rglob("*.html")):
            original = path.read_text(encoding="utf-8")
            updated = apply_rules(original, rules, samples)
            if updated != original:
                changed += 1
                if not args.dry_run:
                    path.write_text(updated, encoding="utf-8")
        print(f"\n=== {lang}: {changed} files "
              f"{'would change' if args.dry_run else 'written'} ===")
        for pat, _ in raw_rules:
            counter = samples.get(pat)
            if not counter:
                print(f"  MISS  {pat!r}")
                exit_code = 1
                continue
            total = sum(counter.values())
            print(f"  {total:4}×  {pat!r}")
            for text, n in counter.most_common(args.max_samples):
                print(f"          {n:3}× {text}")
            if len(counter) > args.max_samples:
                print(f"          … {len(counter) - args.max_samples} more distinct matches")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
