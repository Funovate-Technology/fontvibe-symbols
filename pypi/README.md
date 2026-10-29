# copy-paste-symbols

**1,275 copy-and-paste symbols in 23 categories** — hearts, heart combos, stars, arrows,
brackets, math, currency and more — with category names in **six languages** (en · es · pt ·
de · ja · zh) and Unicode 16.0.0 facts for every code point. No dependencies.

Browse and copy them at **[fontvibe.ai/tools/heart-symbol](https://fontvibe.ai/tools/heart-symbol)**.

```bash
pip install copy-paste-symbols
```

```python
import copy_paste_symbols as cps

cps.categories()                  # [{key, slug, labels: {en, es, pt, de, ja, zh}, count, fontvibe_page}, ...]
cps.by_category("Arrows")         # in the order fontvibe.ai shows them
cps.by_category("矢印")            # labels work in all six languages
cps.search("star", limit=5)       # Unicode name, CLDR emoji name, or category
cps.get("U+2665")                 # {'text': '♥', 'unicode_names': ['BLACK HEART SUIT'], ...}
cps.random(category="Stars")
cps.stats                         # counts
```

```bash
copy-paste-symbols heart            # search
copy-paste-symbols -c Corazones     # one category, any language
copy-paste-symbols --categories
```

Every record: `text` (byte-exact), `categories`, `codepoints`, `unicode_names`, `blocks`,
`ages`, `unicode_version`, `emoji` / `emoji_presentation`, `emoji_status`, `emoji_name`,
`alt_code`. Full field list: [SCHEMA.md](https://github.com/Funovate-Technology/fontvibe-symbols/blob/main/SCHEMA.md).

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
