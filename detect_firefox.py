# One visit per distinct URL in Firefox Nightly (desktop) with named.js in 'trace' mode and
# dom.document.name_getter_prevent_shadowing.enabled off (release behavior): which scripts read
# named access on XHTML pages in Firefox. Top-level document only.
# Usage: detect_firefox.py URLS.jsonl OUT.jsonl [WORKERS]   Resumable.
import json, os, queue, sys, threading, time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import harness

FIREFOX = '/Applications/Firefox Nightly.app/Contents/MacOS/firefox'
GECKODRIVER = os.path.expanduser('~/git/web-platform-tests/wpt/_venv3/bin/geckodriver')
PRELOAD = '() => {' + open(harness.here('named.js')).read().replace('__MODE__', 'trace') + '\n}'
src, out = sys.argv[1:3]
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
seen, rows = set(), []
for r in map(json.loads, open(src)):
    if r['page'] not in seen:
        seen.add(r['page'])
        rows.append(r)
done = {json.loads(l)['page'] for l in open(out)} if os.path.exists(out) else set()
q = queue.Queue()
for r in rows:
    if r['page'] not in done:
        q.put(r)
lock = threading.Lock()
f = open(out, 'a')


def browser():
    o = Options()
    o.binary_location = FIREFOX
    o.add_argument('-headless')
    o.enable_bidi = True
    o.set_preference('dom.document.name_getter_prevent_shadowing.enabled', False)
    o.set_preference('dom.disable_open_during_load', True)
    o.set_preference('media.autoplay.default', 5)
    d = webdriver.Firefox(options=o, service=Service(GECKODRIVER))
    d.set_page_load_timeout(30)
    d.set_script_timeout(10)
    errors = []
    d.script.add_javascript_error_handler(lambda e: errors.append(harness.scrub(e.text)[:300]))
    d.script.pin(PRELOAD)
    return d, errors


def work():
    d, errors = browser()
    while True:
        try:
            r = q.get_nowait()
        except queue.Empty:
            break
        errors.clear()
        rec = {'idx': r['idx'], 'page': r['page'], 'client': 'desktop'}
        try:
            try:
                d.get(r['page'])
            except Exception as e:
                rec['load_error'] = type(e).__name__
            time.sleep(3)
            rec['extra'] = json.loads(d.execute_script('return window.__hdNamed ? window.__hdNamed.collect() : "null"'))
            rec['contentType'] = d.execute_script('return document.contentType')
        except Exception as e:
            rec['error'] = harness.scrub(str(e).splitlines()[0])[:200]
            try:
                d.quit()
            except Exception:
                pass
            d, errors = browser()
        rec['pageErrors'] = errors[:10]
        with lock:
            f.write(json.dumps(rec) + '\n')
            f.flush()
    d.quit()


ts = [threading.Thread(target=work) for _ in range(workers)]
for t in ts:
    t.start()
for t in ts:
    t.join()
