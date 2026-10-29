# -*- coding: utf-8 -*-
"""English edition mock: same pages, photos and edges as the Chinese book; text set horizontally."""
import re, yaml, pathlib
import build_outline as B          # photos, edge library, CSS, page geometry (reads the Chinese content.yaml, which we ignore)
B.BAKE = "en_"                     # baked photo files of this edition: img/baked_en_*.png

C = yaml.safe_load(open(pathlib.Path(__file__).with_name("content_en.yaml"), encoding="utf8"))
URL = {str(k): v for k, v in C["urls"].items()}

CSS_EN = """
.page{font-feature-settings:"pwid"}   /* proportional Latin punctuation in the CJK serif (curly quotes etc.) */
.hb{position:absolute}
.hb .h{font-size:34px;font-weight:300;letter-spacing:.03em;line-height:1.25;color:#2b2925}
.hb .sub{font-size:12px;letter-spacing:.32em;text-transform:uppercase;color:#6b665c;margin-top:18px}
.hb .tag{font-size:19px;font-weight:400;line-height:1.7;margin-top:38px;color:#2b2925}
.hb .rule{width:48px;height:1px;background:#2b2925;opacity:.35;margin:34px 0}
.hb .body{font-size:16px;line-height:1.9;color:#403c36;font-weight:300}
.hb .body p{margin:0 0 1.1em}
.hb .body p.quote{margin-top:1.7em;padding-left:18px;border-left:1px solid rgba(43,41,37,.25)}
.hb .body .lab{font-weight:400;color:#2b2925}
.hb .body a{color:inherit;text-decoration:none;border-bottom:1px solid rgba(43,41,37,.4);padding-bottom:1px}
.hfolio{position:absolute;bottom:62px;font-size:12px;letter-spacing:.3em;text-transform:uppercase;color:#6b665c;white-space:nowrap}
.hfolio a{color:inherit;text-decoration:none;text-transform:none;letter-spacing:.18em}
"""

def folio(f, pos):
    if not f: return ""
    u = URL.get(f[:2])
    t = f + (f' · <a href="https://{u}">{u}</a>' if u else "")
    return f'<div class="lat hfolio" style="{pos}:110px">{t}</div>'

def body_html(items):
    out = []
    for it in items:
        if isinstance(it, dict) and "label" in it: out.append(f'<p><span class="lab">{it["label"]}</span>{it["text"]}</p>')
        elif isinstance(it, dict) and "quote" in it: out.append(f'<p class="quote">{it["quote"]}</p>')
        else: out.append(f"<p>{it}</p>")
    return "".join(out)

def photo_prefix(i, d):
    """Let the Chinese builder lay out the photo (edges, bar, stacking) and keep only that part of the page."""
    t = B._page(d)
    html = B.render(i, t)
    cut = html.index('<div class="vb"') if '<div class="vb"' in html else html.index('<div class="lat folio"')
    pre = html[:cut]
    side = d.get("side") or ("L" if (i + 1) % 2 == 1 else "R")
    iw = B.img_w(B.IMG[d["image"]]) if not isinstance(d["image"], list) else int(re.search(r'width:(\d+)px;height:1000px;background-image:url\(img/baked_en_stack', pre).group(1))
    return pre, side, iw + int(d.get("inset", 0))      # an inset photo takes its gap with it

def page_html(i, d):
    kind = d.get("kind", "img")
    if kind == "sanmi":
        lines = "".join(f'<div style="font-size:27px;font-weight:300;line-height:1.7;letter-spacing:.02em">{x}</div>' for x in d["lines"])
        return f'''<div class="page">
  <div class="cjk" style="position:absolute;left:0;right:0;top:330px;text-align:center;color:#2b2925">{lines}
    <div style="width:48px;height:1px;background:#2b2925;opacity:.35;margin:40px auto"></div>
    <div style="font-size:33px;font-weight:300;letter-spacing:.03em">{d["closing"]}</div>
  </div>
  {folio(d.get("folio"), "right")}
</div>'''
    if kind == "zen":
        ps = "".join(f'<p style="margin-bottom:1.3em">{x}</p>' for x in d["body"])
        return f'''<div class="page">
  <div class="cjk" style="position:absolute;left:0;right:0;top:296px;text-align:center;font-size:40px;letter-spacing:.02em;font-weight:200">{d["title"]}</div>
  <div class="lat" style="position:absolute;left:0;right:0;top:372px;text-align:center;font-size:12px;letter-spacing:.35em;color:#7a7568">{d["sub"]}</div>
  <div class="hair" style="left:799px;top:450px;width:1px;height:60px"></div>
  <div class="cjk" style="position:absolute;left:470px;right:470px;top:560px;text-align:center;font-size:16px;line-height:1.9;color:#403c36;font-weight:300">{ps}</div>
  {folio(d.get("folio"), "right")}
</div>'''
    pre, side, iw = photo_prefix(i, d)
    if d.get("edge", "").startswith("bar"): iw += int(d["edge"].split(":")[1])     # the band counts as photo
    P = 1600 - iw                                   # paper width beside the photo
    w = min(d.get("width", 480), P - 220)           # column width (per-page override), never closer than 110px to photo or page edge
    near = d.get("edge") == "near" or d.get("align") == "near"
    if near:
        x = iw + 110 if side == "L" else (1600 - iw) - 110 - w
    else:                                           # centred in the paper area
        x = (iw if side == "L" else 0) + (P - w) / 2
    if "x" in d: x = d["x"]                      # explicit left position (px) overrides the rule
    pos = f"left:{x:.0f}px"
    head = f'<div class="cjk h">{d["title"]}</div><div class="lat sub">{d.get("sub","")}</div>'
    u = URL.get((d.get("folio") or "")[:2])
    if u: head = f'<a href="https://{u}" style="color:inherit;text-decoration:none;display:block">{head}</a>'
    tag = f'<div class="cjk tag">{d["tagline"]}</div>' if d.get("tagline") else ""
    va = d.get("valign", "top")
    # a full-height flex column keeps the block inside the page in print (a translated box would be fragmented by the PDF printer)
    block = f'<div>{head}{tag}<div class="rule"></div><div class="cjk body">{body_html(d.get("body", []))}</div></div>'
    if isinstance(va, (int, float)):            # e.g. 0.33 → free space split 1/3 above : 2/3 below
        inner = f'<div style="flex:{va}"></div>{block}<div style="flex:{1 - va}"></div>'; vpos = ""
    else:
        inner = block
        vpos = {"top": "justify-content:flex-start;padding-top:118px", "middle": "justify-content:center", "bottom": "justify-content:flex-end;padding-bottom:118px"}[va]
    text = f'<div class="hb" style="{pos};width:{w}px;top:0;height:1000px;display:flex;flex-direction:column;{vpos}">{inner}</div>'
    return pre + text + folio(d.get("folio"), "right" if side == "L" else "left") + "</div>"

def cover():
    cw = B.img_w(B.IMG["cover"]); off = 160; k = C["cover"]
    return f'''<div class="page">
  <div class="img fit" style="left:{off}px;top:0;width:{cw}px;height:1000px;background-image:url({B.IMG["cover"]});background-position:left center"></div>
  <div class="cjk" style="position:absolute;right:110px;top:112px;text-align:right;color:#2b2925">
    <div style="font-size:40px;font-weight:300;letter-spacing:.28em;line-height:1;text-transform:uppercase;margin-right:-.28em">{k["name"]}</div>
    <div style="font-size:26px;color:#8a8577;margin:22px 0;line-height:1">×</div>
    <div style="font-size:40px;font-weight:300;letter-spacing:.3em;line-height:1;margin-right:-.3em">{k["brand"]}</div>
    <div style="font-size:13px;letter-spacing:.3em;font-weight:300;color:#4a463f;margin-top:40px;text-transform:uppercase;margin-right:-.3em">{k["subtitle"]}</div>
  </div>
</div>'''

def brand():
    k = C["brand"]
    cells = "".join(f'''<div style="border-left:1px solid rgba(43,41,37,.3);padding-left:20px">
      <div class="lat" style="font-size:11px;letter-spacing:.32em;color:#6b665c">{it["en"]}</div>
      <div class="cjk" style="font-size:21px;letter-spacing:.02em;margin:8px 0 10px;color:#2b2925">{it["zh"]}</div>
      <div class="cjk" style="font-size:15px;line-height:1.8;color:#403c36;font-weight:300">{it["text"]}</div></div>''' for it in k["items"])
    return f'''<div class="page">
  <div style="position:absolute;left:110px;top:118px;right:110px">
    <div class="lat" style="font-size:30px;letter-spacing:.3em;font-weight:300">{k["title"]}</div>
    <div class="cjk" style="font-size:19px;line-height:1.75;font-weight:400;margin-top:28px;max-width:680px">{"<br>".join(k["statement"])}</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:56px 56px;margin-top:96px">{cells}</div>
  </div>
  <div class="lat hfolio" style="right:110px">{k["title"]}</div>
</div>'''

def contact():
    K = C["contact"]; A = 'style="color:inherit;text-decoration:none"'
    items = [("WeChat", K["wechat"]), ("Web", "<br>".join(f'<a href="https://{d}" {A}>{d}</a>' for d in K["web"])), ("Email", f'<a href="mailto:{K["email"]}" {A}>{K["email"]}</a>')]
    cols = "".join(f'<div style="width:300px;text-align:center"><div class="lat" style="font-size:11px;letter-spacing:.4em;color:#8a8577">{a}</div><div class="cjk" style="font-size:15px;line-height:2.2;letter-spacing:.06em;margin-top:10px;color:#4a463f;font-weight:300">{b}</div></div>' for a, b in items)
    return f'''<div class="page">
  <img src="img/logo.png" style="position:absolute;left:670px;top:268px;width:260px">
  <div class="hair" style="left:799px;top:604px;width:1px;height:56px"></div>
  <div style="position:absolute;left:0;right:0;top:704px;display:flex;justify-content:center;gap:40px">{cols}</div>
  <div class="lat" style="position:absolute;left:0;right:0;top:884px;text-align:center;font-size:11px;letter-spacing:.4em;color:#8a8577;font-weight:300">{K["closing"]}</div>
</div>'''

pages = [cover(), brand()] + [page_html(i + 2, d) for i, d in enumerate(C["pages"])] + [contact()]
html = ('<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="base.css"><style>' + B.CSS + CSS_EN +
        "</style></head><body>\n" + "\n".join(pages) + "\n</body></html>")
open("E_outline.html", "w", encoding="utf8").write(html)
print(len(pages), "pages →", "E_outline.html")
