# Load a URL N times in each of: plain (no init script), trace (trace.js), B (emulate.js for
# $CHANGE_VARIANT); print page errors per load. Checks whether the trace itself changes behavior.
# Usage: CHANGE_VARIANT=B2 python3 setup_errors.py CHROME URL [mobile|desktop] [N]
import asyncio, sys
from playwright.async_api import async_playwright
import change, harness


async def main():
    mobile = (sys.argv[3] if len(sys.argv) > 3 else 'mobile') == 'mobile'
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=sys.argv[1])
        for name, js in (('plain', None), ('trace', change.BEFORE_INIT_JS), (change.VARIANT, change.AFTER_INIT_JS)):
            for k in range(n):
                ctx = await br.new_context(viewport={'width': 360, 'height': 640} if mobile else {'width': 1366, 'height': 768},
                                           is_mobile=mobile, has_touch=mobile, ignore_https_errors=True)
                if js:
                    await ctx.add_init_script(js)
                pg = await ctx.new_page()
                errs = []
                pg.on('pageerror', lambda e: errs.append(harness.scrub(str(e))[:150])); pg.on('console', lambda m: m.type in ('error', 'warning') and 'urnstile' in m.text and errs.append('console: ' + harness.scrub(m.text)[:120]))
                try:
                    await pg.goto(sys.argv[2], wait_until='load', timeout=45000)
                    await pg.wait_for_timeout(6000)
                except Exception as e:
                    errs.append('load: ' + str(e)[:80])
                print(name, k, errs)
                await ctx.close()
        await br.close()

asyncio.run(main())
