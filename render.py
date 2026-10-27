import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).parent
out = root / "out"; out.mkdir(exist_ok=True)
files = sys.argv[1:] or ["A_留白.html", "B_墨.html", "C_晨.html"]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    for f in files:
        pg.goto((root / f).as_uri()); pg.wait_for_timeout(600)
        pages = pg.locator(".page")
        n = pages.count(); shots = []
        for i in range(n):
            path = out / f"{f[:-5]}_p{i+1}.png"
            pages.nth(i).screenshot(path=str(path)); shots.append(Image.open(path))
        # stitch vertically
        gap = 40
        H = sum(s.height for s in shots) + gap * (n - 1)
        sheet = Image.new("RGB", (1600, H), "#9a9a9a")
        y = 0
        for s in shots:
            sheet.paste(s, (0, y)); y += s.height + gap
        sheet = sheet.resize((1200, int(H * 1200 / 1600)), Image.LANCZOS)
        sheet.save(out / f"{f[:-5]}.png", optimize=True)
        print(f, n, "pages")
    b.close()
