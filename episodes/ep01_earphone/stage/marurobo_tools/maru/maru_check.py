# 動きの部品集の点検：見本リールの予定を計算し、物理の数値をグラフと表にする（Blender なし）
import sys, os, math, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import marumotion as mm
from maru_reel_plan import reel_plan, extra_plan
for fp in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",):
    if os.path.exists(fp): font_manager.fontManager.addfont(fp); plt.rcParams["font.family"] = "IPAGothic"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "check")
PLAN = sys.argv[2] if len(sys.argv) > 2 else "main"
os.makedirs(OUT, exist_ok=True)
t0 = time.time(); p = reel_plan() if PLAN == "main" else extra_plan(); fr = mm.simulate(p, fps=24)
print("plan", round(p.t, 2), "s,", len(fr), "frames, sim", round(time.time() - t0, 1), "s")
t = np.array([f["t"] for f in fr]); root = np.array([f["root"] for f in fr])
hip = root[:, 2] + mm.HIP_Z
ank = np.array([[f["feet"][j]["ankle"] for j in (0, 1)] for f in fr])
mode = np.array([[f["feet"][j]["mode"] for j in (0, 1)] for f in fr])
ext = np.array([[f["feet"][j]["ext"] for j in (0, 1)] for f in fr])
ant = np.degrees(np.array([f["ant"] for f in fr]))
v = np.array([f["v"] for f in fr]); a = np.array([f["a"] for f in fr]); pitch = np.array([f["pitch"] for f in fr])
roll = np.array([f["roll"] for f in fr]); twist = np.array([f["twist"] for f in fr])
iris = np.array([f["iris"]["scale"] for f in fr]); light = np.array([f["light"] for f in fr])
# ---- 足が滑っていないか：同じ足場にいる間（べた足のとき）、足首の水平位置が変わらない
slide = []
for j in (0, 1):
    for i in range(1, len(fr)):
        if any(fr[i - 1]["t"] <= tc <= fr[i]["t"] + 1e-9 for tc in p.cuts): continue
        if mode[i, j] == "stance" and mode[i - 1, j] == "stance" and abs(fr[i]["feet"][j]["pitch"]) < 1e-6 and abs(fr[i - 1]["feet"][j]["pitch"]) < 1e-6:
            slide.append(np.linalg.norm(ank[i, j, :2] - ank[i - 1, j, :2]))
print("flat-stance ankle slip per frame: max %.5f m (n=%d)" % (max(slide), len(slide)))
gap = np.array([f["gap"] for f in fr])
print("ankle-ball to body clearance: min %.3f m (negative = inside the body); frames inside: %d" % (gap.min(), int((gap < 0).sum())))
shin = np.array([f["shin"] for f in fr])
print("shin top inside body: max r2 %.3f (>1 = shin top outside the body); frames outside: %d" % (shin.max(), int((shin > 1).sum())))
print("leg extension range: %.3f .. %.3f m" % (ext.min(), ext.max()))
print("antenna deflection: pitch %.1f..%.1f deg, side %.1f..%.1f deg" % (ant[:, 0].min(), ant[:, 0].max(), ant[:, 1].min(), ant[:, 1].max()))
print("torso pitch %.1f..%.1f, roll %.1f..%.1f, twist %.1f..%.1f" % (pitch.min(), pitch.max(), roll.min(), roll.max(), twist.min(), twist.max()))
# 歩きの区間ごとの数値
for lb in p.labels:
    a0, a1, txt = lb
    sel = (t >= a0) & (t <= a1)
    if not sel.any(): continue
    vv = v[sel]
    if vv.max() > 0.5 and np.any(v[sel] > 0.97 * vv.max()):
        cruise = sel & (v > 0.97 * vv.max())
        bob = hip[cruise].max() - hip[cruise].min() if cruise.any() else 0
        steps = [e for e in p.events if e["kind"] == "step" and a0 <= e["t"] <= a1]
        st = [e["t"] for e in steps if any(abs(e["t"] - tt) < 0.03 for tt in t[cruise])]
        rate = (len(st) - 1) / (st[-1] - st[0]) if len(st) > 2 else float("nan")
        print("%-14s vmax %.2f  bob %.3f m  steps/s %.2f  lean %+.1f..%+.1f deg  decel max %.2f" % (txt.split("｜")[0], vv.max(), bob, rate, pitch[sel].min(), pitch[sel].max(), -a[sel].min()))
# ---- グラフ
fig, ax = plt.subplots(7, 1, figsize=(16, 20), sharex=True)
ax[0].plot(t, v, label="速さ m/s"); ax[0].plot(t, a, label="加速度 m/s²", alpha=0.7); ax[0].legend(loc="upper right"); ax[0].set_title("進む向きの速さと加速度")
ax[1].plot(t, hip, label="脚の付け根の高さ m"); ax[1].plot(t, ank[:, 0, 2], label="左の足首の高さ"); ax[1].plot(t, ank[:, 1, 2], label="右の足首の高さ"); ax[1].legend(loc="upper right"); ax[1].set_title("高さ（上下の揺れ・跳ぶ）")
for j, c in ((0, "C0"), (1, "C3")):
    sx = ank[:, j, 0]; ax[2].plot(t, sx, c, lw=1.0, label="足首 x（%s）" % ("左" if j == 0 else "右"))
    st = mode[:, j] == "stance"; ax[2].plot(t[st], sx[st], c + ".", ms=2)
ax[2].plot(t, root[:, 0], "k--", lw=0.8, label="体 x"); ax[2].legend(loc="upper right"); ax[2].set_title("足の置き場所（点＝地面に着いている。平らな所＝滑っていない）")
ax[3].plot(t, ext[:, 0], label="左脚の伸び"); ax[3].plot(t, ext[:, 1], label="右脚の伸び"); ax[3].axhline(0.10, ls=":", c="k"); ax[3].axhline(-0.10, ls=":", c="k"); ax[3].plot(t, np.minimum(gap, 0.1), "k", lw=0.8, label="足首の玉と胴の隙間"); ax[3].legend(loc="upper right"); ax[3].set_title("脚の伸び縮み（±10cm 以内）と、足首の玉と胴の隙間（負＝胴に入る）")
ax[4].plot(t, pitch, label="前後の傾き（＋＝前）"); ax[4].plot(t, roll, label="左右の傾き（＋＝左）"); ax[4].plot(t, twist, label="ひねり（＋＝左）"); ax[4].legend(loc="upper right"); ax[4].set_title("胴の角度（度）")
ax[5].plot(t, ant[:, 0], label="アンテナ 前後"); ax[5].plot(t, ant[:, 1], label="アンテナ 左右"); ax[5].legend(loc="upper right"); ax[5].set_title("アンテナの振れ（度）：根元の加速度で揺れるばね 2.5Hz・減衰0.2")
ax[6].plot(t, iris, label="目の輪の大きさ"); ax[6].plot(t, light / 4, label="アンテナの光（÷4）"); ax[6].legend(loc="upper right"); ax[6].set_title("目と光")
for lb in p.labels:
    for x in ax: x.axvspan(lb[0], lb[1], color="0.92", zorder=-5)
    ax[0].text(lb[0], ax[0].get_ylim()[1] * 0.95, lb[2].split("｜")[0], fontsize=7, va="top")
ax[-1].set_xlabel("秒"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "reel_channels%s.png" % ("" if PLAN == "main" else "_" + PLAN)), dpi=70)
json.dump(p.events, open(os.path.join(OUT, "events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("labels:"); [print("  %6.2f-%6.2f %s" % (lb[0], lb[1], lb[2][:40])) for lb in p.labels]
