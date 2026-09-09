/**
 * Canonical host + English-only URL graph for Netlify Edge.
 *
 * - `/` is the English homepage and must return 200 (never language-redirect it).
 * - Public pages live at the site root (`/docs/`, `/whats-new`, …). `/en/…` 301s
 *   to the same path without the prefix.
 * - Former language trees (`/de`, `/fr`, `/it`, `/es`, `/pt`) 301 to the English
 *   equivalent. Localized slugs (Italian `/novita`, German guide paths, …) map
 *   through the tables below, then land on the unprefixed English URL.
 * - Accept-Language and the cipi-lang cookie are never used for redirects.
 * - Unknown paths are not rewritten (real 404 — no redirect-to-404).
 */
export const CANONICAL_HOST = 'cipi.sh';

const LANG_PREFIXES = ['en', 'de', 'fr', 'it', 'es', 'pt'];
const LANG_PREFIX_RE = /^\/(en|de|fr|it|es|pt)(\/|$)/;

const ASSET_EXT_RE =
  /\.(?:css|js|mjs|map|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|txt|xml|xsl|json|webmanifest|pdf|zip|gz|tgz|sh|mp4|webm|wasm)$/i;

const GUIDE_SLUGS = {
  '/guides/deploy-laravel-ubuntu-vps': {
    de: '/guides/laravel-auf-ubuntu-vps-deployen',
    fr: '/guides/deployer-laravel-sur-vps-ubuntu',
    es: '/guides/desplegar-laravel-en-vps-ubuntu',
    pt: '/guides/deploy-laravel-em-vps-ubuntu',
    it: '/guide/deploy-laravel-su-ubuntu-vps',
  },
  '/guides/laravel-security-checklist': {
    de: '/guides/laravel-sicherheitscheckliste',
    fr: '/guides/checklist-securite-laravel',
    es: '/guides/checklist-seguridad-laravel',
    pt: '/guides/checklist-seguranca-laravel',
    it: '/guide/checklist-sicurezza-laravel',
  },
  '/guides/laravel-ecosystem-2026': {
    de: '/guides/laravel-oekosystem-2026',
    fr: '/guides/ecosysteme-laravel-2026',
    es: '/guides/ecosistema-laravel-2026',
    pt: '/guides/ecossistema-laravel-2026',
    it: '/guide/ecosistema-laravel-2026',
  },
  '/guides/laravel-ci-cd-git-workflow': {
    de: '/guides/ci-cd-git-workflow-fuer-laravel',
    fr: '/guides/ci-cd-et-workflow-git-laravel',
    es: '/guides/ci-cd-flujo-git-laravel',
    pt: '/guides/ci-cd-e-workflow-git-laravel',
    it: '/guide/ci-cd-workflow-git-laravel',
  },
  '/guides/spec-driven-development-ai-laravel': {
    de: '/guides/spezifikationsgetriebene-ki-entwicklung-laravel',
    fr: '/guides/developpement-spec-driven-ia-laravel',
    es: '/guides/desarrollo-spec-driven-ia-laravel',
    pt: '/guides/desenvolvimento-spec-driven-ia-laravel',
    it: '/guide/sviluppo-spec-driven-ai-laravel',
  },
  '/guides/laravel-developer-stack-2026': {
    de: '/guides/self-hosted-entwickler-stack-2026',
    fr: '/guides/stack-developpeur-self-hosted-2026',
    es: '/guides/stack-desarrollador-self-hosted-2026',
    pt: '/guides/stack-desenvolvedor-self-hosted-2026',
    it: '/guide/stack-developer-self-hosted-2026',
  },
  '/guides/backup-vps-s3': {
    de: '/guides/vps-backup-auf-s3',
    fr: '/guides/sauvegarde-vps-vers-s3',
    es: '/guides/copias-seguridad-vps-s3',
    pt: '/guides/backup-vps-para-s3',
    it: '/guide/backup-vps-s3-con-cipi',
  },
  '/guides/deploy-wordpress-custom-app': {
    de: '/guides/wordpress-als-custom-app-deployen',
    fr: '/guides/deployer-wordpress-app-personnalisee',
    es: '/guides/desplegar-wordpress-app-personalizada',
    pt: '/guides/deploy-wordpress-app-personalizado',
    it: '/guide/deploy-wordpress-app-custom-github',
  },
  '/guides/cipi-agent-laravel-mcp': {
    de: '/guides/cipi-agent-in-laravel-nutzen',
    fr: '/guides/utiliser-cipi-agent-laravel',
    es: '/guides/usar-cipi-agent-en-laravel',
    pt: '/guides/usar-cipi-agent-no-laravel',
    it: '/guide/usare-cipi-agent-in-laravel',
  },
  '/guides/cipi-gui-and-api': {
    de: '/guides/gui-panel-und-api',
    fr: '/guides/panneau-ui-et-api',
    es: '/guides/panel-ui-y-api',
    pt: '/guides/painel-ui-e-api',
    it: '/guide/pannello-ui-e-api-cipi',
  },
  '/guides/manage-apps-with-cipi-yml': {
    de: '/guides/apps-mit-cipi-yml-verwalten',
    fr: '/guides/gerer-apps-avec-cipi-yml',
    es: '/guides/gestionar-apps-con-cipi-yml',
    pt: '/guides/gerenciar-apps-com-cipi-yml',
    it: '/guide/gestire-app-con-cipi-yml',
  },
};

export const SLUGS_IT = {
  '/': '/',
  '/404': '/404',
  '/whats-new': '/novita',
  '/cipi-yml': '/cipi-yml',
  '/discovery': '/discovery',
  '/alternatives': '/alternative',
  '/best-laravel-forge-alternatives': '/migliori-alternative-a-laravel-forge',
  '/alternative-to-20i': '/alternativa-a-20i',
  '/alternative-to-cleavr': '/alternativa-a-cleavr',
  '/alternative-to-cloudpanel': '/alternativa-a-cloudpanel',
  '/alternative-to-coolify': '/alternativa-a-coolify',
  '/alternative-to-cpanel': '/alternativa-a-cpanel',
  '/alternative-to-directadmin': '/alternativa-a-directadmin',
  '/alternative-to-dokku': '/alternativa-a-dokku',
  '/alternative-to-easypanel': '/alternativa-a-easypanel',
  '/alternative-to-fortrabbit': '/alternativa-a-fortrabbit',
  '/alternative-to-kamal': '/alternativa-a-kamal',
  '/alternative-to-laravel-cloud': '/alternativa-a-laravel-cloud',
  '/alternative-to-laravel-forge': '/alternativa-a-laravel-forge',
  '/alternative-to-moss': '/alternativa-a-moss',
  '/alternative-to-plesk': '/alternativa-a-plesk',
  '/alternative-to-ploi': '/alternativa-a-ploi',
  '/alternative-to-ploi-cloud': '/alternativa-a-ploi-cloud',
  '/alternative-to-render': '/alternativa-a-render',
  '/alternative-to-runcloud': '/alternativa-a-runcloud',
  '/alternative-to-serverpilot': '/alternativa-a-serverpilot',
  '/alternative-to-sevalla': '/alternativa-a-sevalla',
  '/alternative-to-vito-deploy': '/alternativa-a-vito-deploy',
  '/docs/': '/docs/',
  '/docs/getting-started': '/docs/primi-passi',
  '/docs/agent': '/docs/agent',
  '/docs/apps': '/docs/app',
  '/docs/deploy': '/docs/deploy',
  '/docs/infrastructure': '/docs/infrastruttura',
  '/docs/cli-client': '/docs/client-cli',
  '/docs/gui': '/docs/gui',
  '/docs/advanced': '/docs/avanzato',
  '/docs/about': '/docs/informazioni',
  '/guides/': '/guide/',
};

for (const [en, langs] of Object.entries(GUIDE_SLUGS)) {
  SLUGS_IT[en] = langs.it;
}

export const SLUGS_BY_LANG = { it: SLUGS_IT };
for (const lang of ['de', 'fr', 'es', 'pt']) {
  SLUGS_BY_LANG[lang] = Object.fromEntries(
    Object.entries(GUIDE_SLUGS).map(([en, langs]) => [en, langs[lang]]),
  );
}

export const SLUGS_TO_EN = {};
export const SLUG_LANG = {};
for (const [lang, mapping] of Object.entries(SLUGS_BY_LANG)) {
  for (const [en, loc] of Object.entries(mapping)) {
    if (loc !== en) {
      SLUGS_TO_EN[loc] = en;
      SLUG_LANG[loc] = lang;
    }
  }
}

export const SLUGS_EN = Object.fromEntries(Object.entries(SLUGS_IT).map(([en, it]) => [it, en]));

const IT_ONLY_PREFIXES = ['/alternativa-a-', '/guide/'];
const IT_ONLY_EXACT = new Set([
  '/novita',
  '/alternative',
  '/migliori-alternative-a-laravel-forge',
  '/guide',
  '/guide/',
  '/docs/primi-passi',
  '/docs/app',
  '/docs/infrastruttura',
  '/docs/client-cli',
  '/docs/avanzato',
  '/docs/informazioni',
]);

export function normalizeBarePath(pathname) {
  let p = pathname || '/';
  if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);
  if (p.endsWith('.html')) p = p.slice(0, -5);
  if (p === '/index' || p.endsWith('/index')) p = p.slice(0, -'/index'.length) || '/';
  if (p === '/') return '/';
  if (p === '/docs' || p === '/guides' || p === '/guide') return p + '/';
  return p;
}

export function toEnglishCanon(bare) {
  let p = bare;
  if (p === '/guide') p = '/guide/';

  if (SLUGS_TO_EN[p]) return SLUGS_TO_EN[p];
  if (SLUGS_EN[p]) return SLUGS_EN[p];

  if (p === '/alternative') return '/alternatives';
  if (p === '/novita') return '/whats-new';
  if (p === '/migliori-alternative-a-laravel-forge') return '/best-laravel-forge-alternatives';
  if (p.startsWith('/alternativa-a-')) {
    return '/alternative-to-' + p.slice('/alternativa-a-'.length);
  }

  if (p === '/guide/') return '/guides/';
  if (p.startsWith('/guide/')) {
    if (SLUGS_TO_EN[p]) return SLUGS_TO_EN[p];
    if (SLUGS_EN[p]) return SLUGS_EN[p];
    return '/guides/' + p.slice('/guide/'.length);
  }

  return p;
}

export function localizeCanon(bare, lang) {
  const en = toEnglishCanon(bare);
  if (lang === 'en') return en;
  const table = SLUGS_BY_LANG[lang];
  if (table && table[en]) return table[en];
  if (lang === 'it' && en.startsWith('/alternative-to-')) {
    return '/alternativa-a-' + en.slice('/alternative-to-'.length);
  }
  return en;
}

export function langHref(lang, canon) {
  // Public site is unprefixed English. `lang` is ignored; kept for call-site compatibility.
  if (canon === '/') return '/';
  return canon;
}

export function languageForBarePath(bare) {
  if (SLUG_LANG[bare]) return SLUG_LANG[bare];
  if (IT_ONLY_EXACT.has(bare)) return 'it';
  for (const prefix of IT_ONLY_PREFIXES) {
    if (bare.startsWith(prefix)) return 'it';
  }
  return 'en';
}

export function isAssetPath(path) {
  if (path.startsWith('/css/') || path.startsWith('/.well-known/')) return true;
  const last = path.slice(path.lastIndexOf('/') + 1);
  if (!last.includes('.')) return false;
  if (last.endsWith('.html')) return false;
  return ASSET_EXT_RE.test(last) || last.includes('.');
}

export function isTranslatedSlug(path) {
  const bare = normalizeBarePath(path);
  if (bare === '/') return false;
  if (SLUGS_TO_EN[bare] || SLUG_LANG[bare]) return true;
  if (IT_ONLY_EXACT.has(bare)) return true;
  for (const prefix of IT_ONLY_PREFIXES) {
    if (bare.startsWith(prefix)) return true;
  }
  if (bare.startsWith('/alternativa-a-')) return true;
  return false;
}

export function isKnownLegacyPath(path) {
  return isTranslatedSlug(path);
}

function isUglyPath(path, pretty) {
  if (path === pretty) return false;
  if (path.endsWith('.html') || path.endsWith('/index.html') || path === '/index.html') return true;
  const strip = (p) => (p.length > 1 && p.endsWith('/') ? p.slice(0, -1) : p);
  return strip(path) === strip(pretty);
}

function decidePath(path) {
  if (isAssetPath(path) && !path.endsWith('.html')) {
    return { pass: true };
  }

  if (path === '/index.html') {
    return { redirect: '/', status: 301 };
  }

  if (LANG_PREFIX_RE.test(path)) {
    const rest = path.replace(/^\/(en|de|fr|it|es|pt)/, '') || '/';
    const expected = langHref('en', toEnglishCanon(normalizeBarePath(rest)));
    if (path !== expected) {
      return { redirect: expected, status: 301 };
    }
    return { pass: true };
  }

  if (isAssetPath(path)) {
    return { pass: true };
  }

  const expected = langHref('en', toEnglishCanon(normalizeBarePath(path)));
  if (path !== expected && (isTranslatedSlug(path) || isUglyPath(path, expected))) {
    return { redirect: expected, status: 301 };
  }

  return { pass: true };
}

/**
 * Pure routing decision. `pass` means serve the origin file (or a real 404).
 * `redirect` is a pathname on the same origin.
 */
export function decide(url, { isPreview = false } = {}) {
  const hostNeedsCanon =
    !isPreview && (url.protocol === 'http:' || url.hostname === `www.${CANONICAL_HOST}`);
  const pathDecision = decidePath(url.pathname);

  if (hostNeedsCanon) {
    const next = new URL(url.toString());
    next.protocol = 'https:';
    next.hostname = CANONICAL_HOST;
    if (pathDecision.redirect) {
      next.pathname = pathDecision.redirect;
    }
    return { redirect: next.pathname + next.search, status: 301, absolute: next.toString() };
  }

  return pathDecision;
}

function redirectTo(request, pathname, status = 301, absolute) {
  const location = absolute || (() => {
    const url = new URL(request.url);
    url.pathname = pathname;
    return url.toString();
  })();
  return new Response(null, {
    status,
    headers: {
      Location: location,
      'Cache-Control': 'public, max-age=3600',
    },
  });
}

export default async (request) => {
  const url = new URL(request.url);
  const isPreview =
    url.hostname.endsWith('.netlify.app') || url.hostname.endsWith('.pages.dev');
  const decision = decide(url, { isPreview });
  if (decision.pass) return;
  return redirectTo(request, decision.redirect, decision.status, decision.absolute);
};

export const config = { path: '/*' };
