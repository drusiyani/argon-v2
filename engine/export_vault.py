import os,json,asyncio
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        await pg.goto('file://'+os.path.join(ROOT,'docs','lab.html')); await pg.wait_for_timeout(2500)
        files=await pg.evaluate("window.__exportFiles()")
        for f in files:
            path=os.path.join(ROOT,'vault',f['path']); os.makedirs(os.path.dirname(path),exist_ok=True)
            open(path,'w').write(f['content'])
        print('vault notes',len(files)); await b.close()
asyncio.run(main())
