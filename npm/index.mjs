import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const s = require('./index.js');

export const { all, categories, byCategory, get, search, random, stats, LANGS } = s;
export default s;
