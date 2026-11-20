`probe.html` (with `doc.py`) is a throwaway wpt test that dumps, for navigated documents of each
type (in iframes), DOMParser, XHR and DOMImplementation results: the toString tag,
`constructor.name`, prototype chain, `instanceof HTMLDocument`/`XMLDocument`, `contentType` and the
root's namespace. Copy both into a wpt checkout and load `probe.html` from `./wpt serve`.
Results in `../browsers.md`.

`iframe-name/` has `iframe-name.xhtml` and `iframe-name.xml` (same markup, served as
`application/xhtml+xml` and `application/xml`): for `<iframe name=x id=y>` they print
`frames[0].name`, `window.x`/`window.y`, whether `<a target>` navigates the iframe, and what
`window.open("", name)` returns. Serve the directory over HTTP and load either file.
