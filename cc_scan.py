# Scan Common Crawl WARCs: count HTTP 200 responses by document type (text/html vs
# application/xhtml+xml) and find inline-markup hits for patterns that observe the document
# interface. Usage: python3 cc_scan.py OUT.jsonl WARC...
import json, re, sys
from multiprocessing import Pool

PATTERNS = {
    'HTMLDocument': re.compile(r'\bHTMLDocument\b'),
    'XMLDocument': re.compile(r'\bXMLDocument\b'),
    'tag_object_Document': re.compile(r'\[object (?:HTML|XML)?Document\]'),
    'constructor_name_doc': re.compile(r'document\.constructor(?:\.name)?\b'),
    'contentType_doc': re.compile(r'document\.contentType\b'),
    'documentElement_ns': re.compile(r'documentElement\.namespaceURI\b'),
}


def scan(path):
    from warcio.archiveiterator import ArchiveIterator
    counts = {'html': 0, 'xhtml': 0, 'other_html': 0}
    hits = []
    with open(path, 'rb') as f:
        for rec in ArchiveIterator(f):
            if rec.rec_type != 'response' or not rec.http_headers:
                continue
            if rec.http_headers.get_statuscode() != '200':
                continue
            ctype = (rec.http_headers.get_header('Content-Type') or '').lower()
            mime = ctype.split(';')[0].strip()
            if mime == 'text/html':
                kind = 'html'
            elif mime == 'application/xhtml+xml':
                kind = 'xhtml'
            elif 'html' in mime:
                kind = 'other_html'
            else:
                continue
            counts[kind] += 1
            body = rec.content_stream().read(3_000_001)
            if len(body) > 3_000_000:
                continue
            text = body.decode('utf-8', 'replace')
            found = {}
            for name, rx in PATTERNS.items():
                ms = [text[max(0, m.start() - 100):m.end() + 100] for m in rx.finditer(text)][:5]
                if ms:
                    found[name] = ms
            if found or kind == 'xhtml':
                hits.append({'url': rec.rec_headers.get_header('WARC-Target-URI'), 'mime': mime,
                             'found': found, 'warc': path.rsplit('/', 1)[-1]})
    return counts, hits


if __name__ == '__main__':
    out, warcs = sys.argv[1], sys.argv[2:]
    total = {'html': 0, 'xhtml': 0, 'other_html': 0}
    with Pool(min(8, len(warcs))) as pool, open(out, 'w') as f:
        for counts, hits in pool.imap_unordered(scan, warcs):
            for k, v in counts.items():
                total[k] += v
            for h in hits:
                f.write(json.dumps(h) + '\n')
    print(json.dumps(total))
