# Loads tests/nowindow/probe.html in a local Firefox build with dom.use_counters.dump.document on,
# once per value of dom.document.named_getter_without_window.enabled, and prints window.__probe
# and the htmldocument_named_getter_hit* use counter lines printed when the tab closes.
# Usage: nowindow_probe.py <firefox binary>
import json, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

base = harness.serve(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nowindow'))
url = base + 'probe.html'
res = {}
for enabled in (True, False):
    log = tempfile.NamedTemporaryFile('r', suffix='.log', delete=False)
    o = Options()
    o.binary_location = sys.argv[1]
    o.add_argument('-headless')
    o.set_preference('dom.use_counters.dump.document', True)
    o.set_preference('dom.document.named_getter_without_window.enabled', enabled)
    d = webdriver.Firefox(options=o, service=Service(os.path.expanduser('~/git/web-platform-tests/wpt/_venv3/bin/geckodriver'), log_output=log.name, service_args=['--log', 'info']))
    try:
        first = d.current_window_handle
        d.switch_to.new_window('tab')
        d.get(url)
        probe = None
        for _ in range(60):
            probe = d.execute_script('return window.__probe || null')
            if probe:
                break
            time.sleep(0.5)
        d.close()
        d.switch_to.window(first)
        time.sleep(3)
    finally:
        d.quit()
    lines = sorted({l.strip() for l in open(log.name) if 'USE_COUNTER_DOCUMENT' in l and 'htmldocument_named_getter_hit' in l})
    res[f'enabled={enabled}'] = {'probe': probe, 'counters': lines}
    os.unlink(log.name)
print(json.dumps(res, indent=1))
