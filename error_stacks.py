# Load a URL in setup B (emulation for $CHANGE_VARIANT) and print page errors with stacks (URL
# queries scrubbed). Usage: CHANGE_VARIANT=B2 python3 error_stacks.py CHROME URL [mobile|desktop]
import asyncio, sys
from playwright.async_api import async_playwright
import change, harness


async def main():
    mobile = (sys.argv[3] if len(sys.argv) > 3 else 'mobile') == 'mobile'
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=sys.argv[1])
        ctx = await br.new_context(viewport={'width': 360, 'height': 640} if mobile else {'width': 1366, 'height': 768},
                                   is_mobile=mobile, has_touch=mobile, ignore_https_errors=True)
        await ctx.add_init_script(change.AFTER_INIT_JS)
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: print('ERR', harness.scrub(e.stack or str(e))[:900]))
        try:
            await pg.goto(sys.argv[2], wait_until='load', timeout=45000)
            await pg.wait_for_timeout(5000)
        except Exception as e:
            print('load', str(e)[:100])
        await br.close()

asyncio.run(main())
