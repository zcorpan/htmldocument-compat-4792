# Code review of scripts that read a changed value (candidate 2)

`trace.js` recorded, in visits A and A2, every script read of the document's interface whose value
differs under candidate 2 (tag, `constructor`, `HTMLDocument.name`, prototype of `document` or of
`HTMLDocument.prototype`, `instanceof HTMLDocument`/`XMLDocument`). `trace_summary.py` grouped them by
API, values and calling script (327 groups over the random, targeted and subframe runs;
`out-*/trace-groups.csv`). `build_dossiers.py` fetched the calling scripts live and cut out the code
around the stack frames; one representative per script family and API (155) was code-reviewed by
`httparchive:page-reviewer` agents and spot-checked by hand. Verdicts are the outcome under
candidate 2 compared with today.

User-facing (confirmed live, see README):

- insuit accessibility widget (`insuit.net/i4tservice/insuit-app.js`): maps
  `Object.prototype.toString` tags to wrapper types and lists only `[object HTMLDocument]` for
  documents; startup then throws and the accessibility button never appears.
- Aniview/avplayer video player (`player.avplayer.com/script/8.3/.../avcplayer.js`): a schema check
  of the document compares its tag name with "HTMLDocument"; the player's setup promise rejects and
  the floating video player isn't created.

Invisible (only data never shown to users changes):

- Cloudflare challenge platform and Turnstile, a Southwest anti-bot VM, Group-IB fraud detection:
  the document's prototype or stringified globals feed bot-detection signals.
- Yandex video-ads loader: checks whether `hidden` is an own property of the document's direct
  prototype (true only under candidate 2), so it starts reporting visibility statistics.
- zone.js (Angular): `constructor.name` goes into task source labels
  ("Document.addEventListener:..." instead of "HTMLDocument.addEventListener:...").
- An `addEventListener` wrapper in a script named `event-observer-collector.js` (no URL; seen on
  Shopify pages) stringifies the event target for its own logging.
- FullStory: hooks `adoptedStyleSheets` on `Object.getPrototypeOf(document)`, which becomes
  `Document.prototype` (so the hook also covers other documents). Not tested; I think only session
  recording is affected.

Same outcome (the changed value doesn't change what the script does): jQuery/Sizzle `type`,
`isPlainObject` and sort comparators; Swiper/ssr-window `extend` (`constructor === Object`);
Bootstrap 3 tooltip (`instanceof document.constructor`); New Relic, GeoEdge and Quantum Metric
prototype walks to a member's owner; WP Meteor (its `constructor.name` keys are built the same way
when stored and replayed); Yandex Metrica (`constructor.prototype` method lookup); react-tooltip
4.2.16 and later (has a "Document" case); PayPal SDK, Popper, Dynatrace, Cookiebot, Forter,
hCaptcha, MooTools/Slick `isXML`, Prototype.js, lodash, Jssor, QuoJS, es5-shim, Svelte, Snipcart,
AdRiver, LadiPage.

Per random-sample page (most significant verdict): of 165 pages with a changed read, 0
user-facing, 32 invisible, the rest same outcome or invisible.
