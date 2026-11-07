# Compat impact of the document interfaces in whatwg/html#4792

Two candidates (named properties such as `document.foo` are out of scope):

1. Chrome and Safari make navigated `application/xhtml+xml` documents `HTMLDocument`, as Firefox
   does. Today they are `XMLDocument`.
2. As the spec reads: every navigated document is a plain `Document`, and `window.HTMLDocument` is
   the `Document` interface object. Text/html documents (navigated, DOMParser, XHR,
   `createHTMLDocument()`) then stringify as `[object Document]`, `document.constructor.name` and
   `HTMLDocument.name` are "Document", navigated XML and SVG documents stop being `XMLDocument`, and
   every document, including `XMLDocument`s from DOMParser, XHR or `createDocument()`, is
   `instanceof HTMLDocument`.

Current behavior per document type, in the spec, Firefox Nightly 162 and Chrome Canary 159:
[browsers.md](browsers.md). The two browsers differ only for navigated XHTML documents.

## Summary

Candidate 1 looks safe. XHTML is rare: 326 mobile and 270 desktop root pages in HTTP Archive serve
it (0.002% of mobile root pages), and 16 of 256,012 HTML responses in Common Crawl. On 300 sampled
XML-typed root pages (150 XHTML), emulating candidate 1 in Chrome changed nothing visible. Only 8
pages had scripts read a value that changes, all through generic jQuery or Prototype.js type
helpers that return the same result either way.

Candidate 2 breaks a few widgets that name-check the document. Exposure is broad: 6,697 of 24,580
pages in the HTTP Archive 10k sample mention `HTMLDocument`, `XMLDocument` or an
`[object …Document]` tag in a response body. In the 500 random mobile root pages, 165 of 451
traced pages had scripts read a value that changes. Code review found none of those reads
user-facing (at least 32 pages have invisible effects such as bot-detection signals; the rest
behave the same). Nothing changed visibly: 0 worse of 435 assessable pages (95% upper bound 0.84%
of mobile root pages). Targeted loads of risky code found:

- insuit accessibility widget, on 526 mobile and 490 desktop root pages (mostly Spanish government
  sites: Seguridad Social, SEPE, Ministerio de Justicia). It maps toString tags to types and lists
  only `[object HTMLDocument]`, so startup throws and the accessibility button disappears. Worse on
  all 15 sampled pages, e.g. [SEPE](out-targeted-b2/review/100.png) (A left, B right).
- Aniview/avplayer video player, on 369 mobile and 615 desktop root pages. A schema check of the
  document fails, so the floating video player isn't created. On 2 of 5 pages tried, A has two
  `<video>` elements and B none ([player-check.txt](out-avplayer/player-check.txt)).
- react-tooltip 4.2.14 and 4.2.15 pick `head` only when the root's `constructor.name` is
  "HTMLDocument"; otherwise they `appendChild` a `<style>` to the document itself, which throws
  inside React and unmounts the app ([repro](sanity/react-tooltip.html)). 4.2.16 added a
  "Document" case. In the 10k sample only Adobe's checkout chunks carry it, and they didn't run at
  page load.

These follow from the spec text, not from an implementation bug: fixing them in the spec means
keeping a distinct `HTMLDocument` interface (tag and name) for HTML documents, as whatwg/html#4792
proposes. Keeping `HTMLDocument` for text/html avoids all three. Candidate 1 alone is enough to
make Chrome and Safari match Firefox.

## Scope

- HTTP Archive crawl 2026-10-01, both clients; Common Crawl CC-MAIN-2026-39 (12 local WARCs, seed
  11397) for inline markup. Budget 2 TiB of queries for the whole run.
- Browsers: Chrome Canary 159 (crawl-like mobile emulation, desktop for desktop pages) for live
  runs; Firefox Nightly 162 and Chrome Canary for current behavior. Safari TP skipped (matches
  Canary).
- Setups (`change.py`): A and A2 unmodified, with `trace.js` in all frames recording each script
  observation of the document interface plus the value it would get under each candidate. B1
  (`emulate.js`, candidate 1) gives navigated XHTML documents `HTMLDocument.prototype`. B2
  (candidate 2) gives navigated documents `Document.prototype`, sets `window.HTMLDocument =
  Document`, and re-prototypes HTML documents from DOMParser, XHR, `createHTMLDocument()`,
  `parseHTMLUnsafe()` and frames. The sanity check (`sanity/index.html`) confirms each.
- Samples: root pages whose main document is XML-typed (cap 300); pages with XML-typed subframe
  documents; 500 random root pages; 10k-sample pages hitting risky code patterns. Run to the end.

## 1. Crawl data

| | desktop | mobile |
|---|---|---|
| Root pages ([totals.csv](queries/totals.csv)) | 11,650,352 | 15,366,242 |
| Root pages whose main document is `application/xhtml+xml` ([xml_main_docs.csv](queries/xml_main_docs.csv)) | 270 | 326 |
| Root pages whose main document is another XML type (XML, SVG, RSS, Atom) | 660 | 755 |
| Root pages loading insuit ([libs.csv](queries/libs.csv)) | 490 | 526 |
| Root pages loading avplayer | 615 | 369 |
| Root pages loading AudioEye (takes its `instanceof XMLDocument` path on XHTML) | 37,622 | 39,694 |

None of the 1,055 XHTML-served pages (root and non-root) loads AudioEye, insuit or avplayer.
AudioEye matters for both candidates: on a navigated XHTML document it uses `innerHTML` instead of
its XML-safe path once the document stops being `XMLDocument`.

- Blink's `kXMLDocument` counter (counted for XML documents parsed with a frame view) hits 487,958
  mobile root pages ([counts](queries/xmldoc_features_counts.csv)), against 0.14–0.23% of page loads
  in the field (chromestatus). I think SVG images, which get their own frame view, inflate the
  crawl count, so it wasn't used to find pages.
- XML-typed subframe documents: 76 of 24,580 pages in the 10k sample, 62 of them SVG
  ([xml_subframe_docs_10k.csv](queries/xml_subframe_docs_10k.csv)). The full-crawl query would
  read 18.8 TiB.
- Response bodies (10k sample, [bodies_10k.sql](queries/bodies_10k.sql)): mentions classified by
  `classify_bodies.py` into [bodies_10k-mentions.jsonl](crawl/bodies_10k-mentions.jsonl). Risky
  patterns are in `cluster_patterns.py`. Most mentions are alias-safe: descriptor lookups falling
  back from `Document.prototype` to `HTMLDocument.prototype`, arrive.js adding methods,
  `instanceof HTMLDocument`, which stays true.
- Common Crawl: `cc_scan.py` output in [crawl/](crawl/cc_counts.json). Inline `HTMLDocument` is on
  2,934 of 256,012 HTML responses, mostly arrive.js.

## 2. Live comparison

`compare.py` visits A, A2 (unmodified plus trace) and B (emulation); output in
`out-<sample>-<variant>/`. `analyze.py` auto-rates pages within A-vs-A2 noise; the rest were rated
by eye with `httparchive:page-reviewer` agents, spot-checked, with rechecks for unclear ones
(`recheck.py`). Adult or flagged pages (`nsfw.csv`) were rated from metrics and errors without
committing images.

| Run | Pages | Worse | No visible change | Not assessable |
|---|---|---|---|---|
| XML-typed root pages, B1 ([review](out-xml-b1/review.csv), [summary](out-xml-b1/summary.md)) | 300 | 0 | 248 | 52 |
| XML-typed root pages, B2 ([review](out-xml-b2/review.csv), [summary](out-xml-b2/summary.md)) | 300 | 0 | 251 | 49 |
| Random mobile root pages, B2 ([review](out-random-b2/review.csv), [summary](out-random-b2/summary.md)) | 500 | 0 | 435 | 65 |
| Pages with XML subframes (10k sample), B2 ([review](out-sub-b2/review.csv)) | 76 | 0 | 65 | 11 |
| Risky-pattern pages (10k sample), B2 ([review](out-targeted-b2/review.csv)) | 155 | 15 (insuit) | 90 | 50 |

The traces (`trace_summary.py`: `trace-pages.csv`, `trace-groups.csv` per run) show B1 changes
only on XML-typed pages, and only through jQuery and Prototype.js type helpers. The B2 groups were
code-reviewed: [code-review.md](code-review.md). The avplayer schema error also appeared on 3
targeted pages, where the player sat behind a consent dialog.

## Not covered

- Pages the crawl doesn't visit, logged-in state, and interaction (e.g. Adobe's checkout with
  react-tooltip).
- XSLT-transformed results and documents from `document.open()` in other realms (B2 re-protos
  frame documents when they're accessed).
- Error-stack strings: V8 names frames like `HTMLDocument.<anonymous>`, which a few error filters
  match. The emulation can't change that.
- Firefox wasn't run on the XHTML sample: it already ships candidate 1, and B1 found nothing to
  confirm.
- Live pages change, so reruns won't match exactly. Some XHTML-stratum pages now serve text/html.

## Query bytes

All on the 2026-10-01 crawl (or the 10k sample tables), run on 2026-11-07:

| Query | Bytes processed (TiB) |
|---|---|
| [latest.sql](queries/latest.sql), [totals.sql](queries/totals.sql) | 0.0015 |
| [xmldoc_features.sql](queries/xmldoc_features.sql) | 0.192 |
| [xml_main_docs.sql](queries/xml_main_docs.sql) | 0.304 |
| [xml_subframe_docs_10k.sql](queries/xml_subframe_docs_10k.sql), [pages_10k.sql](queries/pages_10k.sql), a 10k payload field check | 0.002 |
| [bodies_10k.sql](queries/bodies_10k.sql) | 0.152 |
| [random_root.sql](queries/random_root.sql) | 0.0008 |
| [libs.sql](queries/libs.sql) | 0.329 |

## Reproduce

```sh
bq query --use_legacy_sql=false --format=csv --max_rows=10000000 < queries/xml_main_docs.sql > queries/xml_main_docs.csv  # likewise the others
python3 bq_download.py <bodies_10k result table> 9115 crawl/bodies_10k_raw 50 && python3 classify_bodies.py crawl/bodies_10k_raw crawl/bodies_10k
python3 make_samples.py
python3 -m venv .venv && .venv/bin/pip install playwright pillow nudenet pyobjc-framework-Vision warcio
CHANGE_VARIANT=B1 .venv/bin/python compare.py "$CHROME" crawl/samples/xmltyped.jsonl out-xml-b1
CHANGE_VARIANT=B2 .venv/bin/python compare.py "$CHROME" crawl/samples/random.jsonl out-random-b2   # likewise xmltyped, subframes, targeted
.venv/bin/python nsfw_check.py out-random-b2 && .venv/bin/python analyze.py out-random-b2 && .venv/bin/python trace_summary.py out-random-b2
python3 extrapolate.py out-random-b2/review.csv crawl/samples/random.jsonl > out-random-b2/summary.md
.venv/bin/python build_dossiers.py B2 out-random-b2 out-targeted-b2 out-sub-b2   # code review input
CHANGE_VARIANT=B2 .venv/bin/python trace_check.py "$CHROME" react-tooltip.html
```

Playwright 1.64.1, Chrome Canary 159.0.8145.0. Partway through the B1 XML run, `compare.py` was
changed to relaunch a crashed browser and record that visit as an error (one page crashed it); the
random run had started with the old version and never needed it.
Screenshots (`out*/shots/`) aren't committed.
