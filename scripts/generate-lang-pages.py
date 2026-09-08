#!/usr/bin/env python3
"""Generate fr/de/es/pt pages from English sources with machine translation."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from deep_translator import GoogleTranslator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_lib import (  # noqa: E402
    ROOT,
    build_alternates,
    build_og_locales,
    build_switch,
    file_to_en_canon,
    lang_href,
    localize_canon,
    localized_html_path,
    to_en_canon,
)

TARGET_LANGS = ["de", "fr", "es", "pt"]
CACHE_FILE = ROOT / "scripts" / ".translation-cache.json"
BATCH_SEP = "\n|||CIPI|||\n"
MAX_BATCH = 1800

SKIP_TAGS = {"script", "style", "pre", "code", "svg", "path", "meta"}
TRANSLATABLE_ATTRS = ("title", "alt", "aria-label", "placeholder")
META_TRANSLATE = {"description", "keywords", "twitter:title", "twitter:description"}

PROTECTED = re.compile(
    r"since 5\.[01]|"
    r"\b(Cipi|cipi\.sh|Laravel|Forge|Ploi|Kamal|Coolify|Cleavr|RunCloud|"
    r"ServerPilot|CloudPanel|DirectAdmin|cPanel|Dokku|Easypanel|Moss|Vito|"
    r"FrankenPHP|Octane|Horizon|Reverb|Valkey|MariaDB|PostgreSQL|Nginx|"
    r"WordPress|Bedrock|"
    r"Supervisor|GitHub|GitLab|Ubuntu|Let's Encrypt|SSL|TLS|VPS|CLI|MCP|"
    r"API|GUI|CI/CD|DevOps|JSON|YAML|HTTP|HTTPS|DNS|S3|AES|PHP|LEMP|HTML|CSS|"
    r"JavaScript|Python|Docker|Redis|MySQL|npm|composer|artisan|sudo|apt|"
    r"systemd|cron|webhook|README|open.?source|self.?hosted)\b",
    re.IGNORECASE,
)

# Google Translate rewrites English words inside __KEEP_N__ (→ __GARDER_N__, etc.).
BROKEN_PLACEHOLDER = re.compile(r"__\w+_\d+__")

# JSON-LD repeats the page copy for search engines. It lives inside a <script>,
# so the normal walk skips it — translate it explicitly or a localized page
# hands Google English structured data.
LD_JSON_RE = re.compile(
    r'(<script[^>]*type\s*=\s*"application/ld\+json"[^>]*>)(.*?)(</script>)', re.DOTALL | re.IGNORECASE
)
LD_PROSE_KEYS = {"description", "text", "name", "headline", "articleBody",
                 "alternateName", "about"}

ALT_RE = re.compile(r"<!-- i18n:alternates -->.*?<!-- /i18n:alternates -->", re.DOTALL)
SWITCH_RE = re.compile(r"<!-- i18n:switch -->.*?<!-- /i18n:switch -->", re.DOTALL)
OG_LOCALE_RE = re.compile(
    r'<meta[^>]*property="og:locale"[^>]*>\s*(?:<meta[^>]*property="og:locale:alternate"[^>]*>\s*)*',
    re.DOTALL,
)


def load_cache() -> dict[str, str]:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")


def protect(text: str) -> tuple[str, dict[str, str]]:
    tokens: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        # Private-use Unicode — not treated as translatable text by Google.
        key = f"\uE000{len(tokens)}\uE001"
        tokens[key] = m.group(0)
        return key

    return PROTECTED.sub(repl, text), tokens


def restore(text: str, tokens: dict[str, str]) -> str:
    for key, val in tokens.items():
        text = text.replace(key, val)
    # Fallback when legacy __KEEP_N__ placeholders were translated (KEEP → GARDER, …).
    for key, val in tokens.items():
        idx: str | None = None
        m = re.fullmatch(r"\uE000(\d+)\uE001", key)
        if m:
            idx = m.group(1)
        else:
            m = re.fullmatch(r"__KEEP_(\d+)__", key)
            if m:
                idx = m.group(1)
        if idx is not None:
            text = re.sub(rf"__\w+_{idx}__", val, text)
    return text


def repair_value(src: str, val: str) -> str:
    """Restore brand/tech terms in an already-translated string."""
    if not BROKEN_PLACEHOLDER.search(val):
        return val
    index_to_val: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        idx = str(len(index_to_val))
        index_to_val[idx] = m.group(0)
        return f"__KEEP_{idx}__"

    PROTECTED.sub(repl, src)
    result = val
    for idx, original in index_to_val.items():
        result = re.sub(rf"__\w+_{idx}__", original, result)
    return result


def should_skip_text(text: str) -> bool:
    s = text.strip()
    if not s:
        return True
    if s.startswith(("http://", "https://", "/", "#", "$", "curl ", "ssh ", "git ", "cipi ")):
        return True
    if re.fullmatch(r"[\d\s\W]+", s):
        return True
    if len(s) <= 2 and s.isupper():
        return True
    return False


def in_lang_switch(node: NavigableString) -> bool:
    parent = node.parent
    while parent and isinstance(parent, Tag):
        classes = parent.get("class") or []
        if "lang-switch" in classes or "lang-menu" in classes:
            return True
        parent = parent.parent
    return False


def collect_strings(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    strings: set[str] = set()

    if soup.title and soup.title.string and not should_skip_text(str(soup.title.string)):
        strings.add(str(soup.title.string))

    for meta in soup.find_all("meta"):
        prop = meta.get("property") or ""
        name = meta.get("name") or ""
        key = prop or name
        if key in META_TRANSLATE | {"og:title", "og:description"} and meta.get("content"):
            strings.add(meta["content"])

    for tag in soup.find_all(True):
        if tag.name in SKIP_TAGS:
            continue
        for attr in TRANSLATABLE_ATTRS:
            if tag.has_attr(attr) and not should_skip_text(tag[attr]):
                strings.add(tag[attr])

    for node in soup.strings:
        if not isinstance(node, NavigableString):
            continue
        parent = node.parent
        if not parent or not isinstance(parent, Tag):
            continue
        if parent.name in SKIP_TAGS or in_lang_switch(node):
            continue
        text = str(node)
        if not should_skip_text(text):
            strings.add(text)

    return strings


def batch_translate(engine: GoogleTranslator, items: list[str], cache: dict[str, str], lang: str) -> None:
    pending: list[str] = []

    def flush() -> None:
        if not pending:
            return
        protected_items = []
        token_maps = []
        for item in pending:
            protected, tokens = protect(item)
            protected_items.append(protected)
            token_maps.append(tokens)
        payload = BATCH_SEP.join(protected_items)
        try:
            result = engine.translate(payload)
            time.sleep(0.15)
            parts = (result or payload).split(BATCH_SEP)
            if len(parts) != len(pending):
                raise ValueError(f"batch split {len(parts)} != {len(pending)}")
        except Exception as exc:  # noqa: BLE001
            print(f"  warn: batch failed ({exc!r}), retrying one-by-one")
            parts = []
            for src, prot in zip(pending, protected_items):
                try:
                    parts.append(engine.translate(prot) or src)
                    time.sleep(0.12)
                except Exception:
                    parts.append(src)
        for src, out, tokens in zip(pending, parts, token_maps):
            cache[f"{lang}::{src}"] = restore(out, tokens)
        pending.clear()

    for item in items:
        if f"{lang}::{item}" in cache:
            continue
        if len(BATCH_SEP.join(pending + [item])) > MAX_BATCH:
            flush()
        pending.append(item)
    flush()


def warm_cache(all_html: list[str], lang: str, cache: dict[str, str]) -> None:
    unique: set[str] = set()
    for html in all_html:
        unique.update(collect_strings(html))
    missing = [s for s in sorted(unique, key=len) if f"{lang}::{s}" not in cache]
    print(f"  translating {len(missing)} unique strings ({len(unique)} total)")
    if not missing:
        return
    engine = GoogleTranslator(source="en", target=lang)
    batch_translate(engine, missing, cache, lang)
    save_cache(cache)


class Lookup:
    def __init__(self, lang: str, cache: dict[str, str]) -> None:
        self.lang = lang
        self.cache = cache

    def get(self, text: str) -> str:
        return self.cache.get(f"{self.lang}::{text}", text)


def apply_translations(html: str, lang: str, lookup: Lookup) -> str:
    soup = BeautifulSoup(html, "html.parser")

    if soup.title and soup.title.string:
        soup.title.string.replace_with(lookup.get(str(soup.title.string)))

    for meta in soup.find_all("meta"):
        prop = meta.get("property") or ""
        name = meta.get("name") or ""
        key = prop or name
        if key in META_TRANSLATE | {"og:title", "og:description"} and meta.get("content"):
            meta["content"] = lookup.get(meta["content"])

    for tag in soup.find_all(True):
        if tag.name in SKIP_TAGS:
            continue
        for attr in TRANSLATABLE_ATTRS:
            if tag.has_attr(attr) and not should_skip_text(tag[attr]):
                tag[attr] = lookup.get(tag[attr])

    for node in list(soup.strings):
        if not isinstance(node, NavigableString):
            continue
        parent = node.parent
        if not parent or not isinstance(parent, Tag):
            continue
        if parent.name in SKIP_TAGS or in_lang_switch(node):
            continue
        text = str(node)
        if should_skip_text(text):
            continue
        node.replace_with(lookup.get(text))

    rewrite_links(soup, lang)
    return str(soup)


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


def ld_lookup(lookup: Lookup, src: str) -> str | None:
    """Translation for a JSON-LD string, tolerating trailing punctuation.

    JSON-LD usually drops the full stop the visible heading or step carries, so
    an exact lookup would miss translations the cache already holds.
    """
    got = lookup.cache.get(f"{lookup.lang}::{src}")
    if got is not None:
        return got
    collapsed = " ".join(src.split())
    got = lookup.cache.get(f"{lookup.lang}::{collapsed}")
    if got is not None:
        return " ".join(got.split())
    bare = collapsed.rstrip(" .:;\u2014-")
    tail = collapsed[len(bare):]
    for candidate in (bare, bare + ".", bare + ":"):
        got = lookup.cache.get(f"{lookup.lang}::{candidate}")
        if got is not None:
            return " ".join(got.split()).rstrip(" .:;\u2014-") + tail
    return None


def translate_jsonld(html: str, lookup: Lookup) -> str:
    """Replace JSON-LD prose with cached translations, keeping the JSON valid."""

    def one_block(m: re.Match[str]) -> str:
        body = m.group(2)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)
        found: list[str] = []
        ld_prose(data, found)
        new_body = body
        for src in found:
            if len(src.split()) < 4:
                continue
            dst = ld_lookup(lookup, src)
            if not dst or dst == src:
                continue
            needle = json.dumps(src, ensure_ascii=False)[1:-1]
            if needle not in new_body:
                continue
            new_body = new_body.replace(needle, json.dumps(dst, ensure_ascii=False)[1:-1])
        try:
            json.loads(new_body)
        except json.JSONDecodeError:
            return m.group(0)  # never write a block that stopped parsing
        return m.group(1) + new_body + m.group(3)

    return LD_JSON_RE.sub(one_block, html)


def rewrite_links(soup: BeautifulSoup, lang: str) -> None:
    for tag in soup.find_all(["a", "link"]):
        attr = "href"
        if not tag.has_attr(attr):
            continue
        href = tag[attr]
        if not href or href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
            continue
        m = re.match(r"^/(en|it|de|fr|es|pt)(/.*)?$", href)
        if m:
            rest = m.group(2) or "/"
            if rest == "/":
                tag[attr] = lang_href(lang, "/")
            else:
                en_canon = to_en_canon(rest)
                tag[attr] = lang_href(lang, localize_canon(en_canon, lang))


def post_process(text: str, lang: str, en_canon: str) -> str:
    canon_path = lang_href(lang, localize_canon(en_canon, lang))
    canon_url = f"https://cipi.sh{canon_path}"

    text = re.sub(r'(<html\b[^>]*\blang=")[^"]*(")', rf'\1{lang}\2', text, count=1)
    text = re.sub(r'"inLanguage": "en"', f'"inLanguage": "{lang}"', text)
    text = re.sub(
        r'(<link\b[^>]*rel="canonical"[^>]*href=")[^"]*(")',
        rf'\1{canon_url}\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<link\b[^>]*href=")[^"]*("[^>]*rel="canonical")',
        rf'\1{canon_url}\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<meta\b[^>]*property="og:url"[^>]*content=")[^"]*(")',
        rf'\1{canon_url}\2',
        text,
        count=1,
    )
    text = re.sub(
        r'(<meta\b[^>]*content=")[^"]*("[^>]*property="og:url")',
        rf'\1{canon_url}\2',
        text,
        count=1,
    )
    if ALT_RE.search(text):
        text = ALT_RE.sub(build_alternates(en_canon), text, count=1)
    if SWITCH_RE.search(text):
        m = re.search(r"(\s*)<!-- i18n:switch -->", text)
        indent = m.group(1) if m else ""
        text = SWITCH_RE.sub(indent + build_switch(lang, en_canon), text, count=1)
    if OG_LOCALE_RE.search(text):
        text = OG_LOCALE_RE.sub(build_og_locales(lang), text, count=1)
    return text


def en_sources() -> list[Path]:
    return sorted(p for p in (ROOT / "en").rglob("*.html"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing translated pages instead of skipping them.",
    )
    parser.add_argument(
        "--only-docs",
        action="store_true",
        help="Only process pages under en/docs/.",
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="PATH",
        help="Only process these paths relative to en/ (repeatable). Example: whats-new.html",
    )
    parser.add_argument(
        "--lang",
        action="append",
        choices=TARGET_LANGS,
        help="Limit to one or more languages (repeatable).",
    )
    args = parser.parse_args()

    cache = load_cache()
    sources = en_sources()
    if args.only_docs:
        sources = [p for p in sources if p.relative_to(ROOT / "en").parts[:1] == ("docs",)]
    if args.only:
        wanted = {Path(item) for item in args.only}
        sources = [
            p
            for p in sources
            if p.relative_to(ROOT / "en") in wanted or p.name in {w.name for w in wanted}
        ]
        if not sources:
            sys.exit("No matching --only sources under en/")
    langs = args.lang or TARGET_LANGS
    all_html = [p.read_text(encoding="utf-8") for p in sources]
    print(f"Generating {len(sources)} pages × {len(langs)} languages", flush=True)

    for lang in langs:
        print(f"\n=== {lang.upper()} ===")
        warm_cache(all_html, lang, cache)
        lookup = Lookup(lang, cache)
        for src, html in zip(sources, all_html):
            rel = src.relative_to(ROOT / "en")
            en_canon = file_to_en_canon(src)
            assert en_canon is not None
            dst = localized_html_path(en_canon, lang)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not args.force and dst.exists() and dst.stat().st_size > 1000:
                print(f"  skip {rel} → {dst.relative_to(ROOT)} (exists)")
                continue
            print(f"  write {dst.relative_to(ROOT)}")
            translated = apply_translations(html, lang, lookup)
            translated = translate_jsonld(translated, lookup)
            translated = post_process(translated, lang, en_canon)
            dst.write_text(translated, encoding="utf-8")

    save_cache(cache)
    print("\nDone.")


if __name__ == "__main__":
    main()
