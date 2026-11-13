# 5章（どこまで隠したら読めなくなる？）の時刻とまるロボの動きの予定。声の時刻は本番の組み立て（chapters.py c5）と同じ（c5_v20_times.json）
#   PC で描くのは中の世界の場面（W29・W30・W28・W31・W31b）だけ。S10_low・S07_sh_step は冒頭、K16 は 1章の描画を使い回す
#   結び（end）は、全部これまでの章の描画の使い回し（W28 は 5章の W28 を使う）
import math, json, os
import marumotion as mm
import plan_util as U
from plan_util import at, cut, TILE_TOP, QZ_TOP
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
_J = json.load(open(os.path.join(HERE, 'c5_v20_times.json'), encoding='utf-8'))
LN = {k: tuple(v) for k, v in _J['lines'].items()}
SHOTS = [tuple(s) for s in _J['shots']]
T_END = _J['T_END']
def s(i, o=0.0): return LN[i][0] + o
def e(i, o=0.0): return LN[i][1] + o
def fr_of(t): return int(round(t * FPS)) + 1
WORLD_KEYS = {'W29', 'W30', 'W28', 'W31', 'W31b'}
def ranges(pad=0.5):
    out = []
    for a, b, k in SHOTS:
        if k not in WORLD_KEYS: continue
        if out and abs(out[-1][1] - a) < 1e-6: out[-1][1] = b
        else: out.append([a, b])
    return [(max(0.0, a - pad), min(T_END, b + pad)) for a, b in out]
WORLD_RANGES = ranges()
def shot_start(key, after=0.0): return next(a for a, b, k in SHOTS if k == key and a >= after - 1e-6)
def hd(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
N, MOD = 21, 1.5
H = N * MOD / 2
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
_A = json.load(open(os.path.join(HERE, 'qr_assets.json'), encoding='utf-8')); E = _A['experiments']
BOX_TOP = 1.0                                              # 箱の上（ふたの上）
P_STEP = rc(*E['robot_step']['center_rc']); P_STAND = rc(*E['robot_stand']['center_rc'])
P_SIDE = (H + 2.5, -H + 2.0)                               # 右下の白いフチ（大地を見る）
STATE = {'W29': 'robot_step', 'W30': 'ink12', 'W28': 'robot_stand', 'W31': 'logo7', 'W31b': 'logo7_ink1'}
# ---- 出来事の時刻
T_COUNT29 = s('29-03', 0.9)                                # 「壊れた箱は……10個」：1 つずつ灰色に
T_DROPS = s('30-05', 1.2)                                  # 12 か所に、しずくが順に落ちる
T_LOGO = s('31-03', 0.6)                                   # ロゴが透ける
T_COUNT31 = s('31-04', 0.6)                                # ロゴの下の 8 個が灰色に
T_DROP31 = shot_start('W31b') + 0.4                        # しずくが 1 つ落ちて、9 個目
def plan():
    U.LATE.clear()
    p = mm.Plan(pos=P_STEP, heading=200, ground=BOX_TOP)
    cut(p, shot_start('W29'), P_STEP, 200, BOX_TOP)
    at(p, T_COUNT29 + 0.2, lambda q: q.look(0, -24, hold=2.6, body=True, label='足もとの箱を数える'), 'count29')
    at(p, s('29-04', 0.6), lambda q: q.surprise(label='新しい箱にかかった'), 'step29')
    at(p, s('29-05', 0.8), lambda q: q.nod(n=2, amp=8.0, label='8 個まで'), 'nod29')
    cut(p, shot_start('W30'), P_SIDE, hd(P_SIDE, (0, 0)), QZ_TOP)
    at(p, T_DROPS + 0.2, lambda q: q.look_around(label='しずくを目で追う'), 'drops')
    at(p, s('30-05b', 0.8), lambda q: q.surprise(label='12 個'), 'n12')
    cut(p, shot_start('W28'), P_STAND, 200, BOX_TOP)
    at(p, s('30-06', 0.8), lambda q: q.look(0, -24, hold=2.4, body=True, label='足もとの 6 個'), 'w28')
    at(p, s('30-06b', 0.8), lambda q: q.nod(n=1, amp=10.0, label='まとまっていた'), 'w28b')
    cut(p, shot_start('W30', 80.0), P_SIDE, hd(P_SIDE, (0, 0)), QZ_TOP)
    at(p, s('30-07b', 0.6), lambda q: q.nod(n=2, amp=8.0, label='箱の数で決まる'), 'w30b')
    cut(p, shot_start('W31'), P_SIDE, hd(P_SIDE, (0, 0)), QZ_TOP)
    at(p, T_LOGO + 0.2, lambda q: q.awe(dur=2.6, pitch=10.0, label='ロゴの下を見る'), 'logo')
    at(p, s('31-05', 0.6), lambda q: q.think(dur=2.2, label='ぎりぎり'), 'logo2')
    cut(p, shot_start('W31b'), P_SIDE, hd(P_SIDE, (0, 0)), QZ_TOP)
    at(p, T_DROP31 + 0.4, lambda q: q.surprise(label='9 個目'), 'drop31')
    p.wait(max(0.0, WORLD_RANGES[-1][1] + 0.5 - p.t))
    return p
def frames():
    p = plan(); return p, mm.simulate(p, fps=FPS, t_end=p.t + 0.5)
if __name__ == '__main__':
    p, fr = frames(); print('frames', len(fr), 'LATE', U.LATE); print('WORLD', WORLD_RANGES)
