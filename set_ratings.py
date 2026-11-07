# Fill manual ratings into <out-dir>/review.csv. Usage: python3 set_ratings.py OUT_DIR RATINGS.json
# RATINGS.json: {"<idx>": ["<rating>", "<note>"], ...}; only rows still unrated (or method manual) change.
import csv, json, sys
out_dir, ratings = sys.argv[1], json.load(open(sys.argv[2]))
rows = list(csv.DictReader(open(f'{out_dir}/review.csv')))
for r in rows:
    if r['idx'] in ratings and r['method'] != 'auto':
        r['rating'], note = ratings[r['idx']]
        r['note'] = (r['note'] + '; ' if r['note'] else '') + note
with open(f'{out_dir}/review.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(sum(1 for r in rows if not r['rating']), 'unrated left in', out_dir)
