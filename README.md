# Compat impact of the document interfaces in whatwg/html#4792

Candidates:

1. Chrome/Safari make navigated `application/xhtml+xml` documents `HTMLDocument` (as Firefox does).
2. As the spec reads: every navigated document is a plain `Document`, and `window.HTMLDocument` is
   the `Document` interface object. So text/html documents (navigated, DOMParser, XHR,
   `createHTMLDocument()`) stringify as `[object Document]`, `document.constructor.name` and
   `HTMLDocument.name` are `"Document"`, navigated XML/SVG documents stop being `XMLDocument`, and
   every document (including `XMLDocument`s from DOMParser/XHR/`createDocument()`) is
   `instanceof HTMLDocument`.

Named properties (`document.foo`) are out of scope.

## Scope

As agreed at kickoff (2026-11-07):

- HTTP Archive crawl 2026-10-01, both clients; Common Crawl CC-MAIN-2026-39 (12 local WARCs, seed
  11397) for inline markup. Budget 2 TiB of queries for the whole run.
- Browsers: Chrome Canary (crawl-like mobile emulation) for the live runs; Firefox Nightly as a
  cross-check on XHTML pages (it already does candidate 1). Safari TP skipped (matches Canary).
- Setups: A and A2 unmodified, with a preload trace in all frames that records each script
  observation of the document interface together with the value it would get under each candidate;
  B1 emulates candidate 1, B2 candidate 2 (see `change.py`).
- Samples: root pages whose main document is XML-typed (cap 300); pages with XML-typed subframe
  documents; 500 random root pages; 10k-sample pages hitting risky code patterns. Run to the end
  even if early review shows breakage.
