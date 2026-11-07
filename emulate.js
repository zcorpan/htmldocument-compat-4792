// Emulates a candidate in Chrome, in every frame before page scripts run. __VARIANT__ is replaced
// by change.py: 'B1' (navigated XHTML documents are HTMLDocument, like Firefox) or 'B2' (spec:
// no HTMLDocument interface; window.HTMLDocument is Document; navigated documents and HTML
// documents from DOMParser/XHR/createHTMLDocument/parseHTMLUnsafe are plain Document; XMLDocument
// stays for non-navigated XML documents, as browsers do today).
(() => {
  const VARIANT = '__VARIANT__';
  const W = window, O = Object;
  const HP = W.HTMLDocument.prototype, DP = W.Document.prototype;
  const setProto = O.setPrototypeOf, getProto = O.getPrototypeOf, getOwn = O.getOwnPropertyDescriptor, defProp = O.defineProperty;
  if (VARIANT === 'B1') {
    if (document.contentType === 'application/xhtml+xml') setProto(document, HP);
    return;
  }
  if (VARIANT !== 'B2') return;
  const fix = d => { try { if (d && getProto(d) === HP) setProto(d, DP); } catch (e) {} return d; };
  try { if (getProto(document) !== DP) setProto(document, DP); } catch (e) {}
  defProp(W, 'HTMLDocument', { value: W.Document, writable: true, configurable: true, enumerable: false });
  const wrapMethod = (P, name) => {
    const d = getOwn(P, name);
    if (!d || typeof d.value !== 'function') return;
    const orig = d.value;
    defProp(P, name, { ...d, value: { [name](...args) { return fix(orig.apply(this, args)); } }[name] });
  };
  const wrapGetter = (P, name) => {
    const d = getOwn(P, name);
    if (!d || !d.get) return;
    const orig = d.get;
    defProp(P, name, { ...d, get: { [name]() { const v = orig.call(this); return v && typeof v === 'object' && getProto(v) === HP ? fix(v) : v; } }[name] });
  };
  wrapMethod(W.DOMParser.prototype, 'parseFromString');
  wrapMethod(W.DOMImplementation.prototype, 'createHTMLDocument');
  if (W.Document.parseHTMLUnsafe) {
    const orig = W.Document.parseHTMLUnsafe;
    defProp(W.Document, 'parseHTMLUnsafe', { value: function parseHTMLUnsafe(...a) { return fix(orig.apply(this, a)); }, writable: true, configurable: true });
  }
  wrapGetter(W.XMLHttpRequest.prototype, 'responseXML');
  wrapGetter(W.XMLHttpRequest.prototype, 'response');
  // Child documents the init script hasn't reached yet (initial about:blank, document.open()).
  const fixChild = w => {
    try {
      if (!w || w === W) return;
      const cd = w.document;
      if (cd && w.Document && getProto(cd) !== w.Document.prototype && getProto(getProto(cd)) === w.Document.prototype) {
        setProto(cd, w.Document.prototype);
        defProp(w, 'HTMLDocument', { value: w.Document, writable: true, configurable: true, enumerable: false });
      }
    } catch (e) {}
  };
  for (const C of [W.HTMLIFrameElement, W.HTMLFrameElement, W.HTMLObjectElement, W.HTMLEmbedElement]) {
    if (!C) continue;
    for (const name of ['contentDocument', 'contentWindow']) {
      const d = getOwn(C.prototype, name);
      if (!d || !d.get) continue;
      const orig = d.get;
      defProp(C.prototype, name, { ...d, get: { [name]() {
        const v = orig.call(this);
        if (v) fixChild(name === 'contentWindow' ? v : v.defaultView);
        return v;
      } }[name] });
    }
  }
})();
//# sourceURL=hdemulate.js
