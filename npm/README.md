# copy-paste-symbols

**1,275 copy-and-paste symbols in 23 categories** — hearts, heart combos, stars, arrows,
brackets, math, currency and more — with category names in **six languages** (en · es · pt ·
de · ja · zh) and Unicode 16.0.0 facts for every code point. Zero dependencies.

Browse and copy them at **[fontvibe.ai/tools/heart-symbol](https://fontvibe.ai/tools/heart-symbol)**.

```bash
npm i copy-paste-symbols
```

```js
const symbols = require('copy-paste-symbols');   // or: import symbols from 'copy-paste-symbols'

symbols.categories();                 // [{ key, slug, labels: {en, es, pt, de, ja, zh}, count, fontvibe_page }, …]
symbols.byCategory('Arrows');         // in the order fontvibe.ai shows them
symbols.byCategory('矢印');            // labels work in all six languages
symbols.search('star', { limit: 5 }); // Unicode name, CLDR emoji name, or category
symbols.get('U+2665');                // { text: '♥', unicode_names: ['BLACK HEART SUIT'], blocks: […], … }
symbols.random({ category: 'Stars' });
symbols.stats;                        // counts
```

```bash
npx copy-paste-symbols heart          # search
npx copy-paste-symbols -c Corazones   # one category, any language
npx copy-paste-symbols --categories
```

Every record: `text` (byte-exact), `categories`, `codepoints`, `unicode_names`, `blocks`,
`ages`, `unicode_version`, `emoji` / `emoji_presentation`, `emoji_status`, `emoji_name`,
`alt_code`. Full field list and TypeScript types: [SCHEMA.md](https://github.com/Funovate-Technology/fontvibe-symbols/blob/main/SCHEMA.md),
`index.d.ts`.

## Attribution

Data is **CC BY 4.0**; code is MIT. If you show these symbols on a site, please credit:

```html
Symbols from <a href="https://fontvibe.ai/tools/heart-symbol">FontVibe</a> ·
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
```

`rel="nofollow"` is fine. Please link the site rather than this package — it's where the
symbols can be copied with one click. Each category also carries its own page as
`fontvibe_page` if you'd rather link that. More options in the
[repository README](https://github.com/Funovate-Technology/fontvibe-symbols#attribution).
