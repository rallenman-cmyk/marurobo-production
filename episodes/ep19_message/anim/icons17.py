# 17本目（カード）：札・画面・カードで使う、字のない絵（3D の絵 make_tex17.py と、2D の札 overlays.py の両方で使う）。16本目から写した
from PIL import ImageDraw
TEAL = (47, 217, 200); NAVY = (24, 38, 74); WHITE = (255, 255, 255); ORANGE = (255, 154, 60); CASTLE = (120, 96, 170)


def castle_logo(d, cx, cy, r, col=CASTLE):
    """架空のお店の印：丸の中にお城の形（どこの会社とも言えない形）"""
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    w = r * 1.1; h = r * 0.7; x0 = cx - w / 2; y1 = cy + h * 0.55
    d.rectangle((x0, cy - h * 0.2, x0 + w, y1), fill=WHITE)
    for k in range(5):
        if k % 2 == 0: d.rectangle((x0 + k * w / 5, cy - h * 0.45, x0 + (k + 1) * w / 5, cy - h * 0.2), fill=WHITE)
    d.pieslice((cx - w * 0.16, y1 - h * 0.5, cx + w * 0.16, y1 + h * 0.1), 180, 360, fill=col)
    d.rectangle((cx - w * 0.16, y1 - h * 0.2, cx + w * 0.16, y1), fill=col)


def icon(d, kind, cx, cy, r, col):
    """名札の 4 つの絵（字なし）：face＝まるロボの丸い顔／house＝家／phone＝電話／mail＝手紙。ほかの札の cake・bldg・bag"""
    if kind == "face":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(236, 240, 244), outline=col, width=int(r * 0.12))
        d.ellipse((cx - r * 0.38, cy - r * 0.38, cx + r * 0.38, cy + r * 0.38), fill=TEAL)
        d.line((cx, cy - r, cx, cy - r * 1.35), fill=col, width=int(r * 0.12)); d.ellipse((cx - r * 0.13, cy - r * 1.5, cx + r * 0.13, cy - r * 1.24), fill=TEAL)
    elif kind == "house":
        d.polygon([(cx - r, cy - r * 0.05), (cx, cy - r * 0.95), (cx + r, cy - r * 0.05)], fill=col)
        d.rectangle((cx - r * 0.72, cy - r * 0.1, cx + r * 0.72, cy + r * 0.85), fill=col)
        d.rectangle((cx - r * 0.2, cy + r * 0.3, cx + r * 0.2, cy + r * 0.85), fill=WHITE)
    elif kind == "phone":
        d.rounded_rectangle((cx - r * 0.5, cy - r * 0.9, cx + r * 0.5, cy + r * 0.9), radius=r * 0.18, fill=col)
        d.rounded_rectangle((cx - r * 0.38, cy - r * 0.7, cx + r * 0.38, cy + r * 0.55), radius=r * 0.06, fill=WHITE)
        d.ellipse((cx - r * 0.09, cy + r * 0.63, cx + r * 0.09, cy + r * 0.81), fill=WHITE)
    elif kind == "mail":
        d.rectangle((cx - r, cy - r * 0.65, cx + r, cy + r * 0.65), fill=col)
        d.line((cx - r, cy - r * 0.65, cx, cy + r * 0.1, cx + r, cy - r * 0.65), fill=WHITE, width=int(r * 0.14))
    elif kind == "cake":
        d.rectangle((cx - r * 0.85, cy - r * 0.1, cx + r * 0.85, cy + r * 0.75), fill=col)
        d.rectangle((cx - r * 0.85, cy + r * 0.2, cx + r * 0.85, cy + r * 0.32), fill=WHITE)
        for k in (-1, 0, 1):
            d.rectangle((cx + k * r * 0.45 - r * 0.06, cy - r * 0.6, cx + k * r * 0.45 + r * 0.06, cy - r * 0.1), fill=col)
            d.ellipse((cx + k * r * 0.45 - r * 0.1, cy - r * 0.85, cx + k * r * 0.45 + r * 0.1, cy - r * 0.6), fill=ORANGE)
    elif kind == "bldg":
        d.rectangle((cx - r * 0.6, cy - r * 0.95, cx + r * 0.6, cy + r * 0.9), fill=col)
        for i in range(3):
            for j in range(2):
                x = cx - r * 0.35 + j * r * 0.45; y = cy - r * 0.7 + i * r * 0.5
                d.rectangle((x, y, x + r * 0.25, y + r * 0.28), fill=WHITE)
    elif kind == "bag":
        d.rectangle((cx - r * 0.75, cy - r * 0.35, cx + r * 0.75, cy + r * 0.85), fill=col)
        d.arc((cx - r * 0.4, cy - r * 0.85, cx + r * 0.4, cy + r * 0.05), 180, 360, fill=col, width=int(r * 0.14))




def icon5(d, kind, cx, cy, r, col=NAVY):
    """5章の絵（字なし）：テストの板（apple・car・tree・sun・fish・cup・flower・star・boat）と、設定の段（bell・receipt・shield・handset）、本人確認の例（keypad・finger）"""
    W_ = max(2, int(r * 0.12))
    if kind == "apple":
        d.ellipse((cx - r * 0.75, cy - r * 0.55, cx + r * 0.75, cy + r * 0.85), fill=(226, 58, 48))
        d.line((cx, cy - r * 0.55, cx + r * 0.1, cy - r * 0.9), fill=(110, 70, 40), width=W_)
        d.ellipse((cx + r * 0.1, cy - r * 0.95, cx + r * 0.5, cy - r * 0.7), fill=(70, 160, 80))
    elif kind == "car":
        d.rounded_rectangle((cx - r * 0.95, cy - r * 0.15, cx + r * 0.95, cy + r * 0.45), radius=r * 0.15, fill=(52, 120, 230))
        d.rounded_rectangle((cx - r * 0.5, cy - r * 0.55, cx + r * 0.45, cy - r * 0.1), radius=r * 0.15, fill=(52, 120, 230))
        for sx in (-1, 1): d.ellipse((cx + sx * r * 0.55 - r * 0.22, cy + r * 0.3, cx + sx * r * 0.55 + r * 0.22, cy + r * 0.74), fill=(40, 46, 52))
    elif kind == "tree":
        d.rectangle((cx - r * 0.12, cy + r * 0.2, cx + r * 0.12, cy + r * 0.9), fill=(110, 70, 40))
        d.ellipse((cx - r * 0.7, cy - r * 0.9, cx + r * 0.7, cy + r * 0.4), fill=(70, 160, 80))
    elif kind == "sun":
        import math as _mm
        for k in range(8):
            a = k * _mm.pi / 4; d.line((cx + r * 0.55 * _mm.cos(a), cy + r * 0.55 * _mm.sin(a), cx + r * 0.95 * _mm.cos(a), cy + r * 0.95 * _mm.sin(a)), fill=(255, 190, 40), width=W_)
        d.ellipse((cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45), fill=(255, 200, 50))
    elif kind == "fish":
        d.ellipse((cx - r * 0.8, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4), fill=(255, 154, 60))
        d.polygon([(cx + r * 0.3, cy), (cx + r * 0.9, cy - r * 0.45), (cx + r * 0.9, cy + r * 0.45)], fill=(255, 154, 60))
        d.ellipse((cx - r * 0.55, cy - r * 0.15, cx - r * 0.35, cy + r * 0.05), fill=NAVY)
    elif kind == "cup":
        d.rectangle((cx - r * 0.55, cy - r * 0.5, cx + r * 0.4, cy + r * 0.7), fill=(138, 77, 255))
        d.arc((cx + r * 0.15, cy - r * 0.3, cx + r * 0.8, cy + r * 0.35), 270, 90, fill=(138, 77, 255), width=W_ * 2)
    elif kind == "flower":
        for (ox, oy) in ((0, -0.45), (0.43, -0.14), (0.27, 0.36), (-0.27, 0.36), (-0.43, -0.14)):
            d.ellipse((cx + ox * r - r * 0.3, cy + oy * r - r * 0.3, cx + ox * r + r * 0.3, cy + oy * r + r * 0.3), fill=(232, 98, 122))
        d.ellipse((cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22), fill=(255, 210, 74))
    elif kind == "star":
        import math as _mm
        pts = []
        for k in range(10):
            a = -_mm.pi / 2 + k * _mm.pi / 5; rr = r * (0.9 if k % 2 == 0 else 0.4)
            pts.append((cx + rr * _mm.cos(a), cy + rr * _mm.sin(a)))
        d.polygon(pts, fill=(255, 200, 50))
    elif kind == "boat":
        d.polygon([(cx - r * 0.9, cy + r * 0.2), (cx + r * 0.9, cy + r * 0.2), (cx + r * 0.55, cy + r * 0.7), (cx - r * 0.55, cy + r * 0.7)], fill=(110, 70, 40))
        d.polygon([(cx, cy - r * 0.9), (cx, cy + r * 0.1), (cx + r * 0.6, cy + r * 0.1)], fill=(52, 120, 230))
    elif kind == "bell":
        d.pieslice((cx - r * 0.7, cy - r * 0.8, cx + r * 0.7, cy + r * 0.6), 180, 360, fill=col)
        d.rectangle((cx - r * 0.7, cy - r * 0.1, cx + r * 0.7, cy + r * 0.45), fill=col)
        d.rectangle((cx - r * 0.85, cy + r * 0.4, cx + r * 0.85, cy + r * 0.58), fill=col)
        d.ellipse((cx - r * 0.18, cy + r * 0.55, cx + r * 0.18, cy + r * 0.9), fill=col)
    elif kind == "receipt":
        d.polygon([(cx - r * 0.6, cy - r * 0.9), (cx + r * 0.6, cy - r * 0.9), (cx + r * 0.6, cy + r * 0.9), (cx + r * 0.3, cy + r * 0.75), (cx, cy + r * 0.9), (cx - r * 0.3, cy + r * 0.75), (cx - r * 0.6, cy + r * 0.9)], fill=col)
        for k in range(4): d.rectangle((cx - r * 0.4, cy - r * 0.6 + k * r * 0.35, cx + r * (0.4 if k % 2 == 0 else 0.15), cy - r * 0.5 + k * r * 0.35), fill=WHITE)
    elif kind == "shield":
        d.polygon([(cx, cy - r * 0.95), (cx + r * 0.8, cy - r * 0.6), (cx + r * 0.65, cy + r * 0.4), (cx, cy + r * 0.95), (cx - r * 0.65, cy + r * 0.4), (cx - r * 0.8, cy - r * 0.6)], fill=col)
        d.ellipse((cx - r * 0.2, cy - r * 0.5, cx + r * 0.2, cy - r * 0.1), fill=WHITE)
        d.pieslice((cx - r * 0.4, cy - r * 0.05, cx + r * 0.4, cy + r * 0.6), 180, 360, fill=WHITE)
    elif kind == "handset":
        d.arc((cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9), 120, 240, fill=col, width=int(r * 0.35))
        d.ellipse((cx - r * 0.95, cy - r * 0.95, cx - r * 0.35, cy - r * 0.45), fill=col)
        d.ellipse((cx - r * 0.95, cy + r * 0.45, cx - r * 0.35, cy + r * 0.95), fill=col)
        for k in range(3): d.arc((cx - r * (0.1 + 0.25 * k), cy - r * (0.4 + 0.25 * k), cx + r * (0.4 + 0.25 * k), cy + r * (0.4 + 0.25 * k)), 320, 40, fill=col, width=W_)
    elif kind == "keypad":       # スマホに届いた数字を打ちこむ（4 つのますに丸。数字は書かない）
        icon(d, "phone", cx, cy, r, col)
        for k in range(4): d.rounded_rectangle((cx - r * 0.33 + k * r * 0.17, cy - r * 0.2, cx - r * 0.2 + k * r * 0.17, cy + r * 0.0), radius=2, fill=(52, 120, 230))
    elif kind == "finger":       # 指で画面にふれる
        icon(d, "phone", cx - r * 0.2, cy, r, col)
        d.rounded_rectangle((cx + r * 0.05, cy - r * 0.15, cx + r * 0.32, cy + r * 1.0), radius=r * 0.13, fill=(244, 200, 160), outline=col, width=W_)
        d.ellipse((cx - r * 0.1, cy - r * 0.35, cx + r * 0.35, cy + r * 0.1), outline=(52, 120, 230), width=W_)
