# 9本目 v2（36 章で、上のものさしの図がまるロボを隠した）：札・図が、まるロボ（体の真ん中・頭）を隠す所を数える
#   MARU_WORK=<作業> python3 cover_check.py <描いたフォルダ> <フォントのフォルダ>
#   札・図ごとに、出ている間を 0.25 秒おきに、その札だけを透明な絵に描き、まるロボの体の真ん中（maru_c）が
#   札の四角の中に入る時間を出す（COVER 札の種類 時刻 隠れる割合）。まるロボを指す札（ring・bubble）は数えない
import os, sys, json, glob
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import overlays as OV

R3, FONTS = sys.argv[1], sys.argv[2]
CL = json.load(open(os.path.join(HERE, "clips.json")))
ORDER = sorted(CL, key=lambda k: CL[k][2])
LOG = {}
for nm in CL:
    p = os.path.join(R3, nm, nm + "_log.json")
    if os.path.exists(p): LOG[nm] = json.load(open(p))
FPS = 24


def clip_at(t):
    cur = None
    for nm in ORDER:
        if CL[nm][2] <= t: cur = nm
    return cur or ORDER[0]


def where(name, t):
    nm = clip_at(t)
    if nm not in LOG or name not in LOG[nm]["track"]: return None
    tr = LOG[nm]["track"][name]
    if not tr: return None
    k = (t - CL[nm][0]) * FPS
    b = min(tr, key=lambda r: abs(r[0] - k))
    return None if b[3] <= 0 else (b[1], b[2])


SKIP = ("ring", "bubble", "vline", "tint", "dbl")
ALL = OV.ev_list()
OV.D.FDIR[0] = FONTS
bad = 0
for ev in ALL:
    t0, t1, kind, p = ev
    if kind in SKIP: continue
    OV.EVENTS = [ev]
    n = hit = 0; t = t0 + 0.3
    while t < t1 - 0.2:
        m = where("maru_c", t)
        if m is not None and 0 <= m[0] <= 1280 and 0 <= m[1] <= 720:
            im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
            OV.draw(t, im, where)
            bb = im.getchannel("A").point(lambda v: 255 if v > 100 else 0).getbbox()
            n += 1
            if bb and bb[0] <= m[0] <= bb[2] and bb[1] <= m[1] <= bb[3]: hit += 1
        t += 0.25
    if hit:
        bad += 1
        print("COVER %-9s %7.1f〜%7.1f  まるロボが隠れる %d/%d（%s）" % (kind, t0, t1, hit, n, clip_at(t0)))
print("COVER_DONE 隠す札 %d" % bad)
