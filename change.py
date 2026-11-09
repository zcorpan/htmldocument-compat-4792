# The change under test. compare.py, recheck.py, and analyze.py import this; the rest is generic.
# Visits A and A2 use the "before" setup (unmodified Chrome plus trace.js), B the "after" setup
# (emulate.js for the variant in $CHANGE_VARIANT: B1 = candidate 1, B2 = candidate 2).
# Variant N: named access on XHTML. A and A2 are plain Chrome; B adds Firefox's named access
# (named.js in 'emulate' mode), which also logs the reads.
import os

VARIANT = os.environ.get('CHANGE_VARIANT', 'B2')
assert VARIANT in ('B1', 'B2', 'N'), VARIANT
_here = os.path.dirname(os.path.abspath(__file__))

BEFORE_ARGS = []
AFTER_ARGS = []
BEFORE_EXTENSION = None
AFTER_EXTENSION = None

if VARIANT == 'N':
    AFTER_INIT_JS = open(os.path.join(_here, 'named.js')).read().replace('__MODE__', 'emulate')
else:
    AFTER_INIT_JS = open(os.path.join(_here, 'emulate.js')).read().replace('__VARIANT__', VARIANT)
AFTER_LOAD_JS = None

# Only in the before setup (harness.py): the trace of document-interface observations.
BEFORE_INIT_JS = None if VARIANT == 'N' else open(os.path.join(_here, 'trace.js')).read()
INIT_JS = None

EXTRA_MEASURE_JS = ("""() => window.__hdNamed ? JSON.parse(window.__hdNamed.collect()) : null""" if VARIANT == 'N' else
                    """() => window.__hdTrace ? JSON.parse(JSON.stringify(window.__hdTrace.collectProtoAdds())) : null""")

IGNORE_MESSAGES = None

SANITY_PAGE = 'named.xhtml' if VARIANT == 'N' else 'index.html'
_frames = """(() => { const f = [...document.querySelectorAll('iframe')]; const t = d => Object.prototype.toString.call(d);
  return { top: t(document), xhtml: t(f[0].contentDocument), blank: t(f[1].contentDocument), xml: t(f[2].contentDocument),
    parsed: t(new DOMParser().parseFromString('', 'text/html')), parsedXml: t(new DOMParser().parseFromString('<x/>', 'text/xml')),
    alias: HTMLDocument === Document }; })()"""
SANITY_JS = {
    'B1': f"""(r => r.xhtml === '[object HTMLDocument]' && r.top === '[object HTMLDocument]' && r.xml === '[object XMLDocument]' && !r.alias)({_frames})""",
    'B2': f"""(r => r.top === '[object Document]' && r.xhtml === '[object Document]' && r.blank === '[object Document]' && r.xml === '[object Document]'
      && r.parsed === '[object Document]' && r.parsedXml === '[object XMLDocument]' && r.alias)({_frames})""",
    'N': """(() => document.f1 instanceof Element && window.d1 instanceof Element && document.title instanceof Element && document.contentType === 'application/xhtml+xml')()""",
}[VARIANT]


def classify(r):
    """Change-specific auto-rating for a page analyze.py couldn't rate: (rating, reason) or None."""
    return None
