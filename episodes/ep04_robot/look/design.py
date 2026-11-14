# まるロボ回の 2D の新しい見た目（2026-11-14 ユーザー「チープ感すごく感じてしまう」「吹き出しの形雑すぎ」）
#   決まり：
#   - 2 倍の大きさで描いて縮める（ふちがギザギザにならない）
#   - 黒いふち線をやめ、やわらかい影で浮かせる。札・吹き出しは「ふち＋しっぽ」を 1 つの形として塗る（つなぎ目の線が出ない）
#   - 出るときは、ぽんと少し大きくなってから落ち着く（0.3 秒）。切り替えは字幕の切り替わりと同じコマ
#   - 背景は平らな 1 色にしない（上から下へのグラデーション＋うすい点の格子＋ゆっくり流れる）
#   - 図の場面にも、まるロボ（cutout.py の切り抜き）を当事者として置く
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SS = 2
NAVY = (22, 38, 74); NAVY2 = (47, 74, 115); TEAL = (33, 193, 179); TEAL_D = (18, 140, 130)
ORANGE = (255, 138, 42); GREEN = (52, 178, 102); RED = (226, 76, 66); WHITE = (255, 255, 255)
INK = (40, 52, 74); MUTED = (120, 134, 156)
FONTS = {}
FDIR = [None]


def font(n, w="700Bold"):
    k = (n, w)
    if k not in FONTS: FONTS[k] = ImageFont.truetype("%s/%s/NotoSansJP_%s.ttf" % (FDIR[0], w, w), n)
    return FONTS[k]


def ease_out_back(x, s=1.9):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------- 形
def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m


def shadow_of(mask, blur=18, alpha=70, dy=10, col=NAVY):
    """mask（L）の影。返す絵は mask より余白 pad ぶん大きい"""
    pad = blur * 3
    big = Image.new("L", (mask.width + pad * 2, mask.height + pad * 2), 0)
    big.paste(mask, (pad, pad + dy))
    big = big.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", big.size, col + (0,)); sh.putalpha(big)
    return sh, pad


def finish(shape_rgba, mask, blur=18, alpha=70, dy=10):
    """影をつけて 1/SS に縮めたスプライト（RGBA）と、中心のずれを返す"""
    sh, pad = shadow_of(mask, blur * SS, alpha, dy * SS)
    sh.alpha_composite(shape_rgba, (pad, pad))
    out = sh.resize((sh.width // SS, sh.height // SS), Image.LANCZOS)
    return out, pad // SS


def tail_poly(base_c, half, tip, bend=0.25):
    """付け根（中心・半分の幅）から先へ、少し曲がったしっぽ"""
    bx, by = base_c; tx, ty = tip
    dx, dy = tx - bx, ty - by; L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L; px, py = -uy, ux
    pts = []
    for side in (1, -1):
        for k in range(13):
            u = k / 12
            w = half * (1 - u) ** 1.3
            cx_ = bx + dx * u + px * L * bend * math.sin(u * math.pi) * 0.35
            cy_ = by + dy * u + py * L * bend * math.sin(u * math.pi) * 0.35
            pts.append((cx_ + px * w * side, cy_ + py * w * side))
        if side == 1: pts.append((tx, ty))
    a = pts[:14]; b = pts[14:][::-1]
    return a + b


def pill(text, size=46, fg=NAVY, bg=WHITE, accent=None, tail=None, pad=(30, 16), icon=None):
    """札。tail＝しっぽの先（札の中心からの相対の画面座標）。返す：sprite, (中心からスプライトの左上までのずれ)"""
    f = font(size * SS); d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f); tw, th = bb[2] - bb[0], int(size * SS * 1.02)
    acc_w = (size * SS * 0.55 + 14 * SS) if accent else 0
    w = int(tw + pad[0] * 2 * SS + acc_w); h = int(th + pad[1] * 2 * SS)
    r = h // 2
    ext = 0
    if tail: ext = int(max(abs(tail[0]), abs(tail[1])) * SS) + 20
    W_, H_ = w + ext * 2, h + ext * 2
    m = Image.new("L", (W_, H_), 0); dm = ImageDraw.Draw(m)
    dm.rounded_rectangle([ext, ext, ext + w - 1, ext + h - 1], r, fill=255)
    if tail:
        cx, cy = ext + w / 2, ext + h / 2
        tip = (cx + tail[0] * SS, cy + tail[1] * SS)
        ang = math.atan2(tail[1], tail[0])
        # 付け根は札のふちの内側
        bx = cx + math.cos(ang) * min(w / 2 - r * 0.6, abs(tail[0]) * SS) * (1 if tail[0] >= 0 else 1)
        bx = min(max(cx + tail[0] * SS * 0.25, ext + r), ext + w - r)
        by = cy + (h / 2 - 6 * SS) * (1 if tail[1] > 0 else -1)
        dm.polygon(tail_poly((bx, by), h * 0.28, tip), fill=255)
    img = Image.new("RGBA", (W_, H_), bg + (0,)); img.putalpha(m)
    fill = Image.new("RGBA", (W_, H_), bg + (255,)); img = Image.composite(fill, img, m)
    d = ImageDraw.Draw(img)
    x = ext + pad[0] * SS
    if accent:
        rr = size * SS * 0.275
        d.ellipse([x, ext + h / 2 - rr, x + rr * 2, ext + h / 2 + rr], fill=accent)
        x += acc_w
    d.text((x - bb[0], ext + h / 2 - th / 2 - bb[1] + (th - (bb[3] - bb[1])) / 2), text, font=f, fill=fg)
    spr, p = finish(img, m, blur=12, alpha=60, dy=6)
    return spr, (-(W_ / 2) / SS - p, -(H_ / 2) / SS - p)


def bubble(w, h, tail, draw=None, bg=WHITE, r=34):
    """吹き出し。w,h は 1 倍の大きさ。tail＝しっぽの先（吹き出しの中心からの相対）。draw(d, cx, cy, s) で中身"""
    W_, H_ = w * SS, h * SS
    ext = int(max(abs(tail[0]), abs(tail[1])) * SS) + 30
    m = Image.new("L", (W_ + ext * 2, H_ + ext * 2), 0); dm = ImageDraw.Draw(m)
    dm.rounded_rectangle([ext, ext, ext + W_ - 1, ext + H_ - 1], r * SS, fill=255)
    cx, cy = ext + W_ / 2, ext + H_ / 2
    tip = (cx + tail[0] * SS, cy + tail[1] * SS)
    # 付け根：しっぽの向きにある辺の上、角を避けて
    if abs(tail[1]) * w >= abs(tail[0]) * h:
        by = cy + (H_ / 2 - 8 * SS) * (1 if tail[1] > 0 else -1)
        bx = min(max(cx + tail[0] * SS * 0.45, ext + r * SS * 1.4), ext + W_ - r * SS * 1.4)
    else:
        bx = cx + (W_ / 2 - 8 * SS) * (1 if tail[0] > 0 else -1)
        by = min(max(cy + tail[1] * SS * 0.45, ext + r * SS * 1.2), ext + H_ - r * SS * 1.2)
    dm.polygon(tail_poly((bx, by), min(W_, H_) * 0.16, tip), fill=255)
    img = Image.composite(Image.new("RGBA", m.size, bg + (255,)), Image.new("RGBA", m.size, bg + (0,)), m)
    if draw: draw(ImageDraw.Draw(img), cx, cy, SS, img)
    spr, p = finish(img, m, blur=16, alpha=65, dy=8)
    return spr, (-(m.width / 2) / SS - p, -(m.height / 2) / SS - p)


def card(w, h, r=28, bg=WHITE, draw=None, header=None):
    W_, H_ = w * SS, h * SS
    m = rrect_mask(W_, H_, r * SS)
    img = Image.composite(Image.new("RGBA", m.size, bg + (255,)), Image.new("RGBA", m.size, bg + (0,)), m)
    d = ImageDraw.Draw(img)
    if header:
        col, txt = header
        hm = Image.new("L", m.size, 0); ImageDraw.Draw(hm).rectangle([0, 0, W_, 74 * SS], fill=255)
        hm = ImageChops.multiply(hm, m)
        img.paste(Image.new("RGBA", m.size, col + (255,)), (0, 0), hm)
        if txt:
            f = font(40 * SS); bb = d.textbbox((0, 0), txt, font=f)
            d.text((W_ / 2 - (bb[2] - bb[0]) / 2 - bb[0], 37 * SS - (bb[3] + bb[1]) / 2), txt, font=f, fill=WHITE)
    if draw: draw(d, W_, H_, SS, img)
    spr, p = finish(img, m, blur=22, alpha=60, dy=12)
    return spr, (-(W_ / 2) / SS - p, -(H_ / 2) / SS - p)


def ctext(d, xy, text, f, fill):
    bb = d.textbbox((0, 0), text, font=f)
    d.text((xy[0] - (bb[2] + bb[0]) / 2, xy[1] - (bb[3] + bb[1]) / 2), text, font=f, fill=fill)


def check_icon(d, cx, cy, r, col=GREEN):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    w = max(3, int(r * 0.22))
    d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)], fill=WHITE, width=w, joint="curve")


def cross_icon(d, cx, cy, r, col=RED):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    w = max(3, int(r * 0.22)); k = r * 0.38
    d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=WHITE, width=w); d.line([(cx + k, cy - k), (cx - k, cy + k)], fill=WHITE, width=w)


def person(size=150, shirt=(62, 124, 177), skin=(246, 212, 184)):
    """人の印（丸い頭と肩）。影つき"""
    S_ = size * SS
    img = Image.new("RGBA", (S_, S_), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.ellipse([S_ * 0.3, S_ * 0.08, S_ * 0.7, S_ * 0.48], fill=skin)
    d.ellipse([S_ * 0.33, S_ * 0.06, S_ * 0.67, S_ * 0.28], fill=(70, 52, 44))  # 髪
    d.ellipse([S_ * 0.31, S_ * 0.14, S_ * 0.69, S_ * 0.48], fill=skin)
    d.ellipse([S_ * 0.33, S_ * 0.06, S_ * 0.67, S_ * 0.22], fill=(70, 52, 44))
    d.rounded_rectangle([S_ * 0.14, S_ * 0.54, S_ * 0.86, S_ * 1.05], int(S_ * 0.28), fill=shirt)
    m = img.split()[3]
    spr, p = finish(img, m, blur=10, alpha=55, dy=6)
    return spr, (-(S_ / 2) / SS - p, -(S_ / 2) / SS - p)


def background(w=1280, h=720, top=(236, 244, 249), bottom=(206, 223, 234), dots=(150, 175, 200), margin=60):
    """グラデーション＋点の格子＋左上のやわらかい光。margin ぶん大きく作り、ゆっくり流す"""
    W_, H_ = w + margin * 2, h + margin * 2
    g = Image.new("RGB", (1, H_))
    for y in range(H_):
        u = y / (H_ - 1); g.putpixel((0, y), tuple(int(top[i] * (1 - u) + bottom[i] * u) for i in range(3)))
    im = g.resize((W_, H_)).convert("RGBA")
    glow = Image.new("L", (W_, H_), 0); ImageDraw.Draw(glow).ellipse([-W_ * 0.1, -H_ * 0.5, W_ * 0.6, H_ * 0.6], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im.alpha_composite(Image.merge("RGBA", [Image.new("L", (W_, H_), 255)] * 3 + [glow]))
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, H_, 36):
        for x in range(0, W_, 36):
            d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=dots + (70,))
    return im


class Stage:
    """1 コマずつ組む。add(sprite, 中心, 出る時刻, 消える時刻, 動き)"""
    def __init__(self, bg, w=1280, h=720, drift=(40, 18), dur=30.0, t0=0.0):
        self.bg, self.w, self.h, self.drift, self.dur, self.t0 = bg, w, h, drift, dur, t0
        self.items = []

    def add(self, spr, center, t_in, t_out=1e9, pop=True, slide=None, bob=0.0, z=0, fade_out=0.25, hop=()):
        sp, off = spr
        self.items.append(dict(sp=sp, off=off, c=center, a=t_in, b=t_out, pop=pop, slide=slide, bob=bob, z=z, fo=fade_out, hop=hop))
        return self.items[-1]

    def frame(self, t):
        m = (self.bg.width - self.w) // 2
        u = min(max((t - self.t0) / max(self.dur, 1e-3), 0.0), 1.0)
        ox = int(m - self.drift[0] / 2 + self.drift[0] * u); oy = int(m - self.drift[1] / 2 + self.drift[1] * u)
        im = self.bg.crop((ox, oy, ox + self.w, oy + self.h))
        for it in sorted(self.items, key=lambda i: i["z"]):
            if t < it["a"] or t >= it["b"] + it["fo"]: continue
            k = (t - it["a"]) / 0.32
            s = ease_out_back(k) if it["pop"] else 1.0
            al = ease(k * 1.6)
            if t > it["b"]: al *= 1 - (t - it["b"]) / it["fo"]
            cx, cy = it["c"]
            if it["slide"]:
                e = ease((t - it["a"]) / 0.45); cx += it["slide"][0] * (1 - e); cy += it["slide"][1] * (1 - e); s = 1.0
            if it["bob"]: cy += math.sin(t * 2.4 + cx) * it["bob"]
            for h0 in it["hop"]:
                if h0 <= t < h0 + 0.42: cy -= math.sin((t - h0) / 0.42 * math.pi) * 22
            sp = it["sp"]
            if abs(s - 1) > 0.004:
                sw, sh = max(1, int(sp.width * s)), max(1, int(sp.height * s))
                sp = sp.resize((sw, sh), Image.BILINEAR)
            if al < 0.999:
                a_ = sp.split()[3].point(lambda v, al=al: int(v * al)); sp = sp.copy(); sp.putalpha(a_)
            x = int(cx + it["off"][0] * s); y = int(cy + it["off"][1] * s)
            im.alpha_composite(sp, (x, y))
        return im.convert("RGB")
