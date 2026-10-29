#!/usr/bin/env node
'use strict';
const s = require('./index.js');

const argv = process.argv.slice(2);
const flags = new Set();
const words = [];
let limit = 10;
let category = null;

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '-n' || a === '--limit') {
    const v = parseInt(argv[++i], 10);
    if (!Number.isFinite(v) || v < 1) {
      console.error('--limit needs a positive number');
      process.exit(2);
    }
    limit = v;
  } else if (a === '-c' || a === '--category') {
    category = argv[++i];
    if (!category) { console.error('--category needs a name'); process.exit(2); }
  } else if (a.startsWith('-')) {
    flags.add(a);
  } else {
    words.push(a);
  }
}

if (flags.has('-h') || flags.has('--help')) {
  console.log(`copy-paste-symbols — ${s.stats.symbols.toLocaleString('en-US')} symbols in ${s.stats.categories} categories

  npx copy-paste-symbols heart            search by Unicode / emoji name
  npx copy-paste-symbols -c arrows        every symbol in one category
  npx copy-paste-symbols -c Corazones     category labels work in en/es/pt/de/ja/zh
  npx copy-paste-symbols U+2665           look up a code point
  npx copy-paste-symbols --categories     list categories
  npx copy-paste-symbols --json star      machine-readable output

Data CC BY 4.0 · https://fontvibe.ai/tools/heart-symbol`);
  process.exit(0);
}

if (flags.has('--stats')) {
  console.log(JSON.stringify(s.stats, null, 2));
  process.exit(0);
}

if (flags.has('--categories')) {
  for (const c of s.categories()) console.log(String(c.count).padStart(5) + '  ' + c.key.padEnd(14) + c.fontvibe_page);
  process.exit(0);
}

const q = words.join(' ');
let results;
if (/^U\+[0-9A-Fa-f]{4,6}$/i.test(q)) {
  const r = s.get(q);
  results = r ? [r] : [];
} else if (q) {
  results = s.search(q, { limit, category: category || undefined });
} else if (category) {
  results = s.byCategory(category, { limit });
} else {
  results = [s.random()];
}

if (flags.has('--json')) {
  console.log(JSON.stringify(results, null, 2));
  process.exit(0);
}

if (!results.length) {
  console.error('no match for "' + (q || category) + '"');
  process.exit(1);
}
for (const r of results) {
  const label = r.emoji_name || (r.length === 1 ? r.unicode_names[0] : r.codepoints.join(' '));
  console.log(r.text + '  ' + label);
}
