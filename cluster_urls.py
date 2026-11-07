# For each named risky pattern, list the scripts (URL without query) whose bodies match it in the
# 10k-sample mentions, with page counts. Usage: python3 cluster_urls.py crawl/bodies_10k-mentions.jsonl
import collections, json, re, sys

from cluster_patterns import PATTERNS
rx = {k: re.compile(v) for k, v in PATTERNS.items()}
pages = collections.defaultdict(set)
urls = collections.defaultdict(lambda: collections.defaultdict(set))
for r in map(json.loads, open(sys.argv[1])):
    u = re.sub(r'[?#].*', '', r['url'])
    for m in r['mentions']:
        for k, x in rx.items():
            if x.search(m['ctx']):
                pages[k].add((r['client'], r['page']))
                urls[k][u].add((r['client'], r['page']))
for k in PATTERNS:
    print(f'== {k}: {len(pages[k])} pages')
    for u, p in sorted(urls[k].items(), key=lambda x: -len(x[1]))[:6]:
        print(f'   {len(p):4d} {u[:150]}')
