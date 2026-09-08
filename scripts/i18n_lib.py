"""Shared i18n configuration for cipi.sh (must stay in sync with netlify/edge-functions/i18n.js)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cipi.sh"

# Display order in the language dropdown
LANGUAGES = [
    ("en", "English", "EN"),
    ("de", "Deutsch", "DE"),
    ("fr", "Français", "FR"),
    ("it", "Italiano", "IT"),
    ("es", "Español", "ES"),
    ("pt", "Português", "PT"),
]

LANG_CODES = [code for code, _, _ in LANGUAGES]

OG_LOCALES = {
    "en": "en_US",
    "de": "de_DE",
    "fr": "fr_FR",
    "it": "it_IT",
    "es": "es_ES",
    "pt": "pt_PT",
}

# English canon → localized path per language (must match netlify/edge-functions/i18n.js)
_GUIDE_SLUGS = {
    "/guides/deploy-laravel-ubuntu-vps": {
        "de": "/guides/laravel-auf-ubuntu-vps-deployen",
        "fr": "/guides/deployer-laravel-sur-vps-ubuntu",
        "es": "/guides/desplegar-laravel-en-vps-ubuntu",
        "pt": "/guides/deploy-laravel-em-vps-ubuntu",
        "it": "/guide/deploy-laravel-su-ubuntu-vps",
    },
    "/guides/laravel-security-checklist": {
        "de": "/guides/laravel-sicherheitscheckliste",
        "fr": "/guides/checklist-securite-laravel",
        "es": "/guides/checklist-seguridad-laravel",
        "pt": "/guides/checklist-seguranca-laravel",
        "it": "/guide/checklist-sicurezza-laravel",
    },
    "/guides/laravel-ecosystem-2026": {
        "de": "/guides/laravel-oekosystem-2026",
        "fr": "/guides/ecosysteme-laravel-2026",
        "es": "/guides/ecosistema-laravel-2026",
        "pt": "/guides/ecossistema-laravel-2026",
        "it": "/guide/ecosistema-laravel-2026",
    },
    "/guides/laravel-ci-cd-git-workflow": {
        "de": "/guides/ci-cd-git-workflow-fuer-laravel",
        "fr": "/guides/ci-cd-et-workflow-git-laravel",
        "es": "/guides/ci-cd-flujo-git-laravel",
        "pt": "/guides/ci-cd-e-workflow-git-laravel",
        "it": "/guide/ci-cd-workflow-git-laravel",
    },
    "/guides/spec-driven-development-ai-laravel": {
        "de": "/guides/spezifikationsgetriebene-ki-entwicklung-laravel",
        "fr": "/guides/developpement-spec-driven-ia-laravel",
        "es": "/guides/desarrollo-spec-driven-ia-laravel",
        "pt": "/guides/desenvolvimento-spec-driven-ia-laravel",
        "it": "/guide/sviluppo-spec-driven-ai-laravel",
    },
    "/guides/laravel-developer-stack-2026": {
        "de": "/guides/self-hosted-entwickler-stack-2026",
        "fr": "/guides/stack-developpeur-self-hosted-2026",
        "es": "/guides/stack-desarrollador-self-hosted-2026",
        "pt": "/guides/stack-desenvolvedor-self-hosted-2026",
        "it": "/guide/stack-developer-self-hosted-2026",
    },
        "/guides/backup-vps-s3": {
            "de": "/guides/vps-backup-auf-s3",
            "fr": "/guides/sauvegarde-vps-vers-s3",
            "es": "/guides/copias-seguridad-vps-s3",
            "pt": "/guides/backup-vps-para-s3",
            "it": "/guide/backup-vps-s3-con-cipi",
        },
        "/guides/deploy-wordpress-custom-app": {
            "de": "/guides/wordpress-als-custom-app-deployen",
            "fr": "/guides/deployer-wordpress-app-personnalisee",
            "es": "/guides/desplegar-wordpress-app-personalizada",
            "pt": "/guides/deploy-wordpress-app-personalizado",
            "it": "/guide/deploy-wordpress-app-custom-github",
        },
        "/guides/cipi-agent-laravel-mcp": {
            "de": "/guides/cipi-agent-in-laravel-nutzen",
            "fr": "/guides/utiliser-cipi-agent-laravel",
            "es": "/guides/usar-cipi-agent-en-laravel",
            "pt": "/guides/usar-cipi-agent-no-laravel",
            "it": "/guide/usare-cipi-agent-in-laravel",
        },
        "/guides/cipi-gui-and-api": {
            "de": "/guides/gui-panel-und-api",
            "fr": "/guides/panneau-ui-et-api",
            "es": "/guides/panel-ui-y-api",
            "pt": "/guides/painel-ui-e-api",
            "it": "/guide/pannello-ui-e-api-cipi",
        },
        "/guides/manage-apps-with-cipi-yml": {
            "de": "/guides/apps-mit-cipi-yml-verwalten",
            "fr": "/guides/gerer-apps-avec-cipi-yml",
            "es": "/guides/gestionar-apps-con-cipi-yml",
            "pt": "/guides/gerenciar-apps-com-cipi-yml",
            "it": "/guide/gestire-app-con-cipi-yml",
        },
    }

SLUGS_IT = {
    "/": "/",
    "/404": "/404",
    "/whats-new": "/novita",
    "/cipi-yml": "/cipi-yml",
    "/discovery": "/discovery",
    "/alternatives": "/alternative",
    "/best-laravel-forge-alternatives": "/migliori-alternative-a-laravel-forge",
    "/alternative-to-20i": "/alternativa-a-20i",
    "/alternative-to-cleavr": "/alternativa-a-cleavr",
    "/alternative-to-cloudpanel": "/alternativa-a-cloudpanel",
    "/alternative-to-coolify": "/alternativa-a-coolify",
    "/alternative-to-cpanel": "/alternativa-a-cpanel",
    "/alternative-to-directadmin": "/alternativa-a-directadmin",
    "/alternative-to-dokku": "/alternativa-a-dokku",
    "/alternative-to-easypanel": "/alternativa-a-easypanel",
    "/alternative-to-fortrabbit": "/alternativa-a-fortrabbit",
    "/alternative-to-kamal": "/alternativa-a-kamal",
    "/alternative-to-laravel-cloud": "/alternativa-a-laravel-cloud",
    "/alternative-to-laravel-forge": "/alternativa-a-laravel-forge",
    "/alternative-to-moss": "/alternativa-a-moss",
    "/alternative-to-plesk": "/alternativa-a-plesk",
    "/alternative-to-ploi": "/alternativa-a-ploi",
    "/alternative-to-ploi-cloud": "/alternativa-a-ploi-cloud",
    "/alternative-to-render": "/alternativa-a-render",
    "/alternative-to-runcloud": "/alternativa-a-runcloud",
    "/alternative-to-serverpilot": "/alternativa-a-serverpilot",
    "/alternative-to-sevalla": "/alternativa-a-sevalla",
    "/alternative-to-vito-deploy": "/alternativa-a-vito-deploy",
    "/docs/": "/docs/",
    "/docs/getting-started": "/docs/primi-passi",
    "/docs/agent": "/docs/agent",
    "/docs/apps": "/docs/app",
    "/docs/deploy": "/docs/deploy",
    "/docs/infrastructure": "/docs/infrastruttura",
    "/docs/cli-client": "/docs/client-cli",
    "/docs/gui": "/docs/gui",
    "/docs/advanced": "/docs/avanzato",
    "/docs/about": "/docs/informazioni",
    "/guides/": "/guide/",
}

for _en, _langs in _GUIDE_SLUGS.items():
    SLUGS_IT[_en] = _langs["it"]

SLUGS_BY_LANG: dict[str, dict[str, str]] = {"it": SLUGS_IT}
for _lang in ("de", "fr", "es", "pt"):
    SLUGS_BY_LANG[_lang] = {en: langs[_lang] for en, langs in _GUIDE_SLUGS.items()}

# Localized path → English canon (identity mappings omitted)
SLUGS_TO_EN: dict[str, str] = {}
# Localized path → language that owns it
SLUG_LANG: dict[str, str] = {}
for _lang, _mapping in SLUGS_BY_LANG.items():
    for _en, _loc in _mapping.items():
        if _loc != _en:
            SLUGS_TO_EN[_loc] = _en
            SLUG_LANG[_loc] = _lang

SLUGS_EN = {it: en for en, it in SLUGS_IT.items()}


def to_en_canon(bare: str) -> str:
    if bare == "/guide":
        bare = "/guide/"
    if bare in SLUGS_TO_EN:
        return SLUGS_TO_EN[bare]
    if bare in SLUGS_EN:
        return SLUGS_EN[bare]
    if bare == "/alternative":
        return "/alternatives"
    if bare == "/novita":
        return "/whats-new"
    if bare == "/migliori-alternative-a-laravel-forge":
        return "/best-laravel-forge-alternatives"
    if bare.startswith("/alternativa-a-"):
        return "/alternative-to-" + bare[len("/alternativa-a-") :]
    if bare == "/guide/":
        return "/guides/"
    if bare.startswith("/guide/"):
        return SLUGS_TO_EN.get(bare, "/guides/" + bare[len("/guide/") :])
    return bare


def localize_canon(en_canon: str, lang: str) -> str:
    en = to_en_canon(en_canon)
    if lang == "en":
        return en
    mapped = SLUGS_BY_LANG.get(lang, {}).get(en)
    if mapped:
        return mapped
    if lang == "it" and en.startswith("/alternative-to-"):
        return "/alternativa-a-" + en[len("/alternative-to-") :]
    return en


def localized_html_path(en_canon: str, lang: str) -> Path:
    loc = localize_canon(en_canon, lang)
    if loc == "/":
        return ROOT / "index.html" if lang == "en" else ROOT / lang / "index.html"
    if loc.endswith("/"):
        return ROOT / lang / loc.strip("/") / "index.html"
    return ROOT / lang / f"{loc.lstrip('/')}.html"


def lang_href(lang: str, localized_canon: str) -> str:
    if localized_canon == "/":
        return "/" if lang == "en" else f"/{lang}/"
    return f"/{lang}{localized_canon}"


def abs_href(lang: str, en_canon: str) -> str:
    return f"{BASE}{lang_href(lang, localize_canon(en_canon, lang))}"


def file_to_en_canon(path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith("404.html"):
        return "/404"
    if rel == "index.html":
        return "/"
    if not (rel.startswith("en/") or rel.startswith("it/") or rel.startswith("de/")
            or rel.startswith("fr/") or rel.startswith("es/") or rel.startswith("pt/")):
        return None
    lang, rest = rel.split("/", 1)
    if rest.endswith("/index.html"):
        bare = "/" + rest[: -len("index.html")]
    elif rest == "index.html":
        bare = "/"
    else:
        bare = "/" + rest[: -len(".html")]
    if lang == "en":
        return bare
    return to_en_canon(bare)


def detect_page_lang(path: Path) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html" or rel == "404.html":
        return "en"
    if rel.startswith(("en/", "it/", "de/", "fr/", "es/", "pt/")):
        return rel.split("/", 1)[0]
    return None


def build_alternates(en_canon: str) -> str:
    lines = ["    <!-- i18n:alternates -->"]
    for code, _, _ in LANGUAGES:
        lines.append(
            f'    <link rel="alternate" hreflang="{code}" href="{abs_href(code, en_canon)}">'
        )
    lines.append(f'    <link rel="alternate" hreflang="x-default" href="{abs_href("en", en_canon)}">')
    lines.append("    <!-- /i18n:alternates -->")
    return "\n".join(lines)


def build_switch(current_lang: str, en_canon: str) -> str:
    summary = next(label for code, _, label in LANGUAGES if code == current_lang)
    links = []
    for code, name, _ in LANGUAGES:
        href = lang_href(code, localize_canon(en_canon, code))
        active = ' class="active"' if code == current_lang else ""
        links.append(
            f'<a{active} href="{href}" hreflang="{code}" lang="{code}" '
            f"onclick=\"document.cookie='cipi-lang={code};path=/;max-age=31536000;SameSite=Lax'\">{name}</a>"
        )
    menu = "".join(links)
    return (
        f'<!-- i18n:switch --><details class="lang-switch" '
        f'ontoggle="if(this.open){{const s=this;const c=e=>{{if(!s.contains(e.target)){{s.removeAttribute(\'open\');document.removeEventListener(\'pointerdown\',c)}}}};setTimeout(()=>document.addEventListener(\'pointerdown\',c),0)}}">'
        f'<summary aria-label="Language">{summary}</summary><div class="lang-menu">{menu}</div></details><!-- /i18n:switch -->'
    )


def build_og_locales(current_lang: str) -> str:
    primary = OG_LOCALES[current_lang]
    alternates = [OG_LOCALES[c] for c in LANG_CODES if c != current_lang]
    lines = [f'    <meta property="og:locale" content="{primary}">']
    for alt in alternates:
        lines.append(f'    <meta property="og:locale:alternate" content="{alt}">')
    return "\n".join(lines)
