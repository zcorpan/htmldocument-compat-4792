// Named access (document.foo, window.foo, bare foo) on navigated XHTML documents. Chrome and Safari
// have none there; Firefox and the spec do, with named elements shadowing document's prototype
// chain (Firefox release; Nightly's dom.document.name_getter_prevent_shadowing.enabled doesn't).
//   'emulate' (Chrome): give XHTML documents Firefox's named access. Window names and document names
//     not on document's prototype chain get accessors on EventTarget.prototype (below Window's
//     named properties object, so own globals and `var` still shadow them, as in Firefox); names on
//     document's prototype chain (title, cookie) get own accessors on document.
//   'trace' (Firefox): own accessors on window and document returning Firefox's own value, to log
//     which scripts read them.
// Accessors are added when a matching element appears (MutationObserver and DOMContentLoaded).
// Reads are logged with A (Chrome's value) and B (Firefox's value). window.__hdNamed.collect().
(() => {
  const MODE = '__MODE__';
  if (window.__hdNamed) return;
  const log = window.__hdNamed = {contentType: document.contentType, mode: MODE, events: [], counts: {}, dropped: 0, names: 0};
  log.collect = () => JSON.stringify({contentType: log.contentType, mode: log.mode, events: log.events, counts: log.counts, dropped: log.dropped, names: log.names, docSkipped: log.docSkipped || 0});
  if (document.contentType !== 'application/xhtml+xml') return;
  const HTML_NS = 'http://www.w3.org/1999/xhtml';
  const IDENT = /^[A-Za-z_$][\w$]*$/;
  const DOC_TAGS = new Set(['embed', 'form', 'iframe', 'img', 'object']);
  const WIN_TAGS = new Set(['embed', 'form', 'img', 'object']);
  const doc = document, win = window, hasOwn = Object.prototype.hasOwnProperty;
  const byId = n => [...doc.querySelectorAll('[id="' + CSS.escape(n) + '"]')];
  const byName = n => [...doc.getElementsByName(n)].filter(el => el.namespaceURI === HTML_NS);
  const order = (a, b) => a === b ? 0 : (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);
  const uniq = els => [...new Set(els)].sort(order);
  const docElements = n => uniq(byName(n).filter(el => DOC_TAGS.has(el.localName)).concat(byId(n).filter(el =>
    el.namespaceURI === HTML_NS && (el.localName === 'object' || (el.localName === 'img' && el.getAttribute('name'))))));
  // Child navigables by name are left to the browser (Chrome has them on XHTML too).
  const winElements = n => uniq(byName(n).filter(el => WIN_TAGS.has(el.localName)).concat(byId(n)));
  // Collections are arrays with item() (an approximation of HTMLCollection).
  const coll = els => Object.assign(els, {item: i => els[i] || null, namedItem: () => null});
  const docValue = els => els.length === 1 ? (els[0].localName === 'iframe' ? els[0].contentWindow : els[0]) : coll(els);
  const winValue = els => els.length === 1 ? els[0] : coll(els);
  function frameNamed(n) {
    for (let i = 0; i < win.length; i++) { try { if (win[i].name === n) return win[i]; } catch (e) {} }
  }
  function describe(v) {
    if (v === undefined) return 'undefined';
    if (v === null) return 'null';
    if (Array.isArray(v)) return 'collection(' + v.length + ')';
    if (typeof v === 'object' && v.window === v) return 'window';
    if (v instanceof Element) return v.localName;
    return typeof v === 'string' ? 'string' : typeof v;
  }
  const stack = () => (new Error().stack || '').split('\n').filter(l => l && !/hdnamed\.js|^Error/.test(l)).slice(0, 8).join(' | ');
  function record(target, n, op, a, b) {
    const k = target + '.' + n + ':' + op;
    log.counts[k] = (log.counts[k] || 0) + 1;
    if (log.counts[k] > 3) return;
    if (log.events.length >= 400) { log.dropped++; return; }
    log.events.push({target, name: n, op, A: describe(a), B: describe(b), stack: stack()});
  }
  function findDesc(p, n) {
    for (; p; p = Object.getPrototypeOf(p)) { const d = Object.getOwnPropertyDescriptor(p, n); if (d) return d; }
  }
  function onDocChain(n) {
    for (let p = Object.getPrototypeOf(doc); p && p !== EventTarget.prototype; p = Object.getPrototypeOf(p))
      if (hasOwn.call(p, n)) return true;
    return false;
  }
  const dataProp = (obj, n, value) => Object.defineProperty(obj, n, {value, writable: true, enumerable: true, configurable: true});
  // document: own accessor (names on the prototype chain in 'emulate'; every name in 'trace').
  const docDone = new Set();
  function docAccessor(n) {
    // Firefox reports a current named element as an own property of document and refuses to
    // define one over it ([LegacyOverrideBuiltIns], no named setter), so 'trace' can't follow
    // document reads there; 'emulate' in Chrome logs them.
    if (docDone.has(n) || (hasOwn.call(doc, n) && MODE !== 'trace')) return;
    docDone.add(n);
    if (MODE === 'trace') { log.docSkipped = (log.docSkipped || 0) + 1; return; }
    const proto = Object.getPrototypeOf(doc);
    Object.defineProperty(doc, n, {configurable: true, get() {
      const native = Reflect.get(proto, n, doc), els = docElements(n);
      if (!els.length) return native;
      record('document', n, 'get', native, docValue(els));
      return docValue(els);
    }, set(v) {
      if (docElements(n).length) record('document', n, 'set', undefined, undefined);
      const d = findDesc(proto, n);
      if (d && d.set) d.set.call(doc, v);
      else { delete doc[n]; dataProp(doc, n, v); }
    }});
  }
  // window: own accessor ('trace') or EventTarget.prototype accessor ('emulate').
  const winDone = new Set();
  function winAccessor(n) {
    if (winDone.has(n)) return;
    if (MODE === 'trace') {
      // Firefox's named properties object sits below Window.prototype, so check own members only.
      if (hasOwn.call(win, n) || hasOwn.call(Window.prototype, n)) return;
      winDone.add(n);
      Object.defineProperty(win, n, {configurable: true, get() {
        const els = winElements(n);
        if (!els.length) return Reflect.get(Object.getPrototypeOf(win), n, win);
        record('window', n, 'get', undefined, winValue(els));
        return winValue(els);
      }, set(v) { delete win[n]; dataProp(win, n, v); }});
      return;
    }
    if (hasOwn.call(EventTarget.prototype, n)) return;
    winDone.add(n);
    Object.defineProperty(EventTarget.prototype, n, {configurable: true, get() {
      // Chrome's frames-by-name lookup is non-masking, so this accessor would hide it: redo it here.
      const fallback = () => (this === win && frameNamed(n)) || Reflect.get(Object.getPrototypeOf(EventTarget.prototype), n, this);
      let els;
      // Child navigables come first (and Chrome already has them).
      if (this === win && frameNamed(n)) return frameNamed(n);
      if (this === win && (els = winElements(n)).length) {
        record('window', n, 'get', fallback(), winValue(els));
        return winValue(els);
      }
      if (this === doc && (els = docElements(n)).length) {
        record('document', n, 'get', fallback(), docValue(els));
        return docValue(els);
      }
      return fallback();
    }, set(v) { dataProp(this, n, v); }});
  }
  function add(el) {
    if (!(el instanceof Element)) return;
    const html = el.namespaceURI === HTML_NS, name = html ? el.getAttribute('name') : null, tag = el.localName;
    const names = [];
    if (el.id && IDENT.test(el.id)) names.push([el.id, 'win']);
    if (name && IDENT.test(name) && html && WIN_TAGS.has(tag)) names.push([name, 'win']);
    if (name && IDENT.test(name) && html && DOC_TAGS.has(tag)) names.push([name, 'doc']);
    if (el.id && IDENT.test(el.id) && html && (tag === 'object' || (tag === 'img' && name))) names.push([el.id, 'doc']);
    for (const [n, kind] of names) {
      log.names++;
      if (kind === 'win') winAccessor(n);
      else if (MODE === 'trace' || onDocChain(n)) docAccessor(n);
      else winAccessor(n);
    }
  }
  const sweep = root => { add(root); if (root.querySelectorAll) for (const el of root.querySelectorAll('[name],[id]')) add(el); };
  new MutationObserver(ms => {
    for (const m of ms) {
      if (m.type === 'attributes') add(m.target);
      for (const node of m.addedNodes) if (node.nodeType === 1) sweep(node);
    }
  }).observe(doc, {childList: true, subtree: true, attributes: true, attributeFilter: ['name', 'id']});
  doc.addEventListener('DOMContentLoaded', () => sweep(doc));
})();
//# sourceURL=hdnamed.js
