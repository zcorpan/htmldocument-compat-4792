# Writes <out-dir>/review-brief.csv listing review images of pages analyze.py couldn't rate.
# Usage: python3 write_brief.py OUT_DIR...
import csv, os, sys
for d in sys.argv[1:]:
    rows = [r for r in csv.DictReader(open(f'{d}/auto.csv')) if not r['auto_rating']]
    n = 0
    with open(f'{d}/review-brief.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['image', 'idx', 'textRatioAA2', 'textRatioAB', 'pixAA2', 'pixAB', 'new_errors_in_B'])
        for r in rows:
            img = f"{d}/review/{int(r['idx']):03}.png"
            if os.path.exists(img):
                w.writerow([img, r['idx'], r['textRatioAA2'], r['textRatioAB'], r['pixAA2'], r['pixAB'], r['new_errors_in_B'][:200]]); n += 1
    print(d, n)
