# Loads tests/named.xhtml and tests/named.html in Chrome Canary (Playwright) and Firefox Nightly
# (Selenium + BiDi), optionally with an init script, and prints window.__probe per page as JSON.
# Usage: named_probe.py [INIT_JS_FILE] [--ff-pref-off]
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness
from playwright.async_api import async_playwright

CHROME = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
FIREFOX = '/Applications/Firefox Nightly.app/Contents/MacOS/firefox'
GECKODRIVER = os.path.expanduser('~/git/web-platform-tests/wpt/_venv3/bin/geckodriver')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
init = open(args[0]).read() if args else None
base = harness.serve(os.path.dirname(os.path.abspath(__file__)))
pages = ['named.xhtml', 'named.html']


async def chrome():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME)
        for name in pages:
            ctx = await b.new_context()
            if init:
                await ctx.add_init_script(init)
            pg = await ctx.new_page()
            await pg.goto(base + name, wait_until='load')
            out[name] = await pg.evaluate('window.__probe')
            out[name + '@load'] = await pg.evaluate('window.__probeLoad')
            await ctx.close()
        out['version'] = b.version
        await b.close()
    return out


def firefox():
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service
    o = Options()
    o.binary_location = FIREFOX
    o.add_argument('-headless')
    o.enable_bidi = True
    if '--ff-pref-off' in sys.argv:
        o.set_preference('dom.document.name_getter_prevent_shadowing.enabled', False)
    d = webdriver.Firefox(options=o, service=Service(GECKODRIVER))
    try:
        if init:
            d.script.pin('() => {' + init + '\n}')
        out = {}
        for name in pages:
            d.get(base + name)
            time.sleep(1)
            out[name] = d.execute_script('return window.__probe')
            out[name + '@load'] = d.execute_script('return window.__probeLoad'); out[name + '@fr'] = d.execute_script('return window.__fr')
        out['version'] = d.capabilities.get('browserVersion')
        return out
    finally:
        d.quit()


res = {'chrome': asyncio.run(chrome()), 'firefox': firefox()}
print(json.dumps(res, indent=1))
