#!/usr/bin/env node
// Copies the dataset from the repo root into the package before packing.
// data/ at the repo root is the single source of truth; it is never committed twice.
// stats.json is copied too — a hand-copied stats file goes stale the first time the data is rebuilt.
'use strict';
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..', 'data');
const pkg = path.join(__dirname, '..');
const dstDir = path.join(pkg, 'data');

for (const f of ['symbols.json', 'categories.json', 'stats.json']) {
  if (!fs.existsSync(path.join(root, f))) {
    console.error('[sync-data] missing ' + path.join(root, f) + ' — run this from inside the repo');
    process.exit(1);
  }
}
fs.mkdirSync(dstDir, { recursive: true });
// Re-serialised without indentation: same content, smaller install.
for (const f of ['symbols.json', 'categories.json']) {
  const obj = JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
  fs.writeFileSync(path.join(dstDir, f), JSON.stringify(obj));
}
fs.copyFileSync(path.join(root, 'stats.json'), path.join(pkg, 'stats.json'));

const n = JSON.parse(fs.readFileSync(path.join(dstDir, 'symbols.json'), 'utf8')).length;
const expected = JSON.parse(fs.readFileSync(path.join(pkg, 'stats.json'), 'utf8')).symbols;
if (n !== expected) {
  console.error('[sync-data] copied ' + n + ' symbols but stats.json says ' + expected + ' — refusing to pack');
  process.exit(1);
}
console.log('[sync-data] ok — ' + n + ' symbols + categories.json + stats.json');
