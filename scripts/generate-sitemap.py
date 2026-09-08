#!/usr/bin/env python3
"""Generate sitemap.xml from multilingual HTML pages + hreflang slug map."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_lib import (  # noqa: E402
    BASE,
    LANG_CODES,
    LANGUAGES,
    ROOT,
    SLUGS_IT,
    abs_href,
    file_to_en_canon,
    localize_canon,
)

TODAY = date.today().isoformat()


def priority_for(canon: str) -> tuple[str, str]:
    if canon == "/":
        return "1.0", "weekly"
    if canon in ("/alternatives", "/best-laravel-forge-alternatives", "/whats-new"):
        return "0.9", "weekly"
    if canon in ("/docs/", "/guides/"):
        return "0.9", "weekly"
    if canon.startswith("/docs/") or canon.startswith("/guides/"):
        return "0.8", "weekly"
    if canon.startswith("/alternative-to-") or canon == "/discovery":
        return "0.8", "monthly"
    return "0.8", "monthly"


def url_entry(en_canon: str, priority: str, freq: str, image: bool = False) -> str:
    lines = [
        "  <url>",
        f"    <loc>{abs_href('en', en_canon)}</loc>",
    ]
    for code, _, _ in LANGUAGES:
        lines.append(
            f'    <xhtml:link rel="alternate" hreflang="{code}" href="{abs_href(code, en_canon)}"/>'
        )
    lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{abs_href("en", en_canon)}"/>')
    lines += [
        f"    <lastmod>{TODAY}</lastmod>",
        f"    <changefreq>{freq}</changefreq>",
        f"    <priority>{priority}</priority>",
    ]
    if image:
        lines += [
            "    <image:image>",
            f"      <image:loc>{BASE}/og.png</image:loc>",
            "      <image:title>Cipi — Free Open-Source Laravel Deployment CLI</image:title>",
            "    </image:image>",
        ]
    lines.append("  </url>")
    return "\n".join(lines)


def main() -> None:
    canons: set[str] = set()
    for path in sorted(ROOT.rglob("*.html")):
        c = file_to_en_canon(path)
        if c is not None and c != "/404":
            canons.add(c)

    canons.update(SLUGS_IT.keys())
    canons.discard("/404")

    def sort_key(c: str):
        pri, _ = priority_for(c)
        return (0 if c == "/" else 1, -float(pri), c)

    ordered = sorted(canons, key=sort_key)

    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]

    for canon in ordered:
        pri, freq = priority_for(canon)
        chunks.append(url_entry(canon, pri, freq, image=(canon == "/")))

    chunks.append("</urlset>")
    chunks.append("")

    out = ROOT / "sitemap.xml"
    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {out} ({len(ordered)} URL groups × {len(LANG_CODES)} hreflang)")


if __name__ == "__main__":
    main()
