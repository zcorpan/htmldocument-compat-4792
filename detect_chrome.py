# One visit per URL in Chrome Canary with named.js in 'emulate' mode (CHANGE_VARIANT=N, setup
# "after"), no screenshots: which scripts read Firefox-style named access on XHTML pages.
# Usage: CHANGE_VARIANT=N detect_chrome.py CHROME URLS.jsonl OUT.jsonl [CONCURRENCY]
# URLS.jsonl rows: {"idx", "page", "client"}. Resumable.
import asyncio, json, os, sys
import harness
from playwright.async_api import async_playwright

chrome, src, out = sys.argv[1:4]
conc = int(sys.argv[4]) if len(sys.argv) > 4 else 6
rows = [json.loads(l) for l in open(src)]
done = {json.loads(l)['idx'] for l in open(out)} if os.path.exists(out) else set()


async def main():
    async with async_playwright() as p:
        browser = await harness.launch(p, chrome, 'after')
        sem, lock = asyncio.Semaphore(conc), asyncio.Lock()
        f = open(out, 'a')

        async def one(r):
            nonlocal browser
            async with sem:
                async with lock:
                    if not browser.is_connected():
                        browser = await harness.launch(p, chrome, 'after')
                try:
                    v = await harness.guarded(harness.visit(browser, r['page'], r['client'], 'after', None))
                except Exception as e:
                    v = {'error': 'visit failed: ' + harness.scrub(str(e).splitlines()[0])[:150]}
                f.write(json.dumps({**r, 'B': v}) + '\n')
                f.flush()
        await asyncio.gather(*(one(r) for r in rows if r['idx'] not in done))
        await browser.close()

asyncio.run(main())
