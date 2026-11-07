# Print windows of a 10k-sample body (first row whose URL contains URL_PART) around REGEX matches.
# Usage: python3 body_ctx.py RAW_DIR URL_PART REGEX [BEFORE] [AFTER] [MAX]
import glob, json, re, sys
raw, part, rx = sys.argv[1], sys.argv[2], re.compile(sys.argv[3])
before = int(sys.argv[4]) if len(sys.argv) > 4 else 600
after = int(sys.argv[5]) if len(sys.argv) > 5 else 600
mx = int(sys.argv[6]) if len(sys.argv) > 6 else 3
for path in sorted(glob.glob(f'{raw}/*.json')):
    for r in json.load(open(path)):
        if part in r['url']:
            b = r['body'] or ''
            for i, m in enumerate(rx.finditer(b)):
                if i >= mx:
                    break
                print(f'--- {m.start()}/{len(b)}')
                print(b[max(0, m.start() - before):m.end() + after])
            sys.exit(0)
