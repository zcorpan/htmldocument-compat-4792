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
is false in both browsers and under both candidates; the toString tag works across realms.
