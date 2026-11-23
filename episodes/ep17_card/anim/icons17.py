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


