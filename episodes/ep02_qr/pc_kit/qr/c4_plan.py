# 4章（直す）の時刻とまるロボの動きの予定。声の時刻は本番の組み立て（chapters.py c4）と同じ（c4_v20_times.json）
#   秒は4章の頭から（24fps）。舞台は 3 つ：数字の空間（C・R）／QR の大地（G・W・B）／工場の机（F）。T35・T28 は冒頭の描画を使い回す
import math, json, os
import marumotion as mm
import plan_util as U
from plan_util import at, cut, TILE_TOP, QZ_TOP
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
_J = json.load(open(os.path.join(HERE, 'c4_v20_times.json'), encoding='utf-8'))
LN = {k: tuple(v) for k, v in _J['lines'].items()}
SHOTS = [tuple(s) for s in _J['shots']]
T_END = _J['T_END']
def s(i, o=0.0): return LN[i][0] + o
def e(i, o=0.0): return LN[i][1] + o
def fr_of(t): return int(round(t * FPS)) + 1
FIG = {'c4_bignum', 'c4_bits0', 'c4_bits1', 'D5a', 'D5b', 'D5c', 'D5d'}
STAGE = lambda k: 'crates' if k[0] in 'CR' else ('factory' if k[0] == 'F' else ('reuse' if k[0] == 'T' else ('fig' if k in FIG else 'world')))
def ranges(stage, pad=0.5):
    out = []
    for a, b, k in SHOTS:
        if STAGE(k) != stage: continue
        if out and abs(out[-1][1] - a) < 1e-6: out[-1][1] = b
        else: out.append([a, b])
    return [(max(0.0, a - pad), min(T_END, b + pad)) for a, b in out]
def shot_start(key, after=0.0): return next(a for a, b, k in SHOTS if k == key and a >= after - 1e-6)
def hd(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))

# ================================================================ 数字の空間（C・R）：青い箱 3 つ（数字は箱の顔。大きく）・台・汚れ・布
XS = [-5.4, -2.6, 0.2]
CRATE_RANGES = ranges('crates')
P_C1 = (XS[0] + 2.2, -2.2); P_C2 = (XS[2] + 1.35, -2.3); P_C7 = (XS[2] + 1.7, -2.6); P_C12A = (XS[2] + 1.7, -2.6); P_C12 = (XS[2] + 1.7, -2.6)   # 箱の前に立たない（箱の数字を隠さない）
P_R1 = (3.4, -2.6); P_R2 = (0.0, -2.6)
T_CRATES = [s('22-03', 1.0 + 0.7 * k) for k in range(3)]   # 「左から 2・5・3」：箱が順に降りてくる
T_CLOTH = s('22-04', 1.8)                                   # 真ん中の箱に布がかかる（隠す）
T_REVEAL = s('22-05c', 0.2)                                 # 布が取れて 5 が見える
T_STAIN = (shot_start('C6a'), shot_start('C6'))             # 黒い汚れが落ちて、5 が 7 に見える
T_STANDS = s('25-02', 0.6)                                  # ×1 ×2 ×3 の台がせり上がる（字は 2D）
T_GLOW2 = s('25-05b', 0.3)                                  # 2 番目の台が光る
T_FIX = s('25-06a', 2.4)                                    # 7 が 5 に戻る（汚れが消える）
T_DIAL = (s('27-01', 0.8), s('27-01', 3.8))                  # 0〜255 の輪を、光の点が 1 周
T_LINKS = s('27-02', 0.4)                                   # たくさんの予備の札から、箱へ線
def crate_plan():
    U.LATE.clear()
    p = mm.Plan(pos=P_C1, heading=hd(P_C1, (XS[0], 0)), ground=0.0)
    at(p, s('22-01', 1.0), lambda q: q.look(0, 10, hold=1.4, body=True, label='箱を見る'), 'c1')
    cut(p, shot_start('C2a'), P_C2, hd(P_C2, (XS[1], 0)), 0.0)
    at(p, T_CRATES[0] + 0.2, lambda q: q.look(30, 12, hold=2.6, body=True, label='降りてくる箱を順に見る'), 'see_crates')
    at(p, T_CLOTH + 0.4, lambda q: q.surprise(label='隠れた'), 'cloth')
    at(p, s('22-05b', 0.8), lambda q: q.think(dur=2.2, label='考える'), 'think')
    at(p, T_REVEAL + 0.4, lambda q: q.hops(n=2, label='5 だった'), 'reveal')
    at(p, T_STAIN[0] + 0.3, lambda q: q.surprise(label='汚れが落ちた'), 'stain')
    cut(p, shot_start('C7'), P_C7, hd(P_C7, (XS[0], 0)), 0.0)
    at(p, s('23-05', 0.8), lambda q: q.confused(label='どれがすり替わった？'), 'confused')
    at(p, s('23-05', 3.4), lambda q: q.look_around(label='3 つの箱を見比べる'), 'compare')
    cut(p, shot_start('C8'), P_C2, hd(P_C2, (4.9, 0)), 0.0)
    at(p, s('24-02', 0.8), lambda q: q.nod(n=1, amp=10.0, label='合計がずれている'), 'nod1')
    at(p, s('24-02b', 0.6), lambda q: q.think(dur=2.2, label='どれかは分からない'), 'think2')
    at(p, T_STANDS + 0.2, lambda q: q.look(40, -8, hold=1.6, body=True, label='台がせり上がる'), 'stands')
    at(p, s('25-04b', 0.6), lambda q: q.surprise(label='ちょうど 2 倍'), 'twice')
    cut(p, shot_start('C12a'), P_C12A, hd(P_C12A, (XS[1], 0)), 0.0)
    at(p, T_GLOW2 + 0.3, lambda q: q.look(0, 6, hold=1.4, body=True, label='光った台を見る'), 'glow2')
    cut(p, shot_start('C12'), P_C12, hd(P_C12, (XS[1], 0)), 0.0)
    at(p, T_FIX + 0.4, lambda q: q.hops(n=2, label='直った'), 'fixed')
    cut(p, shot_start('R1'), P_R1, hd(P_R1, (0, 0)), 0.0)
    at(p, T_DIAL[0] + 0.2, lambda q: q.look(-30, 22, hold=3.0, body=True, label='輪を目で追う'), 'dial')
    cut(p, shot_start('R2'), P_R2, 0.0, 0.0)
    at(p, T_LINKS + 0.4, lambda q: q.awe(dur=3.0, pitch=24.0, label='たくさんの線を見上げる'), 'links')
    at(p, s('27-03b', 0.8), lambda q: q.nod(n=2, amp=8.0, label='うなずく'), 'rs')
    p.wait(max(0.0, CRATE_RANGES[-1][1] + 0.5 - p.t))
    return p
def crate_frames():
    p = crate_plan(); return p, mm.simulate(p, fps=FPS, t_end=p.t + 0.5)

# ================================================================ QR の大地（G9・G6・W23・W26・B28）
N, MOD = 21, 1.5
H = N * MOD / 2
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
WORLD_RANGES = ranges('world')
ROW_X = H + 3.0
def row_pos(k): return (ROW_X, -H + 1.6 + k * 2.3)
_A = json.load(open(os.path.join(HERE, 'qr_assets.json'), encoding='utf-8'))
STAND = _A['experiments']['robot_stand']; BAD = STAND['bad_boxes']; CTR = rc(*STAND['center_rc'])
P_G9 = (ROW_X - 1.3, row_pos(4)[1]); P_G6 = (row_pos(0)[0] - 1.5, row_pos(0)[1] + 0.9)
W23_CELL = next((r, c) for r in range(9, 13) for c in range(9, 13) if _A['symbols']['HELLO_H']['matrix'][r][c] == 0)
W23_XY = rc(*W23_CELL); P_W23 = (W23_XY[0] + 3.2, W23_XY[1] - 1.2)
P_B28 = (CTR[0] - 7.5, CTR[1] + 5.0)
T_STAIN_W = s('23-02a', 1.6)                                # 白いマスに黒い汚れが落ちる
T_MARK26 = (s('26-02', 1.0), s('26-02', 3.0))                # 体で隠れたマス・汚れたマスに赤い輪
T_BEAMS28 = (s('28-03', 1.2), s('28-03', 4.4))              # 予備の 17 個から、壊れた 6 個へ光の線
T_RESTORE = s('28-03', 5.6)                                 # 壊れた 6 個が組み上がる（水色）
def world_plan():
    U.LATE.clear()
    p = mm.Plan(pos=P_G9, heading=75, ground=QZ_TOP)
    at(p, s('21-00', 1.0), lambda q: q.awe(dur=2.6, pitch=8.0, label='予備の箱が光る'), 'g9')
    at(p, s('21-00b', 0.5), lambda q: q.think(dur=2.2, label='なぜ多い？'), 'why')
    cut(p, shot_start('G9', 40.0), P_G9, 75, QZ_TOP)
    at(p, s('21-02c', 1.0), lambda q: q.nod(n=1, amp=10.0, label='うなずく'), 'g9b')
    cut(p, shot_start('G6'), P_G6, hd(P_G6, row_pos(0)), QZ_TOP)
    at(p, s('22-02', 0.8), lambda q: q.look(0, 24, hold=2.4, body=True, label='0 と 1 を見上げる'), 'g6')
    cut(p, shot_start('W23'), P_W23, hd(P_W23, W23_XY), TILE_TOP)
    at(p, T_STAIN_W + 0.3, lambda q: q.surprise(label='汚れが落ちた'), 'w23')
    at(p, s('23-02b', 0.6), lambda q: q.look(0, -20, hold=2.0, body=True, label='黒く見える'), 'w23b')
    cut(p, shot_start('W26'), CTR, 200, TILE_TOP)
    at(p, T_MARK26[0] + 0.2, lambda q: q.look(0, -24, hold=2.0, body=True, label='足もとを見る'), 'w26')
    cut(p, shot_start('B28a'), P_B28, hd(P_B28, CTR), TILE_TOP)
    at(p, s('28-02', 0.6), lambda q: q.look(0, -12, hold=1.8, body=True, label='壊れた箱を見る'), 'b28a')
    at(p, s('28-02c', 0.4), lambda q: q.think(dur=2.2, label='どうして読めた？'), 'b28why')
    at(p, T_BEAMS28[0] + 0.2, lambda q: q.awe(dur=2.8, pitch=10.0, label='光の線'), 'b28b')
    at(p, T_RESTORE + 0.4, lambda q: q.hops(n=2, label='直った'), 'b28c')
    at(p, s('28-04', 0.2), lambda q: q.look(0, 24, hold=2.0, body=True, label='HELLO を見上げる'), 'b28d')
    at(p, s('28-04.6', 0.5), lambda q: q.nod(n=2, amp=8.0, label='うなずく'), 'b28e')
    p.wait(max(0.0, WORLD_RANGES[-1][1] + 0.5 - p.t))
    return p
def world_frames():
    p = world_plan(); return p, mm.simulate(p, fps=FPS, t_end=p.t + 0.5)

# ================================================================ 工場の机（F1・F2）：1994 年の工場。伝票が油で汚れる（看板の字はなし）
FACTORY_RANGES = ranges('factory')
P_F = (1.7, 0.6); SLIP2 = (-0.3, -0.6); Z_BENCH = 2.09
T_OIL = s('21-02', 1.6)                                     # 伝票に油が落ちて広がる
def factory_plan():
    U.LATE.clear()
    p = mm.Plan(pos=P_F, heading=hd(P_F, SLIP2), ground=Z_BENCH)
    at(p, s('21-01', 1.0), lambda q: q.look_around(label='工場を見回す'), 'f1')
    at(p, s('21-01b', 0.4), lambda q: q.look(0, -16, hold=1.8, body=True, label='伝票を見る'), 'f1b')
    at(p, T_OIL + 0.4, lambda q: q.surprise(label='油が落ちた'), 'oil')
    at(p, s('21-02b', 0.8), lambda q: q.nod(n=2, amp=8.0, label='汚れに強くしないと'), 'f2b')
    p.wait(max(0.0, FACTORY_RANGES[-1][1] + 0.5 - p.t))
    return p
def factory_frames():
    p = factory_plan(); return p, mm.simulate(p, fps=FPS, t_end=p.t + 0.5)

if __name__ == '__main__':
    p, fr = crate_frames(); print('crates', len(fr), 'LATE', U.LATE); print('CRATE', CRATE_RANGES)
    print('WORLD', WORLD_RANGES); print('FACTORY', FACTORY_RANGES); print('REUSE', ranges('reuse'))
    p, fr = world_frames(); print('world', len(fr), 'LATE', U.LATE)
    p, fr = factory_frames(); print('factory', len(fr), 'LATE', U.LATE)
