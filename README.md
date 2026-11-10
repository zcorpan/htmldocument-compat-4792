# Compat impact of the document interfaces in whatwg/html#4792

Three candidates for the interfaces (named access such as `document.foo` is in
[section 3](#3-named-access-on-xhtml-documentfoo-windowfoo)):

1. Chrome and Safari make navigated `application/xhtml+xml` documents `HTMLDocument`, as Firefox
   does. Today they are `XMLDocument`.
2. As the spec reads: every navigated document is a plain `Document`, and `window.HTMLDocument` is
   the `Document` interface object. Text/html documents (navigated, DOMParser, XHR,
   `createHTMLDocument()`) then stringify as `[object Document]`, `document.constructor.name` and
   `HTMLDocument.name` are "Document", navigated XML and SVG documents stop being `XMLDocument`, and
   every document, including `XMLDocument`s from DOMParser, XHR or `createDocument()`, is
   `instanceof HTMLDocument`.
3. Firefox makes navigated XHTML documents `XMLDocument`, as Chrome and Safari do (the reverse of
   1).

Current behavior per document type, in the spec, Firefox Nightly 162 and Chrome Canary 159:
[browsers.md](browsers.md). The two browsers differ only for navigated XHTML documents: in the
interface, and in named access (`document.foo`, `window.foo`), which Firefox has there and Chrome
doesn't.

## Summary

Candidates 1 and 3 each make the browsers match on XHTML; neither breaks pages as far as I can
tell. Candidate 3 needs changes to Firefox's own features.

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
proposes. Keeping `HTMLDocument` for text/html avoids all three breakages. Candidate 1 alone is enough to
make Chrome and Safari match Firefox.

Candidate 3 also looks web-compatible. It is the same diff as the B1 run, reversed: Chrome and Safari
already give XHTML pages `XMLDocument`, none of the 248 assessable XML-typed pages in that run (150
sampled were XHTML) differed visibly between the two, and the only reads that change (8 pages, jQuery `type()` and Prototype.js
`Object.isString`) return the same result for either tag. The 10k sample has no XHTML subframes.
What would break is Firefox's own: Reader View is offered only when `HTMLDocument.isInstance(doc)`
([Readerable.js](https://github.com/mozilla-firefox/firefox/blob/b16e2e7707150c623c413326c14c5111f930e920/toolkit/components/reader/Readerable.js#L31),
[AboutReaderChild.sys.mjs](https://github.com/mozilla-firefox/firefox/blob/b16e2e7707150c623c413326c14c5111f930e920/browser/actors/AboutReaderChild.sys.mjs#L168)), and thumbnails skip
`XMLDocument`s ([PageThumbUtils.sys.mjs](https://github.com/mozilla-firefox/firefox/blob/b16e2e7707150c623c413326c14c5111f930e920/toolkit/components/thumbnails/PageThumbUtils.sys.mjs#L351)),
so XHTML pages would lose both unless those checks change. XHTML documents would also lose
`HTMLDocument`'s named getter (out of scope here; Chrome and Safari lack it on XHTML too). Page
code that only runs in Firefox, and Firefox extensions, weren't traced.

Named access on XHTML (section 3) looks safe to change in either direction. Firefox gives navigated
XHTML documents `document.foo` and `window.foo` for named elements and ids, as the spec does;
Chrome and Safari give neither. Traced on the 683 XHTML URLs in the crawl (618 still served as
XHTML in Firefox Nightly, 880 visits in Chrome Canary), scripts read such a name on 3 pages, and
none of the reads changes what the script does.

Dropping `document.foo` from HTML documents without a browsing context (DOMParser, XHR,
`createHTMLDocument()`, `parseHTMLUnsafe()`), as Chrome already lacks it there, looks compatible
for Firefox (section 5). With a new use counter in a local Firefox build, no page in 2,000 random
desktop root pages read a named element from such a document (95% upper bound 0.15%), while 260 of
them parse HTML with DOMParser.

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
AudioEye matters for every candidate: it takes its XML-safe path only for `XMLDocument`s, so on a
navigated XHTML document it switches to `innerHTML` under candidates 1 and 2, and to the XML-safe
path in Firefox under candidate 3.

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
code-reviewed: [code-review.md](code-review.md). The B1 groups are also candidate 3's changed reads
(Firefox today matches B1 on XHTML, candidate 3 matches A). The avplayer schema error also appeared on 3
targeted pages, where the player sat behind a consent dialog.

## 3. Named access on XHTML (`document.foo`, `window.foo`)

In navigated XHTML documents Firefox has `document.foo` for named elements (`form`, `img`,
`embed`, `object` and `iframe` with `name`, `object` with `id`, `img` with `id` and `name`) and
`window.foo` or bare `foo` for named elements and any element with an `id`, as in text/html and
as the spec says for every `Document`. Chrome and Safari tie both to their `HTMLDocument` class,
so XHTML documents get `undefined` (and a `ReferenceError` for bare `foo`); only iframes by name
work there. Details and source links: [browsers.md](browsers.md#named-access-on-navigated-xhtml-documents).
A side finding: in Firefox an XHTML iframe's `name` isn't on its browsing context at first
(`frames[0].name` stays `""` for an `about:blank` iframe), so `window.<iframe name>` gives the
iframe element or `undefined` instead of its window.

Two directions: Chrome and Safari add named access to XHTML (the spec), or Firefox drops it.

- No local data covers this: whatwg/html#10687's research (`~/git/zcorpan/document-shadowing-compat-10687`)
  has no XHTML pages (Chrome's counter there can't fire on XHTML and its Common Crawl scan was
  text/html only), and none of the 16 Common Crawl XHTML responses has inline script reading a
  named element ([cc_named.jsonl](crawl/cc_named.jsonl), `cc_named.py`). Crawl response bodies
  would cost about 106 TiB for mobile alone, so no new query was run.
- `named.js` traces reads of names that named elements provide. In Chrome ('emulate' mode) it adds
  Firefox's named access, so Chrome code paths see the elements and their reads are logged; in
  Firefox ('trace' mode) it logs window and bare reads with Firefox's own values. Both were checked
  against Firefox's native behavior on [tests/named.xhtml](tests/named.xhtml)
  (`tests/named_probe.py`, `tests/named-probe-*.json`). Firefox ran with
  `dom.document.name_getter_prevent_shadowing.enabled` off, as in release.
- Detection on every XHTML main document in the 2026-10-01 crawl
  ([xhtml-all.jsonl](crawl/samples/xhtml-all.jsonl): 1,050 rows, 683 distinct URLs, 593 rows root
  pages): Chrome Canary 1,050 visits with the crawl clients' emulation (880 still XHTML;
  [detect-chrome.jsonl](out-named/detect-chrome.jsonl)), Firefox Nightly 683 desktop visits (618
  still XHTML, 522 with at least one named element or id; [detect-firefox.jsonl](out-named/detect-firefox.jsonl)).
  Groups: [detect-groups.csv](out-named/detect-groups.csv).

| Page | Read | Chrome today | Firefox, spec | Outcome |
|---|---|---|---|---|
| mpk-krasnik.pl | gtag.js reads `window.ga` (`<span id=ga>`) | undefined | the span | same: gtag uses it only if its `.q` is an array |
| mpk-krasnik.pl | jQuery's UMD check reads `module` (`<div id=module>`, Firefox trace only) | undefined | the div | same: `module.exports` isn't an object, so jQuery takes the browser path |
| scalablebrainatlas.incf.org | the page reads `window.TEMPLATE` (`<iframe name=TEMPLATE id=TEMPLATE>`) | the iframe's window | the iframe's window (spec); early reads in Firefox: the iframe element | same per spec; in Firefox the page works once the frame has its name |
| diverzanti.cz | AdSense reads `window.google_esf` (its own iframe) | the iframe's window | as left (spec); early reads in Firefox: the iframe element | same per spec |

A/B in Chrome on these 3 pages (A, A2 plain, B with Firefox's named access;
[review](out-named-chrome/review.csv)): no visible change on any. So neither direction shows
breakage: 0 of 618 XHTML pages in Firefox and 0 of 880 visits in Chrome (95% upper bound about
0.5% of XHTML pages). Document named reads (as opposed to window and bare ones) are traced in
Chrome only: Firefox reports a current named element as an own property of `document`, so the
trace leaves those alone; 70 of the 618 pages had a document-named element.

## 4. Checks for Firefox adopting the Chrome/Safari model

- Safari TP 255 matches Chrome Canary 159 on every interface and named access probe
  ([browsers.md](browsers.md#all-three-browsers-including-safari-tp)), so Chrome and Safari share
  one model.
- No browser has named access in XML or SVG documents, though the spec gives it to every
  `Document`. The spec would need to limit `document.foo` to HTML documents (an `HTMLDocument`
  named getter) and window named access to windows whose document is an HTML document.
- Chrome alone lacks `document.foo` in HTML documents without a browsing context (DOMParser, XHR,
  `createHTMLDocument()`, `parseHTMLUnsafe()`); Firefox and Safari have it, which an `HTMLDocument`
  named getter matches. This is the Chromium bug whatwg/html#4792 links (594008). Dropping it in
  Firefox too looks compatible (section 5).
- Firefox drops an iframe's `name` from its browsing context in every XML-parsed document (XHTML,
  XML, SVG): `window.<iframe name>` is undefined there, while Chrome and Safari return its window.
  That's a Firefox bug either way.
- History: from Web Apps 1.0's first check-in (2006) every `Document` had to implement
  `HTMLDocument`, through binding-specific casting, so its members (`title`, `cookie`, the named
  getter) would work in any document, SVG and XML included. W3C bug 14037 (2011, about
  `XMLDocument` and Sarissa's `XMLDocument.prototype.load` hook) turned that into
  `HTMLDocument === Document`, with `XMLDocument` only from `createDocument()` (commit 83f13eef).
  Gecko had no plans to implement it, and WebKit preferred navigated `.svg` and `.xhtml`
  documents to be `XMLDocument`; no browser ever implemented the alias. All former `HTMLDocument`
  members except the named getter now live on `Document` in all three browsers, so the original
  motivation is met without the alias. whatwg/html#4792 (Boris Zbarsky, 2019) proposed bringing
  back `HTMLDocument` with the named getter, because named properties on XML documents (with
  `[LegacyOverrideBuiltIns]`) would be a compat risk.

## 5. Named getter on HTML documents without a browsing context

Chrome Canary 159 has no `document.foo` on HTML documents without a browsing context (DOMParser
text/html, XHR text/html, `createHTMLDocument()`, `parseHTMLUnsafe()`); Firefox Nightly 162 and
Safari TP 255 have it ([browsers.md](browsers.md#all-three-browsers-including-safari-tp)). Blink
adds a document's named items through its window
([html_document.cc](https://github.com/chromium/chromium/blob/6ca4e60b94475fa916dfb688608e6cc72693a1bf/third_party/blink/renderer/core/html/html_document.cc#L96-L105)),
so a document without one never gets any.

Firefox's `HTMLDocumentNamedGetterHit` counter can't tell whether pages rely on it: only documents
created for a window report use counters, so hits on these documents are lost. A local Firefox
build ([patch](firefox/named-getter-no-window.patch), on mozilla/firefox 47f2a88cbab9) adds:

- a use counter, `HTMLDocumentNamedGetterHitNoWindow`, set on the document of the creating global
  when the named getter finds something on a document that never had a window;
- a pref, `dom.document.named_getter_without_window.enabled` (default on), that empties the named
  getter and its supported names on those documents.

On a local page ([tests/nowindow](tests/nowindow/probe.html),
[results](tests/nowindow-probe-results.json)) which reads a named element from each of the
four kinds of document, the counter fires with the pref on or off, and with the pref off `doc.foo` is undefined, `'foo' in doc` false, and
no names are own properties.

Detection ran on 2,000 random desktop root pages from the 2026-10-01 crawl
([query](queries/random_desktop_nowindow.sql), the first 2,000 of 5,000 seeded rows). Each page
loaded in its own tab with `dom.use_counters.dump.document` on and closed 4 s after load; the
counter lines its documents printed are in [detect.jsonl](out-nowindow/detect.jsonl), with URLs
cut to origins (`idx` is the row in [the query's CSV](queries/random_desktop_nowindow.csv)).

| Counter | Pages |
|---|---|
| `htmldocument_named_getter_hit_no_window` | 0 |
| `domparser_parsefromstring` | 260 |
| `htmldocument_named_getter_hit` (the page's own document) | 3 |

So no page read a named element from a document without a window (95% upper bound 0.15% of
desktop root pages), though 13% of them create one with DOMParser, and more with
`createHTMLDocument()` (jQuery calls it at load; Gecko has no counter for it). 54 pages timed out
or failed to load; their counters up to that point are included. With no hits there was nothing to
compare with the pref off.

## Not covered

- Pages the crawl doesn't visit, logged-in state, and interaction (e.g. Adobe's checkout with
  react-tooltip).
- XSLT-transformed results and documents from `document.open()` in other realms (B2 re-protos
  frame documents when they're accessed).
- Error-stack strings: V8 names frames like `HTMLDocument.<anonymous>`, which a few error filters
  match. The emulation can't change that.
- Named access: reads before the element exists (both browsers give undefined), reads after load
  plus 3 s or on interaction, frames (top-level documents only), and Safari (its source matches
  Chrome's). The Chrome emulation changes `'foo' in node` to true for every node while an element
  with that id exists, and missed one read that Firefox's trace saw (`module` on mpk-krasnik.pl).
- Firefox wasn't run on the XHTML sample, for candidate 1 or 3: it already ships candidate 1, B1
  found nothing to confirm, and the Chrome trace stands in for candidate 3. So Firefox-only page
  code (UA- or Gecko-sniffed branches) and Firefox extensions on XHTML pages weren't observed.
- Named getter without a browsing context: reads after load plus 4 s or on interaction, logged-in
  pages, Firefox-only page code beyond what the random sample ran, mobile, and Safari TP.
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
| [random_desktop_nowindow.sql](queries/random_desktop_nowindow.sql) (2026-11-10) | 0.0006 |

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
.venv/bin/python tests/named_probe.py --ff-pref-off   # named access probe; pass a named.js copy with __MODE__ set to check the modes
CHANGE_VARIANT=N .venv/bin/python detect_chrome.py "$CHROME" crawl/samples/xhtml-all.jsonl out-named/detect-chrome.jsonl 8
.venv/bin/python detect_firefox.py crawl/samples/xhtml-all.jsonl out-named/detect-firefox.jsonl 5
.venv/bin/python named_summary.py out-named/detect-chrome.jsonl out-named/detect-firefox.jsonl > out-named/detect-groups.csv
CHANGE_VARIANT=N .venv/bin/python compare.py "$CHROME" crawl/samples/named-hits.jsonl out-named-chrome && CHANGE_VARIANT=N .venv/bin/python analyze.py out-named-chrome
# Firefox built with firefox/named-getter-no-window.patch ($FX_BUILD: its dist/Nightly.app/Contents/MacOS/firefox)
.venv/bin/python tests/nowindow_probe.py "$FX_BUILD"
head -2001 queries/random_desktop_nowindow.csv > /tmp/2000.csv && .venv/bin/python detect_nowindow.py "$FX_BUILD" /tmp/2000.csv out-nowindow/detect.jsonl 8
```

Playwright 1.64.1, Chrome Canary 159.0.8145.0. Partway through the B1 XML run, `compare.py` was
changed to relaunch a crashed browser and record that visit as an error (one page crashed it); the
random run had started with the old version and never needed it.
Screenshots (`out*/shots/`) aren't committed.
