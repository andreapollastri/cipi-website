#!/usr/bin/env python3
"""
Splits docs-source.html (monolith) into docs/*.html with shared docs.css.
Run from repo root: python3 scripts/build_docs_pages.py

Edit documentation in docs-source.html, then run this script to regenerate /docs/* and docs.html redirect.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_HTML = ROOT / "docs-source.html"
DOCS_DIR = ROOT / "docs"
CSS_OUT = DOCS_DIR / "docs.css"

# 1-based line numbers where each <div class="doc-section" starts (from docs-source.html)
SECTION_STARTS = [
    1176, 1295, 1310, 1403, 1471, 1517, 1591, 1646, 1684, 1923, 2041, 2116, 2173, 2224,
    2283, 2415, 2447, 2466, 2550, 2603, 2684, 2723, 2863, 2983, 3156, 3340, 3574, 3896,
    3939, 3965, 3982, 4012, 4127, 4219, 4270, 4288, 4325, 4358, 4405, 4447, 4733, 5131,
    5200, 5287, 5335, 5367, 5397, 5474, 5488, 5708, 5839, 6018, 6036, 6122, 6178,
]

# (first_section_line_1based, output_filename, page_key for active state)
CHAPTER_RANGES = [
    (1176, "getting-started.html", "getting-started"),
    (1517, "agent.html", "agent"),
    (2116, "apps.html", "apps"),
    (2550, "deploy.html", "deploy"),
    (3896, "infrastructure.html", "infrastructure"),
    (4447, "advanced.html", "advanced"),
    (5708, "about.html", "about"),
]

# Reading order for Previous / Next (href, short label for pager)
CHAPTER_NAV_ORDER: list[tuple[str, str]] = [
    ("getting-started.html", "Getting started"),
    ("agent.html", "Cipi Agent"),
    ("apps.html", "Apps"),
    ("deploy.html", "Deploy & CI/CD"),
    ("infrastructure.html", "Infrastructure"),
    ("advanced.html", "Advanced"),
    ("about.html", "About Cipi"),
]

# Per-chapter <title> and meta description (og/twitter use the same)
CHAPTER_HEAD: dict[str, tuple[str, str]] = {
    "getting-started.html": (
        "Getting started — Cipi documentation",
        "Install Cipi on Ubuntu, server requirements, quick start, production stack, and how apps are laid out on the VPS.",
    ),
    "agent.html": (
        "Cipi Agent — Cipi documentation",
        "Install and configure the Cipi Agent: webhooks, health checks, MCP server, database anonymizer, and environment variables.",
    ),
    "apps.html": (
        "Apps — Cipi documentation",
        "Create and manage Laravel and custom applications: app create, env files, logs, Artisan, Tinker, and SSH as the app user.",
    ),
    "deploy.html": (
        "Deploy & CI/CD — Cipi documentation",
        "Deploy from Git, auth.json, Git providers and auto-setup, deploy hooks, CI/CD examples, notifications, safe deploy, and preview environments.",
    ),
    "infrastructure.html": (
        "Infrastructure — Cipi documentation",
        "Server operations: PHP versions, databases, SSL, backups, cron, workers, firewall, fail2ban, services, SSH keys, and host settings.",
    ),
    "advanced.html": (
        "Advanced — Cipi documentation",
        "REST API, encrypted sync, vault and encryption, SMTP alerts, log retention, Redis, updates, wildcard SSL, Nginx, and uninstall.",
    ),
    "about.html": (
        "About Cipi — Cipi documentation",
        "Project history, security model, why MariaDB and Laravel, the Ci-Pi name, and how Cipi compares to other hosting tools.",
    ),
}

OVERVIEW_HEAD = (
    "Documentation — Cipi",
    "Cipi documentation index: installation, Agent, applications, deploy and CI/CD, infrastructure, advanced topics, and project background.",
)

SIDEBAR_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("getting started", [
        ("installation", "installation"),
        ("requirements", "requirements"),
        ("quickstart", "quick start"),
        ("tech-stack", "tech stack"),
        ("app-structure", "app structure"),
    ]),
    ("Cipi Agent", [
        ("agent-install", "installation"),
        ("agent-webhook", "webhook"),
        ("agent-health", "health check"),
        ("agent-mcp", "MCP server"),
        ("agent-anonymizer", "database anonymizer"),
        ("agent-env", "ENV variables"),
    ]),
    ("apps", [
        ("cli-app-create", "<code>app create</code>"),
        ("cli-app-custom", "custom apps"),
        ("cli-app-manage", "<code>app list / show / edit</code>"),
        ("cli-app-env", "<code>app env</code>"),
        ("cli-app-logs", "<code>app logs</code>"),
        ("cli-app-artisan", "<code>app artisan / tinker</code>"),
        ("cli-app-ssh", "SSH as app user"),
    ]),
    ("deploy & CI/CD", [
        ("cli-deploy", "<code>deploy</code>"),
        ("cli-auth", "<code>auth.json</code>"),
        ("git-providers", "Git providers"),
        ("git-auto-setup", "Git auto-setup"),
        ("cli-deploy-script", "deploy script"),
        ("ci-pipelines", "CI/CD pipelines"),
        ("deploy-notifications", "deploy notifications"),
        ("safe-deploy", "safe deploy w/ backup"),
        ("preview-environments", "preview environments"),
    ]),
    ("infrastructure", [
        ("cli-php", "<code>php</code>"),
        ("cli-db", "<code>db</code>"),
        ("cli-aliases", "<code>alias</code>"),
        ("cli-ssl", "<code>ssl</code>"),
        ("cli-backup", "<code>backup</code>"),
        ("cli-app-cron", "user crontab"),
        ("cli-workers", "<code>worker</code>"),
        ("cli-firewall", "<code>firewall</code>"),
        ("cli-ban", "<code>ban</code>"),
        ("cli-services", "<code>service</code>"),
        ("cli-ssh", "<code>ssh</code>"),
        ("cli-cipi", "<code>cipi</code>"),
    ]),
    ("advanced", [
        ("cipi-api", "<code>cipi api</code>"),
        ("cipi-sync", "<code>cipi sync</code>"),
        ("cipi-vault", "vault &amp; encryption"),
        ("cipi-smtp", "email notifications"),
        ("cipi-log-retention", "log retention (GDPR)"),
        ("redis", "redis"),
        ("self-update", "self-update"),
        ("wildcard-domains", "wildcard domains"),
        ("nginx-config", "edit Nginx config"),
        ("uninstall", "uninstall Cipi"),
    ]),
    ("about cipi", [
        ("history", "history"),
        ("security-model", "security model"),
        ("why-mariadb", "why MariaDB?"),
        ("why-laravel", "why Laravel?"),
        ("why-cipi", "why \"Ci-Pi\"?"),
        ("vs-alternatives", "Cipi vs alternatives"),
    ]),
]

ANCHOR_TO_PAGE: dict[str, str] = {}


def extract_sections(lines: list[str]) -> dict[str, str]:
    """Section id -> inner HTML lines joined (including the opening div)."""
    by_id: dict[str, str] = {}
    for i, start_line in enumerate(SECTION_STARTS):
        slice_end = SECTION_STARTS[i + 1] - 1 if i + 1 < len(SECTION_STARTS) else 6943
        chunk = "".join(lines[start_line - 1 : slice_end])
        m = re.search(r'id="([^"]+)"', chunk[:200])
        if not m:
            raise RuntimeError(f"No id in section starting line {start_line}")
        by_id[m.group(1)] = chunk
    return by_id


def rewrite_internal_links(html: str, current_file: str) -> str:
    """Cross-link #anchors to the correct chapter file."""

    def repl_anchor(m: re.Match[str]) -> str:
        aid = m.group(1)
        target = ANCHOR_TO_PAGE.get(aid)
        if not target:
            return m.group(0)
        if target == current_file:
            return f'href="#{aid}"'
        return f'href="{target}#{aid}"'

    out = re.sub(r'href="#([a-zA-Z][a-zA-Z0-9_-]*)"', repl_anchor, html)

    def repl_abs(m: re.Match[str]) -> str:
        aid = m.group(1)
        target = ANCHOR_TO_PAGE.get(aid, "getting-started.html")
        return f'href="{target}#{aid}"'

    out = re.sub(r'href="https://cipi\.sh/docs#([a-zA-Z0-9_-]+)"', repl_abs, out)
    return out


GROUP_META = [
    ("getting-started.html", "getting-started"),
    ("agent.html", "agent"),
    ("apps.html", "apps"),
    ("deploy.html", "deploy"),
    ("infrastructure.html", "infrastructure"),
    ("advanced.html", "advanced"),
    ("about.html", "about"),
]


def sidebar_html(current_key: str | None) -> str:
    """
    current_key: None for overview index, or CHAPTER_RANGES page_key.
    """
    parts: list[str] = []
    ov_cls = "sidebar-link active" if current_key is None else "sidebar-link"
    parts.append(f'''            <div class="sidebar-group">
                <span class="sidebar-group-label">documentation</span>
                <a href="index.html" class="{ov_cls}">Overview</a>
            </div>
''')
    for (label, items), (fname, pkey) in zip(SIDEBAR_GROUPS, GROUP_META, strict=True):
        parts.append("            <div class=\"sidebar-group\">\n")
        parts.append(f"                <span class=\"sidebar-group-label\">{label}</span>\n")
        for anchor, title in items:
            if current_key == pkey:
                parts.append(f'                <a href="#{anchor}" class="sidebar-link">{title}</a>\n')
            else:
                parts.append(f'                <a href="{fname}#{anchor}" class="sidebar-link">{title}</a>\n')
        parts.append("            </div>\n\n")
    return "".join(parts)


NAV_BLOCK = """    <nav>
        <div class="nav-inner">
            <div class="nav-left">
                <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                        stroke-linecap="round">
                        <line x1="4" y1="7" x2="20" y2="7" />
                        <line x1="4" y1="12" x2="20" y2="12" />
                        <line x1="4" y1="17" x2="20" y2="17" />
                    </svg>
                </button>
                <a href="../index.html" class="nav-logo">
                    <svg class="tux-logo" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" fill="none">
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M16.2182,35.9c-3.1368,0-6.8982,1.496-7.2988,5.6766a.916.916,0,0,0,.9061,1.0025h11.97A.9.9,0,0,0,22.7,41.643C22.6175,39.8048,21.7865,35.9,16.2182,35.9Z" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M18.0508,20.564c-1.35,1.0368-7.3687,7.51-4.3595,15.6667" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M31.7818,35.9c3.1368,0,6.8982,1.496,7.2988,5.6766a.916.916,0,0,1-.9061,1.0025h-11.97A.9.9,0,0,1,25.3,41.643C25.3825,39.8048,26.2135,35.9,31.7818,35.9Z" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M35.0148,36.4556c3.1848-2.8438,2.7468-7.5246,2.7468-8.7785,2.8935.82,5.0306,2.9709,5.5941,2.17,1.3744-1.9531-7.5193-7.5461-7.6918-10.8989C35.4951,15.6692,35.1706,5.4214,24,5.4214S12.5049,15.6692,12.3361,18.9484c-.1725,3.3528-9.0662,8.9458-7.6918,10.8989.5635.8007,2.7006-1.35,5.5941-2.17,0,1.2539-.438,5.9347,2.7468,8.7785" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M29.2763,19.8324c1.9318,1.5032,8.0416,8.242,5.0324,16.3983" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M24,24.8431l3.9479-4.2791c-.3858-1.0127-1.712-1.929-3.9479-1.929s-3.5621.9163-3.9479,1.929Z" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M20.0521,20.564c-3.424.5063-3.9062-2.7247-3.9062-4.7019,0-2.7006,1.4467-4.4367,3.9062-4.4367S23.79,14.7529,23.79,16.3443A3.8486,3.8486,0,0,1,23.181,18.68" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M27.7205,20.1334c.6751.0482,3.9538-.3892,3.9538-3.331s-1.76-3.7615-4.1232-3.7615a3.7861,3.7861,0,0,0-3.8164,2.6682" />
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                            d="M22.7012,41.4815a6.8371,6.8371,0,0,0,2.6076,0" />
                        <circle fill="currentColor" cx="22.1579" cy="16.5888" r="0.75" />
                        <circle fill="currentColor" cx="25.5497" cy="16.5888" r="0.75" />
                    </svg>
                    <span>Cipi</span>
                </a>
                <span class="nav-badge">Docs</span>
            </div>
            <div class="nav-search">
                <button type="button" class="docs-search-trigger" id="docsSearchOpen"
                    aria-haspopup="dialog" aria-expanded="false" aria-controls="docsSearchDialog">
                    <svg class="docs-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
                        <circle cx="11" cy="11" r="7" />
                        <line x1="16.65" y1="16.65" x2="21" y2="21" />
                    </svg>
                    <span class="docs-search-trigger-label">Search</span>
                    <kbd class="docs-search-kbd-hint" aria-hidden="true"><span class="docs-kbd-mod">⌘</span>K</kbd>
                </button>
            </div>
            <div class="nav-right">
                <a href="../index.html" class="nav-link">Home</a>
                <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
                    <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                        stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
                    </svg>
                    <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                        stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="5" />
                        <line x1="12" y1="1" x2="12" y2="3" />
                        <line x1="12" y1="21" x2="12" y2="23" />
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                        <line x1="1" y1="12" x2="3" y2="12" />
                        <line x1="21" y1="12" x2="23" y2="12" />
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                    </svg>
                </button>
                <a href="https://github.com/cipi-sh/cipi" target="_blank" class="btn-nav-sm">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path
                            d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                    GitHub
                </a>
            </div>
        </div>
    </nav>
"""

FOOTER_AND_SCRIPT = """    <div class="docs-search-overlay" id="docsSearchOverlay" hidden>
        <div class="docs-search-backdrop" id="docsSearchBackdrop" tabindex="-1"></div>
        <div class="docs-search-panel" role="dialog" aria-modal="true" aria-labelledby="docsSearchHeading"
            id="docsSearchDialog">
            <div class="docs-search-header">
                <span id="docsSearchHeading" class="docs-sr-only">Search documentation</span>
                <svg class="docs-search-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="1.5" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" />
                    <line x1="16.65" y1="16.65" x2="21" y2="21" />
                </svg>
                <input type="search" id="docsSearchInput" class="docs-search-input"
                    placeholder="Search documentation…" autocomplete="off" autocorrect="off" autocapitalize="off"
                    spellcheck="false" />
                <button type="button" class="docs-search-close" id="docsSearchClose" aria-label="Close search">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                </button>
            </div>
            <p class="docs-search-status docs-sr-only" id="docsSearchStatus" role="status" aria-live="polite"></p>
            <ul class="docs-search-results" id="docsSearchResults" role="listbox" aria-label="Search results"></ul>
            <p class="docs-search-empty" id="docsSearchEmpty" hidden>No matching sections.</p>
        </div>
    </div>

    <footer>
        <div class="footer-inner">
            <span>Made with ❤️ by <a href="https://web.ap.it" target="_blank">Andrea Pollastri</a> — Open source, MIT
                Licensed</span>
            <ul class="footer-links">
                <li><a href="https://conn.web.ap.it" target="_blank">Try SSH
                        Connection Manager with Cipi</a></li>
            </ul>
        </div>
    </footer>

    <script>
        function updateFavicon(theme) {
            const variant = theme === 'dark' ? 'dark' : 'light';
            document.getElementById('favicon').href = `/favicon-${variant}.png`;
        }

        function toggleTheme() {
            const html = document.documentElement;
            const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', next);
            localStorage.setItem('cipi-theme', next);
            updateFavicon(next);
        }

        (function () {
            const saved = localStorage.getItem('cipi-theme');
            if (saved) { document.documentElement.setAttribute('data-theme', saved); updateFavicon(saved); }
            else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.setAttribute('data-theme', 'dark'); updateFavicon('dark');
            }
        })();

        const sidebarToggle = document.getElementById('sidebarToggle');
        const docsSidebar = document.getElementById('docsSidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');

        function openSidebar() { docsSidebar.classList.add('open'); sidebarOverlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
        function closeSidebar() { docsSidebar.classList.remove('open'); sidebarOverlay.classList.remove('open'); document.body.style.overflow = ''; }

        sidebarToggle.addEventListener('click', () => docsSidebar.classList.contains('open') ? closeSidebar() : openSidebar());
        sidebarOverlay.addEventListener('click', closeSidebar);

        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', () => { if (window.innerWidth < 900) closeSidebar(); });
        });

        const sections = document.querySelectorAll('.doc-section[id]');
        const sidebarLinks = document.querySelectorAll('.sidebar-link');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    sidebarLinks.forEach(l => l.classList.remove('active'));
                    const active = document.querySelector('.sidebar-link[href="#' + entry.target.id + '"]');
                    if (active) {
                        active.classList.add('active');
                        active.scrollIntoView({ block: 'nearest' });
                    }
                }
            });
        }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });

        sections.forEach(s => observer.observe(s));

        function copyCode(btn) {
            const pre = btn.closest('.code-block').querySelector('pre');
            const text = pre.innerText;
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            });
        }
    </script>

    <script defer src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
    <script defer src="docs-search.js"></script>

    <script data-collect-dnt="true" async src="https://scripts.simpleanalyticscdn.com/latest.js"></script>
    <noscript><img src="https://queue.simpleanalyticscdn.com/noscript.gif?collect-dnt=true" alt=""
            referrerpolicy="no-referrer-when-downgrade" /></noscript>
"""


def head_html(
    title: str,
    description: str,
    canonical: str,
    og_url: str,
) -> str:
    te = html.escape(title)
    de = html.escape(description)
    ce = html.escape(canonical, quote=True)
    oe = html.escape(og_url, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{te}</title>
    <meta name="description" content="{de}">
    <meta name="keywords"
        content="Cipi documentation, Laravel deploy docs, cipi CLI reference, Laravel VPS setup, PHP server configuration, Ubuntu Laravel stack">
    <meta name="author" content="Andrea Pollastri">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{ce}">
    <link rel="sitemap" type="application/xml" href="/sitemap.xml">

    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Cipi">
    <meta property="og:url" content="{oe}">
    <meta property="og:title" content="{te}">
    <meta property="og:description" content="{de}">
    <meta property="og:image" content="https://cipi.sh/og.png">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@cipi_sh">
    <meta name="twitter:title" content="{te}">
    <meta name="twitter:description" content="{de}">
    <meta name="twitter:image" content="https://cipi.sh/og.png">

    <link rel="icon" id="favicon" type="image/png" sizes="48x48" href="/favicon-light.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-light-96.png">
    <link rel="icon" type="image/png" sizes="192x192" href="/favicon-light-192.png">
    <link rel="apple-touch-icon" sizes="192x192" href="/favicon-light-192.png">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=JetBrains+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&display=swap"
        rel="stylesheet">
    <link rel="stylesheet" href="docs.css">
</head>
"""


def pager_html(
    prior: tuple[str, str] | None,
    nxt: tuple[str, str] | None,
) -> str:
    """Previous / Next links between chapters (relative hrefs)."""

    def esc_txt(s: str) -> str:
        return html.escape(s)

    lines: list[str] = []
    lines.append('            <nav class="docs-pager" aria-label="Chapter navigation">')
    if prior:
        href, label = prior
        he = html.escape(href, quote=True)
        lines.append(
            f'                <a class="docs-pager-link docs-pager-prev" href="{he}" rel="prev">'
            f'<span class="docs-pager-kicker">Previous</span>'
            f'<span class="docs-pager-label">{esc_txt(label)}</span></a>'
        )
    else:
        lines.append('                <span class="docs-pager-placeholder" aria-hidden="true"></span>')
    if nxt:
        href, label = nxt
        he = html.escape(href, quote=True)
        lines.append(
            f'                <a class="docs-pager-link docs-pager-next" href="{he}" rel="next">'
            f'<span class="docs-pager-kicker">Next</span>'
            f'<span class="docs-pager-label">{esc_txt(label)}</span></a>'
        )
    else:
        lines.append('                <span class="docs-pager-placeholder" aria-hidden="true"></span>')
    lines.append("            </nav>")
    return "\n".join(lines) + "\n"


def pager_for_chapter(out_name: str) -> str:
    pairs = CHAPTER_NAV_ORDER
    idx = next(i for i, (f, _) in enumerate(pairs) if f == out_name)
    prev_item: tuple[str, str] | None = ("index.html", "Overview") if idx == 0 else pairs[idx - 1]
    next_item: tuple[str, str] | None = (
        ("index.html", "Documentation") if idx == len(pairs) - 1 else pairs[idx + 1]
    )
    return pager_html(prev_item, next_item)


def pager_overview() -> str:
    return pager_html(None, CHAPTER_NAV_ORDER[0])


OVERVIEW_MAIN = """            <div class="doc-section doc-overview">
                <p class="doc-section-label">Documentation</p>
                <h1>Welcome to the Cipi docs</h1>
                <p class="doc-lead">Cipi is the open-source deploy CLI for Laravel. The documentation is split into
                    chapters so you can focus on one topic at a time — similar to how frameworks like
                    <a href="https://filamentphp.com/docs/5.x/introduction/overview" target="_blank" rel="noopener">Filament</a>
                    structure their guides.</p>

                <div class="docs-chapter-grid">
                    <a class="docs-chapter-card" href="getting-started.html">
                        <span class="docs-chapter-card-label">Start here</span>
                        <span class="docs-chapter-card-title">Getting started</span>
                        <span class="docs-chapter-card-desc">Installation, requirements, quick start, stack, and app layout.</span>
                    </a>
                    <a class="docs-chapter-card" href="agent.html">
                        <span class="docs-chapter-card-label">Automation</span>
                        <span class="docs-chapter-card-title">Cipi Agent</span>
                        <span class="docs-chapter-card-desc">Webhook, health, MCP server, anonymizer, and agent env.</span>
                    </a>
                    <a class="docs-chapter-card" href="apps.html">
                        <span class="docs-chapter-card-label">Applications</span>
                        <span class="docs-chapter-card-title">Apps</span>
                        <span class="docs-chapter-card-desc"><code>app create</code>, env, logs, Artisan, and SSH.</span>
                    </a>
                    <a class="docs-chapter-card" href="deploy.html">
                        <span class="docs-chapter-card-label">Shipping</span>
                        <span class="docs-chapter-card-title">Deploy &amp; CI/CD</span>
                        <span class="docs-chapter-card-desc">Deploy, Git providers, pipelines, notifications, previews.</span>
                    </a>
                    <a class="docs-chapter-card" href="infrastructure.html">
                        <span class="docs-chapter-card-label">Server</span>
                        <span class="docs-chapter-card-title">Infrastructure</span>
                        <span class="docs-chapter-card-desc">PHP, DB, SSL, backups, workers, firewall, services.</span>
                    </a>
                    <a class="docs-chapter-card" href="advanced.html">
                        <span class="docs-chapter-card-label">Power users</span>
                        <span class="docs-chapter-card-title">Advanced</span>
                        <span class="docs-chapter-card-desc">API, sync, vault, SMTP, Redis, wildcards, uninstall.</span>
                    </a>
                    <a class="docs-chapter-card" href="about.html">
                        <span class="docs-chapter-card-label">Context</span>
                        <span class="docs-chapter-card-title">About Cipi</span>
                        <span class="docs-chapter-card-desc">History, security model, and comparisons.</span>
                    </a>
                </div>
            </div>
"""


EXTRA_CSS = """

        .doc-overview h1 {
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 0.75rem;
        }

        .doc-lead {
            font-size: 1.05rem;
            color: var(--text-secondary);
            max-width: 52rem;
            margin-bottom: 2rem;
        }

        .doc-lead a {
            color: var(--accent);
        }

        .docs-chapter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 16px;
            margin-top: 0.5rem;
        }

        .docs-chapter-card {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 20px 20px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            text-decoration: none;
            color: inherit;
            box-shadow: var(--shadow-sm);
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .docs-chapter-card:hover {
            border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
            box-shadow: var(--shadow-md);
        }

        .docs-chapter-card-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
            font-weight: 600;
        }

        .docs-chapter-card-title {
            font-family: var(--font-display);
            font-size: 1.15rem;
            font-weight: 600;
        }

        .docs-chapter-card-desc {
            font-size: 0.88rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .docs-chapter-card-desc code {
            font-size: 0.82em;
        }

        .docs-pager {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px 32px;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
        }

        .docs-pager-link {
            display: flex;
            flex-direction: column;
            gap: 4px;
            max-width: min(100%, 20rem);
            text-decoration: none;
            color: var(--text);
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            background: var(--bg-card);
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .docs-pager-link:hover {
            border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
            box-shadow: var(--shadow-sm);
        }

        .docs-pager-next {
            text-align: right;
            align-items: flex-end;
            margin-left: auto;
        }

        .docs-pager-next .docs-pager-kicker {
            align-self: flex-end;
        }

        .docs-pager-kicker {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
            font-weight: 600;
        }

        .docs-pager-label {
            font-family: var(--font-display);
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent);
            line-height: 1.35;
        }

        .docs-pager-placeholder {
            flex: 1;
            min-width: 0;
            max-width: 12rem;
        }

        .docs-pager-link:only-child {
            margin-left: auto;
        }

        @media (max-width: 600px) {
            .docs-pager {
                flex-direction: column;
            }

            .docs-pager-next {
                margin-left: 0;
                text-align: left;
                align-items: flex-start;
            }

            .docs-pager-next .docs-pager-kicker {
                align-self: flex-start;
            }

            .docs-pager-link:only-child {
                margin-left: 0;
                max-width: 100%;
            }
        }

        .docs-sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }

        nav .nav-inner {
            display: grid;
            grid-template-columns: minmax(0, auto) minmax(0, 1fr) minmax(0, auto);
            align-items: center;
            gap: 0 12px;
            justify-content: unset;
        }

        .nav-search {
            display: flex;
            justify-content: center;
            min-width: 0;
        }

        .docs-search-trigger {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            max-width: 320px;
            padding: 7px 12px;
            border-radius: 100px;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text-muted);
            font-size: 0.8rem;
            cursor: pointer;
            transition: border-color 0.2s, color 0.2s;
        }

        .docs-search-trigger:hover {
            border-color: color-mix(in srgb, var(--accent) 35%, var(--border));
            color: var(--text-secondary);
        }

        .docs-search-icon {
            width: 16px;
            height: 16px;
            flex-shrink: 0;
        }

        .docs-search-trigger-label {
            flex: 1;
            text-align: left;
        }

        .docs-search-kbd-hint {
            font-family: var(--font-mono);
            font-size: 0.65rem;
            font-weight: 500;
            padding: 2px 6px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--bg-warm);
            color: var(--text-muted);
        }

        .docs-kbd-mod {
            font-size: 0.75em;
        }

        .docs-search-overlay[hidden] {
            display: none !important;
        }

        .docs-search-overlay {
            position: fixed;
            inset: 0;
            z-index: 400;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 10vh 16px 16px;
        }

        .docs-search-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(15, 15, 18, 0.45);
            backdrop-filter: blur(4px);
        }

        [data-theme="dark"] .docs-search-backdrop {
            background: rgba(0, 0, 0, 0.55);
        }

        .docs-search-panel {
            position: relative;
            width: min(100%, 32rem);
            max-height: min(70vh, 520px);
            display: flex;
            flex-direction: column;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow-md);
            overflow: hidden;
        }

        .docs-search-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-light);
        }

        .docs-search-input-icon {
            width: 18px;
            height: 18px;
            flex-shrink: 0;
            color: var(--text-muted);
        }

        .docs-search-input {
            flex: 1;
            border: none;
            background: transparent;
            font: inherit;
            font-size: 0.95rem;
            color: var(--text);
            min-width: 0;
        }

        .docs-search-input:focus {
            outline: none;
        }

        .docs-search-input::placeholder {
            color: var(--text-muted);
        }

        .docs-search-close {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 6px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: var(--text-muted);
            cursor: pointer;
            transition: color 0.2s, background 0.2s;
        }

        .docs-search-close:hover {
            color: var(--text);
            background: var(--bg-warm);
        }

        .docs-search-results {
            list-style: none;
            margin: 0;
            padding: 6px;
            overflow-y: auto;
            flex: 1;
        }

        .docs-search-results a {
            display: block;
            padding: 10px 12px;
            border-radius: var(--radius-sm);
            text-decoration: none;
            color: inherit;
            transition: background 0.15s;
        }

        .docs-search-results a:hover,
        .docs-search-results a:focus-visible {
            background: var(--bg-warm);
            outline: none;
        }

        .docs-search-result-chapter {
            display: block;
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--accent);
            font-weight: 600;
            margin-bottom: 2px;
        }

        .docs-search-result-title {
            display: block;
            font-family: var(--font-display);
            font-size: 1rem;
            font-weight: 600;
            color: var(--text);
        }

        .docs-search-result-snippet {
            display: -webkit-box;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
            line-height: 1.45;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .docs-search-empty {
            padding: 16px;
            text-align: center;
            font-size: 0.88rem;
            color: var(--text-muted);
        }

        @media (max-width: 900px) {
            .nav-search {
                max-width: none;
                margin: 0 8px;
            }

            .docs-search-trigger-label {
                display: none;
            }

            .docs-search-kbd-hint {
                display: none;
            }

            .docs-search-trigger {
                width: auto;
                padding: 8px 12px;
            }
        }

        @media (max-width: 480px) {
            .nav-inner {
                flex-wrap: wrap;
                row-gap: 8px;
            }

            .nav-search {
                order: 3;
                flex: 1 1 100%;
                margin: 0;
                max-width: none;
            }

            .docs-search-trigger {
                max-width: none;
            }
        }
"""


def build_sidebar_mapping() -> None:
    """Populate ANCHOR_TO_PAGE from SIDEBAR_GROUPS."""
    global ANCHOR_TO_PAGE
    ANCHOR_TO_PAGE = {}
    page_by_group = {
        "getting started": "getting-started.html",
        "Cipi Agent": "agent.html",
        "apps": "apps.html",
        "deploy & CI/CD": "deploy.html",
        "infrastructure": "infrastructure.html",
        "advanced": "advanced.html",
        "about cipi": "about.html",
    }
    for label, items in SIDEBAR_GROUPS:
        fname = page_by_group[label]
        for anchor, _ in items:
            ANCHOR_TO_PAGE[anchor] = fname


def _strip_small_html_fragment(fragment: str) -> str:
    """Plain text from a short HTML string (e.g. sidebar titles with <code>)."""
    t = re.sub(r"<[^>]+>", " ", fragment)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _html_chunk_to_plain(chunk: str, max_len: int = 8000) -> str:
    """Strip tags and scripts from a doc section for search text."""
    chunk = re.sub(r"<script[^>]*>.*?</script>", "", chunk, flags=re.DOTALL | re.IGNORECASE)
    chunk = re.sub(r"<style[^>]*>.*?</style>", "", chunk, flags=re.DOTALL | re.IGNORECASE)
    chunk = re.sub(r"<[^>]+>", " ", chunk)
    chunk = html.unescape(chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip()
    if len(chunk) > max_len:
        chunk = chunk[:max_len].rsplit(" ", 1)[0] + " …"
    return chunk


def _section_h2_title(html_chunk: str, fallback: str) -> str:
    m = re.search(r"<h2[^>]*>(.*?)</h2>", html_chunk, re.DOTALL | re.IGNORECASE)
    if m:
        return _strip_small_html_fragment(m.group(1))
    return fallback


def anchor_sidebar_meta() -> dict[str, tuple[str, str]]:
    """anchor -> (group label, plain sidebar title)."""
    out: dict[str, tuple[str, str]] = {}
    for label, items in SIDEBAR_GROUPS:
        for anchor, title_html in items:
            out[anchor] = (label, _strip_small_html_fragment(title_html))
    return out


def build_search_index(sections: dict[str, str]) -> list[dict[str, str]]:
    """Records for client-side Fuse.js (docs/search-index.json)."""
    meta = anchor_sidebar_meta()
    records: list[dict[str, str]] = []
    for anchor in sorted(sections.keys()):
        chunk = sections[anchor]
        group_label, sidebar_title = meta.get(anchor, ("", anchor))
        title = _section_h2_title(chunk, sidebar_title)
        page = ANCHOR_TO_PAGE.get(anchor)
        if not page:
            continue
        records.append(
            {
                "id": anchor,
                "url": f"{page}#{anchor}",
                "chapter": group_label,
                "title": title,
                "text": _html_chunk_to_plain(chunk),
            }
        )
    return records


def main() -> None:
    build_sidebar_mapping()
    text = DOCS_HTML.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    m = re.search(r"<style>\s*\n(.*)\n\s*</style>", text, re.DOTALL)
    if not m:
        raise SystemExit("Could not extract <style> from docs-source.html")
    base_css = m.group(1)
    DOCS_DIR.mkdir(exist_ok=True)
    CSS_OUT.write_text(base_css + EXTRA_CSS, encoding="utf-8")

    sections = extract_sections(lines)

    search_path = DOCS_DIR / "search-index.json"
    search_path.write_text(
        json.dumps(build_search_index(sections), ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # Chapter HTML
    for start_line, out_name, pkey in CHAPTER_RANGES:
        end_line = None
        for i, sl in enumerate(CHAPTER_RANGES):
            if sl[0] == start_line:
                end_line = CHAPTER_RANGES[i + 1][0] - 1 if i + 1 < len(CHAPTER_RANGES) else 6943
                break
        assert end_line is not None
        chapter_ids: list[str] = []
        for sl in SECTION_STARTS:
            if sl < start_line:
                continue
            if sl > end_line:
                break
            line_content = lines[sl - 1]
            mm = re.search(r'id="([^"]+)"', line_content)
            if mm:
                chapter_ids.append(mm.group(1))

        body_chunks = [sections[sid] for sid in chapter_ids]
        main_inner = "".join(body_chunks)
        main_inner = rewrite_internal_links(main_inner, out_name)

        title, desc = CHAPTER_HEAD[out_name]
        canon = f"https://cipi.sh/docs/{out_name}"

        out = head_html(title, desc, canon, canon)
        out += "\n<body>\n\n"
        out += NAV_BLOCK
        out += '\n    <div class="mobile-sidebar-overlay" id="sidebarOverlay"></div>\n\n'
        out += '    <div class="docs-layout">\n\n'
        out += '        <aside class="docs-sidebar" id="docsSidebar">\n\n'
        out += sidebar_html(pkey)
        out += "        </aside>\n\n"
        out += '        <main class="docs-content" id="docsContent">\n\n'
        out += main_inner
        out += pager_for_chapter(out_name)
        out += "\n        </main>\n    </div>\n\n"
        out += FOOTER_AND_SCRIPT
        out += "\n</body>\n</html>\n"
        (DOCS_DIR / out_name).write_text(out, encoding="utf-8")

    # Index
    title, desc = OVERVIEW_HEAD
    canon = "https://cipi.sh/docs/"
    out = head_html(title, desc, canon, canon)
    out += "\n<body>\n\n"
    out += NAV_BLOCK
    out += '\n    <div class="mobile-sidebar-overlay" id="sidebarOverlay"></div>\n\n'
    out += '    <div class="docs-layout">\n\n'
    out += '        <aside class="docs-sidebar" id="docsSidebar">\n\n'
    out += sidebar_html(None)
    out += "        </aside>\n\n"
    out += '        <main class="docs-content" id="docsContent">\n\n'
    out += OVERVIEW_MAIN
    out += pager_overview()
    out += "\n        </main>\n    </div>\n\n"
    out += FOOTER_AND_SCRIPT
    out += "\n</body>\n</html>\n"
    (DOCS_DIR / "index.html").write_text(out, encoding="utf-8")

    # Legacy docs.html → multi-page docs (preserve #anchors)
    redirect_map = json.dumps(ANCHOR_TO_PAGE, separators=(",", ":"))
    legacy = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting to documentation…</title>
    <link rel="canonical" href="https://cipi.sh/docs/">
    <script>
        (function () {{
            var ANCHOR_TO_PAGE = {redirect_map};
            var h = (location.hash || "").slice(1);
            if (h && ANCHOR_TO_PAGE[h]) {{
                location.replace("docs/" + ANCHOR_TO_PAGE[h] + "#" + h);
            }} else {{
                location.replace("docs/");
            }}
        }})();
    </script>
    <meta http-equiv="refresh" content="0;url=docs/">
</head>
<body>
    <p style="font-family: system-ui, sans-serif; padding: 2rem;">Redirecting to <a href="docs/">documentation</a>…</p>
</body>
</html>
"""
    (ROOT / "docs.html").write_text(legacy, encoding="utf-8")

    print("Wrote", CSS_OUT, "and pages under", DOCS_DIR)


if __name__ == "__main__":
    main()
