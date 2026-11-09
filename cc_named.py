# Named access on the XHTML responses in crawl/cc_hits.jsonl: lists named elements (document's
# named-getter filter), elements with an id or a window-named name, and inline script or event
# handler text that reads one of those names as document.X, window.X or a bare identifier.
# Usage: python3 cc_named.py WARC_DIR > crawl/cc_named.jsonl
import json, os, re, sys
from warcio.archiveiterator import ArchiveIterator

warc_dir = sys.argv[1]
want = {}
for l in open('crawl/cc_hits.jsonl'):
    r = json.loads(l)
    if r['mime'] == 'application/xhtml+xml':
        want.setdefault(os.path.basename(r['warc']), set()).add(r['url'])
TAG = re.compile(r'<([A-Za-z][\w:.-]*)(\s[^<>]*?)?/?>', re.S)
ATTR = re.compile(r'([\w:.-]+)\s*=\s*("[^"]*"|\'[^\']*\')')
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script>', re.S | re.I)
for warc, urls in sorted(want.items()):
    with open(os.path.join(warc_dir, warc), 'rb') as f:
        for rec in ArchiveIterator(f):
            if rec.rec_type != 'response' or rec.rec_headers.get_header('WARC-Target-URI') not in urls:
                continue
            body = rec.content_stream().read().decode('utf-8', 'replace')
            doc_names, win_names, handlers = set(), set(), []
            for m in TAG.finditer(body):
                tag = m.group(1).lower().split(':')[-1]
                attrs = {k.lower(): v[1:-1] for k, v in ATTR.findall(m.group(2) or '')}
                name, id_ = attrs.get('name', ''), attrs.get('id', '')
                if name and tag in ('embed', 'form', 'iframe', 'img', 'object'):
                    doc_names.add(name)
                    win_names.add(name)
                if id_ and (tag == 'object' or (tag == 'img' and name)):
                    doc_names.add(id_)
                if id_:
                    win_names.add(id_)
                handlers += [v for k, v in attrs.items() if k.startswith('on')]
            code = '\n'.join(SCRIPT.findall(body) + handlers)
            refs = {}
            for n in sorted(doc_names | win_names):
                if not re.fullmatch(r'[A-Za-z_$][\w$]*', n):
                    continue
                for kind, rx in (('document.', rf'\bdocument\s*\.\s*{re.escape(n)}\b'),
                                 ('window.', rf'\bwindow\s*\.\s*{re.escape(n)}\b'),
                                 ('bare', rf'(?<![\w$.\'"#-]){re.escape(n)}\b(?!\s*[:=(]|[\'"-])')):
                    c = len(re.findall(rx, code))
                    if c:
                        refs.setdefault(n, {})[kind] = c
            print(json.dumps({'url': rec.rec_headers.get_header('WARC-Target-URI'), 'doc_names': len(doc_names),
                              'win_names': len(win_names), 'script_chars': len(code), 'refs': refs}))
