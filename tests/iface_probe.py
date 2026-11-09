# Loads tests/iface/probe.html in Chrome Canary (Playwright), Firefox Nightly and Safari Technology
# Preview (Selenium) and prints window.__probe per browser as JSON.
# Usage: iface_probe.py [chrome] [firefox] [safari]
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness
from playwright.async_api import async_playwright

base = harness.serve(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iface'))
url = base + 'probe.html'
which = sys.argv[1:] or ['chrome', 'firefox', 'safari']


def wait(get):
    for _ in range(60):
        r = get()
        if r:
            return r
        time.sleep(0.5)


async def chrome():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary')
        pg = await b.new_page()
        await pg.goto(url)
        await pg.wait_for_function('window.__probe', timeout=30000)
        r = await pg.evaluate('window.__probe')
        await b.close()
        return r


def selenium(kind):
    from selenium import webdriver
    if kind == 'firefox':
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        o = Options()
        o.binary_location = '/Applications/Firefox Nightly.app/Contents/MacOS/firefox'
        o.add_argument('-headless')
        d = webdriver.Firefox(options=o, service=Service(os.path.expanduser('~/git/web-platform-tests/wpt/_venv3/bin/geckodriver')))
    else:
        from selenium.webdriver.safari.options import Options
        from selenium.webdriver.safari.service import Service
        o = Options()
        o.use_technology_preview = True
        d = webdriver.Safari(options=o, service=Service('/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'))
    try:
        d.get(url)
        return wait(lambda: d.execute_script('return window.__probe || null'))
    finally:
        d.quit()


res = {}
for k in which:
    try:
        res[k] = asyncio.run(chrome()) if k == 'chrome' else selenium(k)
    except Exception as e:
        res[k] = {'error': str(e).splitlines()[0][:300]}
print(json.dumps(res, indent=1))
