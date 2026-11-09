# Summarizes named-access reads from detect_chrome.py / detect_firefox.py / compare.py (variant N) output:
# pages with reads, and groups by target (document/window), op and calling script.
# Usage: named_summary.py OUT.jsonl [OUT.jsonl ...] > summary.csv
import csv, collections, json, re, sys

FRAME = re.compile(r'(?:at |@)(?:.*?\()?((?:https?|file):[^\s)]+?):\d+:\d+')


def script_of(stack):
    for part in stack.split(' | '):
        m = FRAME.search(part)
        if m:
            u = re.sub(r'[?#].*', '', m.group(1))
            return re.sub(r'\d{4,}|[0-9a-f]{8,}', '<n>', u)
    return '(no frame)'


def extra_of(r):
    if 'extra' in r:
        return r.get('extra')
    v = r.get('B') or {}
    return v.get('extra')


groups = collections.defaultdict(lambda: {'pages': set(), 'names': collections.Counter(), 'values': collections.Counter(), 'example': ''})
stats = collections.Counter()
for path in sys.argv[1:]:
    for r in map(json.loads, open(path)):
        stats[path, 'rows'] += 1
        e = extra_of(r)
        if not e or e.get('contentType') != 'application/xhtml+xml':
            stats[path, 'not xhtml now' if e else 'no trace'] += 1
            continue
        stats[path, 'xhtml'] += 1
        if isinstance(e['events'], str):  # a page's Array.prototype.toJSON (Prototype.js) stringified it
            e['events'] = json.loads(e['events'])
        if e['events']:
            stats[path, 'with reads'] += 1
        for ev in e['events']:
            k = (path.split('/')[-1], ev['target'], ev['op'], script_of(ev['stack']))
            g = groups[k]
            g['pages'].add(r['page'])
            g['names'][ev['name']] += 1
            g['values'][ev['A'] + '->' + ev['B']] += 1
            g['example'] = g['example'] or r['page']
for k, v in sorted(stats.items()):
    print(*k, v, file=sys.stderr)
w = csv.writer(sys.stdout)
w.writerow(['run', 'target', 'op', 'script', 'pages', 'names', 'values', 'example_page'])
for k, g in sorted(groups.items(), key=lambda kv: -len(kv[1]['pages'])):
    w.writerow([*k, len(g['pages']), ' '.join(n for n, _ in g['names'].most_common(6)),
                ' '.join(f'{a}:{c}' for a, c in g['values'].most_common(3)), g['example']])
