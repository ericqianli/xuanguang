# -*- coding: utf-8 -*-
"""Generate P_outline.html from a simple page list (one source → PDF + web later)."""
PAPER = "#f3efe6"
BAKE = ""            # prefix for baked image files (the English build sets "en_" so the two editions never share a file)
from PIL import Image as _I
IMG = {"rose": "img/36.jpg", "oncidium": "img/21.jpg", "poem": "img/poem_right.png", "guqin": "img/guqin.jpg", "lumilab": "img/lumilab_sq.jpg", "crystal_sq": "img/crystal_sq.jpg", "attic_render": "img/attic_render.jpg", "attic_photo": "img/attic_photo.jpg", "objects": "img/objects_sq.jpg", "portrait": "img/portrait.jpg", "cover": "img/cover.jpg", "rose_top10": "img/rose_top10.jpg", "workshop": "img/workshop.jpg", "seal": "img/seal.jpg"}

import yaml as _yaml, pathlib as _pl
C = _yaml.safe_load(open(_pl.Path(__file__).with_name("content.yaml"), encoding="utf8"))

brand = [(it["en"], it["zh"], it["text"]) for it in C["brand"]["items"]]
URL = {str(k): v for k, v in C["urls"].items()}          # section number → site, shown in the folio

def _body(items):
    out = []
    for it in items:
        if isinstance(it, dict) and "label" in it: out.append((it["label"], it["text"]))
        elif isinstance(it, dict) and "quote" in it: out.append(("quote", it["quote"]))
        else: out.append(str(it))
    return out

def _page(d):
    """content.yaml entry → the (kind, title, sub, paras, image, folio, note, side, edge) tuple render() expects"""
    kind = d.get("kind", "img")
    if kind in ("sanmi", "zen"):
        return (kind, None, None, None, None, d.get("folio", ""), None)
    paras = ([d["tagline"]] if d.get("tagline") else []) + _body(d.get("body", []))
    image = d.get("image"); image = tuple(image) if isinstance(image, list) else image
    return ("img", d["title"], d.get("sub", ""), paras, image, d.get("folio", ""), None, d.get("side"), d.get("edge"), d.get("inset", 0), bool(d.get("tagline")), d.get("halign"))

pages = [("cover", None, None, None, "cover", None, None), ("brand", None, None, None, None, C["brand"]["title"], None)] \
      + [_page(d) for d in C["pages"]] + [("contact", None, None, None, None, "", None)]
_special = {i + 2: d for i, d in enumerate(C["pages"]) if d.get("kind")}   # page index → yaml entry for sanmi / zen


import re as _re
_DIG="〇一二三四五六七八九"
def _num(m):
    n=m.group(0)
    if len(n)==4: return "".join(_DIG[int(c)] for c in n)          # years
    v=int(n)
    if v<10: return _DIG[v]
    if v<100: t,o=divmod(v,10); return ("十" if t==1 else _DIG[t]+"十")+(_DIG[o] if o else "")
    return "".join(_DIG[int(c)] for c in n)
_LAT=r"[A-Za-z][A-Za-z0-9.&' ]*[A-Za-z0-9.]|[A-Za-z]"
_RUN=r"[A-Za-z0-9][A-Za-z0-9.&'@_\u2009 ]*[A-Za-z0-9.]|[A-Za-z0-9]|·"
def lt(t, lc=None):
    """wrap sideways (rotated) Latin/digit runs: .lt nudges caps/digits, .lt.lc nudges lowercase runs"""
    def w(m):
        r=m.group(0)
        if r.startswith("<") or r.startswith("&"): return r          # leave tags / entities alone
        c="lt lc" if (lc if lc is not None else any(ch.islower() for ch in r)) else "lt"
        return f'<span class="{c}">{r}</span>'
    return _re.sub(r"<[^>]+>|&[a-z]+;|" + _RUN, w, t)
def zh(t):
    if "<" in t:   # never touch markup: convert only the text between tags
        parts=_re.split(r"(<[^>]+>)", t)
        return "".join(p if p.startswith("<") else zh(p) for p in parts)
    t=_re.sub(r"\d+",_num,t)
    t=_re.sub(r"(?<=[\u3000-\u9fff])\s+(?=[\u3000-\u9fff])", "", t)   # no spaces between CJK characters
    # strip ordinary spaces around Latin runs, then put ONE thin space between Latin and CJK ideographs
    t=_re.sub(r"\s*(" + _LAT + r")\s*", r"\1", t)
    t=_re.sub(r"([\u4e00-\u9fff])(" + _LAT + r")", "\\1\u2009\\2", t)
    t=_re.sub(r"(" + _LAT + r")([\u4e00-\u9fff])", "\\1\u2009\\2", t)
    return lt(t)

import base64 as _b64, numpy as _np, io as _io
from PIL import ImageFilter as _IF
def _noise1d(n, scales, seed):
    rng=_np.random.default_rng(seed); out=_np.zeros(n)
    for sc,a in scales:
        k=max(2,n//sc+2); pts=rng.standard_normal(k)
        x=_np.linspace(0,k-1,n); out+=a*_np.interp(x,_np.arange(k),pts)
    return out/_np.abs(out).max()
def _mask_array(W, side, seed, drift=14, tear=14, fiber=6):
    H=1000; xs=_np.arange(W)[None,:]
    edge=_noise1d(H,((500,1.0),(200,0.5)),seed)*drift+_noise1d(H,((35,1.0),(90,0.7)),seed+1)*tear+_noise1d(H,((3,1.0),(8,0.6)),seed+2)*fiber
    fringe=_np.abs(_noise1d(H,((5,1.0),(14,0.8)),seed+3))*fiber*1.2
    edge=edge+(W-(edge+fringe).max())-1      # tear hugs the photo edge: deepest bite inward, fringe never beyond W
    m=(xs<edge[:,None]).astype(_np.float32)
    edge2=edge+fringe
    m=_np.maximum(m,(xs<edge2[:,None]).astype(_np.float32)*0.4)
    if side=="R": m=m[:,::-1]
    img=_I.fromarray((m*255).astype(_np.uint8)).filter(_IF.GaussianBlur(0.7))
    return _np.array(img).astype(_np.float32)/255.0
def wall_colour(src, side):
    im=_I.open(src).convert("RGB"); w,h=im.size
    box=(int(w*.93),int(h*.05),w,int(h*.4)) if side=="L" else (0,int(h*.05),int(w*.07),int(h*.4))
    a=_np.array(im.crop(box)).reshape(-1,3).mean(0)
    return "#%02x%02x%02x"%tuple(int(v) for v in a)

# ---- edge library (all baked into opaque images) ----
def _edge_mask(kind, W, side, seed, band=260):
    """Return float mask (H,W) in [0,1]; 1 = photo, 0 = paper. Edge is on the LEFT for side=R, mirrored for side=L."""
    H=1000; xs=_np.arange(W)[None,:].astype(_np.float32); rng=_np.random.default_rng(seed)
    if kind=="deckle":
        m=_mask_array(W, "R", seed)            # built as right-side (edge on left)
        return m if side=="R" else m[:,::-1]
    if kind=="fade":
        fw = band if band != 260 else int(W*0.45)
        t=_np.clip(xs/fw,0,1); t=t*t*t*(t*(t*6-15)+10)   # quintic smoothstep: zero slope at both ends
        m=_np.repeat(t,H,0)
    elif kind=="ink":      # 墨晕: wavy soft front (±20px), wide smoothstep band, grain only mid-band
        front=20+_noise1d(H,((40,1.0),(120,.6),(300,.35)),seed)[:,None]*20; width=band
        t=_np.clip((xs-front)/width,0,1); m=t*t*(3-2*t)
        g=rng.random((H,W)).astype(_np.float32)
        mid=_np.clip(1-_np.abs(t-0.5)*2,0,1)          # 1 at band centre, 0 at both ends
        m=_np.clip(m+(g-0.5)*0.35*mid,0,1)
        m=_np.array(_I.fromarray((m*255).astype(_np.uint8)).filter(_IF.GaussianBlur(1.2))).astype(_np.float32)/255
    elif kind=="grain":    # 颗粒溶解: particles grow in density AND opacity, fully paper at the edge
        gw = band if band != 260 else 176
        t=_np.clip(xs/gw,0,1); p=t*t*(3-2*t); P=_np.repeat(p,H,0)     # starts at the photo's own edge
        hit=(rng.random((H,W))<P).astype(_np.float32)
        m=hit*P**0.5
        m=_np.maximum(m,_np.clip((xs-(gw-30))/30,0,1))
        m=_np.array(_I.fromarray((m*255).astype(_np.uint8)).filter(_IF.GaussianBlur(0.6))).astype(_np.float32)/255
    else:
        raise ValueError(kind)
    return m if side=="R" else m[:,::-1]

CSS = """
.page{background:%s;color:#2b2925}
.hair{position:absolute;background:#2b2925;opacity:.35}
.fit{background-size:auto 100%%}
.up{writing-mode:vertical-rl;text-orientation:upright}
.side{writing-mode:vertical-rl;text-orientation:mixed}
.small{font-size:12px;letter-spacing:.35em;text-transform:uppercase;color:#6b665c}
.vb{position:absolute;top:110px;height:780px;writing-mode:vertical-rl;text-orientation:mixed}
.vb>*{display:block}
.vb .h{font-size:30px;letter-spacing:.3em;font-weight:300;text-orientation:mixed;margin-left:16px}
.vb .sub{font-size:12px;letter-spacing:.35em;text-transform:uppercase;color:#6b665c;margin-left:44px}
.vb .tag{font-size:17px;letter-spacing:.14em;font-weight:400;line-height:1.9;text-orientation:mixed;margin-left:36px}
.vb .rule{width:1px;height:48px;background:#2b2925;opacity:.35;margin-left:36px}
.vb .body{font-size:17px;line-height:2.3;letter-spacing:.08em;color:#4a463f;font-weight:300;text-orientation:mixed}
.vb .body p{margin-left:1.1em}
.vb .body p.quote{margin-right:2.4em}
.vb .body a{color:inherit;text-decoration:none;border-right:1px solid rgba(43,41,37,.35);padding-right:1px}
.fade-r{-webkit-mask-image:linear-gradient(90deg,#000 0%%,#000 55%%,rgba(0,0,0,0) 100%%);mask-image:linear-gradient(90deg,#000 0%%,#000 55%%,rgba(0,0,0,0) 100%%)}
.fade-l{-webkit-mask-image:linear-gradient(270deg,#000 0%%,#000 55%%,rgba(0,0,0,0) 100%%);mask-image:linear-gradient(270deg,#000 0%%,#000 55%%,rgba(0,0,0,0) 100%%)}
.lt{position:relative;left:.11em}.lt.lc{left:.2em}
.folio{position:absolute;bottom:62px;writing-mode:vertical-rl;text-orientation:mixed;font-size:12px;letter-spacing:.35em;color:#6b665c;text-transform:uppercase}
.ph{position:absolute;bottom:62px;font-size:11px;letter-spacing:.3em;color:#b0a894}
""" % PAPER

def img_w(src):
    w,h=_I.open(src).size; return int(1000*w/h)

def stack_div(srcs, side, blend=80, n=0, edge=None):
    """Two images stacked in one column, overlapping by `blend` px with a soft vertical dissolve; baked to one opaque PNG."""
    pos = "left" if side == "L" else "right"
    ims=[_I.open(x).convert("RGB") for x in srcs]
    ratios=[im.size[1]/im.size[0] for im in ims]
    W=int((1000+blend*(len(ims)-1))/sum(ratios))
    hs=[round(W*r) for r in ratios]
    hs[-1]+=1000-(sum(hs)-blend*(len(ims)-1))   # absorb rounding so the column is exactly page height
    H=1000
    canvas=_np.zeros((H,W,3),_np.float32); y=0
    for k,(im,h) in enumerate(zip(ims,hs)):
        a=_np.array(im.resize((W,h),_I.LANCZOS)).astype(_np.float32)
        if k==0:
            canvas[y:y+h]=a
        else:
            top=y
            alpha=_np.ones((h,1,1),_np.float32)
            t=_np.linspace(0,1,blend)
            alpha[:blend,0,0]=(1-_np.cos(t*_np.pi))/2   # smooth ramp 0→1
            canvas[top:top+h]=canvas[top:top+h]*(1-alpha)+a*alpha
        y+=h-blend
    if edge and not edge.startswith("bar"):   # same edge library as single photos (e.g. "fade:120"), applied to the paper-facing side of the column
        kind, _, bandstr = edge.partition(":"); band = int(bandstr) if bandstr else 260
        m=_edge_mask(kind, W, side, 11+n, band)[..., None]
        canvas=canvas*m+_np.array([243,239,230],_np.float32)*(1-m)
    path=f"img/baked_{BAKE}stack_{n}.png"
    _I.fromarray(canvas.clip(0,255).astype(_np.uint8)).save(path)
    return f'<div class="img" style="{pos}:0;top:0;width:{W}px;height:{H}px;background-image:url({path});background-size:100% 100%"></div>', W

def img_div(src, side, cls="", extra=""):
    pos = "left" if side == "L" else "right"
    return f'<div class="img fit {cls}" style="{pos}:0;top:0;width:{img_w(src)}px;height:1000px;background-image:url({src});background-position:{pos} center;{extra}"></div>'

def folio_html(folio, pos):
    if not folio: return ""
    u=URL.get(folio[:2])
    folio=lt(folio, lc=False)
    if u: folio=f'{folio} <span class="lt">·</span> <a href="https://{u}" style="color:inherit;text-decoration:none;text-transform:none;font-size:11px;letter-spacing:.22em"><span class="lt lc">{u}</span></a>'
    return f'<div class="lat folio" style="{pos}:110px">{folio}</div>'
def render(i, p):
    kind, title, sub, paras, image, folio, ph = p[:7]
    n = i + 1
    side = p[7] if len(p) > 7 and p[7] else ("L" if n % 2 == 1 else "R")
    edge = p[8] if len(p) > 8 else None
    inset = p[9] if len(p) > 9 else 0
    if isinstance(image, (list, tuple)):
        stack_html, iw = stack_div([IMG[x] for x in image], side, n=n, edge=edge)
    else:
        stack_html = None
        iw = img_w(IMG[image]) if image else 800
    # vertical text block is anchored by its RIGHT edge (columns flow right→left)
    vb_right = "110px" if side == "L" else f"{iw+110}px"
    folio_side = "right" if side == "L" else "left"
    ph_side = "left" if side == "L" else "right"
    if kind == "cover":
        cw=img_w(IMG[image]); off=int(1600*0.10)
        return f'''<div class="page">
  <div class="img fit" style="left:{off}px;top:0;width:{cw}px;height:1000px;background-image:url({IMG[image]});background-position:left center"></div>
  <div class="cjk side" style="position:absolute;right:110px;top:100px;font-size:48px;font-weight:300;line-height:1;letter-spacing:.38em"><span class="up">{C["cover"]["name"]}<span style="color:{C["cover"].get("mark_color", "#8a8577")};font-size:{C["cover"].get("mark_size", ".9em")};margin:{C["cover"].get("mark_margin", "0")} 0">{C["cover"].get("mark", "×")}</span></span><span style="letter-spacing:.3em;position:relative;left:3px">{C["cover"]["brand"]}</span></div>
  <div class="cjk up" style="position:absolute;right:196px;top:116px;font-size:18px;letter-spacing:.45em;font-weight:300;color:#4a463f">{C["cover"]["subtitle"]}</div>
</div>'''
    if kind == "brand":
        cells = "".join(f'<div style="border-right:1px solid rgba(43,41,37,.3);padding-right:16px;margin-left:24px;height:fit-content"><div class="lat small" style="margin-left:12px">{lt(en, lc=False)}</div><div class="cjk side" style="font-size:19px;letter-spacing:.15em;margin-left:10px">{z}</div><div class="cjk body" style="font-size:14px;line-height:2.1">{zh(txt)}</div></div>' for en, z, txt in brand)
        return f'''<div class="page">
  <div class="vb" style="right:110px">
    <div class="lat" style="font-size:30px;letter-spacing:.3em;font-weight:300;margin-left:28px">{C["brand"]["title"]}</div>
    <div class="cjk side" style="font-size:17px;line-height:1.9;letter-spacing:.12em;font-weight:400;margin-left:36px">{"<br>".join(zh(x) for x in C["brand"]["statement"])}</div>
    {cells}
  </div>
  {folio_html(folio,"right")}
</div>'''
    if kind == "sanmi":
        L='font-size:26px;letter-spacing:.3em;font-weight:300;line-height:1;margin-left:34px'
        d=_special[i]
        lines="\n".join(f'    <div class="cjk" style="{L}">{zh(x)}</div>' for x in d["lines"])
        return f'''<div class="page">
  <div class="vb" style="right:620px;top:230px;height:560px">
{lines}
    <div class="rule" style="margin-left:44px"></div>
    <div class="cjk h" style="margin-left:44px">{zh(d["closing"])}</div>
  </div>
  {folio_html(folio,"right")}
</div>'''
    if kind == "contact":
        A='style="color:inherit;text-decoration:none"'
        K=C["contact"]
        items=[("WeChat",str(K["wechat"])),
               ("Web","<br>".join(f'<a href="https://{d}" {A}>{d}</a>' for d in K["web"])),
               ("Email",f'<a href="mailto:{K["email"]}" {A}>{K["email"]}</a>')]
        cols="".join(f'<div style="width:300px;text-align:center"><div class="lat" style="font-size:11px;letter-spacing:.4em;color:#8a8577">{a}</div><div class="cjk" style="font-size:15px;line-height:2.2;letter-spacing:.12em;margin-top:10px;color:#4a463f;font-weight:300">{b}</div></div>' for a,b in items)
        return f'''<div class="page">
  <img src="img/logo.png" style="position:absolute;left:670px;top:268px;width:260px">
  <div class="hair" style="left:799px;top:604px;width:1px;height:56px"></div>
  <div style="position:absolute;left:0;right:0;top:704px;display:flex;justify-content:center;gap:40px">{cols}</div>
  <div class="cjk" style="position:absolute;left:0;right:0;top:884px;text-align:center;font-size:12px;letter-spacing:.5em;color:#8a8577;font-weight:300">{K["closing"]}</div>
</div>'''
    if kind == "zen":
        d=_special[i]; zb=d["body"]
        zsub=d["sub"].replace(" · ", " &nbsp;·&nbsp; ")
        zps="\n".join(f'    <p{" style=\"margin-bottom:1.3em\"" if k < len(zb)-1 else ""}>{zh(x)}</p>' for k,x in enumerate(zb))
        return f'''<div class="page">
  <div class="cjk" style="position:absolute;left:0;right:0;top:294px;text-align:center;font-size:44px;letter-spacing:.42em;padding-left:.42em;font-weight:200">{zh(d["title"])}</div>
  <div class="lat" style="position:absolute;left:0;right:0;top:380px;text-align:center;font-size:13px;letter-spacing:.35em;color:#7a7568">{zsub}</div>
  <div class="hair" style="left:799px;top:436px;width:1px;height:60px"></div>
  <div class="cjk" style="position:absolute;left:390px;right:390px;top:536px;text-align:center;font-size:17px;line-height:2.3;letter-spacing:.06em;color:#4a463f;font-weight:300">
{zps}
  </div>
  {folio_html(folio,"right")}
</div>'''
    has_tag = p[10] if len(p) > 10 else False
    tagline, rest = (paras[0], paras[1:]) if has_tag else (None, paras)
    def _p(t):
        if isinstance(t, tuple) and t[0] == "quote":
            return f'<p class="quote">{zh(t[1])}</p>'
        if isinstance(t, tuple):
            return f'<p><span style="font-weight:400;color:#2b2925">{t[0]}</span>{zh(t[1])}</p>'
        return f"<p>{zh(t)}</p>"
    body = "".join(_p(t) for t in rest)
    phd = f'<div class="cjk ph" style="{ph_side}:110px">{ph}</div>' if ph else ""
    tag = f'<div class="cjk tag">{tagline.replace("；","；<br>").replace("，由","，<br>由")}</div>' if tagline else ""
    page_style = ""
    bar = ""
    if edge and edge.startswith("bar"):      # e.g. "bar:10:#4a2b23" — solid band on the paper side of the photo, no gap
        _, bw, bc = (edge.split(":") + ["10", "#4a2b23"])[:3]
        # drawn under the photo and 1px wider, so that a scaled web page (fractional CSS pixels) never shows a seam between the two
        bar = f'<div style="position:absolute;top:0;height:1000px;{"left" if side == "L" else "right"}:{iw - 1}px;width:{int(bw) + 1}px;background:{bc}"></div>'
        edge = None
    if stack_html:
        photo = stack_html
    elif edge and edge.split(":")[0] in ("deckle", "fade", "ink", "grain"):
        kind, _, bandstr = edge.partition(":"); band = int(bandstr) if bandstr else 260
        # bake the edge into an opaque image (no soft mask in the PDF → no viewer hairlines)
        W=iw; H=1000
        src=_I.open(IMG[image]).convert("RGB").resize((W,H),_I.LANCZOS)
        m=_edge_mask(kind, W, side, 11+n, band)
        if inset:
            m=_np.roll(m, inset if side=="R" else -inset, axis=1)
            if side=="R": m[:, :inset]=0
            else: m[:, W-inset:]=0
        paper=_np.array([243,239,230],_np.float32)
        out=_np.array(src).astype(_np.float32)*m[...,None]+paper*(1-m[...,None])
        path=f"img/baked_{BAKE}{n}.png"; _I.fromarray(out.clip(0,255).astype(_np.uint8)).save(path)
        photo=f'<div class="img" style="{"left" if side=="L" else "right"}:0;top:0;width:{W}px;height:{H}px;background-image:url({path});background-size:100% 100%"></div>'
    elif edge == "wall":
        photo = img_div(IMG[image], side); page_style = f' style="background:{wall_colour(IMG[image], side)}"'
    elif edge and edge.startswith("deckle2"):   # torn on BOTH sides, floated in from the page edge by `inset` (书法篆刻)
        _, sl, sr = (edge.split(":") + ["77", "20"])[:3]
        W=iw; H=1000
        src=_I.open(IMG[image]).convert("RGB").resize((W,H),_I.LANCZOS)
        ml=_edge_mask("deckle", W, "R", int(sl))[...,None]; mr=_edge_mask("deckle", W, "L", int(sr))[...,None]
        paper=_np.array([243,239,230],_np.float32)
        out=_np.array(src).astype(_np.float32)*ml*mr+paper*(1-ml*mr)
        path=f"img/baked_{BAKE}{n}.png"; _I.fromarray(out.clip(0,255).astype(_np.uint8)).save(path)
        photo=f'<div class="img" style="{"left" if side=="L" else "right"}:{inset}px;top:0;width:{W}px;height:{H}px;background-image:url({path});background-size:100% 100%"></div>'
    elif edge and edge.startswith("wall+"):
        kind = edge.split("+",1)[1]
        wc = wall_colour(IMG[image], side); page_style = f' style="background:{wc}"'
        W=iw; H=1000
        src=_I.open(IMG[image]).convert("RGB").resize((W,H),_I.LANCZOS)
        m=_edge_mask(kind, W, side, 11+n)
        paper=_np.array([int(wc[1:3],16),int(wc[3:5],16),int(wc[5:7],16)],_np.float32)
        out=_np.array(src).astype(_np.float32)*m[...,None]+paper*(1-m[...,None])
        path=f"img/baked_{BAKE}{n}.png"; _I.fromarray(out.clip(0,255).astype(_np.uint8)).save(path)
        photo=f'<div class="img" style="{"left" if side=="L" else "right"}:0;top:0;width:{W}px;height:{H}px;background-image:url({path});background-size:100% 100%"></div>'
    else:
        photo = img_div(IMG[image], side)
    if edge == "cross":
        title_right = f"{1600 - iw + 60}px" if side == "L" else f"{iw - 250}px"
        body_right = f"{1600 - iw - 250}px" if side == "L" else f"{iw + 110}px"
        text = (f'<div class="vb" style="right:{title_right}"><div class="cjk h">{title}</div><div class="lat sub">{lt(sub, lc=False)}</div>{tag}</div>'
                f'<div class="vb" style="right:{body_right};height:700px"><div class="rule" style="margin-left:0"></div><div class="cjk body">{body}</div></div>')
    else:
        halign = p[11] if len(p) > 11 else None
        if edge == "near":   # whole block pulled in next to the photo: anchor its LEFT edge 110px from the photo
            text = f'<div class="vb" style="left:{iw + 93}px;right:auto">'
        elif halign == "center":   # block centred in the paper area beside the photo (flex: the vb shrinks to its columns)
            paper = f"left:{iw}px;right:0" if side == "L" else f"left:0;right:{iw}px"
            text = f'<div style="position:absolute;top:110px;height:780px;{paper};display:flex;justify-content:center"><div class="vb" style="position:static">'
        else:
            text = f'<div class="vb" style="right:{vb_right}">'
        u=URL.get((folio or "")[:2])
        head=f'<div class="cjk h">{title}</div><div class="lat sub">{lt(sub, lc=False)}</div>'
        if u: head=f'<a href="https://{u}" style="color:inherit;text-decoration:none;display:block">{head}</a>'
        text += f'{head}{tag}<div class="rule"></div><div class="cjk body">{body}</div></div>' + ("</div>" if halign == "center" else "")
    return f'<div class="page"{page_style}>{bar}{photo}{text}{phd}{folio_html(folio,folio_side)}</div>'

html = '<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="base.css"><style>' + CSS + "</style></head><body>\n" + "\n".join(render(i, p) for i, p in enumerate(pages)) + "\n</body></html>"
open("P_outline.html", "w", encoding="utf8").write(html)
print(len(pages), "pages")
