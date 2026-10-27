"""Static web version of the portfolio, generated from the same source as the PDF (build_outline.py).

Desktop / landscape  →  the book itself: every 16:10 page scaled to the viewport, vertical scroll with snap.
Phone / portrait     →  the same content reflowed: photo, then horizontal text.
"""
import re, shutil, pathlib, subprocess, html as _html
from PIL import Image
import build_outline as B

ROOT = pathlib.Path(__file__).parent
WEB = ROOT / "web"
PAPER = "#f3efe6"
PDF_SRC = ROOT / "out" / "Starlia_final.pdf"
C = B.C
PDF_NAME = C["site"]["pdf_name"]
DOMAIN = C["site"]["domain"]

shutil.rmtree(WEB, ignore_errors=True)
(WEB / "img").mkdir(parents=True)
(WEB / "fonts").mkdir()

# ---------------------------------------------------------------- images
_done = {}
def web_img(src, max_side=2000, q=86):
    """copy an image into web/img (JPEG unless it has alpha), downscaled for the web; returns the new relative path"""
    src = str(src)
    if src in _done: return _done[src]
    im = Image.open(ROOT / src)
    name = pathlib.Path(src).stem
    if im.mode in ("RGBA", "LA") and im.getextrema()[-1][0] < 255:
        out = f"img/{name}.png"; im.save(WEB / out, optimize=True)
    else:
        im = im.convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
        out = f"img/{name}.jpg"; im.save(WEB / out, quality=q, optimize=True, progressive=True)
    _done[src] = out
    return out

# ---------------------------------------------------------------- book (desktop)
book_pages = []
for i, p in enumerate(B.pages):
    h = B.render(i, p)
    h = re.sub(r'url\((img/[^)]+)\)', lambda m: f'url({web_img(m.group(1))})', h)
    h = re.sub(r'src="(img/[^"]+)"', lambda m: f'src="{web_img(m.group(1))}"', h)
    book_pages.append(f'<div class="sheet">{h}</div>')
book = "\n".join(book_pages)

# ---------------------------------------------------------------- flow (phone)
def esc(t): return t
def flow_section(i, p):
    kind, title, sub, paras, image, folio, ph = p[:7]
    url = B.URL.get((folio or "")[:2])
    if kind == "cover":
        return f'''<section class="f-cover">
  <img src="{web_img(B.IMG["cover"], 1600)}" alt="">
  <div class="f-ct"><div class="f-title cjk"><div style="margin-right:-.38em">{C["cover"]["name"]}</div><div class="x">×</div><div class="lat" style="letter-spacing:.3em;margin-right:-.3em">{C["cover"]["brand"]}</div></div>
  <div class="f-subtitle cjk">{C["cover"]["subtitle"]}</div></div>
</section>'''
    if kind == "brand":
        cells = "".join(f'<div class="f-cell"><div class="lat f-small">{en}</div><div class="cjk f-cellh">{z}</div><div class="cjk f-body">{B.zh(txt)}</div></div>' for en, z, txt in B.brand)
        return f'''<section class="f-sec f-brand">
  <div class="lat f-h" style="letter-spacing:.3em">{C["brand"]["title"]}</div>
  <div class="cjk f-tag">{"<br>".join(B.zh(x) for x in C["brand"]["statement"])}</div>
  <div class="f-rule"></div>
  <div class="f-cells">{cells}</div>
</section>'''
    if kind == "sanmi":
        d = B._special[i]; br = lambda t: B.zh(t).replace("，", "，<br>", 1)      # phone: break after the first comma
        lines = "\n".join(f'  <div class="cjk f-line">{br(x)}</div>' for x in d["lines"])
        return f'''<section class="f-sec f-sanmi">
{lines}
  <div class="f-rule" style="margin:34px auto"></div>
  <div class="cjk f-line f-strong">{br(d["closing"])}</div>
</section>'''
    if kind == "zen":
        d = B._special[i]
        ps = "\n".join(f'    <p>{B.zh(x)}</p>' for x in d["body"])
        return f'''<section class="f-sec f-zen">
  <div class="cjk f-h" style="text-align:center;letter-spacing:.3em">{B.zh(d["title"]).replace("，", "，<br>", 1)}</div>
  <div class="lat f-small" style="text-align:center;margin-top:14px">{d["sub"].replace(" · ", " &nbsp;·&nbsp; ")}</div>
  <div class="f-rule" style="margin:34px auto"></div>
  <div class="cjk f-body" style="text-align:center">
{ps}
  </div>
</section>'''
    if kind == "contact":
        A = 'style="color:inherit;text-decoration:none"'; K = C["contact"]
        return f'''<section class="f-sec f-contact">
  <img class="f-logo" src="{web_img("img/logo.png")}" alt="Starlia">
  <div class="f-rule" style="margin:36px auto"></div>
  <div class="f-ccol"><div class="lat f-small">WeChat</div><div class="cjk f-cval">{K["wechat"]}</div></div>
  <div class="f-ccol"><div class="lat f-small">Web</div><div class="cjk f-cval">{"<br>".join(f'<a href="https://{u}" {A}>{u}</a>' for u in K["web"])}</div></div>
  <div class="f-ccol"><div class="lat f-small">Email</div><div class="cjk f-cval"><a href="mailto:{K["email"]}" {A}>{K["email"]}</a></div></div>
  <div class="f-ccol"><div class="lat f-small">PDF</div><div class="cjk f-cval"><a href="{PDF_NAME}" download {A}>下载本书 ↓</a></div></div>
  <div class="cjk f-end">{K["closing"]}</div>
</section>'''
    # ordinary section
    imgs = []
    if isinstance(image, (list, tuple)):
        imgs = [B.IMG[x] for x in image]
    elif image:
        imgs = [B.IMG[{"rose_top10": "rose"}.get(image, image)]]   # phone shows the uncropped rose
    pics = "".join(f'<img src="{web_img(s, 1600)}" alt="">' for s in imgs)
    has_tag = p[10] if len(p) > 10 else False
    tagline, rest = (paras[0], paras[1:]) if has_tag else (None, paras)
    def _p(t):
        if isinstance(t, tuple) and t[0] == "quote":
            return f'<p class="f-quote">{B.zh(t[1])}</p>'
        if isinstance(t, tuple):
            return f'<p><span class="f-label">{t[0]}</span>{B.zh(t[1])}</p>'
        return f"<p>{B.zh(t)}</p>"
    body = "".join(_p(t) for t in rest)
    tag = f'<div class="cjk f-tag">{tagline}</div>' if tagline else ""
    head = f'<div class="cjk f-h">{title}</div><div class="lat f-small">{sub}</div>'
    if url: head = f'<a href="https://{url}" style="color:inherit;text-decoration:none;display:block">{head}</a>'
    link = f'<div class="f-url lat"><a href="https://{url}">{url}</a></div>' if url else ""
    return f'''<section class="f-sec">
  <div class="f-pics">{pics}</div>
  <div class="f-text">{head}{tag}<div class="f-rule"></div><div class="cjk f-body">{body}</div>{link}</div>
</section>'''

flow = "\n".join(flow_section(i, p) for i, p in enumerate(B.pages))

# ---------------------------------------------------------------- fonts: subset Noto Serif CJK SC to the characters actually used
text = re.sub(r"<[^>]+>", "", book + flow)
text = _html.unescape(text)
chars = set(text) | set(chr(c) for c in range(0x20, 0x7f)) | set("×·「」，。；：、！？（）〇一二三四五六七八九十  ")
(WEB / "fonts" / "chars.txt").write_text("".join(sorted(chars)), encoding="utf8")
FONTS = {200: "ExtraLight", 300: "Light", 400: "Regular"}
from fontTools.ttLib import TTCollection
def _sc_index(ttc):
    for k, f in enumerate(TTCollection(ttc, lazy=True).fonts):
        if f["name"].getDebugName(1).startswith("Noto Serif CJK SC"): return k
    raise SystemExit(f"Noto Serif CJK SC not found in {ttc}")
for w, name in FONTS.items():
    ttc = f"/usr/share/fonts/opentype/noto/NotoSerifCJK-{name}.ttc"
    subprocess.run(["pyftsubset", ttc, f"--font-number={_sc_index(ttc)}",
                    f"--text-file={WEB/'fonts'/'chars.txt'}", "--flavor=woff2", "--layout-features=*", "--no-hinting",
                    f"--output-file={WEB/'fonts'/f'NotoSerifSC-{w}.woff2'}"], check=True)
faces = "\n".join(f'@font-face{{font-family:"Noto Serif CJK SC";font-weight:{w};font-display:swap;src:url(fonts/NotoSerifSC-{w}.woff2) format("woff2")}}' for w in FONTS)

# ---------------------------------------------------------------- page
base_css = (ROOT / "base.css").read_text(encoding="utf8").replace("html,body{background:#888}", "")
book_css = B.CSS
site_css = f"""
html{{background:{PAPER};color:#2b2925;-webkit-text-size-adjust:100%}}
body{{background:{PAPER};margin:0}}
a{{color:inherit;text-decoration:none}}
/* ---- book ---- */
.book{{display:none}}
.sheet{{width:calc(1600px*var(--s));height:calc(1000px*var(--s));margin:0 auto;position:relative;overflow:hidden;scroll-snap-align:start}}
.sheet .page{{transform:scale(var(--s));transform-origin:0 0;margin:0}}
.pdf{{position:fixed;right:22px;bottom:22px;writing-mode:vertical-rl;text-orientation:mixed;font-size:12px;letter-spacing:.35em;color:#6b665c;text-transform:uppercase;text-decoration:none;z-index:9;display:none}}
.pdf .lt{{position:relative;left:.11em}}
/* ---- flow ---- */
.flow{{display:block;max-width:640px;margin:0 auto}}
.flow .lt{{position:static;left:0}}   /* the vertical-text nudge must not apply to horizontal text */
.f-cover img,.f-pics img{{display:block;width:100%;height:auto}}
.f-ct{{padding:56px 28px 40px;text-align:center}}
.f-title{{font-size:30px;font-weight:300;letter-spacing:.38em;line-height:1;display:flex;flex-direction:column;align-items:center;gap:22px}}
.f-title .x{{color:#8a8577;font-size:.9em;letter-spacing:0}}
.f-subtitle{{font-size:14px;letter-spacing:.45em;font-weight:300;color:#4a463f;margin-top:22px;padding-left:.45em}}
.f-sec{{padding:0 0 64px}}
.f-text{{padding:40px 28px 0}}
.f-h{{font-size:26px;letter-spacing:.3em;font-weight:300;line-height:1.4}}
.f-small{{font-size:11px;letter-spacing:.35em;text-transform:uppercase;color:#6b665c;margin-top:10px}}
.f-tag{{font-size:17px;letter-spacing:.12em;font-weight:400;line-height:1.9;margin-top:30px}}
.f-rule{{width:40px;height:1px;background:#2b2925;opacity:.35;margin:30px 0}}
.f-body{{font-size:15px;line-height:2.2;letter-spacing:.06em;color:#4a463f;font-weight:300}}
.f-body p{{margin:0 0 1.2em}}
.f-body p.f-quote{{margin-top:1.8em}}
.f-label{{font-weight:400;color:#2b2925}}
.f-body a{{text-decoration:none;border-bottom:1px solid rgba(43,41,37,.45);padding-bottom:2px}}
.f-url{{font-size:11px;letter-spacing:.3em;color:#6b665c;margin-top:8px}}
.f-url a{{text-decoration:none;text-transform:none;letter-spacing:.2em}}
.f-brand{{padding:72px 28px 40px}}
.f-cells{{margin-top:12px}}
.f-cell{{border-left:1px solid rgba(43,41,37,.3);padding-left:18px;margin:34px 0}}
.f-cellh{{font-size:19px;letter-spacing:.15em;margin:6px 0 8px}}
.f-sanmi{{padding:80px 28px}}
.f-line{{font-size:19px;letter-spacing:.2em;font-weight:300;line-height:1.9;text-align:center;margin-bottom:22px}}
.f-strong{{font-size:21px;font-weight:400}}
.f-zen{{padding:80px 28px}}
.f-contact{{padding:96px 28px 80px;text-align:center}}
.f-logo{{width:150px;display:block;margin:0 auto}}
.f-ccol{{margin:28px 0}}
.f-cval{{font-size:15px;line-height:2;letter-spacing:.1em;color:#4a463f;font-weight:300;margin-top:4px}}
.f-cval a{{text-decoration:none}}
.f-end{{font-size:12px;letter-spacing:.5em;color:#8a8577;font-weight:300;margin-top:64px}}
@media (min-width:900px) and (min-height:560px){{
  html{{scroll-snap-type:y proximity}}
  .book,.pdf{{display:block}} .flow{{display:none}}
}}
"""
index = f'''<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{C["cover"]["name"]} × {C["brand"]["title"]}</title>
<meta name="description" content="{C["site"]["description"]}">
<style>
{faces}
{base_css}
{book_css}
{site_css}
</style>
</head>
<body>
<div class="book">
{book}
</div>
<a class="pdf" href="{PDF_NAME}" download><span class="lt">PDF ↓</span></a>
<div class="flow">
{flow}
</div>
<script>
(function(){{
  var r=document.documentElement;
  function fit(){{ r.style.setProperty('--s', Math.min(innerWidth/1600, innerHeight/1000)); }}
  fit(); addEventListener('resize', fit); addEventListener('orientationchange', fit);
}})();
</script>
</body>
</html>
'''
(WEB / "index.html").write_text(index, encoding="utf8")
(WEB / "CNAME").write_text(DOMAIN + "\n")
(WEB / ".nojekyll").write_text("")

# artifact preview variant: no document skeleton (the host adds one), PDF opens in a new tab instead of downloading
art = f'''<title>玄光 × Starlia</title>
<style>
{faces}
{base_css}
{book_css}
{site_css}
</style>
<div class="book">
{book}
</div>
<a class="pdf" href="{PDF_NAME}" target="_blank" rel="noopener"><span class="lt">PDF ↓</span></a>
<div class="flow">
{flow.replace(f'href="{PDF_NAME}" download', f'href="{PDF_NAME}" target="_blank" rel="noopener"')}
</div>
<script>
(function(){{
  var r=document.documentElement;
  function fit(){{ r.style.setProperty('--s', Math.min(innerWidth/1600, innerHeight/1000)); }}
  fit(); addEventListener('resize', fit); addEventListener('orientationchange', fit);
}})();
</script>
'''
(WEB / "artifact.html").write_text(art, encoding="utf8")
shutil.copy(PDF_SRC, WEB / PDF_NAME)
tot = sum(f.stat().st_size for f in WEB.rglob("*") if f.is_file())
print("web/ built:", len(book_pages), "pages;", f"{tot/1e6:.1f} MB total;",
      "fonts:", [f"{f.name} {f.stat().st_size//1000}k" for f in (WEB/'fonts').glob('*.woff2')])
