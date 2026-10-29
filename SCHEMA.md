# Schema

## Symbol record

One record per distinct symbol. Same shape in `data/symbols.json`, in every
`data/by-category/*.json`, and in the npm / PyPI packages.

```json
{
  "id": "sym_00002",
  "text": "♥",
  "categories": ["Hearts", "Chess"],
  "length": 1,
  "codepoints": ["U+2665"],
  "unicode_names": ["BLACK HEART SUIT"],
  "general_categories": ["So"],
  "blocks": ["Miscellaneous Symbols"],
  "ages": ["1.1"],
  "unicode_version": "1.1",
  "emoji": [true],
  "emoji_presentation": [false],
  "emoji_status": "unqualified",
  "emoji_name": "heart suit",
  "alt_code": "Alt+3"
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | `sym_` + five digits. Stable across releases — use it to reference an entry. |
| `text` | string | The symbol, **byte-exact**. Never normalised (see [Identity](#identity)). May be several code points. |
| `categories` | string[] | English category keys, in site order. A symbol can be in several (`π`: Math, Greek). See `data/categories.json`. |
| `length` | int | Number of Unicode code points in `text` (not UTF-16 units, not grapheme clusters). |
| `codepoints` | string[] | `U+XXXX` per code point. **Every array below has the same length and order.** |
| `unicode_names` | (string\|null)[] | Official character name from Python `unicodedata` (Unicode 16.0.0). `null` would mean the code point has no name; none in this release do. |
| `general_categories` | string[] | Unicode General_Category (`So`, `Sm`, `Mn`, `Cf`, …), from `unicodedata`. |
| `blocks` | string[] | Unicode block, from `Blocks.txt` 16.0.0. |
| `ages` | string[] | Unicode version the code point was added in, from `DerivedAge.txt` 16.0.0. |
| `unicode_version` | string | The highest of `ages` (compared numerically). Roughly: how new a system has to be to know every character. |
| `emoji` | bool[] | Unicode `Emoji` property, from `emoji-data.txt` 16.0.0. Note `©`, `#` and the digits have it too — it means "can be an emoji", not "is drawn as one". |
| `emoji_presentation` | bool[] | Unicode `Emoji_Presentation` property: drawn as a colour emoji by default. |
| `emoji_status` | string\|null | Status of the **whole** `text` in `emoji-test.txt` (Emoji 16.0): `fully-qualified`, `minimally-qualified`, `unqualified` or `component`. `null` = not an emoji sequence listed there. |
| `emoji_name` | string\|null | CLDR English short name from `emoji-test.txt`, e.g. `red heart`. `null` when `emoji_status` is null. |
| `alt_code` | string\|null | Windows Alt code as published on the fontvibe.ai page for that category (e.g. `Alt+0176` for `°`). `null` for almost all entries — only codes the site publishes are carried. |

Not included, because they are one line each:

```python
html  = "".join(f"&#x{ord(c):X};" for c in rec["text"])     # HTML numeric references
utf16 = len(rec["text"].encode("utf-16-le")) // 2            # JavaScript .length
```

## Category record

`data/categories.json`, and the `category` block at the top of each `data/by-category/<slug>.json`.

```json
{
  "key": "Hearts",
  "slug": "hearts",
  "labels": { "en": "Hearts", "es": "Corazones", "pt": "Corações", "de": "Herzen", "ja": "ハート", "zh": "爱心" },
  "count": 142,
  "fontvibe_page": "https://fontvibe.ai/tools/heart-symbol",
  "dedicated_page": true
}
```

| Field | Type | Notes |
|---|---|---|
| `key` | string | English key, as used in `categories` on symbol records. |
| `slug` | string | Lowercase, hyphenated; also the file name under `data/by-category/`. |
| `labels` | object | Display name in `en` `es` `pt` `de` `ja` `zh` — the labels the localized fontvibe.ai pages show. |
| `count` | int | Symbols in this category. |
| `fontvibe_page` | string | Where to browse and copy this category on fontvibe.ai (English URL; insert `/es`, `/pt`, `/de`, `/ja` or `/zh` before `/tools` for the localized page). |
| `dedicated_page` | bool | `true` if the category has a page of its own. `false` = it's in the Symbols tab of the fancy text generator, which is what `fontvibe_page` then points to. |

## `data/symbols.csv`

Header row, UTF-8, RFC 4180 quoting. Columns:
`id, text, categories, codepoints, unicode_names, blocks, unicode_version, emoji_status, emoji_name, alt_code`.
Multi-valued cells are joined with `|` (codepoints with a space). Per-code-point emoji
properties and ages are only in the JSON.

## `data/stats.json`

Totals, recomputed by `scripts/verify.py`: `symbols`, `category_memberships`, `categories`,
`categories_with_dedicated_page`, `single_code_point`, `multi_code_point`,
`distinct_code_points`, `in_multiple_categories`, `rgi_emoji_fully_qualified`,
`with_alt_code`, `per_category`, plus `locales`, `unicode_version`, `emoji_version`,
`snapshot_date`, and `excluded` — entries the site served that were dropped, each with the
reason.

---

## Identity

`text` is byte-exact. In particular:

- **Variation selectors are kept.** `❤` (U+2764) and `❤️` (U+2764 U+FE0F) are different
  entries: the first is text-style on many systems, the second asks for the colour emoji.
- **No Unicode normalisation.** A couple of decorative combos with stacked combining marks
  are not in NFC; normalising them would reorder the marks and change how they render.
- **Spaces inside combos are part of the combo** (`˚₊‧꒰ა❤︎໒꒱ ‧₊`). No entry has leading or
  trailing whitespace.

Deduplication is byte-exact. A symbol shown in two categories on the site is one record
with both categories; it appears in both by-category files.

## Exclusions

An entry is dropped if any code point in it is unassigned (`Cn`) or private use (`Co`) in
Unicode 16.0.0 — those aren't standard characters, and render as a box or as whatever a
given font puts there. Dropped entries are listed in `stats.json` under `excluded`;
nothing is silently patched.
