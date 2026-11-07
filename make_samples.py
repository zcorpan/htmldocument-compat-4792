# Builds the sample files from committed query output.
# Usage: python3 make_samples.py
import csv, hashlib, json, collections

SEED = 'hd4792'
key = lambda page: hashlib.sha256((page + SEED).encode()).hexdigest()

# Random mobile root pages (queries/random_root.csv is already a seeded random 500).
total_mobile_root = next(int(r['pages']) for r in csv.DictReader(open('queries/totals.csv'))
                         if r['client'] == 'mobile' and r['is_root_page'] == 'true')
with open('crawl/samples/random.jsonl', 'w') as f:
    for r in csv.DictReader(open('queries/random_root.csv')):
        f.write(json.dumps({'page': r['page'], 'rank': r['rank'], 'client': 'mobile', 'stratum': 'random-mobile',
                            'stratum_size': total_mobile_root}) + '\n')

# Root pages whose main document is XML-typed: 75 per (xhtml|xml) x client.
strata = collections.defaultdict(dict)
for r in csv.DictReader(open('queries/xml_main_docs.csv')):
    if r['is_root_page'] != 'true':
        continue
    kind = 'xhtml' if 'xhtml' in r['mime'] else 'xml'
    strata[f"{kind}-{r['client']}"][r['page']] = r
with open('crawl/samples/xmltyped.jsonl', 'w') as f:
    for name in sorted(strata):
        rows = sorted(strata[name].values(), key=lambda r: key(r['page']))
        for r in rows[:75]:
            f.write(json.dumps({'page': r['page'], 'rank': r['rank'], 'client': r['client'], 'mime': r['mime'],
                                'stratum': name, 'stratum_size': len(rows)}) + '\n')
        print(name, len(rows), min(75, len(rows)))

# 10k-sample pages with XML-typed subframe documents (all of them).
pages = {}
for r in csv.DictReader(open('queries/xml_subframe_docs_10k.csv')):
    k = (r['client'], r['page'])
    pages.setdefault(k, {'page': r['page'], 'rank': r['rank'], 'client': r['client'], 'is_root_page': r['is_root_page'],
                         'frame_mimes': set()})['frame_mimes'].add(r['mime'])
with open('crawl/samples/subframes.jsonl', 'w') as f:
    for (client, page), r in sorted(pages.items()):
        f.write(json.dumps({**r, 'frame_mimes': sorted(r['frame_mimes']), 'stratum': f'subframe-{client}',
                            'stratum_size': sum(1 for k in pages if k[0] == client)}) + '\n')
print('subframe pages', len(pages), collections.Counter(m for r in pages.values() for m in r['frame_mimes']))

# 10k-sample root pages whose bodies match a risky pattern (cluster_urls.py), up to 15 per pattern.
import re, importlib.util
spec = importlib.util.spec_from_file_location('cu_patterns', 'cluster_patterns.py')
cu = importlib.util.module_from_spec(spec); spec.loader.exec_module(cu)
rx = {k: re.compile(v) for k, v in cu.PATTERNS.items()}
by_pat = collections.defaultdict(dict)
for r in map(json.loads, open('crawl/bodies_10k-mentions.jsonl')):
    if not r['is_root_page']:
        continue
    for m in r['mentions']:
        for k, x in rx.items():
            if x.search(m['ctx']):
                by_pat[k].setdefault((r['client'], r['page']), r['rank'])
chosen = {}
for k in sorted(by_pat):
    for (client, page), rank in sorted(by_pat[k].items(), key=lambda kv: key(kv[0][1] + kv[0][0]))[:15]:
        chosen.setdefault((client, page), {'page': page, 'rank': rank, 'client': client, 'patterns': []})['patterns'].append(k)
# Every pattern a chosen page matches, not just the one it was picked for.
for (client, page), c in chosen.items():
    c['patterns'] = sorted(k for k in by_pat if (client, page) in by_pat[k])
with open('crawl/samples/targeted.jsonl', 'w') as f:
    for (client, page), c in sorted(chosen.items()):
        f.write(json.dumps({**c, 'stratum': 'targeted-' + client, 'stratum_size': 0}) + '\n')
print('targeted', len(chosen), {k: len(v) for k, v in sorted(by_pat.items())})
