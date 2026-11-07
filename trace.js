// Preload trace (runs in every frame before page scripts). Records script observations of the
// document interface and, for each, the value under today's Chrome (A), candidate 1 (XHTML
// documents are HTMLDocument) and candidate 2 (navigated documents are plain Document,
// HTMLDocument === Document, no HTMLDocument interface at all). Results in window.__hdTrace.
(() => {
  if (window.__hdTrace) return;
  const W = window, O = Object, R = Reflect;
  const HD = W.HTMLDocument, XD = W.XMLDocument, D = W.Document;
  const HP = HD.prototype, XP = XD.prototype, DP = D.prototype;
  const getProto = O.getPrototypeOf, defProp = O.defineProperty, getOwn = O.getOwnPropertyDescriptor;
  const isProtoOf = O.prototype.isPrototypeOf, fnHasInstance = Function.prototype[Symbol.hasInstance];
  const ctGet = getOwn(DP, 'contentType').get, dvGet = getOwn(DP, 'defaultView').get;
  const baseline = { HP: R.ownKeys(HP).map(String), XP: R.ownKeys(XP).map(String) };
  const events = new Map();
  let busy = false;
  const trace = { events: [], protoAdds: null, docType: null, url: location.origin };
  W.__hdTrace = trace;
  defProp(trace, 'protos', { value: { HP, XP, DP }, enumerable: false });
  try { trace.docType = ctGet.call(document); } catch (e) {}

  // Kind of document for a value: 'html'/'xhtml'/'xml' plus whether it's navigated (has a window).
  function docInfo(v) {
    if (v === null || typeof v !== 'object') return null;
    let ct;
    try { ct = ctGet.call(v); } catch (e) { return null; }
    let win = null;
    try { win = dvGet.call(v); } catch (e) {}
    const nav = win != null;
    let protos = { HP, XP, DP };
    if (!isProtoOf.call(DP, v)) { // another realm (e.g. an iframe's document): use that realm's
      try { protos = (win && win.__hdTrace && win.__hdTrace.protos) || null; } catch (e) { protos = null; }
    }
    let iface = '?';
    if (protos) {
      const p = getProto(v);
      iface = p === protos.HP ? 'HTMLDocument' : p === protos.XP ? 'XMLDocument' : p === protos.DP ? 'Document' : '?';
    }
    const kind = ct === 'text/html' ? 'html' : ct === 'application/xhtml+xml' ? 'xhtml' : 'xml';
    return { kind, nav, iface };
  }
  // Interface each candidate gives a document.
  function ifaceUnder(info, variant) {
    if (variant === 'A') return info.iface;
    if (variant === 'B1') return info.nav && info.kind === 'xhtml' ? 'HTMLDocument' : info.iface;
    // B2: no HTMLDocument interface; navigated docs are Document; XMLDocument stays for
    // non-navigated XML documents (DOMParser/XHR/createDocument, as browsers do today).
    if (info.iface === 'HTMLDocument') return 'Document';
    if (info.nav) return 'Document';
    return info.iface;
  }
  function frames() {
    const st = (new Error().stack || '').split('\n').slice(1).filter(s => !s.includes('hdtrace.js')).slice(0, 4).map(s => s.trim().replace(/^at /, ''));
    return st.map(s => s.replace(/([a-z][a-z0-9+.-]*:\/\/[^\s?#)]+)[?#][^\s):]*/gi, '$1'));
  }
  function rec(api, values) {
    if (busy) return;
    busy = true;
    try {
      const st = frames();
      const changed = (values && values.A !== undefined) ? { B1: values.B1 !== values.A, B2: values.B2 !== values.A } : { B1: false, B2: false };
      const key = api + '|' + JSON.stringify(values) + '|' + st.join('|');
      const e = events.get(key);
      if (e) { e.n++; return; }
      if (events.size >= 400) return;
      const ev = { api, values, changed, stack: st, n: 1 };
      events.set(key, ev);
      trace.events.push(ev);
    } finally { busy = false; }
  }

  // 1. Reads of the HTMLDocument / XMLDocument globals.
  for (const [name, val] of [['HTMLDocument', HD], ['XMLDocument', XD]]) {
    let cur = val;
    defProp(W, name, { configurable: true, enumerable: false,
      get() { rec('global.' + name); return cur; },
      set(v) { cur = v; } });
  }

  // 2. instanceof HTMLDocument / XMLDocument.
  for (const [name, C] of [['HTMLDocument', HD], ['XMLDocument', XD]]) {
    defProp(C, Symbol.hasInstance, { configurable: true, value: function (v) {
      const r = fnHasInstance.call(this, v);
      if (!busy) {
        const info = docInfo(v);
        if (info) {
          const under = variant => {
            const i = ifaceUnder(info, variant);
            if (variant === 'B2' && name === 'HTMLDocument') return true; // alias of Document
            return i === name;
          };
          // Cross-realm values are never instances; candidates don't change that.
          const same = isProtoOf.call(DP, v);
          rec('instanceof ' + name, { doc: info.kind + (info.nav ? ':nav' : ':parsed'), A: r,
            B1: same ? under('B1') : r, B2: same ? under('B2') : r });
        } else {
          rec('instanceof ' + name, { doc: 'non-document', A: r, B1: r, B2: r });
        }
      }
      return r;
    } });
  }

  // 3. Symbol.toStringTag on the three prototypes (Object.prototype.toString, String(document)).
  for (const [name, P] of [['HTMLDocument', HP], ['XMLDocument', XP], ['Document', DP]]) {
    const d = getOwn(P, Symbol.toStringTag);
    if (!d) continue;
    const val = d.value;
    defProp(P, Symbol.toStringTag, { configurable: true, enumerable: false, get() {
      if (this !== P && !busy) {
        const info = docInfo(this);
        if (info) rec('toStringTag', { doc: info.kind + (info.nav ? ':nav' : ':parsed'), A: info.iface,
          B1: ifaceUnder(info, 'B1'), B2: ifaceUnder(info, 'B2') });
      }
      return val;
    } });
  }

  // 4. constructor on the HTMLDocument / XMLDocument prototypes (document.constructor).
  for (const [name, P] of [['HTMLDocument', HP], ['XMLDocument', XP]]) {
    const d = getOwn(P, 'constructor');
    let val = d.value;
    defProp(P, 'constructor', { configurable: true, enumerable: false, get() {
      if (!busy) {
        const info = this === P ? null : docInfo(this);
        if (info) rec('constructor', { doc: info.kind + (info.nav ? ':nav' : ':parsed'), A: info.iface,
          B1: ifaceUnder(info, 'B1'), B2: ifaceUnder(info, 'B2') });
        else rec(name + '.prototype.constructor');
      }
      return val;
    }, set(v) { defProp(this, 'constructor', { value: v, writable: true, configurable: true, enumerable: true }); } });
  }

  // 5. HTMLDocument.name / XMLDocument.name (e.g. via document.constructor.name).
  for (const [name, C] of [['HTMLDocument', HD], ['XMLDocument', XD]]) {
    defProp(C, 'name', { configurable: true, get() {
      rec(name + '.name', { A: name, B1: name, B2: name === 'HTMLDocument' ? 'Document' : name });
      return name;
    } });
  }

  // 6. Object.getPrototypeOf / Reflect.getPrototypeOf / __proto__ on documents and on
  // HTMLDocument.prototype (candidate 2 removes HTMLDocument.prototype from the chain).
  const protoName = p => p === HP ? 'HTMLDocument.prototype' : p === XP ? 'XMLDocument.prototype' : p === DP ? 'Document.prototype' : p === Node.prototype ? 'Node.prototype' : 'other';
  function onGetProto(v, how) {
    if (busy) return;
    if (v === HP) { rec(how + '(HTMLDocument.prototype)', { A: 'Document.prototype', B1: 'Document.prototype', B2: 'Node.prototype' }); return; }
    if (v === XP) { rec(how + '(XMLDocument.prototype)'); return; }
    const info = docInfo(v);
    if (info) rec(how + '(document)', { doc: info.kind + (info.nav ? ':nav' : ':parsed'), A: info.iface + '.prototype',
      B1: ifaceUnder(info, 'B1') + '.prototype', B2: ifaceUnder(info, 'B2') + '.prototype' });
  }
  O.getPrototypeOf = new Proxy(getProto, { apply(t, th, args) { onGetProto(args[0], 'Object.getPrototypeOf'); return R.apply(t, th, args); } });
  R.getPrototypeOf = new Proxy(R.getPrototypeOf, { apply(t, th, args) { onGetProto(args[0], 'Reflect.getPrototypeOf'); return R.apply(t, th, args); } });
  const protoDesc = getOwn(O.prototype, '__proto__');
  defProp(O.prototype, '__proto__', { configurable: true, enumerable: false,
    get: new Proxy(protoDesc.get, { apply(t, th, args) { onGetProto(th, '__proto__'); return R.apply(t, th, args); } }),
    set: protoDesc.set });

  // 7. Own properties pages add to HTMLDocument.prototype / XMLDocument.prototype (under
  // candidate 2 they land on Document.prototype), and whether Document.prototype has the same name.
  trace.collectProtoAdds = () => {
    const adds = [];
    for (const [name, P, base] of [['HTMLDocument', HP, baseline.HP], ['XMLDocument', XP, baseline.XP]]) {
      for (const k of R.ownKeys(P).map(String)) {
        if (base.includes(k)) continue;
        adds.push({ proto: name, key: k, onDocumentPrototype: O.prototype.hasOwnProperty.call(DP, k) });
      }
    }
    trace.protoAdds = adds;
    return trace;
  };
})();
//# sourceURL=hdtrace.js
