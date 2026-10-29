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
  <div class="f-ct"><div class="f-title cjk"><div style="margin-right:-.38em">{C["cover"]["name"]}</div><div class="x" style="font-size:{C["cover"].get("mark_size", ".9em")};color:{C["cover"].get("mark_color", "#8a8577")}">{C["cover"].get("mark", "×")}</div><div class="lat" style="letter-spacing:.3em;margin-right:-.3em">{C["cover"]["brand"]}</div></div>
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
chars = set(text) | set(chr(c) for c in range(0x20, 0x7f)) | set("×●•·「」，。；：、！？（）〇一二三四五六七八九十  “”‘’—–…")
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
/* ---- corner labels (language toggle top-right, PDF bottom-right): drawn as SVG by the script below ---- */
.corner{{position:fixed;right:22px;z-index:9;display:none;color:#6b665c;font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif}}
.corner.top{{top:22px}} .corner.bottom{{bottom:22px}}
.corner a{{color:#6b665c;transition:color .2s}} .corner a:hover{{color:#2b2925}}
.corner .cur{{color:#2b2925}}
/* ---- flow ---- */
.flow{{display:block;max-width:640px;margin:0 auto}}
.flow .lt{{position:static;left:0}}   /* the vertical-text nudge must not apply to horizontal text */
.f-cover img,.f-pics img{{display:block;width:100%;height:auto}}
.f-ct{{padding:56px 28px 40px;text-align:center}}
.f-title{{font-size:30px;font-weight:300;letter-spacing:.38em;line-height:1;display:flex;flex-direction:column;align-items:center;gap:22px}}
.f-title .x{{line-height:.6}}   /* the mark's own box is small so the gaps around it stay even */
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
  .book{{display:block}} .corner{{display:block}} .flow{{display:none}}
}}
"""
FIT_JS = '''<script>
(function(){
  var r=document.documentElement;
  function fit(){ r.style.setProperty('--s', Math.min(innerWidth/1600, innerHeight/1000)); }
  fit(); addEventListener('resize', fit); addEventListener('orientationchange', fit);
})();
// Corner labels, drawn as SVG. Every glyph run is measured on a canvas (tight ink box) and placed so that its ink
// centre sits exactly on the column/row axis; runs are spaced by ink, not by font boxes. Independent of font, size
// and browser, so the labels stay centred and symmetric whatever the corners are set in.
(function(){
  var AXIS=document.documentElement.className.indexOf('axis-h')>=0?'h':'v', SIZE=12, NS='http://www.w3.org/2000/svg';
  var LS=(AXIS==='v'?0.35:0.2)*SIZE, W=16;                 // W: box width → axis 22+8 = 30px from the edge
  function go(){
    var cv=document.createElement('canvas').getContext('2d');
    document.querySelectorAll('.corner').forEach(function(box){
      var FONT=getComputedStyle(box).fontFamily; cv.font=SIZE+'px '+FONT;
      function ink(s){ var x=0,L=null,R=0,A=0,D=0; for(var ch of s){ var m=cv.measureText(ch);
          var l=x-m.actualBoundingBoxLeft, rr=x+m.actualBoundingBoxRight; if(L===null)L=l; R=rr;
          A=Math.max(A,m.actualBoundingBoxAscent); D=Math.max(D,m.actualBoundingBoxDescent); x+=m.width+LS; } return {L:L,R:R,A:A,D:D}; }
      function el(n,at){ var e=document.createElementNS(NS,n); for(var k in at) e.setAttribute(k,at[k]); return e; }
      var items=JSON.parse(box.dataset.items), svg=el('svg',{}), cur=0, c=W/2, nodes=[], pdf=box.classList.contains('bottom');
      var GAP = pdf ? (AXIS==='v'?10:6) : 9;
      items.forEach(function(it,i){
        if(i) cur+=GAP;
        var node;
        if(it.t){ var m=ink(it.t), cjk=/[\u3400-\u9fff]/.test(it.t), rot=(AXIS==='v' && !cjk);
          node=el('text',{'font-family':FONT,'font-size':SIZE,'letter-spacing':LS,fill:'currentColor'}); node.textContent=it.t;
          if(AXIS==='v'){
            if(rot){ node.setAttribute('transform','translate('+(c-(m.A-m.D)/2)+','+(cur-m.L)+') rotate(90)'); cur+=m.R-m.L; }
            else   { node.setAttribute('x',c-(m.L+m.R)/2); node.setAttribute('y',cur+m.A); cur+=m.A+m.D; }
          } else { node.setAttribute('x',cur-m.L); node.setAttribute('y',c+(m.A-m.D)/2); cur+=m.R-m.L; }
        } else if(it.sep){
          node = AXIS==='v' ? el('line',{x1:c-6,x2:c+6,y1:cur+.5,y2:cur+.5}) : el('line',{y1:c-6,y2:c+6,x1:cur+.5,x2:cur+.5});
          node.setAttribute('stroke','rgba(43,41,37,.3)'); cur+=1;
        } else if(it.arrow){
          node=el('path',{d:'M4 0.5v10M1 7.5l3 3 3-3',fill:'none',stroke:'currentColor','stroke-width':'1'});
          node.setAttribute('transform', AXIS==='v' ? 'translate('+(c-4)+','+cur+')' : 'translate('+cur+','+(c-5.5)+')'); cur+= AXIS==='v' ? 11 : 8;
        }
        if(it.href){ var a=el('a',{href:it.href}); if(it.dl) a.setAttribute('download',''); else if(!it.nav){a.setAttribute('target','_blank');a.setAttribute('rel','noopener');} a.appendChild(node); node=a; }
        if(it.cur) node.setAttribute('class','cur');
        nodes.push(node);
      });
      var len=Math.ceil(cur);
      svg.setAttribute('width', AXIS==='v'?W:len); svg.setAttribute('height', AXIS==='v'?len:W);
      svg.setAttribute('viewBox','0 0 '+(AXIS==='v'?W:len)+' '+(AXIS==='v'?len:W)); svg.style.display='block'; svg.style.overflow='visible';
      nodes.forEach(function(n){svg.appendChild(n);}); box.innerHTML=''; box.appendChild(svg);
    });
  }
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(go); else go();
})();
</script>'''

def corners(ed, preview=False):
    """data for the SVG corner renderer: current language · separator · other language (top); PDF · arrow (bottom)"""
    C = ed["C"]; PDF_NAME = C["site"]["pdf_name"]; oth, ohref = ed["other"]
    top = f'[{{"t":"{ed["cur"]}","cur":1}},{{"sep":1}},{{"t":"{oth}","href":"{ohref}","nav":1}}]'
    bottom = f'[{{"t":"PDF","href":"{ed["prefix"]}{PDF_NAME}"{"" if preview else ",\"dl\":1"}}},{{"arrow":1}}]'
    return f"<div class=\"corner top\" data-items='{top}'></div>\n<div class=\"corner bottom\" data-items='{bottom}'></div>"

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
<link rel="icon" href="{P}favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{P}favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="{P}favicon-192.png">
<link rel="apple-touch-icon" href="{P}apple-touch-icon.png">
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
# favicon: the seal impression (img/favicon_src.png), its own alpha kept as is
fav = Image.open(ROOT / "img" / "favicon_src.png").convert("RGBA")
for n in (32, 192, 512): fav.resize((n, n), Image.LANCZOS).save(WEB / f"favicon-{n}.png")
fav.resize((48, 48), Image.LANCZOS).save(WEB / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
fav.resize((180, 180), Image.LANCZOS).save(WEB / "apple-touch-icon.png")
DOMAIN = B.C["site"]["domain"]
if DOMAIN: (WEB / "CNAME").write_text(DOMAIN + "\n")      # leave site.domain empty to publish at ericqianli.github.io/xuanguang/
(WEB / ".nojekyll").write_text("")
tot = sum(f.stat().st_size for f in WEB.rglob("*") if f.is_file())
print("web/ built: zh + en;", f"{tot/1e6:.1f} MB total;", "fonts:", [f"{f.name} {f.stat().st_size//1000}k" for f in (WEB/'fonts').glob('*.woff2')])
