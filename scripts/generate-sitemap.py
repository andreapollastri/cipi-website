#!/usr/bin/env python3
"""Generate sitemap.xml from English HTML pages at the site root."""
from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cipi.sh"
TODAY = date.today().isoformat()
SKIP_DIRS = {".git", "scripts", "netlify", "css"}


def file_to_canon(path: Path) -> str | None:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
        return None
    name = rel.as_posix()
    if name.endswith("404.html"):
        return None
    if name == "index.html":
        return "/"
    if name.endswith("/index.html"):
        return "/" + name[: -len("index.html")]
    if name.endswith(".html"):
        return "/" + name[: -len(".html")]
    return None


def href(canon: str) -> str:
    if canon == "/":
        return f"{BASE}/"
    return f"{BASE}{canon}"


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


def url_entry(canon: str, priority: str, freq: str, image: bool = False) -> str:
    loc = href(canon)
    lines = [
        "  <url>",
        f"    <loc>{loc}</loc>",
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
        c = file_to_canon(path)
        if c is not None:
            canons.add(c)

    def sort_key(c: str):
        pri, _ = priority_for(c)
        return (0 if c == "/" else 1, -float(pri), c)

    ordered = sorted(canons, key=sort_key)
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for canon in ordered:
        pri, freq = priority_for(canon)
        chunks.append(url_entry(canon, pri, freq, image=(canon == "/")))
    chunks.append("</urlset>")
    chunks.append("")
    out = ROOT / "sitemap.xml"
    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {out} ({len(ordered)} URLs)")


if __name__ == "__main__":
    main()
