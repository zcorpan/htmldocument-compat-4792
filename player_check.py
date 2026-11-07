# For pages loading a library, load in plain Chrome and with emulation ($CHANGE_VARIANT) and count
# video elements, iframes and elements whose id/class mention the library, plus page errors.
# Usage: CHANGE_VARIANT=B2 python3 player_check.py CHROME LIBS_CSV LIB N [SEED]
import asyncio, csv, hashlib, sys
from playwright.async_api import async_playwright
import change, harness

COUNT_JS = """(lib) => ({videos: document.querySelectorAll('video').length, iframes: document.querySelectorAll('iframe').length,
  lib: document.querySelectorAll(`[id*="${lib}" i], [class*="${lib}" i]`).length})"""


async def load(br, url, js, lib):
    ctx = await br.new_context(viewport={'width': 360, 'height': 640}, is_mobile=True, has_touch=True, ignore_https_errors=True)
    if js:
        await ctx.add_init_script(js)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(harness.scrub(str(e))[:100]))
    try:
        await pg.goto(url, wait_until='load', timeout=30000)
        for y in (600, 1200, 1800, 2400):
            await pg.mouse.wheel(0, 600)
            await pg.wait_for_timeout(1500)
        c = await pg.evaluate(COUNT_JS, lib)
    except Exception as e:
        c = {'error': str(e)[:80]}
    await ctx.close()
    return c, [e for e in errs if 'Document' in e or 'Invalid type' in e]


async def main():
    exe, path, lib, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    seed = sys.argv[5] if len(sys.argv) > 5 else 'hd4792'
    rows = sorted({r['page'] for r in csv.DictReader(open(path)) if r['lib'] == lib and r['client'] == 'mobile' and r['is_root_page'] == 'true'},
                  key=lambda p: hashlib.sha256((p + seed).encode()).hexdigest())[:n]
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=exe)
        for url in rows:
            a = await harness.guarded(load(br, url, None, lib), 90)
            b = await harness.guarded(load(br, url, change.AFTER_INIT_JS, lib), 90)
            print(url, '| A', a, '| B', b, flush=True)
        await br.close()

asyncio.run(main())
