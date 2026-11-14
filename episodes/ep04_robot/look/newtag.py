# 3D の場面の札を、新しい形（design.pill：影つき・角の丸い札・しっぽと 1 つの形）で描く（ep04 v10「チープ感」「吹き出しの形雑すぎ」）
#   board_overlay.py の tag・preview.py の tag の代わり。返す：札の四角（x0, y0, x1, y1）
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
from PIL import ImageDraw


def tag_new(im, text, cx, cy, size=48, bg=(255, 255, 255), fg=None, tail=None, fontdir=None):
    if fontdir and not D.FDIR[0]: D.FDIR[0] = fontdir
    fg = fg or D.NAVY
    f = D.font(size); bb = ImageDraw.Draw(im).textbbox((0, 0), text, font=f); w, th = bb[2] - bb[0], bb[3] - bb[1]
    cx = min(max(cx, w / 2 + 40), 1280 - w / 2 - 40)
    rel = None
    if tail:
        dx, dy = tail[0] - cx, tail[1] - cy
        h2 = th / 2 + 16
        rel = (max(min(dx, w / 2 + 60), -w / 2 - 60), dy if abs(dy) > h2 + 10 else (h2 + 30) * (1 if dy >= 0 else -1))
    spr, off = D.pill(text, size, fg=fg, bg=tuple(bg[:3]), tail=rel)
    if im.mode == "RGBA": im.alpha_composite(spr, (int(cx + off[0]), int(cy + off[1])))
    else: im.paste(spr, (int(cx + off[0]), int(cy + off[1])), spr)
    return cx - w / 2 - 30, cy - th / 2 - 16, cx + w / 2 + 30, cy + th / 2 + 16
