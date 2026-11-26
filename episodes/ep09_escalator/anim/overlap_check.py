# 9本目 v4：札どうしの重なりを数える（cover_check.py の頭を写した）
#   MARU_WORK=<作業> python3 cover_check.py <描いたフォルダ> <フォントのフォルダ>
#   札・図ごとに、出ている間を 0.25 秒おきに、その札だけを透明な絵に描き、まるロボの体の真ん中（maru_c）が
#   札の四角の中に入る時間を出す（v2 の点検で、頭（maru_top）が隠れるのも数えるようにした）（COVER 札の種類 時刻 隠れる割合）。まるロボを指す札（ring・bubble）は数えない
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



# 札と札（図・地図・小窓）が重ならないかを数える（9本目 v4 のコメント 4:42「いまここの図解と順番のテロップが重なってる」）
#   0.25 秒ごとに、出ている札を 1 つずつ透明な絵に描いて、四角どうしが重なる所を出す（OVERLAP 札1 札2 時刻 重なりの大きさ）
ALL = OV.ev_list()
OV.D.FDIR[0] = FONTS
def bbox_of(ev, t):
    OV.EVENTS = [ev]
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); OV.draw(t, im, where)
    return im.getchannel("A").point(lambda v: 255 if v > 60 else 0).getbbox()
res = {}
T0 = min(e[0] for e in ALL); T1 = max(e[1] for e in ALL); t = T0
while t < T1:
    act = [e for e in ALL if e[0] + 0.15 <= t < e[1] - 0.1 and e[2] not in ("tint",)]
    if len(act) >= 2:
        bbs = [(e, bbox_of(e, t)) for e in act]
        for i in range(len(bbs)):
            for j in range(i + 1, len(bbs)):
                (ea, a), (eb, b) = bbs[i], bbs[j]
                if not a or not b: continue
                w_ = min(a[2], b[2]) - max(a[0], b[0]); h_ = min(a[3], b[3]) - max(a[1], b[1])
                if w_ > 4 and h_ > 4:
                    k = (ea[2], round(ea[0], 1), eb[2], round(eb[0], 1))
                    r = res.setdefault(k, [t, t, 0, 0]); r[1] = t; r[2] += 1; r[3] = max(r[3], w_ * h_)
    t += 0.25
for (ka, ta, kb, tb), (a, b, n, ar) in sorted(res.items(), key=lambda x: x[1][0]):
    print("OVERLAP %-9s %-9s %7.2f〜%7.2f %d回 %dpx²" % (ka, kb, a, b, n, ar))
print("OVERLAP_DONE", len(res))
