export type Lang = 'en' | 'es' | 'pt' | 'de' | 'ja' | 'zh';

export interface SymbolRecord {
  /** Stable identifier, e.g. "sym_00002". */
  id: string;
  /** The symbol, byte-exact. May be several code points (combos, emoji sequences). */
  text: string;
  /** English category keys; a symbol can sit in more than one. */
  categories: string[];
  /** Number of Unicode code points in `text`. */
  length: number;
  /** One entry per code point, e.g. ["U+2665"]. All arrays below are aligned with it. */
  codepoints: string[];
  /** Official Unicode character names (Unicode 16.0.0); null only for code points that have none. */
  unicode_names: Array<string | null>;
  /** Unicode General_Category, e.g. "So". */
  general_categories: string[];
  /** Unicode block names. */
  blocks: string[];
  /** Unicode version each code point was added in, e.g. "1.1". */
  ages: string[];
  /** Highest of `ages`: the Unicode version a font/OS needs to know every character. */
  unicode_version: string;
  /** Unicode Emoji property, per code point. */
  emoji: boolean[];
  /** Unicode Emoji_Presentation property, per code point. */
  emoji_presentation: boolean[];
  /** Status of the whole `text` in emoji-test.txt (Emoji 16.0), or null if it is not listed. */
  emoji_status: 'fully-qualified' | 'minimally-qualified' | 'unqualified' | 'component' | null;
  /** CLDR short name from emoji-test.txt, e.g. "red heart"; null if not listed. */
  emoji_name: string | null;
  /** Windows Alt code as published on fontvibe.ai, e.g. "Alt+0176"; null for most. */
  alt_code: string | null;
}

export interface Category {
  key: string;
  slug: string;
  labels: Record<Lang, string>;
  count: number;
  /** The fontvibe.ai page where these symbols can be browsed and copied. */
  fontvibe_page: string;
  /** True if the category has a page of its own; false = shown in the fancy-text tool's Symbols tab. */
  dedicated_page: boolean;
}

export interface Stats {
  symbols: number;
  category_memberships: number;
  categories: number;
  categories_with_dedicated_page: number;
  single_code_point: number;
  multi_code_point: number;
  distinct_code_points: number;
  in_multiple_categories: number;
  rgi_emoji_fully_qualified: number;
  with_alt_code: number;
  locales: Lang[];
  unicode_version: string;
  emoji_version: string;
  per_category: Record<string, number>;
  excluded: Array<{ text: string; category: string; codepoints: string[]; reason: string }>;
  snapshot_date: string;
}

export interface SearchOptions { category?: string; limit?: number }

export function all(): SymbolRecord[];
export function categories(): Category[];
export function byCategory(name: string, opts?: { limit?: number }): SymbolRecord[];
export function get(textOrCodepoint: string): SymbolRecord | null;
export function search(query: string, opts?: SearchOptions): SymbolRecord[];
export function random(opts?: { category?: string }): SymbolRecord | null;
export const stats: Stats;
export const LANGS: Lang[];
