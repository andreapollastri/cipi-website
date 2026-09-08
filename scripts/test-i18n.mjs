#!/usr/bin/env node
/**
 * Unit tests for netlify/edge-functions/i18n.js routing (no Netlify runtime).
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import {
  decide,
  langHref,
  languageForBarePath,
  localizeCanon,
  normalizeBarePath,
} from '../netlify/edge-functions/i18n.js';

let failed = 0;
let passed = 0;

function url(path, { host = 'cipi.sh', proto = 'https:' } = {}) {
  return new URL(`${proto}//${host}${path}`);
}

function assert(name, cond) {
  if (cond) {
    passed += 1;
    return;
  }
  failed += 1;
  console.error('FAIL', name);
}

function assertPass(path, note = '') {
  const d = decide(url(path));
  assert(`pass ${path} ${note}`.trim(), d.pass === true);
}

function assertRedirect(path, dest, note = '') {
  const d = decide(url(path));
  assert(
    `301 ${path} → ${dest} ${note}`.trim(),
    d.redirect === dest && d.status === 301 && !d.pass,
  );
}

// Homepage: never redirected (the GSC "Page with redirect" bug)
assertPass('/', 'English homepage must be 200');
assertPass('/', 'Accept-Language must not matter');
assertRedirect('/index.html', '/');
assertRedirect('/en', '/');
assertRedirect('/en/', '/');
assertRedirect('/en/index.html', '/');

// Italian home
assertPass('/it/');
assertRedirect('/it', '/it/');
assertRedirect('/it/index.html', '/it/');

// In-tree English pages stay put
assertPass('/en/docs/');
assertPass('/en/docs/getting-started');
assertPass('/en/alternatives');
assertPass('/en/whats-new');

// In-tree Italian pages stay put
assertPass('/it/docs/');
assertPass('/it/docs/primi-passi');
assertPass('/it/alternative');
assertPass('/it/novita');

// Slug localization inside a language tree
assertRedirect('/it/docs/getting-started', '/it/docs/primi-passi');
assertRedirect('/en/docs/primi-passi', '/en/docs/getting-started');
assertRedirect('/it/whats-new', '/it/novita');
assertRedirect('/en/novita', '/en/whats-new');
assertRedirect('/en/docs', '/en/docs/');
assertRedirect('/it/guide', '/it/guide/');

// Legacy bare English paths → /en/… (not /)
assertRedirect('/docs', '/en/docs/');
assertRedirect('/docs/', '/en/docs/');
assertRedirect('/docs/getting-started', '/en/docs/getting-started');
assertRedirect('/guides', '/en/guides/');
assertRedirect('/alternatives', '/en/alternatives');
assertRedirect('/whats-new', '/en/whats-new');
assertRedirect('/alternative-to-ploi', '/en/alternative-to-ploi');
assertRedirect('/alternative-to-sevalla', '/en/alternative-to-sevalla');
assertRedirect('/it/alternative-to-sevalla', '/it/alternativa-a-sevalla');
assertRedirect('/it/alternative-to-20i', '/it/alternativa-a-20i');
assertRedirect('/it/alternative-to-fortrabbit', '/it/alternativa-a-fortrabbit');
assertRedirect('/it/alternative-to-render', '/it/alternativa-a-render');
assertRedirect('/it/alternative-to-ploi-cloud', '/it/alternativa-a-ploi-cloud');
assertPass('/it/alternativa-a-sevalla');
assertPass('/it/alternativa-a-20i');
assertPass('/it/alternativa-a-fortrabbit');
assertPass('/it/alternativa-a-render');
assertPass('/it/alternativa-a-ploi-cloud');
assertRedirect('/it/alternatives', '/it/alternative');
assertRedirect('/it/whats-new', '/it/novita');
assertRedirect('/it/best-laravel-forge-alternatives', '/it/migliori-alternative-a-laravel-forge');
assertRedirect('/en/alternativa-a-sevalla', '/en/alternative-to-sevalla');

// Legacy bare Italian slugs → /it/… (slug language, not Accept-Language)
assertRedirect('/novita', '/it/novita');
assertRedirect('/alternative', '/it/alternative');
assertRedirect('/alternativa-a-ploi', '/it/alternativa-a-ploi');
assertRedirect('/guide/', '/it/guide/');
assertRedirect('/guide/deploy-laravel-su-ubuntu-vps', '/it/guide/deploy-laravel-su-ubuntu-vps');
assertRedirect('/guide/backup-vps-s3-con-cipi', '/it/guide/backup-vps-s3-con-cipi');
assertRedirect('/it/guides/backup-vps-s3', '/it/guide/backup-vps-s3-con-cipi');
assertRedirect('/en/guide/backup-vps-s3-con-cipi', '/en/guides/backup-vps-s3');
assertRedirect('/guide/deploy-wordpress-app-custom-github', '/it/guide/deploy-wordpress-app-custom-github');
assertRedirect('/it/guides/deploy-wordpress-custom-app', '/it/guide/deploy-wordpress-app-custom-github');
assertRedirect('/en/guide/deploy-wordpress-app-custom-github', '/en/guides/deploy-wordpress-custom-app');
assertRedirect('/guide/usare-cipi-agent-in-laravel', '/it/guide/usare-cipi-agent-in-laravel');
assertRedirect('/it/guides/cipi-agent-laravel-mcp', '/it/guide/usare-cipi-agent-in-laravel');
assertRedirect('/en/guide/usare-cipi-agent-in-laravel', '/en/guides/cipi-agent-laravel-mcp');
assertRedirect('/guide/pannello-ui-e-api-cipi', '/it/guide/pannello-ui-e-api-cipi');
assertRedirect('/it/guides/cipi-gui-and-api', '/it/guide/pannello-ui-e-api-cipi');
assertRedirect('/en/guide/pannello-ui-e-api-cipi', '/en/guides/cipi-gui-and-api');
assertRedirect('/guide/gestire-app-con-cipi-yml', '/it/guide/gestire-app-con-cipi-yml');
assertRedirect('/it/guides/manage-apps-with-cipi-yml', '/it/guide/gestire-app-con-cipi-yml');
assertRedirect('/en/guide/gestire-app-con-cipi-yml', '/en/guides/manage-apps-with-cipi-yml');
assertRedirect('/docs/primi-passi', '/it/docs/primi-passi');

// Unknown paths: real 404, not redirect-to-/en/404
assertPass('/this-page-does-not-exist');
assertPass('/random-old-url');
assertPass('/en/this-page-does-not-exist');

// Assets never rewritten
assertPass('/robots.txt');
assertPass('/sitemap.xml');
assertPass('/llms.txt');
assertPass('/css/site.css');
assertPass('/setup.sh');
assertPass('/og.png');
assertPass('/.well-known/security.txt');

// Host / protocol canonicalization
{
  const d = decide(url('/', { proto: 'http:' }));
  assert('http → https 301', d.status === 301 && d.absolute === 'https://cipi.sh/');
}
{
  const d = decide(url('/it/', { host: 'www.cipi.sh' }));
  assert('www → apex 301', d.status === 301 && d.absolute === 'https://cipi.sh/it/');
}
{
  const d = decide(url('/', { host: 'deploy-preview-1.netlify.app' }), { isPreview: true });
  assert('preview host not rewritten', d.pass === true);
}

// New language trees
assertPass('/de/');
assertPass('/fr/');
assertPass('/es/');
assertPass('/pt/');
assertRedirect('/de', '/de/');
assertRedirect('/fr', '/fr/');
assertPass('/de/docs/getting-started');
assertPass('/fr/alternatives');

// Helpers
assert('langHref en home is /', langHref('en', '/') === '/');
assert('langHref it home is /it/', langHref('it', '/') === '/it/');
assert('langHref de home is /de/', langHref('de', '/') === '/de/');
assert('langHref fr home is /fr/', langHref('fr', '/') === '/fr/');
assert('languageForBarePath /novita is it', languageForBarePath('/novita') === 'it');
assert('languageForBarePath /docs/ is en', languageForBarePath('/docs/') === 'en');
assert('normalize /docs/ → /docs/', normalizeBarePath('/docs/') === '/docs/');
assert('localize it getting-started', localizeCanon('/docs/getting-started', 'it') === '/docs/primi-passi');
assert('localize de getting-started stays EN slug', localizeCanon('/docs/getting-started', 'de') === '/docs/getting-started');
assert('localize de deploy guide', localizeCanon('/guides/deploy-laravel-ubuntu-vps', 'de') === '/guides/laravel-auf-ubuntu-vps-deployen');
assert('localize fr backup guide', localizeCanon('/guides/backup-vps-s3', 'fr') === '/guides/sauvegarde-vps-vers-s3');
assert('localize de wordpress guide', localizeCanon('/guides/deploy-wordpress-custom-app', 'de') === '/guides/wordpress-als-custom-app-deployen');
assert('localize es security guide', localizeCanon('/guides/laravel-security-checklist', 'es') === '/guides/checklist-seguridad-laravel');
assert('localize pt ecosystem guide', localizeCanon('/guides/laravel-ecosystem-2026', 'pt') === '/guides/ecossistema-laravel-2026');
assert('localize it agent guide', localizeCanon('/guides/cipi-agent-laravel-mcp', 'it') === '/guide/usare-cipi-agent-in-laravel');
assert('localize de agent guide', localizeCanon('/guides/cipi-agent-laravel-mcp', 'de') === '/guides/cipi-agent-in-laravel-nutzen');
assert('localize fr agent guide', localizeCanon('/guides/cipi-agent-laravel-mcp', 'fr') === '/guides/utiliser-cipi-agent-laravel');
assert('localize es agent guide', localizeCanon('/guides/cipi-agent-laravel-mcp', 'es') === '/guides/usar-cipi-agent-en-laravel');
assert('localize pt agent guide', localizeCanon('/guides/cipi-agent-laravel-mcp', 'pt') === '/guides/usar-cipi-agent-no-laravel');
assert('localize it gui api guide', localizeCanon('/guides/cipi-gui-and-api', 'it') === '/guide/pannello-ui-e-api-cipi');
assert('localize de gui api guide', localizeCanon('/guides/cipi-gui-and-api', 'de') === '/guides/gui-panel-und-api');
assert('localize fr gui api guide', localizeCanon('/guides/cipi-gui-and-api', 'fr') === '/guides/panneau-ui-et-api');
assert('localize es gui api guide', localizeCanon('/guides/cipi-gui-and-api', 'es') === '/guides/panel-ui-y-api');
assert('localize pt gui api guide', localizeCanon('/guides/cipi-gui-and-api', 'pt') === '/guides/painel-ui-e-api');
assert('localize it cipi yml guide', localizeCanon('/guides/manage-apps-with-cipi-yml', 'it') === '/guide/gestire-app-con-cipi-yml');
assert('localize de cipi yml guide', localizeCanon('/guides/manage-apps-with-cipi-yml', 'de') === '/guides/apps-mit-cipi-yml-verwalten');
assert('localize fr cipi yml guide', localizeCanon('/guides/manage-apps-with-cipi-yml', 'fr') === '/guides/gerer-apps-avec-cipi-yml');
assert('localize es cipi yml guide', localizeCanon('/guides/manage-apps-with-cipi-yml', 'es') === '/guides/gestionar-apps-con-cipi-yml');
assert('localize pt cipi yml guide', localizeCanon('/guides/manage-apps-with-cipi-yml', 'pt') === '/guides/gerenciar-apps-com-cipi-yml');

// In-tree English slugs 301 to localized guide slugs
assertRedirect('/de/guides/deploy-laravel-ubuntu-vps', '/de/guides/laravel-auf-ubuntu-vps-deployen');
assertRedirect('/fr/guides/backup-vps-s3', '/fr/guides/sauvegarde-vps-vers-s3');
assertRedirect('/de/guides/deploy-wordpress-custom-app', '/de/guides/wordpress-als-custom-app-deployen');
assertRedirect('/fr/guides/deploy-wordpress-custom-app', '/fr/guides/deployer-wordpress-app-personnalisee');
assertRedirect('/es/guides/deploy-wordpress-custom-app', '/es/guides/desplegar-wordpress-app-personalizada');
assertRedirect('/pt/guides/deploy-wordpress-custom-app', '/pt/guides/deploy-wordpress-app-personalizado');
assertRedirect('/de/guides/cipi-gui-and-api', '/de/guides/gui-panel-und-api');
assertRedirect('/fr/guides/cipi-gui-and-api', '/fr/guides/panneau-ui-et-api');
assertRedirect('/es/guides/cipi-gui-and-api', '/es/guides/panel-ui-y-api');
assertRedirect('/pt/guides/cipi-gui-and-api', '/pt/guides/painel-ui-e-api');
assertRedirect('/de/guides/manage-apps-with-cipi-yml', '/de/guides/apps-mit-cipi-yml-verwalten');
assertRedirect('/fr/guides/manage-apps-with-cipi-yml', '/fr/guides/gerer-apps-avec-cipi-yml');
assertRedirect('/es/guides/manage-apps-with-cipi-yml', '/es/guides/gestionar-apps-con-cipi-yml');
assertRedirect('/pt/guides/manage-apps-with-cipi-yml', '/pt/guides/gerenciar-apps-com-cipi-yml');
assertRedirect('/es/guides/laravel-security-checklist', '/es/guides/checklist-seguridad-laravel');
assertRedirect('/pt/guides/laravel-ecosystem-2026', '/pt/guides/ecossistema-laravel-2026');
assertRedirect('/de/guides/cipi-agent-laravel-mcp', '/de/guides/cipi-agent-in-laravel-nutzen');
assertRedirect('/fr/guides/cipi-agent-laravel-mcp', '/fr/guides/utiliser-cipi-agent-laravel');
assertRedirect('/es/guides/cipi-agent-laravel-mcp', '/es/guides/usar-cipi-agent-en-laravel');
assertRedirect('/pt/guides/cipi-agent-laravel-mcp', '/pt/guides/usar-cipi-agent-no-laravel');
assertPass('/de/guides/laravel-auf-ubuntu-vps-deployen');
assertPass('/fr/guides/sauvegarde-vps-vers-s3');
assertPass('/de/guides/wordpress-als-custom-app-deployen');
assertPass('/fr/guides/deployer-wordpress-app-personnalisee');
assertPass('/es/guides/desplegar-wordpress-app-personalizada');
assertPass('/pt/guides/deploy-wordpress-app-personalizado');
assertPass('/de/guides/gui-panel-und-api');
assertPass('/fr/guides/panneau-ui-et-api');
assertPass('/es/guides/panel-ui-y-api');
assertPass('/pt/guides/painel-ui-e-api');
assertPass('/it/guide/pannello-ui-e-api-cipi');
assertPass('/en/guides/cipi-gui-and-api');
assertPass('/de/guides/apps-mit-cipi-yml-verwalten');
assertPass('/fr/guides/gerer-apps-avec-cipi-yml');
assertPass('/es/guides/gestionar-apps-con-cipi-yml');
assertPass('/pt/guides/gerenciar-apps-com-cipi-yml');
assertPass('/it/guide/gestire-app-con-cipi-yml');
assertPass('/en/guides/manage-apps-with-cipi-yml');
assertPass('/es/guides/checklist-seguridad-laravel');
assertPass('/pt/guides/ecossistema-laravel-2026');
assertPass('/de/guides/cipi-agent-in-laravel-nutzen');
assertPass('/fr/guides/utiliser-cipi-agent-laravel');
assertPass('/es/guides/usar-cipi-agent-en-laravel');
assertPass('/pt/guides/usar-cipi-agent-no-laravel');
assertPass('/it/guide/usare-cipi-agent-in-laravel');
assertPass('/en/guides/cipi-agent-laravel-mcp');

// Bare localized guide slugs go to the owning language
assertRedirect('/guides/laravel-auf-ubuntu-vps-deployen', '/de/guides/laravel-auf-ubuntu-vps-deployen');
assertRedirect('/guides/sauvegarde-vps-vers-s3', '/fr/guides/sauvegarde-vps-vers-s3');
assertRedirect('/guides/copias-seguridad-vps-s3', '/es/guides/copias-seguridad-vps-s3');
assertRedirect('/guides/backup-vps-para-s3', '/pt/guides/backup-vps-para-s3');
assertRedirect('/guides/wordpress-als-custom-app-deployen', '/de/guides/wordpress-als-custom-app-deployen');
assertRedirect('/guides/deployer-wordpress-app-personnalisee', '/fr/guides/deployer-wordpress-app-personnalisee');
assertRedirect('/guides/desplegar-wordpress-app-personalizada', '/es/guides/desplegar-wordpress-app-personalizada');
assertRedirect('/guides/deploy-wordpress-app-personalizado', '/pt/guides/deploy-wordpress-app-personalizado');
assertRedirect('/guides/cipi-agent-in-laravel-nutzen', '/de/guides/cipi-agent-in-laravel-nutzen');
assertRedirect('/guides/utiliser-cipi-agent-laravel', '/fr/guides/utiliser-cipi-agent-laravel');
assertRedirect('/guides/usar-cipi-agent-en-laravel', '/es/guides/usar-cipi-agent-en-laravel');
assertRedirect('/guides/usar-cipi-agent-no-laravel', '/pt/guides/usar-cipi-agent-no-laravel');
assertRedirect('/guides/gui-panel-und-api', '/de/guides/gui-panel-und-api');
assertRedirect('/guides/panneau-ui-et-api', '/fr/guides/panneau-ui-et-api');
assertRedirect('/guides/panel-ui-y-api', '/es/guides/panel-ui-y-api');
assertRedirect('/guides/painel-ui-e-api', '/pt/guides/painel-ui-e-api');
assertRedirect('/guides/apps-mit-cipi-yml-verwalten', '/de/guides/apps-mit-cipi-yml-verwalten');
assertRedirect('/guides/gerer-apps-avec-cipi-yml', '/fr/guides/gerer-apps-avec-cipi-yml');
assertRedirect('/guides/gestionar-apps-con-cipi-yml', '/es/guides/gestionar-apps-con-cipi-yml');
assertRedirect('/guides/gerenciar-apps-com-cipi-yml', '/pt/guides/gerenciar-apps-com-cipi-yml');
assert('languageForBarePath DE guide slug', languageForBarePath('/guides/laravel-auf-ubuntu-vps-deployen') === 'de');

// Generated pages must not leak machine-translation placeholders
const BROKEN_PLACEHOLDER = /__\w+_\d+__/g;
const GENERATED_LANGS = ['de', 'fr', 'es', 'pt'];

function walk(dir, files = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, files);
    else if (/\.(html|js)$/.test(name)) files.push(path);
  }
  return files;
}

for (const lang of GENERATED_LANGS) {
  const langDir = join(process.cwd(), lang);
  for (const file of walk(langDir)) {
    const matches = readFileSync(file, 'utf8').match(BROKEN_PLACEHOLDER);
    assert(`no broken placeholders in ${file.replace(process.cwd(), '')}`, !matches);
  }
}

// Docs search must load the index for the current page language
for (const lang of ['en', 'it', ...GENERATED_LANGS]) {
  const indexPath = join(process.cwd(), lang, 'docs', 'search-index.js');
  assert(`${lang} docs search-index exists`, readFileSync(indexPath, 'utf8').includes('window.CIPI_DOCS'));
  const docsDir = join(process.cwd(), lang, 'docs');
  for (const file of walk(docsDir).filter((f) => f.endsWith('.html'))) {
    const html = readFileSync(file, 'utf8');
    if (!html.includes('sidebar-search')) continue;
    assert(
      `${file.replace(process.cwd(), '')} uses lang-aware search index`,
      html.includes("(document.documentElement.lang || 'en') + '/docs/search-index.js'"),
    );
  }
}

const ROOT = process.cwd();
const ALL_LANGS = ['en', 'de', 'fr', 'it', 'es', 'pt'];

// Every real Italian page must 200 — never 301 away to the English slug
for (const file of walk(join(ROOT, 'it')).filter((f) => f.endsWith('.html'))) {
  const rel = file.slice(join(ROOT, 'it').length).replace(/\\/g, '/');
  if (rel === '/404.html') continue;
  let path;
  if (rel === '/index.html') path = '/it/';
  else if (rel.endsWith('/index.html')) path = `/it${rel.slice(0, -'index.html'.length)}`;
  else path = `/it${rel.slice(0, -'.html'.length)}`;
  assertPass(path, 'IT page must not redirect away');
}

function htmlPathFor(lang, loc) {
  if (loc === '/') return lang === 'en' ? join(ROOT, 'index.html') : join(ROOT, lang, 'index.html');
  if (loc.endsWith('/')) return join(ROOT, lang, loc.replace(/^\//, ''), 'index.html');
  return join(ROOT, lang, `${loc.replace(/^\//, '')}.html`);
}

function resolvePretty(pathname) {
  let p = pathname.split('#')[0].split('?')[0];
  if (!p || p === '/') return join(ROOT, 'index.html');
  if (p.endsWith('/')) {
    const indexed = join(ROOT, p.slice(1), 'index.html');
    if (existsSync(indexed)) return indexed;
  }
  const exact = join(ROOT, p.replace(/^\//, ''));
  if (existsSync(exact) && statSync(exact).isFile()) return exact;
  const html = exact.endsWith('.html') ? exact : `${exact}.html`;
  if (existsSync(html)) return html;
  const indexed = join(exact, 'index.html');
  if (existsSync(indexed)) return indexed;
  return null;
}

function follow(path) {
  let current = path;
  for (let i = 0; i < 8; i += 1) {
    const d = decide(url(current));
    if (d.pass) return current;
    current = d.redirect;
  }
  return current;
}

// Every English alternative page must 301 the English slug under /it/ to the Italian file
for (const name of readdirSync(join(ROOT, 'en')).filter((f) => f.startsWith('alternative-to-') && f.endsWith('.html'))) {
  const slug = `/${name.slice(0, -5)}`;
  const itSlug = localizeCanon(slug, 'it');
  assertRedirect(`/it${slug}`, `/it${itSlug}`);
  assert(`IT HTML exists for ${slug}`, existsSync(htmlPathFor('it', itSlug)));
}

// Every localized HTML counterpart exists for every English page
for (const file of walk(join(ROOT, 'en')).filter((f) => f.endsWith('.html'))) {
  const rel = file.slice(join(ROOT, 'en').length).replace(/\\/g, '/');
  if (rel === '/404.html') continue;
  let canon;
  if (rel === '/index.html') canon = '/';
  else if (rel.endsWith('/index.html')) canon = rel.slice(0, -'index.html'.length);
  else canon = rel.slice(0, -'.html'.length);
  for (const lang of ALL_LANGS) {
    const loc = localizeCanon(canon, lang);
    const dest = htmlPathFor(lang, loc);
    assert(`${lang} page exists for ${canon} → ${loc}`, existsSync(dest));
  }
}

function extractInternalPaths(html) {
  const paths = new Set();
  const attrRe = /\b(?:href|src|action)=["']([^"']+)["']/gi;
  let m;
  while ((m = attrRe.exec(html))) paths.add(m[1]);
  const absRe = /https:\/\/cipi\.sh(\/[^"'<\s]*)/gi;
  while ((m = absRe.exec(html))) paths.add(m[1]);
  return [...paths];
}

function shouldSkipHref(href) {
  if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return true;
  if (href.startsWith('javascript:') || href.startsWith('data:')) return true;
  if (/^https?:\/\//i.test(href) && !href.startsWith('https://cipi.sh')) return true;
  if (href.startsWith('//')) return true;
  return false;
}

function toPath(href) {
  if (href.startsWith('https://cipi.sh')) {
    try {
      return new URL(href).pathname;
    } catch {
      return null;
    }
  }
  if (href.startsWith('/')) return href.split('#')[0].split('?')[0] || '/';
  return null;
}

const broken = [];
for (const lang of ALL_LANGS) {
  for (const file of walk(join(ROOT, lang)).filter((f) => f.endsWith('.html'))) {
    const html = readFileSync(file, 'utf8');
    for (const href of extractInternalPaths(html)) {
      if (shouldSkipHref(href)) continue;
      const path = toPath(href);
      if (path == null) continue;
      if (path.includes('/this-page-does-not-exist')) continue;
      const finalPath = follow(path);
      const dest = resolvePretty(finalPath);
      if (!dest) {
        broken.push(`${file.replace(ROOT, '')}: ${href} → ${finalPath}`);
      }
    }
  }
}

const sitemap = readFileSync(join(ROOT, 'sitemap.xml'), 'utf8');
for (const m of sitemap.matchAll(/https:\/\/cipi\.sh(\/[^<"]*)/g)) {
  const finalPath = follow(m[1]);
  if (!resolvePretty(finalPath)) broken.push(`sitemap.xml: ${m[1]} → ${finalPath}`);
}

assert(`no broken internal links (${broken.length})`, broken.length === 0);
if (broken.length) {
  for (const row of broken.slice(0, 40)) console.error('BROKEN', row);
  if (broken.length > 40) console.error(`… ${broken.length - 40} more`);
}

console.log(`${passed} passed, ${failed} failed`);
if (failed) process.exit(1);
