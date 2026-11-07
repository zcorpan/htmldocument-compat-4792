# Builds one dossier per (variant, api, calling script) trace group across runs: the group's
# values and pages, and the code around the first stack frames, fetched live (URL query was
# scrubbed at capture, so the fetched copy can differ). Dossiers go to dossiers/ (gitignored:
# live third-party code). Usage: python3 build_dossiers.py VARIANT OUT_DIR...
import collections, csv, hashlib, json, os, re, subprocess, sys

variant, out_dirs = sys.argv[1], sys.argv[2:]
FRAME = re.compile(r'((?:https?)://[^\s()]+?):(\d+):(\d+)\)?$')
os.makedirs('dossiers/scripts', exist_ok=True)
groups = collections.OrderedDict()
for d in out_dirs:
    for r in csv.DictReader(open(f'{d}/trace-groups.csv')):
        if r['variant'] != variant:
            continue
        script = re.sub(r'/<h>|<h>|<n>', '', r['script'])
        key = (r['api'], r['values'], script)
        g = groups.setdefault(key, {'pages': [], 'stacks': []})
        g['pages'] += [f"{d}#{i}" for i in r['page_idxs'].split()]
        if len(g['stacks']) < 2:
            g['stacks'].append(r['example_stack'])


def fetch(url):
    path = 'dossiers/scripts/' + hashlib.sha1(url.encode()).hexdigest()[:16] + '.js'
    if not os.path.exists(path):
        subprocess.run(['curl', '-sSL', '--max-time', '20', '-A', 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/159.0.0.0 Mobile Safari/537.36',
                        '-o', path, url], capture_output=True)
    try:
        return open(path, encoding='utf-8', errors='replace').read()
    except FileNotFoundError:
        return None


def around(src, line, col, before=1500, after=700):
    lines = src.split('\n')
    if line - 1 >= len(lines):
        return None
    off = sum(len(l) + 1 for l in lines[:line - 1]) + col - 1
    return src[max(0, off - before):off] + ' /*<<< HERE >>>*/ ' + src[off:off + after]


index = []
for n, ((api, values, script), g) in enumerate(groups.items()):
    name = f'dossiers/{variant}-{n:03d}.md'
    parts = [f'# Group {n}: {api}', f'values (A = today, B1/B2 = candidates): `{values}`',
             f'calling script (normalized): `{script}`', f'pages: {len(set(g["pages"]))} ({", ".join(sorted(set(g["pages"]))[:12])})', '']
    for st in g['stacks']:
        parts.append('## Stack (innermost first)\n\n' + '\n'.join(f'- `{f}`' for f in st.split(' | ')) + '\n')
        shown = 0
        for f in st.split(' | '):
            m = FRAME.search(f.strip())
            if not m or shown >= 2:
                continue
            src = fetch(m.group(1))
            snippet = src and around(src, int(m.group(2)), int(m.group(3)))
            parts.append(f'### Code at `{m.group(1)}:{m.group(2)}:{m.group(3)}`\n\n```js\n{snippet or "(could not fetch or position out of range)"}\n```\n')
            shown += 1
    open(name, 'w').write('\n'.join(parts))
    index.append((name, api, script, len(set(g['pages']))))
with open(f'dossiers/{variant}-index.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['dossier', 'api', 'script', 'pages'])
    w.writerows(index)
print(len(index), 'dossiers')
