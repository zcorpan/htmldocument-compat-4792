# Document interfaces: spec, Firefox Nightly 162, Chrome Canary 159

From `tests/probe.html`, loaded from `./wpt serve` on 2026-11-07. Interface = the document's
prototype (toString tag and `constructor.name` match it in both browsers).

| Document | Spec | Firefox Nightly | Chrome Canary |
|---|---|---|---|
| navigated text/html | Document | HTMLDocument | HTMLDocument |
| navigated application/xhtml+xml | Document | HTMLDocument | XMLDocument |
| navigated text/xml, application/xml | Document | XMLDocument | XMLDocument |
| navigated image/svg+xml | Document | XMLDocument | XMLDocument |
| DOMParser text/html | Document | HTMLDocument | HTMLDocument |
| DOMParser XML types (incl. XHTML, SVG) | Document | XMLDocument | XMLDocument |
| XHR `responseXML`, HTML | Document (as far as I can tell; XHR says "a document") | HTMLDocument | HTMLDocument |
| XHR `responseXML`, XML types (incl. XHTML) | Document (same) | XMLDocument | XMLDocument |
| `createDocument()` | XMLDocument | XMLDocument | XMLDocument |
| `createHTMLDocument()`, `Document.parseHTMLUnsafe()` | Document | HTMLDocument | HTMLDocument |
| `new Document()` | Document | Document | Document |

In both browsers `HTMLDocument !== Document`, `HTMLDocument.name` is "HTMLDocument", and
`HTMLDocument.prototype` and `XMLDocument.prototype` have only `constructor` and
`Symbol.toStringTag` as own properties. Per spec (HTML `#htmldocument`), `window.HTMLDocument` is
the `Document` interface object, so its name is "Document", every document is
`instanceof HTMLDocument`, and an HTML document's tag is `[object Document]`.

`instanceof` across realms (parent page checking an iframe's document against its own constructors)
is false in both browsers and under all three candidates; the toString tag works across realms.

## Named access on navigated XHTML documents

From `tests/named.xhtml` and `tests/named.html` (`tests/named_probe.py`, results in
`tests/named-probe-*.json`), 2026-11-09, Chrome Canary 159 and Firefox Nightly 162 (with
`dom.document.name_getter_prevent_shadowing.enabled` off, as in release, unless noted).

| Access, in an `application/xhtml+xml` document | Spec | Firefox Nightly | Chrome Canary |
|---|---|---|---|
| `document.foo` for `<form name=foo>`, `<img name>`, `<embed name>`, `<object name>` or `<object id>`, `<img id name>`, `<iframe name>` | element (iframe: its window) | same as spec | undefined |
| `document.title` with `<form name=title>` (named element shadows a `Document` member) | the form | the form (Nightly default: the string) | the string |
| `window.foo` and bare `foo` for an element with `id=foo` (any namespace), or `<form name>`, `<img name>`, `<embed name>`, `<object name>` | element | same as spec | undefined, and bare `foo` throws a `ReferenceError` |
| `window.foo` for `<iframe name=foo>` | the iframe's window | undefined (the child browsing context's name stays empty, [bug 2091332](https://bugzilla.mozilla.org/show_bug.cgi?id=2091332)) | the iframe's window |

In text/html documents both browsers follow the spec for all of these, except that Firefox
Nightly's default doesn't let named elements shadow `Document` members. Chrome's and WebKit's
document and window named items only exist for documents of their `HTMLDocument` class
(Blink [`window_properties.cc`](https://chromium.googlesource.com/chromium/src/+/6ca4e60b94475fa916dfb688608e6cc72693a1bf/third_party/blink/renderer/core/frame/window_properties.cc#72),
WebKit [`JSDOMWindowProperties.cpp`](https://github.com/WebKit/WebKit/blob/15cb3560da6c863025957fce3ee065cf61902e75/Source/WebCore/bindings/js/JSDOMWindowProperties.cpp#L66)),
which navigated XHTML documents aren't; Gecko allows any HTML or XHTML document
([`WindowNamedPropertiesHandler.cpp`](https://github.com/mozilla-firefox/firefox/blob/b16e2e7707150c623c413326c14c5111f930e920/dom/base/WindowNamedPropertiesHandler.cpp#L138)).

## Firefox Nightly, Chrome Canary and Safari TP

From `tests/iface/probe.html` (`tests/iface_probe.py`, results in `tests/iface-probe-results.json`),
2026-11-09: Chrome Canary 159, Firefox Nightly 162, Safari TP 255. Safari TP matches Chrome Canary
on every row: document interfaces (navigated, DOMParser, XHR, `createDocument()`,
`createHTMLDocument()`, `new Document()`, `parseHTMLUnsafe()`) and named access. Where they differ:

| | Chrome Canary | Firefox Nightly | Safari TP |
|---|---|---|---|
| navigated XHTML document's interface | `XMLDocument` | `HTMLDocument` | `XMLDocument` |
| `document.foo`, `window.foo`, bare `foo` for named elements and ids in a navigated XHTML document | undefined | element | undefined |
| `window.foo` for `<iframe name=foo>` in a navigated XHTML, XML or SVG document | its window | undefined | its window |
| `document.foo` for a named element in an HTML document without a browsing context (DOMParser text/html, XHR text/html, `createHTMLDocument()`, `parseHTMLUnsafe()`) | undefined | element | element |

None of the three gives `document.foo`, `window.foo` or bare `foo` for named elements or ids in
navigated XML or SVG documents (iframes by name aside), or `document.foo` in XHTML documents
from DOMParser or XHR. The spec gives both to every `Document`.
