function describe(v) {
  if (v === undefined) return 'undefined';
  if (v === null) return 'null';
  if (v === window) return 'window(self)';
  if (typeof v === 'object' && v.window === v) return 'window';
  if (v instanceof Element) return v.localName + (v.id ? '#' + v.id : '') + (v.getAttribute('name') ? '[' + v.getAttribute('name') + ']' : '');
  if (typeof v === 'object' && 'length' in v && 'item' in v) return 'collection(' + v.length + ')';
  if (typeof v === 'string') return 'string:' + v.slice(0, 30);
  return typeof v;
}
const names = ['f1', 'i1', 'i2', 'i2n', 'i3', 'fr1', 'o1', 'o2', 'e1', 'd1', 's1', 'dup', 'title', 'cookie', 'svgr', 'x1'];
function probe() {
const out = {contentType: document.contentType, tag: Object.prototype.toString.call(document), inline: window.__inline, names: {}};
for (const n of names) {
  let bare;
  try { bare = describe((0, eval)(n)); } catch (e) { bare = e.name; }
  out.names[n] = {doc: describe(document[n]), docIn: n in document, win: describe(window[n]), winIn: n in window, bare};
}
return out;
}
window.__probe = probe();
window.addEventListener('load', () => { window.__probeLoad = probe(); });
