#!/usr/bin/env bash
# Re-apply every reviewed translation fix, in the order they were written.
#
# The order matters: terminology sweeps normalise vocabulary first, then the
# per-page sets rewrite whole sentences on top of the normalised text. Running
# this on a page restored from git reproduces the reviewed translation exactly.
set -u
cd "$(dirname "$0")/.."

sweep()  { python3 scripts/i18n-term-sweep.py  "scripts/i18n-fixes/$1.json" 2>&1 | grep -E '^===' ; }
segs()   { python3 scripts/i18n-apply-fixes.py "scripts/i18n-fixes/$1.json" 2>&1 | grep -E 'pairs matched' ; }

segs  de-01-home
sweep de-02-terms
sweep fr-01-terms
segs  fr-02-home
sweep es-01-terms
sweep es-02-repair
segs  es-03-home
sweep pt-01-terms
sweep pt-02-repair
sweep pt-03-repair
segs  pt-04-home
segs  it-01-home
segs  all-01-brands
sweep all-02-brands
segs  de-03-compare
sweep all-03-brands
sweep fr-03-terms2
segs  fr-04-compare
segs  es-04-compare
segs  pt-05-compare
segs  it-02-compare
segs  it-03-keywords
segs  all-05-untranslated
segs  es-05-untranslated
segs  all-06-whatsnew
segs  all-07-fragments
sweep all-08-cleanup
sweep all-09-patterns
sweep all-04-commands
sweep all-12-commands2
sweep all-13-identifiers
segs  all-10-jsonld
sweep all-11-jsonld2
segs  all-14-guides-brand
segs  all-15-fragments

segs  de-04-reverb

sweep  all-17-cleanup2

sweep  all-16-codelabels

segs  all-18-leftovers

echo "--- code-block language labels ---"
python3 scripts/i18n-sync-code-labels.py 2>&1 | head -1

echo "--- JSON-LD from the visible translations ---"
python3 scripts/i18n-translate-jsonld.py --lang de --lang fr --lang es --lang pt 2>&1 | tail -4
