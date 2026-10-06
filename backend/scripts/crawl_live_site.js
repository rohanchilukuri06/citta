// Extract structured page data from the live cittaai.com bundle.
// The site is a React SPA: all page text lives in data arrays inside one JS bundle. Each array literal
// that holds objects with text fields is evaluated in an isolated vm context where every unknown
// identifier (icons, images, components) resolves to null — so data is read without running site code.
const fs = require("fs"), vm = require("vm");
const [,, bundlePath, outPath] = process.argv;
const src = fs.readFileSync(bundlePath, "utf8");

function matchBracket(s, start) {
  let depth = 0, inStr = null, esc = false;
  for (let i = start; i < s.length; i++) {
    const c = s[i];
    if (inStr) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === inStr) inStr = null; continue; }
    if (c === '"' || c === "'" || c === "`") { inStr = c; continue; }
    if (c === "[" || c === "{") depth++;
    else if (c === "]" || c === "}") { depth--; if (depth === 0) return i; }
  }
  return -1;
}
const sandbox = new Proxy({}, { has: () => true, get: (_, k) => (k === Symbol.unscopables ? undefined : null) });
const ctx = vm.createContext({ sandbox });
const found = [], seen = new Set();
const re = /\[\{(?:id|title|question|label|name|t):/g;
let m;
while ((m = re.exec(src))) {
  const start = m.index, end = matchBracket(src, start);
  if (end < 0 || end - start > 400000) continue;
  const lit = src.slice(start, end + 1);
  if (seen.has(lit)) continue; seen.add(lit);
  try {
    const val = vm.runInContext(`with (sandbox) { (${lit}) }`, ctx, { timeout: 200 });
    const text = JSON.stringify(val);
    if (Array.isArray(val) && text.length > 300 && /[a-z]{4,} [a-z]{4,} [a-z]{4,}/i.test(text)) found.push({ offset: start, items: val });
  } catch (e) { /* not a pure data literal */ }
}
// drop arrays fully contained in a larger extracted array
const keep = found.filter(a => !found.some(b => b !== a && b.offset < a.offset && JSON.stringify(b.items).includes(JSON.stringify(a.items))));
fs.writeFileSync(outPath, JSON.stringify(keep, null, 1));
console.log(`extracted ${keep.length} data arrays (${found.length} before de-duplication)`);
for (const a of keep) console.log(" -", a.items.length, "items |", Object.keys(a.items[0] || {}).slice(0, 8).join(","), "|", JSON.stringify(a.items[0]).slice(0, 110));
