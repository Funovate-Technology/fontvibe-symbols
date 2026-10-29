'use strict';
// Plain-node test. No framework, no dev dependency.
const assert = require('assert');
const s = require('./index.js');

let n = 0;
const t = (name, fn) => { fn(); n++; console.log('  ok  ' + name); };

t('all() matches stats', () => {
  assert.strictEqual(s.all().length, s.stats.symbols);
});

t('ids and texts are unique', () => {
  assert.strictEqual(new Set(s.all().map((r) => r.id)).size, s.stats.symbols);
  assert.strictEqual(new Set(s.all().map((r) => r.text)).size, s.stats.symbols);
});

t('records carry the documented shape', () => {
  for (const r of s.all()) {
    assert.ok(r.text && r.categories.length);
    assert.strictEqual(r.codepoints.length, r.length);
    assert.strictEqual(r.unicode_names.length, r.length);
    assert.strictEqual(r.blocks.length, r.length);
    assert.strictEqual([...r.text].length, r.length);
  }
});

t('categories() counts match byCategory()', () => {
  const cats = s.categories();
  assert.strictEqual(cats.length, s.stats.categories);
  for (const c of cats) assert.strictEqual(s.byCategory(c.key).length, c.count, c.key);
});

t('categories resolve by key, slug and localized label', () => {
  const n = s.byCategory('Hearts').length;
  assert.ok(n > 0);
  assert.strictEqual(s.byCategory('hearts').length, n);
  for (const l of s.LANGS) {
    const label = s.categories().find((c) => c.key === 'Hearts').labels[l];
    assert.strictEqual(s.byCategory(label).length, n, l);
  }
  assert.strictEqual(s.byCategory('heart-combos').length, s.stats.per_category['Heart Combos']);
});

t('no kaomoji category leaked in', () => {
  for (const c of s.categories()) assert.ok(!/kaomoji/i.test(c.key), c.key);
});

t('get() by text and by code point', () => {
  assert.strictEqual(s.get('♥').codepoints[0], 'U+2665');
  assert.strictEqual(s.get('U+2665').text, '♥');
  assert.strictEqual(s.get('u+2665').text, '♥');
  assert.strictEqual(s.get('not a symbol'), null);
});

t('search by Unicode name', () => {
  const r = s.search('heart', { limit: 5 });
  assert.strictEqual(r.length, 5);
  for (const x of s.search('BLACK HEART SUIT')) assert.ok(x);
  assert.strictEqual(s.search('black heart suit')[0].text, '♥');
});

t('search by category label in another language', () => {
  const es = s.search('Corazones', { limit: -1 });
  assert.ok(es.length >= s.stats.per_category.Hearts);
});

t('search honours limit and category', () => {
  assert.strictEqual(s.search('arrow', { limit: 3 }).length, 3);
  assert.strictEqual(s.search('arrow').length <= 50, true);
  for (const r of s.search('arrow', { category: 'Arrows', limit: -1 })) assert.ok(r.categories.includes('Arrows'));
  assert.strictEqual(s.search('arrow', { limit: 0 }).length, 0);
  assert.deepStrictEqual(s.search('arrow', { category: 'no-such-category' }), []);
});

t('search of nonsense returns nothing', () => {
  assert.deepStrictEqual(s.search('zzzzqqqqxxxx'), []);
});

t('random respects its category', () => {
  for (let i = 0; i < 50; i++) assert.ok(s.random({ category: 'Stars' }).categories.includes('Stars'));
  assert.strictEqual(s.random({ category: 'no-such-category' }), null);
});

t('every category links to a fontvibe.ai page', () => {
  for (const c of s.categories()) assert.ok(c.fontvibe_page.startsWith('https://fontvibe.ai/tools/'), c.key);
});

console.log('\n' + n + ' passed');
