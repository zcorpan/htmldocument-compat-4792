# Summarizes trace.js output in compare.py results (visits A and A2, main frame and subframes):
# which pages had scripts observe a document-interface value that differs under candidate 1 (B1)
# or candidate 2 (B2), grouped by API and calling script.
# Usage: python3 trace_summary.py OUT_DIR [OUT_DIR...]  -> OUT_DIR/trace-pages.csv, OUT_DIR/trace-groups.csv
import collections, csv, json, re, sys

FRAME_URL = re.compile(r'((?:https?|chrome-extension)://[^\s)]+?)(?::\d+:\d+)?\)?$')


def script_of(stack):
    """First stack frame with a script URL, normalized (hashes and long ids masked)."""
    for f in stack or []:
        m = FRAME_URL.search(f)
        if m:
            u = re.sub(r':\d+:\d+$', '', m.group(1))
            u = re.sub(r'[0-9a-f]{8,}', '<h>', u)
            u = re.sub(r'\d{4,}', '<n>', u)
            return u
    return '(inline or native)' if stack else '(no stack)'


def visits(r):
    for tag in ('A', 'A2'):
        v = r.get(tag) or {}
        for fr in [v] + v.get('frames', []):
            t = fr.get('extra')
            if t:
                # Pages with an Array.prototype.toJSON (Prototype.js) serialize nested arrays as strings.
                for k in ('events', 'protoAdds'):
                    if isinstance(t.get(k), str):
                        try:
                            t[k] = json.loads(t[k])
                        except ValueError:
                            t[k] = []
                yield tag, t


for out_dir in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f'{out_dir}/results.jsonl')]
    groups = collections.defaultdict(lambda: {'pages': set(), 'n': 0, 'example': None})
    with open(f'{out_dir}/trace-pages.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['idx', 'stratum', 'page', 'traced', 'docTypes', 'changed_B1', 'changed_B2', 'apis_B1', 'apis_B2', 'protoAdds'])
        for r in sorted(rows, key=lambda r: r['idx']):
            traced, types, c1, c2, adds = False, set(), set(), set(), set()
            for tag, t in visits(r):
                traced = True
                types.add(t.get('docType'))
                for a in t.get('protoAdds') or []:
                    adds.add(f"{a['proto']}.{a['key']}{'*' if a['onDocumentPrototype'] else ''}")
                for e in t.get('events', []):
                    ch = e.get('changed') or {}
                    for var, s in (('B1', c1), ('B2', c2)):
                        if ch.get(var):
                            s.add(e['api'])
                            g = groups[(var, e['api'], json.dumps(e.get('values'), sort_keys=True), script_of(e.get('stack')))]
                            g['pages'].add(r['idx'])
                            g['n'] += e.get('n', 1)
                            g['example'] = g['example'] or (r['page'], e.get('stack'))
            w.writerow([r['idx'], r['stratum'], r['page'], traced, ' '.join(sorted(x for x in types if x)),
                        bool(c1), bool(c2), ' '.join(sorted(c1)), ' '.join(sorted(c2)), ' '.join(sorted(adds))])
    with open(f'{out_dir}/trace-groups.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['variant', 'api', 'values', 'script', 'pages', 'events', 'page_idxs', 'example_page', 'example_stack'])
        for (var, api, vals, script), g in sorted(groups.items(), key=lambda kv: (kv[0][0], -len(kv[1]['pages']))):
            w.writerow([var, api, vals, script, len(g['pages']), g['n'], ' '.join(map(str, sorted(g['pages']))),
                        g['example'][0], ' | '.join(g['example'][1] or [])[:400]])
    n = len(rows)
    traced = sum(1 for r in rows if any(True for _ in visits(r)))
    p1 = sum(1 for r in csv.DictReader(open(f'{out_dir}/trace-pages.csv')) if r['changed_B1'] == 'True')
    p2 = sum(1 for r in csv.DictReader(open(f'{out_dir}/trace-pages.csv')) if r['changed_B2'] == 'True')
    print(f'{out_dir}: {n} pages, {traced} traced, {p1} observe a B1 change, {p2} observe a B2 change, {len(groups)} groups')
