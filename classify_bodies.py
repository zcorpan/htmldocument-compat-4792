# Classify each mention of HTMLDocument / XMLDocument / "[object ...Document]" in the 10k-sample
# response bodies (bq_download.py output) by usage kind, and cluster mentions by normalized context.
# Usage: python3 classify_bodies.py RAW_DIR OUT_PREFIX
# Writes OUT_PREFIX-mentions.jsonl (one line per page, body_fp, kind, context) and prints summaries.
import collections, glob, json, re, sys

raw_dir, out = sys.argv[1], sys.argv[2]
MENTION = re.compile(r'\b(?:HTML|XML)Document\b|\[object (?:HTML|XML)?Document\]')
KINDS = [
    ('tag_string', re.compile(r'\[object (?:HTML|XML)?Document\]')),
    ('instanceof', re.compile(r'instanceof\s*(?:window\.|self\.|globalThis\.|\w\.)?(?:HTML|XML)Document\b')),
    ('proto_descriptor', re.compile(r'getOwnPropertyDescriptors?\(\s*(?:window\.)?(?:HTML|XML)Document\.prototype')),
    ('proto_write', re.compile(r'(?:HTML|XML)Document\.prototype(?:\.\w+|\[[^\]]+\])\s*=[^=]|definePropert(?:y|ies)\(\s*(?:window\.)?(?:HTML|XML)Document\.prototype')),
    ('proto_other', re.compile(r'(?:HTML|XML)Document\.prototype')),
    ('string_literal', re.compile(r'''["'`](?:HTML|XML)Document(?:::|["'`])''')),
    ('typeof_or_in', re.compile(r'typeof\s+(?:window\.)?(?:HTML|XML)Document|["\'](?:HTML|XML)Document["\']\s+in\b')),
    ('stack_regex', re.compile(r'(?:HTML|XML)Document\\\.')),
]


def kind_of(ctx, m_start, m_end):
    # Look at a window around the mention.
    win = ctx
    for k, rx in KINDS:
        for m in rx.finditer(win):
            if m.start() <= m_end and m.end() >= m_start:
                return k
    return 'other'


def norm(s):
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\b[a-zA-Z_$][\w$]?\b', 'v', s)  # 1-2 char identifiers from minifiers
    s = re.sub(r'\d+', 'N', s)
    return s


rows = []
for path in sorted(glob.glob(f'{raw_dir}/*.json')):
    rows.extend(json.load(open(path)))
seen_fp = {}
with open(f'{out}-mentions.jsonl', 'w') as f:
    for r in rows:
        fp = r['body_fp']
        if fp not in seen_fp:
            body = r.get('body') or ''
            ms = []
            for m in MENTION.finditer(body):
                ctx = body[max(0, m.start() - 120):m.end() + 120]
                k = kind_of(ctx, m.start() - max(0, m.start() - 120), m.end() - max(0, m.start() - 120))
                ms.append({'kind': k, 'name': m.group(0), 'ctx': ctx})
            seen_fp[fp] = ms[:200]
        f.write(json.dumps({'client': r['client'], 'is_root_page': r['is_root_page'], 'page': r['page'],
                            'rank': r['rank'], 'url': r['url'], 'type': r['type'], 'body_fp': fp,
                            'mentions': seen_fp[fp]}) + '\n')

pages = collections.defaultdict(set)  # kind -> pages
cluster_pages = collections.defaultdict(set)
cluster_example = {}
for r in map(json.loads, open(f'{out}-mentions.jsonl')):
    key = (r['client'], r['page'])
    pages['any'].add(key)
    for m in r['mentions']:
        pages[m['kind']].add(key)
        i = m['ctx'].find(m['name'])
        c = (m['kind'], norm(m['ctx'][max(0, i - 70):i + len(m['name']) + 70]))
        cluster_pages[c].add(key)
        cluster_example.setdefault(c, (r['url'], m['ctx']))
print('pages by kind (client,page):')
for k, v in sorted(pages.items(), key=lambda x: -len(x[1])):
    print(f'  {k}: {len(v)}')
print('\ntop clusters per kind:')
by_kind = collections.defaultdict(list)
for c, v in cluster_pages.items():
    by_kind[c[0]].append((len(v), c))
for k in [k for k, _ in KINDS] + ['other']:
    print('==', k)
    for n, c in sorted(by_kind[k], reverse=True)[:12]:
        print(f'  {n:5d}  {c[1][:230]!r}')
