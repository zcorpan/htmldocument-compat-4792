# Load sanity/trace.html in setup A (trace) and in B1/B2 (emulation) and print what each sees.
# Usage: CHANGE_VARIANT=B2 python3 trace_check.py CHROME [page]
import asyncio, json, sys
from playwright.async_api import async_playwright
import change, harness


async def main():
    url = harness.serve(harness.here('sanity')) + (sys.argv[2] if len(sys.argv) > 2 else 'trace.html')
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=sys.argv[1])
        for setup, js in (('A', change.BEFORE_INIT_JS), (change.VARIANT, change.AFTER_INIT_JS)):
            ctx = await br.new_context()
            await ctx.add_init_script(js)
            pg = await ctx.new_page()
            await pg.goto(url)
            await pg.wait_for_timeout(1500)
            print('==', setup, json.dumps(await pg.evaluate('window.__results')))
            if setup == 'A':
                for fr in pg.frames:
                    t = await fr.evaluate(change.EXTRA_MEASURE_JS)
                    print('frame', fr.url.rsplit('/', 1)[-1], 'docType', t and t['docType'], 'protoAdds', t and t['protoAdds'])
                    for e in (t or {}).get('events', []):
                        print('   ', e['api'], json.dumps(e.get('values')), e['changed'], e['n'], e['stack'][:1])
            await ctx.close()
        await br.close()

asyncio.run(main())
