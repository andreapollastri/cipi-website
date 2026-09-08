#!/usr/bin/env python3
"""Rebuild the translation cache from the pages that are actually published.

generate-lang-pages.py re-applies whatever the cache holds, so a cache older
than the pages will silently undo hand-corrected translations the next time
someone runs it with --force. This walks each English page and its localized
twin in parallel and writes the current translations back into the cache, so
regeneration reproduces the live site instead of overwriting it.

  scripts/i18n-rebuild-cache.py --dry-run
  scripts/i18n-rebuild-cache.py
"""
from __future__ import annotations

import argparse
import difflib
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

CACHE = ROOT / "scripts" / ".translation-cache.json"
LD_JSON_RE = re.compile(
    r'<script[^>]*type\s*=\s*"application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I
)
LD_PROSE_KEYS = {"description", "text", "name", "headline", "articleBody",
                 "alternateName", "about"}
# Proper nouns must never map to anything else. A page whose structure drifted
# from its English source can pair them with the wrong neighbour, and the
# generator would then render "Cipi" as some other label.
PROTECTED_LITERALS = {
    "Cipi", "cipi", "GitHub", "GitLab", "Laravel", "Ubuntu", "Nginx", "MariaDB",
    "PostgreSQL", "Valkey", "Supervisor", "Octane", "Horizon", "Reverb", "Deployer",
    "FrankenPHP", "WHMCS", "Cursor", "Claude", "DigitalOcean", "Hetzner", "Vultr",
    "Linode", "AWS", "cPanel", "Plesk", "Ploi", "Forge", "Coolify", "Cleavr",
    "RunCloud", "CloudPanel", "DirectAdmin", "Dokku", "Easypanel", "Kamal", "Init",
}
# Only the languages generate-lang-pages.py produces; it/ is maintained by hand.
LANGS = ("de", "fr", "es", "pt")


def ld_prose(obj: object, out: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and key in LD_PROSE_KEYS:
                out.append(value)
            else:
                ld_prose(value, out)
    elif isinstance(obj, list):
        for value in obj:
            ld_prose(value, out)


def ld_strings(html: str) -> list[str]:
    """Prose strings inside the page's JSON-LD blocks, in document order."""
    out: list[str] = []
    for m in LD_JSON_RE.finditer(html):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        ld_prose(data, out)
    return out


def align_pairs(en: list[tuple[str, str]], tg: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Pair English segments with their translations.

    Some pages were hand-edited after generation and no longer have the same
    number of segments as their English source, so a strict zip would refuse the
    whole page. Matching on the structural labels (tag and attribute kinds)
    recovers the alignment and simply skips the few segments that differ.
    """
    if len(en) == len(tg):
        return [(a, b) for (_, a), (_, b) in zip(en, tg)]
    matcher = difflib.SequenceMatcher(a=[k for k, _ in en], b=[k for k, _ in tg], autojunk=False)
    pairs: list[tuple[str, str]] = []
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            # A run of same-kind segments can still be off by one; the
            # PROTECTED_LITERALS check in main() is what keeps a proper noun
            # from being paired with the wrong neighbour.
            pairs.append((en[block.a + offset][1], tg[block.b + offset][1]))
    return pairs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    before = len(cache)
    updated = added = skipped = 0

    # Two passes: pages whose structure still matches their English source are
    # trustworthy, so they set the mappings. Pages that were hand-edited can
    # only fill gaps afterwards — never overrule a verified pair.
    for strict_only in (True, False):
        for en_file in sorted((ROOT / "en").rglob("*.html")):
            canon = file_to_en_canon(en_file)
            if canon is None:
                continue
            en = align.segments(en_file.read_text(encoding="utf-8"))
            for lang in LANGS:
                tgt = localized_html_path(canon, lang)
                if not tgt.exists():
                    continue
                tg = align.segments(tgt.read_text(encoding="utf-8"))
                aligned = len(en) == len(tg)
                if aligned != strict_only:
                    continue
                if not aligned and strict_only is False:
                    skipped += 1
                    print(f"  realign {tgt.relative_to(ROOT)} "
                          f"({len(en)} vs {len(tg)} segments)")
                en_ld = ld_strings(en_file.read_text(encoding="utf-8"))
                tg_ld = ld_strings(tgt.read_text(encoding="utf-8"))
                pairs = [(("seg", a), ("seg", b)) for a, b in align_pairs(en, tg)]
                if len(en_ld) == len(tg_ld):
                    pairs += [(("ld", a), ("ld", b)) for a, b in zip(en_ld, tg_ld)]
                for (_, src), (_, dst) in pairs:
                    key = f"{lang}::{src}"
                    existing = cache.get(key)
                    if existing == dst:
                        continue
                    if not aligned and existing is not None:
                        continue  # a verified mapping always wins
                    if dst == src and existing is not None and existing != src:
                        continue
                    if src.strip() in PROTECTED_LITERALS and dst.strip() != src.strip():
                        continue
                    if existing is not None:
                        updated += 1
                    else:
                        added += 1
                    cache[key] = dst

    print(f"\ncache entries: {before} → {len(cache)}  "
          f"({updated} updated, {added} added, {skipped} pages realigned)")
    if args.dry_run:
        print("dry run, nothing written")
        return
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {CACHE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
