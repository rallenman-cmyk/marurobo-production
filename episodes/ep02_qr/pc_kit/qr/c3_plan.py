# 3章（読む）の時刻とまるロボの動きの予定。声の時刻は本番の組み立て（chapters.py c3）と同じ（c3_v20_times.json）
#   秒は3章の頭から（24fps）。3D の場面だけ PC で描く（目次・英数字の表の場面は 2D）
import math, json, os
import numpy as np
import marumotion as mm
import plan_util as U
from plan_util import at, cut, TILE_TOP, QZ_TOP
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
_J = json.load(open(os.path.join(HERE, 'c3_v20_times.json'), encoding='utf-8'))
LN = {k: tuple(v) for k, v in _J['lines'].items()}
SHOTS = [tuple(s) for s in _J['shots']]
T_END = _J['T_END']
def s(i, o=0.0): return LN[i][0] + o
def e(i, o=0.0): return LN[i][1] + o
def fr_of(t): return int(round(t * FPS)) + 1
FIG = {'c3_toc', 'c3_alnum', 'c3_alnum_hl'}
def ranges(keys_ok, pad=0.5):
    out = []
    for a, b, k in SHOTS:
        if not keys_ok(k): continue
        if out and abs(out[-1][1] - a) < 1e-6: out[-1][1] = b
        else: out.append([a, b])
    return [(max(0.0, a - pad), min(T_END, b + pad)) for a, b in out]
WORLD_RANGES = ranges(lambda k: k not in FIG)
def shot_start(key, after=0.0): return next(a for a, b, k in SHOTS if k == key and a >= after - 1e-6)

N, MOD = 21, 1.5
H = N * MOD / 2
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
def hd(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
_A = json.load(open(os.path.join(HERE, 'qr_assets.json'), encoding='utf-8'))
BOX_CELLS = {int(b): [tuple(x) for x in cs] for b, cs in _A['boxes'].items()}
def box_c(b): cs = BOX_CELLS[b]; return (sum(rc(*x)[0] for x in cs) / len(cs), sum(rc(*x)[1] for x in cs) / len(cs))
ROW_X = H + 3.0                                            # 右の白いフチに、読んだ順に箱を並べる
def row_pos(k): return (ROW_X, -H + 1.6 + k * 2.3)
C0 = box_c(1); C0R = row_pos(0)
P_G1 = (rc(20, 19.5)[0], -H - 0.7)                        # 右下の角の、すぐ手前の白いフチ（大地の方を向く）
P_UP = (rc(20, 19.5)[0], -H + 0.75)                        # 右下の角のマス（2列の真ん中）
P_PAST = rc(15.6, 19.5)                                    # 8マスを歩き抜けた所
P_G3 = (C0[0] + 2.2, C0[1] + 0.4)                         # 1つ目の箱の横（白いフチ）
P_G4 = (ROW_X - 0.2, row_pos(2)[1] + 1.4); P_G4B = (ROW_X - 0.2, row_pos(2)[1] + 0.9)
P_G5 = (ROW_X - 1.6, row_pos(9)[1] - 0.2)
P_G6 = (C0R[0] - 1.5, C0R[1] + 0.9)
P_G7 = (ROW_X - 1.4, row_pos(0)[1] - 1.2)
P_G8 = (ROW_X - 1.3, row_pos(4)[1])
# ---- 出来事の時刻
T_HOPUP = s('18-02', 0.6)                                  # 右下の角のマスへ跳び乗る
T_PATH = (s('18-02b', 0.3), e('18-02b', -0.2))              # ジグザグの道が伸びる（真上）
T_WALK = s('18-02b', 0.2)                                  # 最初の 8 マスを歩く
T_FOLD1 = (s('18-03', 2.8), s('18-03', 4.4))                # 通った 8 マスが起き上がって箱に
T_G4, T_G5 = shot_start('G4'), shot_start('G5')            # 早回し：運ぶ（2 個置いた）→ 9 個並んだ
T_G6A = shot_start('G6a')
T_BITS = s('19-01b', 0.6)                                  # 0 と 1 の板が浮かぶ
T_SPARE = s('20-02', 0.3)                                  # 予備の 17 個が光る

def plan():
    U.LATE.clear()
    p = mm.Plan(pos=P_G1, heading=0, ground=QZ_TOP)
    at(p, s('18-01', 1.2), lambda q: q.awe(dur=2.6, pitch=18.0, label='大地を見上げる'), 'awe')
    at(p, T_HOPUP, lambda q: q.jump_to(P_UP, z1=TILE_TOP, label='右下の角のマスへ跳び乗る'), 'hopup')
    def walk8(q): q.walk_to(P_PAST, speed=1.3, label='2列の上を、上へ歩く（8マスを通る）')
    at(p, T_WALK, walk8, 'walk8')
    at(p, s('18-03', 0.0), lambda q: q.turn_to(toward=C0, label='通ってきた 8 マスへ振り返る'), 'turnback')
    at(p, T_FOLD1[0] + 0.3, lambda q: q.look(0, 18, hold=1.4, body=True, label='箱になるのを見上げる'), 'see_fold')
    cut(p, T_G4, P_G4, 180, QZ_TOP)
    at(p, T_G4 + 0.05, lambda q: q.walk_to(P_G4B, speed=0.8, label='箱を頭に載せて運ぶ'), 'carry')
    cut(p, T_G5, P_G5, 200, QZ_TOP)
    at(p, T_G5 + 0.3, lambda q: q.hops(n=1, label='並べ終わった'), 'done9')
    cut(p, T_G6A, P_G6, hd(P_G6, C0R), QZ_TOP)
    at(p, s('19-01', 2.0), lambda q: q.nod(n=1, amp=16.0, label='頭でふたを押し上げる'), 'open')
    at(p, s('19-01', 3.2), lambda q: q.peer(dur=1.2, label='中をのぞく'), 'peer')
    at(p, T_BITS + 1.5, lambda q: q.look(0, 24, hold=3.0, body=True, label='浮かんだ 0 と 1 を見上げる'), 'bits')
    at(p, s('19-01c', 1.0), lambda q: q.nod(n=2, amp=8.0, label='うなずく'), 'nod_bits')
    cut(p, shot_start('G7', 50.0), P_G7, 20, QZ_TOP)
    at(p, s('19-02', 0.6), lambda q: q.look(0, 26, hold=3.0, body=True, label='空を見上げる（図が出る）'), 'look7')
    at(p, s('19-02b', 1.0), lambda q: q.surprise(label='文字ではなかった'), 'notext')
    cut(p, shot_start('G6', 75.0), P_G6, hd(P_G6, C0R), QZ_TOP)
    at(p, s('19-03a', 1.0), lambda q: q.look(0, 24, hold=2.4, body=True, label='0 と 1 を見る'), 'bits2')
    cut(p, shot_start('G7', 96.0), P_G7, 20, QZ_TOP)
    at(p, s('19-04', 0.5), lambda q: q.look(0, 26, hold=3.0, body=True, label='空を見上げる'), 'look7b')
    at(p, s('19-04', 6.2), lambda q: q.hops(n=2, label='HELLO になった'), 'hello')
    at(p, s('19-04.6', 1.0), lambda q: q.nod(n=1, amp=8.0, label='うなずく'), 'nod_end')
    cut(p, shot_start('G8'), P_G8, 160, QZ_TOP)
    at(p, s('20-01', 1.5), lambda q: q.look_around(label='並んだ箱を見渡す'), 'around')
    at(p, s('20-02', 0.1), lambda q: q.turn_to(heading=75, label='大地の予備の箱の方を向く'), 'to_spare')
    at(p, T_SPARE + 1.2, lambda q: q.awe(dur=2.4, pitch=8.0, label='予備の箱が光る'), 'spare')
    p.wait(max(0.0, T_END + 0.5 - p.t))
    return p
LATE = U.LATE
def frames():
    p = plan(); fr = mm.simulate(p, fps=FPS, t_end=p.t + 0.5); return p, fr

if __name__ == '__main__':
    p, fr = frames(); print('frames', len(fr), 'LATE', U.LATE); print('WORLD', WORLD_RANGES)
    print('C0', [round(x, 2) for x in C0], 'box1 cells', BOX_CELLS[1])
