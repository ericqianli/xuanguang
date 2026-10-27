import sys
from playwright.sync_api import sync_playwright
src, out = sys.argv[1], sys.argv[2]
import pathlib; pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1600,"height":1000})
    import pathlib; pg.goto(pathlib.Path(src).resolve().as_uri()); pg.wait_for_timeout(800)
    pg.add_style_tag(content="html,body{background:#f3efe6}.page{margin:0;page-break-after:always}@page{size:1600px 1000px;margin:0}")
    pg.pdf(path=out,width='1600px',height='1000px',print_background=True,prefer_css_page_size=True)
    b.close()
print(out)
