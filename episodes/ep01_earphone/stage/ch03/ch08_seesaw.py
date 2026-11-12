# 第8章の天びん（2D の図）に乗るまるロボ（2026-11-09 ユーザー案）。Blender の外でも同じ計算
#   A（本編 15:33 ごろ・台本 162「待つ余裕を増やすことと、すぐに音が出ることは、いつも両立するとは限りません」）
#     左の「ためる」側に立ち、下の札を見る → 右の「すぐ音が出る」側へ渡る → 上がってしまった左をふり返り、首をかしげる
#   B（本編 16:44 ごろ・台本 174〜176「音が途切れにくいこと。／操作に対して、音がすぐに返ってくること。／使い方に合わせて、その両方を考える…」）
#     左の「途切れにくい」側でうなずく → 右の「すぐ返ってくる」側へ走る → 止まりきれず、板も傾き続けて「おっとっと」→ 真ん中まで慎重に下がる → 釣り合って、うなずく
#
# 天びんは本物の天びんとして動かす：重心が支点より下にあるので、まるロボ（の重心）が x m ずれた所に立つと tan β ＝ K·x で釣り合う。
#   β'' ＝ ω0²（K·x·cos β − sin β）− 2ζω0·β'。1 周 1.7 秒・減衰比 0.22：少し遅れて傾き、止まると行き過ぎて戻る
# まるロボは板の座標（x＝板に沿って、z＝板の上面から上）で歩かせ（marumotion）、毎コマ、板の傾きで世界の座標へ回す：
#   体（根元）は板の上の点の真上（体はまっすぐ立ったまま）、足は板といっしょに回す（足の裏が板に沿う。足首の前後の向き＝pitch に β を足す）
# 2D の図との対応：天びんの腕 300px（1280×720 の図の座標）＝ 2.1m（まるロボの背の高さ 1.3m が図の 4 分の 1 ほど）。支点の中心 ＝ 世界の原点。板の厚み 10px
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "maru"))
import numpy as np
import marumotion as mm

PL = {p["no"]: p for p in json.load(open(os.path.join(HERE, "..", "voice", "achernar", "placement.json"), encoding="utf-8"))}
def L(n): return PL[n]["start"]
def LE(n): return PL[n]["end"]
def at_char(n, k): t = PL[n]["text"]; return L(n) + (LE(n) - L(n)) * k / len(t)

FPS = 24
ARM_PX, ARM_M = 300.0, 2.1                      # 図の腕の長さ（px）＝ 世界の長さ（m）
PXM = ARM_PX / ARM_M                             # 図の 1m（px、1280×720 の座標）
THICK_PX = 10.0; HB = THICK_PX / PXM             # 板の厚み
K_TILT = math.tan(math.radians(15.0)) / 1.5      # 釣り合いの傾き：x＝1.5m で 15°
W0 = 2 * math.pi / 1.7; ZETA = 0.22              # 天びんの揺れ：1 周 1.7 秒・減衰比
# 描く範囲（世界の座標、正面からの平行投影）：x −2.6〜2.6m、z −0.8〜1.9m。本番（1920×1080）の大きさ（図の 1.5 倍）で描く
RPXM = 1.5 * PXM; VIEW_W, VIEW_XC, VIEW_ZC = 5.2, 0.0, 0.55
RES_W = int(round(VIEW_W * RPXM / 2)) * 2; RES_H = int(round(2.7 * RPXM / 2)) * 2; VIEW_H = RES_H / RPXM
SCN = {"A": dict(t_in=L(162) - 0.3, t_out=L(163) - 0.4), "B": dict(t_in=L(174) - 0.3, t_out=L(177) - 0.4)}
for v in SCN.values(): v["t0"] = v["t_in"] - 0.4; v["n"] = int(math.ceil((v["t_out"] - v["t0"]) * FPS)) + 2


def until(pl, t_abs, t0, shifts=False):
    pl.idle(max(t_abs - t0 - pl.t, 0.05), shifts=shifts, glance=False)


def teeter(pl, label=None, amp=13.0, f=1.6, decay=2.4, dur=1.7):
    """おっとっと：止まった所で板がまだ傾き続け、前へのめりかける（＋）→ 後ろへ戻しすぎ（−）→ 揺れがだんだん収まる。
    目を見開き（反射のまばたき）、アンテナの灯が 3 回点滅、すばやく小さく一歩下がる。横にも少し揺れる"""
    lid = pl._lb(label); t0 = pl.t
    pl.blinks.append((t0 + 0.10, "fast")); pl.no_blink.append((t0 - 0.2, t0 + 1.4))
    pl.tracks["iris"].set(t0 + 0.08, 0.08, 0.28); pl.tracks["iris"].set(t0 + 1.25, 0.5, 0.0)
    w = 2 * math.pi * f
    pl.layer(t0, t0 + dur, lambda t, t0=t0: {
        "pitch": amp * math.exp(-decay * (t - t0)) * math.sin(w * (t - t0)),
        "roll": 0.30 * amp * math.exp(-decay * (t - t0)) * math.sin(w * (t - t0) + 1.3),
        "light": 1.5 * sum(mm.hump(t, t0 + 0.22 + 0.18 * k, 0.1) for k in range(3))})
    pl.event(t0 + 0.08, "beep_surprise", 0.6)
    pl.t = t0 + 0.30
    back = np.array(pl._p) - mm.fwd(pl._psi) * 0.22
    pl.back_to(tuple(back), step=0.12, sw=0.20, gap=0.02, look=False)       # 小さく、すばやく一歩下がる（足を入れかえて踏んばる）
    pl.t = max(pl.t, t0 + dur); pl._lb_end(lid); return pl


def plan_A():
    t0 = SCN["A"]["t0"]
    pl = mm.Plan(pos=(-1.15, 0.0), heading=-90.0, seed=23)                 # 左の「ためる」側に、右を向いて立っている（すぐ歩き出せる）
    until(pl, L(162) + 0.15, t0)
    pl.look(yaw=-58.0, pitch=-26.0, hold=0.55, label="ためる側の札を見る")  # 右向きなので、手前（こちら）＝まるロボの右。下の札をのぞく（目線は歩き出しで前へ戻る）
    until(pl, at_char(162, 11) - 0.6, t0)                                  # 「すぐに音が出ることは」で歩き出す（足の運びの出だしの分、少し前から）
    pl.walk_to((1.0, 0.0), speed=mm.V_BRISK, label="すぐ音が出る側へ")
    pl.look(yaw=-55.0, pitch=12.0, hold=0.15, label="上がった左をふり返る")
    pl.confused(label="両立しない？")
    pl.idle(1.0, shifts=False, glance=False)
    return pl


def plan_B():
    t0 = SCN["B"]["t0"]
    pl = mm.Plan(pos=(-1.2, 0.0), heading=-90.0, seed=29)                 # 左の「途切れにくい」側に、右を向いて立っている
    until(pl, L(174) + 0.05, t0)
    pl.look(yaw=-55.0, pitch=-8.0, hold=0.1, label="こちらを見る")
    pl.nod(n=1, amp=9.0, label="途切れにくい側")
    until(pl, L(175) + 0.05, t0)                                           # 「操作に対して、音がすぐに返ってくること」
    pl.run_to((1.15, 0.0), label="すぐ返ってくる側へ走る")
    teeter(pl, label="おっとっと", dur=1.5)
    pl.back_to((0.0, 0.0), step=0.40, sw=0.22, gap=0.03, look=True, label="真ん中まで慎重に下がる")
    pl.look(yaw=-50.0, pitch=0.0, hold=0.0)
    pl.nod(n=1, amp=10.0, label="釣り合った")
    pl.idle(1.5, shifts=False, glance=False)
    return pl


PLANS = {"A": plan_A, "B": plan_B}


def com_x(fr):
    """重心の x（板に沿って）：根元の x ＋ 胴の前後の傾きのぶん"""
    psi = fr["psi"]; f_ = (-math.sin(psi), math.cos(psi))
    return fr["root"][0] + math.sin(math.radians(fr["pitch"])) * (mm.TORSO_Z - mm.HIP_Z) * f_[0]


def beam_angles(frames, fps=FPS, sub=20):
    """β（rad、＋＝右の端が下がる）を毎コマ。最初は釣り合った角度で止まっている"""
    xs = [com_x(fr) for fr in frames]
    th = math.atan(K_TILT * xs[0]); om = 0.0; dt = 1.0 / fps / sub; out = []
    for i in range(len(xs)):
        out.append(th)
        xa, xb = xs[i], xs[min(i + 1, len(xs) - 1)]
        for s in range(sub):
            x = xa + (xb - xa) * (s + 0.5) / sub
            acc = W0 * W0 * (K_TILT * x * math.cos(th) - math.sin(th)) - 2 * ZETA * W0 * om
            om += acc * dt; th += om * dt
    return out


def to_world(fr, beta):
    """板の座標 → 世界の座標（支点の中心が原点。板の上面は z＝HB/2）"""
    c, s = math.cos(beta), math.sin(beta)
    def R(x, y, z): return [x * c + z * s, y, -x * s + z * c]
    g = dict(fr); x, y, z = fr["root"]
    bx, by, bz = R(x, y, HB / 2); g["root"] = [bx, by, bz + z]             # 体はまっすぐ：板の上の点の真上
    feet = []
    for ft in fr["feet"]:
        a = ft["ankle"]; nf = dict(ft)
        nf["ankle"] = R(a[0], a[1], a[2] + HB / 2)                          # 足は板といっしょに回る
        nf["pitch"] = ft["pitch"] + math.degrees(beta) * math.sin(ft["psi"])  # 足の裏を板に沿わせる（横向きのとき正確。向きを変える途中は近い値）
        feet.append(nf)
    g["feet"] = feet
    return g


def build(sc):
    v = SCN[sc]; pl = PLANS[sc]()
    fr = mm.simulate(pl, fps=FPS, t_end=v["n"] / FPS + 0.5)[:v["n"]]
    while len(fr) < v["n"]: fr.append(fr[-1])
    beta = beam_angles(fr)
    return dict(t0=v["t0"], fps=FPS, n=v["n"], beta=beta, local=fr, frames=[to_world(f_, b_) for f_, b_ in zip(fr, beta)], plan=pl)


if __name__ == "__main__":
    for sc in ("A", "B"):
        d = build(sc); pl = d["plan"]; t0 = d["t0"]
        print("== %s  t0 %.2f  frames %d  plan end %.2f (scene out %.2f)" % (sc, t0, d["n"], t0 + pl.t, SCN[sc]["t_out"]))
        for a, b, lab in pl.labels: print("   %7.2f-%7.2f  %s" % (t0 + a, t0 + (b if b is not None else a), lab))
        bd = [math.degrees(b) for b in d["beta"]]
        print("   " + "  ".join("%.1f:%+.2f/%+.1f" % (t0 + k / FPS, d["local"][k]["root"][0], bd[k]) for k in range(0, d["n"], 12)))
        print("   β min %.1f° max %.1f°  end %.1f°" % (min(bd), max(bd), bd[-1]))
