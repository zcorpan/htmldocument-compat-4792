`probe.html` (with `doc.py`) is a throwaway wpt test that dumps, for navigated documents of each
type (in iframes), DOMParser, XHR and DOMImplementation results: the toString tag,
`constructor.name`, prototype chain, `instanceof HTMLDocument`/`XMLDocument`, `contentType` and the
root's namespace. Copy both into a wpt checkout and load `probe.html` from `./wpt serve`.
Results in `../browsers.md`.
