# Detection pass for the HTMLDocument named getter on documents without a window (DOMParser,
# XHR, createHTMLDocument(), parseHTMLUnsafe()): loads each page in its own tab of a local Firefox
# build with the HTMLDocumentNamedGetterHitNoWindow use counter and dom.use_counters.dump.document
# on, closes the tab, and records the related counter lines printed as its documents are destroyed.
# Counter lines carry the reporting document's URL, cut here to its origin. Lines from a document
# destroyed late can land on the worker's next page; the origin shows which. idx is the row in
# PAGES.csv (page URLs stay there, with the crawl data).
# Usage: detect_nowindow.py FIREFOX PAGES.csv OUT.jsonl [WORKERS] [PREF_ENABLED]   Resumable.
import csv, json, os, queue, re, sys, tempfile, threading, time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import harness

GECKODRIVER = os.path.expanduser('~/git/web-platform-tests/wpt/_venv3/bin/geckodriver')
KEEP = re.compile(r'USE_COUNTER_DOCUMENT: (htmldocument_named_getter_hit\w*|domparser_parsefromstring|document_parsehtmlunsafe) - (\S+)')
firefox, src, out = sys.argv[1:4]
workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8
enabled = (sys.argv[5] if len(sys.argv) > 5 else 'true') == 'true'
rows = [dict(r, idx=i) for i, r in enumerate(csv.DictReader(open(src)))]
done = {json.loads(l)['idx'] for l in open(out)} if os.path.exists(out) else set()
q = queue.Queue()
for r in rows:
    if r['idx'] not in done:
        q.put(r)
lock = threading.Lock()
f = open(out, 'a')


class Browser:
    def __init__(self):
        self.log = tempfile.NamedTemporaryFile('r', suffix='.log', delete=False).name
        o = Options()
        o.binary_location = firefox
        o.add_argument('-headless')
        o.set_preference('dom.use_counters.dump.document', True)
        o.set_preference('dom.document.named_getter_without_window.enabled', enabled)
        o.set_preference('dom.disable_open_during_load', True)
        o.set_preference('media.autoplay.default', 5)
        self.d = webdriver.Firefox(options=o, service=Service(GECKODRIVER, log_output=self.log, service_args=['--log', 'info']))
        self.d.set_page_load_timeout(30)
        self.d.set_script_timeout(10)
        self.home = self.d.current_window_handle
        self.pos = 0

    def lines(self):
        with open(self.log, errors='replace') as fh:
            fh.seek(self.pos)
            data = fh.read()
            self.pos = fh.tell()
        res = set()
        for m in KEEP.finditer(data):
            o = harness.ORIGIN.match(m.group(2))
            res.add((m.group(1), harness.scrub(o.group(0) if o else m.group(2))))
        return sorted(res)

    def quit(self):
        try:
            self.d.quit()
        except Exception:
            pass
        os.unlink(self.log)


def work():
    b = Browser()
    while True:
        try:
            r = q.get_nowait()
        except queue.Empty:
            break
        rec = {'idx': r['idx'], 'rank': int(r['rank']), 'enabled': enabled}
        if r.get('stratum'):
            rec['stratum'] = r['stratum']
        try:
            b.d.switch_to.new_window('tab')
            try:
                b.d.get(r['page'])
            except Exception as e:
                rec['load_error'] = type(e).__name__
            time.sleep(4)
            b.d.close()
            b.d.switch_to.window(b.home)
            time.sleep(1.5)
            rec['counters'] = b.lines()
        except Exception as e:
            rec['error'] = harness.scrub(str(e).splitlines()[0])[:200]
            rec['counters'] = b.lines()
            b.quit()
            b = Browser()
        with lock:
            f.write(json.dumps(rec) + '\n')
            f.flush()
    b.quit()


ts = [threading.Thread(target=work) for _ in range(workers)]
for t in ts:
    t.start()
for t in ts:
    t.join()
