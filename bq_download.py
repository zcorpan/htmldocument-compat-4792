# Download a BigQuery table with `bq head` (tabledata.list, not billed) in parallel chunks.
# Usage: python3 bq_download.py TABLE NROWS OUTDIR [CHUNK]
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

table, n, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 100
os.makedirs(outdir, exist_ok=True)


def get(start):
    path = os.path.join(outdir, f'{start:07d}.json')
    if os.path.exists(path) and os.path.getsize(path) > 2:
        return
    for attempt in range(4):
        r = subprocess.run(['bq', 'head', '--format=json', f'--start_row={start}', f'--max_rows={chunk}', table],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith('['):
            with open(path + '.part', 'w') as f:
                f.write(r.stdout)
            os.rename(path + '.part', path)
            return
    print('failed', start, r.stderr[:200], file=sys.stderr)


with ThreadPoolExecutor(6) as ex:
    list(ex.map(get, range(0, n, chunk)))
