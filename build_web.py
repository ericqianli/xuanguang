"""Static web version of the portfolio, generated from the same sources as the PDFs.

  web/index.html      中文   (build_outline.py + content.yaml)
  web/en/index.html   English (build_en.py + content_en.yaml)
  web/*.pdf           both books, side by side; each site's corner link downloads its own edition

Desktop / landscape  →  the book itself: every 16:10 page scaled to the viewport, vertical scroll with snap.
Phone / portrait     →  the same content reflowed: photo, then horizontal text.
"""
import re, shutil, pathlib, subprocess, html as _html
from PIL import Image
import build_outline as B
import build_en as E

ROOT = pathlib.Path(__file__).parent
WEB = ROOT / "web"
PAPER = "#f3efe6"

shutil.rmtree(WEB, ignore_errors=True)
(WEB / "img").mkdir(parents=True)
(WEB / "fonts").mkdir()
(WEB / "en").mkdir()

# ---------------------------------------------------------------- images
_done = {}
def web_img(src, max_side=2000, q=86):
    """copy an image into web/img (JPEG unless it has alpha), downscaled for the web; returns the site-relative path"""
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

def relink(h):
    return re.sub(r'src="(img/[^"]+)"', lambda m: f'src="{web_img(m.group(1))}"',
           re.sub(r'url\((img/[^)]+)\)', lambda m: f'url({web_img(m.group(1))})', h))

# ---------------------------------------------------------------- the two editions
IDENT = lambda t: t
EDITIONS = {
    "zh": dict(C=B.C, lang="zh-Hans", axis="v", prefix="",    book=[B.render(i, p) for i, p in enumerate(B.pages)],
               pages=B.pages, special=B._special, conv=B.zh, brk=lambda t: B.zh(t).replace("，", "，<br>", 1),
               pdf_src=ROOT / "out" / "Starlia_final.pdf",    pdf_label="下载本书 ↓",
               other=("EN", "en/"), cur="中"),
    "en": dict(C=E.C, lang="en",      axis="h", prefix="../", book=E.pages,
               pages=[("cover", None, None, None, "cover", None, None), ("brand", None, None, None, None, E.C["brand"]["title"], None)]
                     + [B._page(d) for d in E.C["pages"]] + [("contact", None, None, None, None, "", None)],
               special={i + 2: d for i, d in enumerate(E.C["pages"]) if d.get("kind")}, conv=IDENT, brk=IDENT,
               pdf_src=ROOT / "out" / "Starlia_final_EN.pdf", pdf_label="Download the PDF ↓",
               other=("中", "../"), cur="EN"),
}

# ---------------------------------------------------------------- flow (phone)
def flow_section(i, p, ed):
    C, conv, brk, PDF_NAME = ed["C"], ed["conv"], ed["brk"], ed["C"]["site"]["pdf_name"]
    URL = {str(k): v for k, v in C["urls"].items()}
    kind, title, sub, paras, image, folio, ph = p[:7]
    url = URL.get((folio or "")[:2])
    if kind == "cover":
        return f'''<section class="f-cover">
  <img src="{web_img(B.IMG["cover"], 1600)}" alt="">
  <div class="f-ct"><div class="f-title cjk"><div style="margin-right:-.38em">{C["cover"]["name"]}</div><div class="x">×</div><div class="lat" style="letter-spacing:.3em;margin-right:-.3em">{C["cover"]["brand"]}</div></div>
  <div class="f-subtitle cjk">{C["cover"]["subtitle"]}</div></div>
</section>'''
    if kind == "brand":
        cells = "".join(f'<div class="f-cell"><div class="lat f-small">{it["en"]}</div><div class="cjk f-cellh">{it["zh"]}</div><div class="cjk f-body">{conv(it["text"])}</div></div>' for it in C["brand"]["items"])
        return f'''<section class="f-sec f-brand">
  <div class="lat f-h" style="letter-spacing:.3em">{C["brand"]["title"]}</div>
  <div class="cjk f-tag">{"<br>".join(conv(x) for x in C["brand"]["statement"])}</div>
  <div class="f-rule"></div>
  <div class="f-cells">{cells}</div>
</section>'''
    if kind == "sanmi":
        d = ed["special"][i]
        lines = "\n".join(f'  <div class="cjk f-line">{brk(x)}</div>' for x in d["lines"])
        return f'''<section class="f-sec f-sanmi">
{lines}
  <div class="f-rule" style="margin:34px auto"></div>
  <div class="cjk f-line f-strong">{brk(d["closing"])}</div>
</section>'''
    if kind == "zen":
        d = ed["special"][i]
        ps = "\n".join(f'    <p>{conv(x)}</p>' for x in d["body"])
        return f'''<section class="f-sec f-zen">
  <div class="cjk f-h" style="text-align:center;letter-spacing:{".3em" if ed["axis"] == "v" else ".02em"}">{brk(d["title"])}</div>
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
  <div class="f-ccol"><div class="lat f-small">PDF</div><div class="cjk f-cval"><a href="{ed["prefix"]}{PDF_NAME}" download {A}>{ed["pdf_label"]}</a></div></div>
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
            return f'<p class="f-quote">{conv(t[1])}</p>'
        if isinstance(t, tuple):
            return f'<p><span class="f-label">{t[0]}</span>{conv(t[1])}</p>'
        return f"<p>{conv(t)}</p>"
    body = "".join(_p(t) for t in rest)
    tag = f'<div class="cjk f-tag">{tagline}</div>' if tagline else ""
    head = f'<div class="cjk f-h">{title}</div><div class="lat f-small">{sub}</div>'
    if url: head = f'<a href="https://{url}" style="color:inherit;text-decoration:none;display:block">{head}</a>'
    link = f'<div class="f-url lat"><a href="https://{url}">{url}</a></div>' if url else ""
    return f'''<section class="f-sec">
  <div class="f-pics">{pics}</div>
  <div class="f-text">{head}{tag}<div class="f-rule"></div><div class="cjk f-body">{body}</div>{link}</div>
</section>'''

for ed in EDITIONS.values():
    ed["book_html"] = "\n".join(f'<div class="sheet">{relink(h)}</div>' for h in ed["book"])
    ed["flow_html"] = "\n".join(flow_section(i, p, ed) for i, p in enumerate(ed["pages"]))

# ---------------------------------------------------------------- fonts: one subset of Noto Serif CJK SC covering both editions
text = _html.unescape(re.sub(r"<[^>]+>", "", "".join(ed["book_html"] + ed["flow_html"] for ed in EDITIONS.values())))
chars = set(text) | set(chr(c) for c in range(0x20, 0x7f)) | set("×·「」，。；：、！？（）〇一二三四五六七八九十  “”‘’—–…")
(WEB / "fonts" / "chars.txt").write_text("".join(sorted(chars)), encoding="utf8")
FONTS = {200: "ExtraLight", 300: "Light", 400: "Regular"}
from fontTools.ttLib import TTCollection
def font_source(name):
    """(file, font-number) for one weight of Noto Serif CJK SC: the repo's own OTF (fonts/ or ~/.local/share/fonts,
    from the `fonts` branch) first, else the system TTC with the SC face index."""
    for d in (ROOT / "fonts", pathlib.Path.home() / ".local/share/fonts", pathlib.Path("/usr/share/fonts/opentype/noto")):
        f = d / f"NotoSerifCJKsc-{name}.otf"
        if f.exists(): return str(f), None
    ttc = pathlib.Path(f"/usr/share/fonts/opentype/noto/NotoSerifCJK-{name}.ttc")
    if ttc.exists():
        for k, f in enumerate(TTCollection(str(ttc), lazy=True).fonts):
            if f["name"].getDebugName(1).startswith("Noto Serif CJK SC"): return str(ttc), k
    raise SystemExit(f"Noto Serif CJK SC {name} not found (looked in fonts/, ~/.local/share/fonts, system noto dir)")
for w, name in FONTS.items():
    src, num = font_source(name)
    subprocess.run(["pyftsubset", src] + ([f"--font-number={num}"] if num is not None else []) +
                   [f"--text-file={WEB/'fonts'/'chars.txt'}", "--flavor=woff2", "--layout-features=*", "--no-hinting",
                    f"--output-file={WEB/'fonts'/f'NotoSerifSC-{w}.woff2'}"], check=True)

# ---------------------------------------------------------------- page
base_css = (ROOT / "base.css").read_text(encoding="utf8").replace("html,body{background:#888}", "")
site_css = f"""
html{{background:{PAPER};color:#2b2925;-webkit-text-size-adjust:100%}}
body{{background:{PAPER};margin:0}}
a{{color:inherit;text-decoration:none}}
/* ---- book ---- */
.book{{display:none}}
.sheet{{width:calc(1600px*var(--s));height:calc(1000px*var(--s));margin:0 auto;position:relative;overflow:hidden;scroll-snap-align:start}}
.sheet .page{{transform:scale(var(--s));transform-origin:0 0;margin:0}}
/* ---- corner labels: vertical column on the Chinese site, horizontal row on the English site ---- */
.pdf{{position:fixed;right:22px;bottom:22px;color:#6b665c;text-decoration:none;z-index:9;display:none;flex-direction:column;align-items:center;gap:10px}}
.pdf-t{{writing-mode:vertical-rl;text-orientation:mixed;font-size:12px;letter-spacing:.35em;text-transform:uppercase;margin-bottom:-.35em;position:relative;left:.11em}}   /* same cap-height nudge as every rotated Latin run in the book */
.pdf-a{{display:block}}
.pdf-t,.lang a,.lang .sys{{font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif}}   /* the five Latin letters of the corners in the plain system sans */
.lang{{position:fixed;right:22px;top:22px;z-index:9;display:none;flex-direction:column;align-items:center;gap:8px;font-size:12px;letter-spacing:.35em;text-transform:uppercase}}
.lang .cur{{writing-mode:vertical-rl;text-orientation:upright;color:#2b2925;margin-bottom:-.35em}}
.lang .sep{{width:12px;height:1px;background:rgba(43,41,37,.3)}}
.lang a{{writing-mode:vertical-rl;text-orientation:mixed;color:#6b665c;text-decoration:none;margin-bottom:-.35em;transition:color .2s}}
.lang a .lt{{position:relative;left:.11em}}
.lang a:hover{{color:#2b2925}}
/* horizontal variants (English site) */
.axis-h .pdf{{flex-direction:row;gap:9px}}
.axis-h .pdf-t{{writing-mode:horizontal-tb;margin-bottom:0;margin-right:-.35em;left:0}}
.axis-h .lang{{flex-direction:row;gap:8px}}
.axis-h .lang .cur,.axis-h .lang a{{writing-mode:horizontal-tb;margin-bottom:0;margin-right:-.35em}}
.axis-h .lang .cur{{text-orientation:initial}}
.axis-h .lang .sep{{width:1px;height:12px}}
.axis-h .lang a .lt{{left:0}}
/* ---- flow ---- */
.flow{{display:block;max-width:640px;margin:0 auto}}
.flow .lt{{position:static;left:0}}   /* the vertical-text nudge must not apply to horizontal text */
.f-cover img,.f-pics img{{display:block;width:100%;height:auto}}
.f-ct{{padding:56px 28px 40px;text-align:center}}
.f-title{{font-size:30px;font-weight:300;letter-spacing:.38em;line-height:1;display:flex;flex-direction:column;align-items:center;gap:22px}}
.axis-h .f-title{{text-transform:uppercase;font-size:26px;letter-spacing:.3em}}
.axis-h .flow{{font-feature-settings:"pwid"}}   /* proportional Latin punctuation (curly quotes, apostrophes) in the CJK serif */
.f-title .x{{color:#8a8577;font-size:.9em;letter-spacing:0}}
.f-subtitle{{font-size:14px;letter-spacing:.45em;font-weight:300;color:#4a463f;margin-top:22px;padding-left:.45em}}
.axis-h .f-subtitle{{font-size:12px;letter-spacing:.3em;text-transform:uppercase;padding-left:.3em}}
.f-sec{{padding:0 0 64px}}
.f-text{{padding:40px 28px 0}}
.f-h{{font-size:26px;letter-spacing:.3em;font-weight:300;line-height:1.4}}
.axis-h .f-h{{letter-spacing:.03em;line-height:1.3}}
.f-small{{font-size:11px;letter-spacing:.35em;text-transform:uppercase;color:#6b665c;margin-top:10px}}
.f-tag{{font-size:17px;letter-spacing:.12em;font-weight:400;line-height:1.9;margin-top:30px}}
.axis-h .f-tag{{letter-spacing:0;line-height:1.7}}
.f-rule{{width:40px;height:1px;background:#2b2925;opacity:.35;margin:30px 0}}
.f-body{{font-size:15px;line-height:2.2;letter-spacing:.06em;color:#4a463f;font-weight:300}}
.axis-h .f-body{{font-size:16px;line-height:1.85;letter-spacing:0;color:#403c36}}
.f-body p{{margin:0 0 1.2em}}
.f-body p.f-quote{{margin-top:1.8em}}
.axis-h .f-body p.f-quote{{padding-left:16px;border-left:1px solid rgba(43,41,37,.25)}}
.f-label{{font-weight:400;color:#2b2925}}
.f-body a{{text-decoration:none;border-bottom:1px solid rgba(43,41,37,.45);padding-bottom:2px}}
.f-url{{font-size:11px;letter-spacing:.3em;color:#6b665c;margin-top:8px}}
.f-url a{{text-decoration:none;text-transform:none;letter-spacing:.2em}}
.f-brand{{padding:72px 28px 40px}}
.f-cells{{margin-top:12px}}
.f-cell{{border-left:1px solid rgba(43,41,37,.3);padding-left:18px;margin:34px 0}}
.f-cellh{{font-size:19px;letter-spacing:.15em;margin:6px 0 8px}}
.axis-h .f-cellh{{letter-spacing:.02em}}
.f-sanmi{{padding:80px 28px}}
.f-line{{font-size:19px;letter-spacing:.2em;font-weight:300;line-height:1.9;text-align:center;margin-bottom:22px}}
.axis-h .f-line{{letter-spacing:.02em;line-height:1.6}}
.f-strong{{font-size:21px;font-weight:400}}
.f-zen{{padding:80px 28px}}
.f-contact{{padding:96px 28px 80px;text-align:center}}
.f-logo{{width:150px;display:block;margin:0 auto}}
.f-ccol{{margin:28px 0}}
.f-cval{{font-size:15px;line-height:2;letter-spacing:.1em;color:#4a463f;font-weight:300;margin-top:4px}}
.f-cval a{{text-decoration:none}}
.f-end{{font-size:12px;letter-spacing:.5em;color:#8a8577;font-weight:300;margin-top:64px}}
.axis-h .f-end{{letter-spacing:.3em;text-transform:uppercase;font-size:11px}}
@media (min-width:900px) and (min-height:560px){{
  html{{scroll-snap-type:y proximity}}
  .book{{display:block}} .pdf,.lang{{display:flex}} .flow{{display:none}}
}}
"""
FIT_JS = '''<script>
(function(){
  var r=document.documentElement;
  function fit(){ r.style.setProperty('--s', Math.min(innerWidth/1600, innerHeight/1000)); }
  fit(); addEventListener('resize', fit); addEventListener('orientationchange', fit);
})();
</script>'''

def corners(ed, preview=False):
    C = ed["C"]; PDF_NAME = C["site"]["pdf_name"]; oth, ohref = ed["other"]
    pdf_attr = ' target="_blank" rel="noopener"' if preview else " download"
    oth_html = f'<span class="lt">{oth}</span>' if oth.isascii() else oth
    return (f'<div class="lang cjk"><span class="cur{" sys" if ed["cur"].isascii() else ""}">{ed["cur"]}</span><span class="sep"></span><a class="lat" href="{ohref}">{oth_html}</a></div>\n'
            f'<a class="pdf lat" href="{ed["prefix"]}{PDF_NAME}"{pdf_attr}><span class="pdf-t">PDF</span><svg class="pdf-a" viewBox="0 0 10 14" width="8" height="11" aria-hidden="true"><path d="M5 0.5v12M1 9l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1"/></svg></a>')

def page(ed, preview=False):
    C = ed["C"]; P = ed["prefix"]
    faces = "\n".join(f'@font-face{{font-family:"Noto Serif CJK SC";font-weight:{w};font-display:swap;src:url({P}fonts/NotoSerifSC-{w}.woff2) format("woff2")}}' for w in FONTS)
    book = ed["book_html"]; flow = ed["flow_html"]
    if preview: flow = flow.replace(f'{P}{C["site"]["pdf_name"]}" download', f'{P}{C["site"]["pdf_name"]}" target="_blank" rel="noopener"')
    if P:   # the English site lives in en/: shared images sit one level up
        book = book.replace("url(img/", f"url({P}img/").replace('src="img/', f'src="{P}img/'); flow = flow.replace('src="img/', f'src="{P}img/')
    style = f"<style>\n{faces}\n{base_css}\n{B.CSS}\n{E.CSS_EN if ed['axis'] == 'h' else ''}\n{site_css}\n</style>"
    body = f'<div class="book">\n{book}\n</div>\n{corners(ed, preview)}\n<div class="flow">\n{flow}\n</div>\n{FIT_JS}'
    title = f'{C["cover"]["name"]} × {C["brand"]["title"]}'
    if preview:
        return f"<title>{title}</title>\n{style}\n{body}\n"
    return f'''<!doctype html>
<html lang="{ed["lang"]}" class="axis-{ed["axis"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{C["site"]["description"]}">
<link rel="alternate" hreflang="{"en" if ed["axis"] == "v" else "zh-Hans"}" href="{ed["other"][1]}">
{style}
</head>
<body>
{body}
</body>
</html>
'''

(WEB / "index.html").write_text(page(EDITIONS["zh"]), encoding="utf8")
(WEB / "en" / "index.html").write_text(page(EDITIONS["en"]), encoding="utf8")
(WEB / "artifact.html").write_text(page(EDITIONS["zh"], preview=True), encoding="utf8")
for ed in EDITIONS.values():
    shutil.copy(ed["pdf_src"], WEB / ed["C"]["site"]["pdf_name"])
DOMAIN = B.C["site"]["domain"]
if DOMAIN: (WEB / "CNAME").write_text(DOMAIN + "\n")      # leave site.domain empty to publish at ericqianli.github.io/xuanguang/
(WEB / ".nojekyll").write_text("")
tot = sum(f.stat().st_size for f in WEB.rglob("*") if f.is_file())
print("web/ built: zh + en;", f"{tot/1e6:.1f} MB total;", "fonts:", [f"{f.name} {f.stat().st_size//1000}k" for f in (WEB/'fonts').glob('*.woff2')])
