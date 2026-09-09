#!/usr/bin/env node
/**
 * Unit tests for netlify/edge-functions/i18n.js routing (no Netlify runtime).
 * Public URLs are unprefixed English. /en/… and former language trees 301 to root.
 */
import { decide, langHref, toEnglishCanon, normalizeBarePath } from '../netlify/edge-functions/i18n.js';

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
  if (!(d.redirect === dest && d.status === 301 && !d.pass)) {
    console.error('  got', d);
  }
}

assertPass('/', 'English homepage must be 200');
assertRedirect('/index.html', '/');
assertRedirect('/en', '/');
assertRedirect('/en/', '/');
assertRedirect('/en/index.html', '/');

assertPass('/docs/');
assertPass('/docs/getting-started');
assertPass('/alternatives');
assertPass('/whats-new');
assertPass('/guides/');
assertPass('/guides/cipi-gui-and-api');
assertPass('/guides/manage-apps-with-cipi-yml');
assertPass('/guides/cipi-agent-laravel-mcp');
assertPass('/alternative-to-ploi');
assertPass('/cipi-yml');
assertPass('/discovery');

assertRedirect('/en/docs/', '/docs/');
assertRedirect('/en/docs/getting-started', '/docs/getting-started');
assertRedirect('/en/alternatives', '/alternatives');
assertRedirect('/en/whats-new', '/whats-new');
assertRedirect('/en/guides/cipi-gui-and-api', '/guides/cipi-gui-and-api');
assertRedirect('/en/docs', '/docs/');
assertRedirect('/en/novita', '/whats-new');
assertRedirect('/en/docs/primi-passi', '/docs/getting-started');
assertRedirect('/en/alternativa-a-sevalla', '/alternative-to-sevalla');
assertRedirect('/en/guide/backup-vps-s3-con-cipi', '/guides/backup-vps-s3');
assertRedirect('/en/this-page-does-not-exist', '/this-page-does-not-exist');

assertRedirect('/docs', '/docs/');
assertRedirect('/docs.html', '/docs/');
assertRedirect('/docs/getting-started.html', '/docs/getting-started');
assertRedirect('/whats-new.html', '/whats-new');
assertRedirect('/guides', '/guides/');

assertRedirect('/it', '/');
assertRedirect('/it/', '/');
assertRedirect('/it/index.html', '/');
assertRedirect('/de', '/');
assertRedirect('/de/', '/');
assertRedirect('/fr/', '/');
assertRedirect('/es/', '/');
assertRedirect('/pt/', '/');

assertRedirect('/it/docs/', '/docs/');
assertRedirect('/it/docs/primi-passi', '/docs/getting-started');
assertRedirect('/it/novita', '/whats-new');
assertRedirect('/it/whats-new', '/whats-new');
assertRedirect('/it/alternative', '/alternatives');
assertRedirect('/it/alternatives', '/alternatives');
assertRedirect('/it/alternativa-a-sevalla', '/alternative-to-sevalla');
assertRedirect('/it/alternative-to-sevalla', '/alternative-to-sevalla');
assertRedirect('/it/migliori-alternative-a-laravel-forge', '/best-laravel-forge-alternatives');
assertRedirect('/de/docs/getting-started', '/docs/getting-started');
assertRedirect('/fr/alternatives', '/alternatives');
assertRedirect('/de/guides/deploy-laravel-ubuntu-vps', '/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/de/guides/laravel-auf-ubuntu-vps-deployen', '/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/fr/guides/sauvegarde-vps-vers-s3', '/guides/backup-vps-s3');
assertRedirect('/it/guide/usare-cipi-agent-in-laravel', '/guides/cipi-agent-laravel-mcp');
assertRedirect('/it/guide/pannello-ui-e-api-cipi', '/guides/cipi-gui-and-api');
assertRedirect('/it/guide/gestire-app-con-cipi-yml', '/guides/manage-apps-with-cipi-yml');

assertRedirect('/novita', '/whats-new');
assertRedirect('/alternative', '/alternatives');
assertRedirect('/alternativa-a-ploi', '/alternative-to-ploi');
assertRedirect('/guide/', '/guides/');
assertRedirect('/guide/deploy-laravel-su-ubuntu-vps', '/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/docs/primi-passi', '/docs/getting-started');
assertRedirect('/guides/laravel-auf-ubuntu-vps-deployen', '/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/guides/sauvegarde-vps-vers-s3', '/guides/backup-vps-s3');
assertRedirect('/guides/usar-cipi-agent-en-laravel', '/guides/cipi-agent-laravel-mcp');

assertPass('/this-page-does-not-exist');
assertPass('/random-old-url');

assertPass('/robots.txt');
assertPass('/sitemap.xml');
assertPass('/llms.txt');
assertPass('/css/site.css');
assertPass('/setup.sh');
assertPass('/og.png');
assertPass('/.well-known/security.txt');

{
  const d = decide(url('/', { proto: 'http:' }));
  assert('http → https 301', d.status === 301 && d.absolute === 'https://cipi.sh/');
}
{
  const d = decide(url('/it/', { host: 'www.cipi.sh' }));
  assert('www + /it/ → https://cipi.sh/', d.status === 301 && d.absolute === 'https://cipi.sh/');
}
{
  const d = decide(url('/en/docs/primi-passi', { host: 'www.cipi.sh' }));
  assert(
    'www + /en/docs/primi-passi → https://cipi.sh/docs/getting-started',
    d.status === 301 && d.absolute === 'https://cipi.sh/docs/getting-started',
  );
}
{
  const d = decide(url('/', { host: 'deploy-preview-1.netlify.app' }), { isPreview: true });
  assert('preview host not rewritten', d.pass === true);
}

assert('langHref home is /', langHref('en', '/') === '/');
assert('langHref it home is also /', langHref('it', '/') === '/');
assert('langHref docs is /docs/', langHref('en', '/docs/') === '/docs/');
assert('toEnglishCanon /novita', toEnglishCanon('/novita') === '/whats-new');
assert('normalize /docs/ → /docs/', normalizeBarePath('/docs/') === '/docs/');

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
