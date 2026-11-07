# Screenshot the first <video>'s area in plain Chrome (A) and with emulation (B), side by side.
# Usage: CHANGE_VARIANT=B2 python3 player_shot.py CHROME URL OUT.png
import asyncio, sys
from playwright.async_api import async_playwright
from PIL import Image
import change


async def shot(br, url, js, path, clip):
    ctx = await br.new_context(viewport={'width': 360, 'height': 640}, device_scale_factor=2, is_mobile=True, has_touch=True)
    if js:
        await ctx.add_init_script(js)
    pg = await ctx.new_page()
    await pg.goto(url, wait_until='load', timeout=30000)
    for _ in range(4):
        await pg.mouse.wheel(0, 600)
        await pg.wait_for_timeout(1500)
    box = clip or await pg.evaluate("""() => { const v = document.querySelector('video'); if (!v) return null;
      const c = v.closest('div') || v; const r = c.getBoundingClientRect();
      return {x: 0, y: Math.max(0, r.top + scrollY - 150), width: 360, height: Math.max(r.height, 200) + 300}; }""")
    await pg.screenshot(path=path, full_page=True, clip=box)
    await ctx.close()
    return box


async def main():
    exe, url, out = sys.argv[1:4]
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=exe)
        box = await shot(br, url, None, out + '.A.png', None)
        print('video box', box)
        await shot(br, url, change.AFTER_INIT_JS, out + '.B.png', box)
        await br.close()
    a, b = Image.open(out + '.A.png'), Image.open(out + '.B.png')
    im = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), 'red')
    im.paste(a, (0, 0)); im.paste(b, (a.width + 12, 0))
    im.thumbnail((1000, 1000)); im.save(out)

asyncio.run(main())
