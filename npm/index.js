'use strict';
/*!
 * copy-paste-symbols — FontVibe's copy-and-paste symbol library with Unicode facts.
 * Data CC BY 4.0 (attribution required), code MIT.
 * Browse and copy: https://fontvibe.ai/tools/heart-symbol
 */
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, 'data');
const LANGS = ['en', 'es', 'pt', 'de', 'ja', 'zh'];

let _all = null;
let _cats = null;

function load(name) {
  const p = path.join(DIR, name);
  if (!fs.existsSync(p)) {
    throw new Error(
      'copy-paste-symbols: data file is missing (' + p + '). ' +
      'The package was probably packed without its prepack step; ' +
      'please open an issue at https://github.com/Funovate-Technology/fontvibe-symbols/issues'
    );
  }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

/** Every symbol record, parsed once and cached. */
function all() {
  if (!_all) _all = load('symbols.json');
  return _all;
}

/** Every category with its labels in six languages, count and fontvibe.ai page. */
function categories() {
  if (!_cats) _cats = load('categories.json');
  return _cats;
}

function norm(s) {
  return String(s == null ? '' : s).trim().toLowerCase();
}

/* A negative limit means "no limit"; it must never fall through to slice(0, -n). */
function take(arr, limit) {
  if (limit == null || limit < 0) return arr;
  return arr.slice(0, limit);
}

/** Resolve a category by key ("Hearts"), slug ("heart-combos") or a label in any language ("Corazones"). */
function findCategory(name) {
  const q = norm(name);
  if (!q) return null;
  for (const c of categories()) {
    if (norm(c.key) === q || c.slug === q) return c;
    for (const l of LANGS) if (norm(c.labels[l]) === q) return c;
  }
  return null;
}

/** Symbols in one category, in the order fontvibe.ai shows them. */
function byCategory(name, opts) {
  const c = findCategory(name);
  if (!c) return [];
  const o = opts || {};
  return take(all().filter((r) => r.categories.includes(c.key)), o.limit);
}

/** Look up one symbol by its exact text, or by a code point like "U+2665" (single-code-point symbols only). */
function get(textOrCodepoint) {
  const s = String(textOrCodepoint == null ? '' : textOrCodepoint);
  const m = /^U\+([0-9A-Fa-f]{4,6})$/i.exec(s.trim());
  if (m) {
    const cp = 'U+' + m[1].toUpperCase().padStart(4, '0');
    return all().find((r) => r.length === 1 && r.codepoints[0] === cp) || null;
  }
  return all().find((r) => r.text === s) || null;
}

/**
 * Search by Unicode name, CLDR emoji name, or category (key or label in any of six languages).
 * Exact category or name matches rank above word matches, which rank above substring matches;
 * within a rank, single characters come before multi-character combos.
 * @param {string} query
 * @param {{category?: string, limit?: number}} [opts]
 */
function search(query, opts) {
  const o = opts || {};
  const q = norm(query);
  if (!q) return [];
  const cat = o.category ? findCategory(o.category) : null;
  if (o.category && !cat) return [];
  const catHits = new Set();
  const catPrefix = new Set();
  for (const c of categories()) {
    const labels = [norm(c.key), c.slug].concat(LANGS.map((l) => norm(c.labels[l])));
    if (labels.includes(q)) catHits.add(c.key);
    else if (q.length >= 3 && labels.some((x) => x.startsWith(q))) catPrefix.add(c.key); // "star" → Stars
  }
  const hits = [];
  for (const r of all()) {
    if (cat && !r.categories.includes(cat.key)) continue;
    let score = 0;
    if (r.text === query) score = 4;
    if (r.categories.some((k) => catHits.has(k))) score = Math.max(score, 3);
    if (r.categories.some((k) => catPrefix.has(k))) score = Math.max(score, 2);
    const names = r.unicode_names.filter(Boolean).map(norm);
    if (r.emoji_name) names.push(norm(r.emoji_name));
    for (const n of names) {
      if (n === q) score = Math.max(score, 3);
      else if (n.split(/[\s-]+/).includes(q)) score = Math.max(score, 2);
      else if (n.includes(q)) score = Math.max(score, 1);
    }
    if (!score) {
      for (const k of r.categories) {
        const c = categories().find((x) => x.key === k);
        if (LANGS.some((l) => norm(c.labels[l]).includes(q))) { score = 1; break; }
      }
    }
    if (score) hits.push({ score, r });
  }
  // Ties: single characters before combos, then site order (Array#sort is stable).
  hits.sort((a, b) => b.score - a.score || a.r.length - b.r.length);
  return take(hits.map((h) => h.r), o.limit == null ? 50 : o.limit);
}

/** One random symbol, optionally from one category; null when nothing matches. */
function random(opts) {
  const o = opts || {};
  const pool = o.category ? byCategory(o.category) : all();
  if (!pool.length) return null;
  return pool[Math.floor(Math.random() * pool.length)];
}

const stats = require('./stats.json');

module.exports = { all, categories, byCategory, get, search, random, stats, LANGS };
