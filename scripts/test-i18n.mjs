#!/usr/bin/env node
/**
 * Unit tests for netlify/edge-functions/i18n.js routing (no Netlify runtime).
 * The public site is English-only; former language trees 301 to /en/….
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
}

assertPass('/', 'English homepage must be 200');
assertRedirect('/index.html', '/');
assertRedirect('/en', '/');
assertRedirect('/en/', '/');
assertRedirect('/en/index.html', '/');

assertPass('/en/docs/');
assertPass('/en/docs/getting-started');
assertPass('/en/alternatives');
assertPass('/en/whats-new');
assertPass('/en/guides/cipi-gui-and-api');
assertPass('/en/guides/manage-apps-with-cipi-yml');
assertPass('/en/guides/cipi-agent-laravel-mcp');

assertRedirect('/en/docs/primi-passi', '/en/docs/getting-started');
assertRedirect('/en/novita', '/en/whats-new');
assertRedirect('/en/docs', '/en/docs/');
assertRedirect('/en/alternativa-a-sevalla', '/en/alternative-to-sevalla');
assertRedirect('/en/guide/backup-vps-s3-con-cipi', '/en/guides/backup-vps-s3');
assertRedirect('/en/guide/deploy-wordpress-app-custom-github', '/en/guides/deploy-wordpress-custom-app');
assertRedirect('/en/guide/usare-cipi-agent-in-laravel', '/en/guides/cipi-agent-laravel-mcp');
assertRedirect('/en/guide/pannello-ui-e-api-cipi', '/en/guides/cipi-gui-and-api');
assertRedirect('/en/guide/gestire-app-con-cipi-yml', '/en/guides/manage-apps-with-cipi-yml');

assertRedirect('/docs', '/en/docs/');
assertRedirect('/docs/', '/en/docs/');
assertRedirect('/docs/getting-started', '/en/docs/getting-started');
assertRedirect('/guides', '/en/guides/');
assertRedirect('/alternatives', '/en/alternatives');
assertRedirect('/whats-new', '/en/whats-new');
assertRedirect('/alternative-to-ploi', '/en/alternative-to-ploi');
assertRedirect('/alternative-to-sevalla', '/en/alternative-to-sevalla');

assertRedirect('/it', '/');
assertRedirect('/it/', '/');
assertRedirect('/it/index.html', '/');
assertRedirect('/de', '/');
assertRedirect('/de/', '/');
assertRedirect('/fr/', '/');
assertRedirect('/es/', '/');
assertRedirect('/pt/', '/');

assertRedirect('/it/docs/', '/en/docs/');
assertRedirect('/it/docs/primi-passi', '/en/docs/getting-started');
assertRedirect('/it/novita', '/en/whats-new');
assertRedirect('/it/whats-new', '/en/whats-new');
assertRedirect('/it/alternative', '/en/alternatives');
assertRedirect('/it/alternatives', '/en/alternatives');
assertRedirect('/it/alternativa-a-sevalla', '/en/alternative-to-sevalla');
assertRedirect('/it/alternative-to-sevalla', '/en/alternative-to-sevalla');
assertRedirect('/it/migliori-alternative-a-laravel-forge', '/en/best-laravel-forge-alternatives');
assertRedirect('/de/docs/getting-started', '/en/docs/getting-started');
assertRedirect('/fr/alternatives', '/en/alternatives');
assertRedirect('/de/guides/deploy-laravel-ubuntu-vps', '/en/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/de/guides/laravel-auf-ubuntu-vps-deployen', '/en/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/fr/guides/sauvegarde-vps-vers-s3', '/en/guides/backup-vps-s3');
assertRedirect('/it/guide/usare-cipi-agent-in-laravel', '/en/guides/cipi-agent-laravel-mcp');
assertRedirect('/it/guide/pannello-ui-e-api-cipi', '/en/guides/cipi-gui-and-api');
assertRedirect('/it/guide/gestire-app-con-cipi-yml', '/en/guides/manage-apps-with-cipi-yml');

assertRedirect('/novita', '/en/whats-new');
assertRedirect('/alternative', '/en/alternatives');
assertRedirect('/alternativa-a-ploi', '/en/alternative-to-ploi');
assertRedirect('/guide/', '/en/guides/');
assertRedirect('/guide/deploy-laravel-su-ubuntu-vps', '/en/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/docs/primi-passi', '/en/docs/getting-started');
assertRedirect('/guides/laravel-auf-ubuntu-vps-deployen', '/en/guides/deploy-laravel-ubuntu-vps');
assertRedirect('/guides/sauvegarde-vps-vers-s3', '/en/guides/backup-vps-s3');
assertRedirect('/guides/usar-cipi-agent-en-laravel', '/en/guides/cipi-agent-laravel-mcp');

assertPass('/this-page-does-not-exist');
assertPass('/random-old-url');
assertPass('/en/this-page-does-not-exist');

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
  assert('www → apex 301', d.status === 301 && d.absolute === 'https://cipi.sh/it/');
}
{
  const d = decide(url('/', { host: 'deploy-preview-1.netlify.app' }), { isPreview: true });
  assert('preview host not rewritten', d.pass === true);
}

assert('langHref home is /', langHref('en', '/') === '/');
assert('langHref it home is also /', langHref('it', '/') === '/');
assert('langHref docs is /en/docs/', langHref('en', '/docs/') === '/en/docs/');
assert('toEnglishCanon /novita', toEnglishCanon('/novita') === '/whats-new');
assert('normalize /docs/ → /docs/', normalizeBarePath('/docs/') === '/docs/');

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
