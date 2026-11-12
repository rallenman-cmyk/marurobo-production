# 2章（見つける）の時刻とまるロボの動きの予定。声の時刻は本番の組み立て（chapters.py c2）と同じ（c2_v20_times.json）
#   秒は2章の頭から（24fps）。3D の場面だけ PC で描く（2D の図の場面は描かない）
import math, json, os
import numpy as np
import marumotion as mm
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
_J = json.load(open(os.path.join(HERE, 'c2_v20_times.json'), encoding='utf-8'))
LN = {k: tuple(v) for k, v in _J['lines'].items()}
SHOTS = [tuple(s) for s in _J['shots']]                 # (始め, 終わり, 絵の名前)
T_END = _J['T_END']
def s(i, o=0.0): return LN[i][0] + o
def e(i, o=0.0): return LN[i][1] + o
def fr_of(t): return int(round(t * FPS)) + 1
FIG = {'c2_nearfar', 'c2_ruler', 'c2_times21', 'c2_three', 'c2_manual', 'c2_shop', 'c2_mask', 'c2_mask_fake', 'c2_mask_pats', 'c2_mask_over', 'D1', 'K25a', 'K25', 'K26a', 'K26b'}
DESK = {'K41', 'K42', 'K43'}                             # 卓上の場面（qr_c2_table.py）
def ranges(keys_ok, pad=0.5):
    """描く範囲（秒）：続いている 3D の場面をまとめて、前後に pad 秒の余り"""
    out = []
    for a, b, k in SHOTS:
        if not keys_ok(k): continue
        if out and abs(out[-1][1] - a) < 1e-6: out[-1][1] = b
        else: out.append([a, b])
    return [(max(0.0, a - pad), min(T_END, b + pad)) for a, b in out]
WORLD_RANGES = ranges(lambda k: k not in FIG and k not in DESK)
DESK_RANGES = ranges(lambda k: k in DESK)

N, MOD, TILE_TOP = 21, 1.5, 0.24
H = N * MOD / 2
def rc(r, c): return (-H + (c + 0.5) * MOD, H - (r + 0.5) * MOD)
def hd(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
TL, TR, BL, BR = rc(3, 3), rc(3, 17), rc(17, 3), rc(17, 17)
P0 = rc(3, -2.2)                                         # 左上の目印の左の白いフチ（目印の方＝右を向く）
P1 = rc(-2.2, -2.2)                                      # 左上の目印の斜め外（斜めになぞる）
P24 = rc(10, 14)
P27 = rc(10, 12)
P29 = [rc(6, c) for c in (8, 10, 12, 14)]                # 黒白交互の列の黒いマス
P30 = rc(6, 13.2)
P40 = rc(10, -2.5)
P31 = rc(10, 9)
P34A, P34B = (H + 2.0 * MOD, -H + 9.0), (H + 2.0 * MOD, -H + 0.5)
# ---- 出来事の時刻（3D の動き）
T_BEAM_ROW = (s('10-02', 0.8), s('10-02', 3.4))          # 「左から黒・白・黒・白・黒」：目の光で横になぞる
T_LIFT = s('10-02b', 0.1)                                 # 通ったマスが浮き上がって帯になる（左から順に）
T_BEAM_AGAIN = (s('10-03', 0.4), s('10-03', 2.6))          # 「目の光で、横になぞって」
T_WALK_DIAG = s('10-03', 3.0)                             # 斜めの位置へ（帯をなぞり終えたら走る）
T_BEAM_DIAG = (s('10-04', 2.8), s('10-04', 5.0))           # 斜めになぞる
T_LIFT_DIAG = s('10-04', 3.4)
T_DROP = s('10-04.5', -0.3)                               # 帯が元のマスに戻る
T_BEAMS4 = [s('10-04.5', 0.6 + 0.55 * k) for k in range(4)]   # 縦・横・斜め 2 本を速く
T_RINGS = [s('10-05b', 0.5 + 0.45 * k) for k in range(3)]  # 3 つの目印が順に光る
T_SPIN = (s('12-01', 0.0), s('12-01', 0.9))                # 「おっとっと」：大地ごと回る
SPIN_DEG = 110.0
T_UNSPIN = (s('12-01.5', 0.3), s('12-01.5', 2.0))           # 「でも、角をよく見て」：元の向きに戻る
T_LSHAPE = s('12-01.5b', 0.3)                              # 目印 3 つを結ぶ L 字
T_CORNER = s('12-01.5b', 2.6)                              # 目印のない右下の角（点線の四角が点滅）
T_TIMING = s('12-02', 0.4)                                 # 黒白交互の列（緑）
T_HOPS = s('12-02', 1.2)
T_TICK = [s('12-03', 0.9 + 0.32 * k) for k in range(10)]   # 物差し：1マスずつ光る（横 5・縦 5）
T_FORMAT = s('13-01b', 0.4)                                # 読み方の帯（紫）
T_TAG1, T_TAG2 = s('13-02.5', 0.2), s('13-02.6', 0.2)
T_LINK = s('13-03', 0.6)                                   # 2 本の帯は同じ中身（結ぶ弧）
T_DIRTY = s('13-03b', 0.3)                                 # 片方が汚れても、もう片方で
T_BORDER = s('15-02', 0.3)                                 # QR の境目の線
T_QTICK = s('15-02', 1.6)                                  # 4 マスの目盛り
T_UNMASK = (s('14-04b', 0.6), s('14-04b', 2.4))             # 柄を外す（光の線が通った所から、元の並びに）

def rot_frame(f, ang):
    """大地ごと回るとき：まるロボの姿勢を、原点まわりに ang（度）回す"""
    if abs(ang) < 1e-6: return f
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    def R(p): return [p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca] + list(p[2:])
    g = dict(f); g['root'] = R(f['root']); g['psi'] = f['psi'] + a
    g['feet'] = [dict(ft, ankle=R(ft['ankle']), psi=ft['psi'] + a) for ft in f['feet']]
    return g
def spin_angle(t):
    def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
    if t < T_SPIN[0]: return 0.0
    if t < T_UNSPIN[0]: return SPIN_DEG * ease((t - T_SPIN[0]) / (T_SPIN[1] - T_SPIN[0]))
    return SPIN_DEG * (1 - ease((t - T_UNSPIN[0]) / (T_UNSPIN[1] - T_UNSPIN[0])))

LATE = []
def at(p, t, fn, name=''):
    if t < p.t - 1e-6: LATE.append((name, round(p.t - t, 2)))
    gap = t - p.t
    if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)
    p.wait(max(0.0, t - p.t)); fn(p)
def cut(p, t, pos, heading):
    """カット（場面の切り替え）で置き直す。前の動きが残っていれば待つ"""
    at(p, t, lambda q: q.teleport(pos, heading), 'cut %.1f' % t)

def plan():
    LATE.clear()
    p = mm.Plan(pos=P0, heading=-90, ground=TILE_TOP)
    at(p, s('10-01', 1.0), lambda q: q.look(-20, 8, hold=1.2, body=False, label='目印を見る'), 'look_fin')
    at(p, T_BEAM_ROW[0] - 0.3, lambda q: q.look(0, -6, hold=2.6, body=False, label='目の光で横になぞる'), 'beam_row')
    at(p, T_LIFT + 0.2, lambda q: q.look(0, 20, hold=1.6, body=True, label='浮いた帯を見上げる'), 'look_band')
    at(p, T_BEAM_AGAIN[0] - 0.2, lambda q: q.look(0, 14, hold=2.2, body=False, label='帯をなぞる'), 'beam_again')
    at(p, T_WALK_DIAG, lambda q: (q.run_to(P1, label='斜めの位置へ走る'), q.turn_to(heading=-135)), 'walk_diag')
    at(p, T_BEAM_DIAG[0] - 0.3, lambda q: q.look(0, -6, hold=2.4, body=False, label='斜めになぞる'), 'beam_diag')
    at(p, T_BEAMS4[0] - 0.2, lambda q: q.look_around(label='いろいろな向きから'), 'beams4')
    cut(p, 53.3, P24, 200)
    at(p, T_RINGS[0] - 0.4, lambda q: q.look(-30, 6, hold=1.4, body=True, label='目印が光る方を見る'), 'rings')
    cut(p, 124.9, P27, hd(P27, TL))
    at(p, T_SPIN[0] + 0.15, lambda q: q.surprise(label='おっとっと'), 'spin')
    at(p, s('12-01b', 0.9), lambda q: q.confused(label='よろける・どっちが上？'), 'confused')
    at(p, T_LSHAPE + 0.2, lambda q: q.turn_to(toward=TL, label='左上の目印を見る'), 'see_L')
    at(p, T_CORNER + 0.1, lambda q: q.turn_to(toward=BR, label='目印のない右下の角を見る'), 'see_BR')
    cut(p, 148.4, P29[0], -90)
    def hops(q):
        for tg in P29[1:]: q.jump_to(tg, z1=TILE_TOP, label='黒いマスへ跳ぶ')
    at(p, T_HOPS, hops, 'hops')
    cut(p, 174.8, P30, -90)
    at(p, T_TICK[0] - 0.4, lambda q: q.look(-40, -12, hold=3.0, body=True, label='目盛りを見る'), 'ticks')
    cut(p, 217.6, P40, -90)
    at(p, T_UNMASK[0] - 0.2, lambda q: q.look(-10, 10, hold=2.0, body=False, label='柄が外れるのを見る'), 'unmask')
    cut(p, 276.2, P31, hd(P31, rc(8, 4)))
    at(p, T_FORMAT - 0.2, lambda q: q.look(0, -10, hold=1.6, body=True, label='紫の帯を見る'), 'format')
    at(p, T_TAG1, lambda q: q.nod(n=1, amp=10.0, label='1つ目'), 'tag1')
    at(p, T_TAG2, lambda q: q.nod(n=1, amp=10.0, label='2つ目'), 'tag2')
    at(p, T_DIRTY + 0.3, lambda q: q.surprise(label='片方が汚れた'), 'dirty')
    at(p, T_DIRTY + 2.6, lambda q: q.nod(n=2, amp=8.0, label='もう片方で読める'), 'dirty_ok')
    cut(p, 321.3, P34A, 180)
    at(p, s('15-01', 0.5), lambda q: q.walk_to(P34B, speed=1.2, label='白いフチを歩く'), 'quiet_walk')
    at(p, T_QTICK + 0.3, lambda q: q.look(60, -14, hold=2.0, body=True, label='目盛りを見る'), 'qtick')
    cut(p, 344.0, P0, -90)
    at(p, s('15-03', 1.0), lambda q: q.look(-20, 8, hold=1.4, body=False, label='目印を見る'), 'look_fin2')
    p.wait(max(0.0, 352.2 - p.t))
    return p

def frames():
    p = plan(); fr = mm.simulate(p, fps=FPS, t_end=p.t + 0.5)
    fr = [rot_frame(f, spin_angle(i / FPS)) for i, f in enumerate(fr)]
    return p, fr

# ================================================================ 卓上（16：小さな箱で目印を隠すと、読めない）。冒頭と同じ机・QR の紙（1マス 0.13m）
DM = 0.13
def drc(r, c): return (-(N * DM) / 2 + (c + 0.5) * DM, (N * DM) / 2 - (r + 0.5) * DM)
C3 = drc(3, 3)                                            # 左上の目印の真ん中
BOX_S = 3 * DM                                            # 小さな箱（3×3マス分）
D_PUT = (C3[0] + 0.15, C3[1] - 1.55)                      # 箱を頭に載せて、目印の手前に立つ
D_BACK = (-2.25, 0.25)                                    # 置いて離れる（スマホの方を向く）
D_NEAR = (C3[0] + 0.15, C3[1] - 1.2)                      # 16-04a：箱の近くへ
PHONE = (0.12, -2.35)
T_D0 = 351.12
T_DROP_BOX = s('16-01b', 0.5)                              # 頭の箱を前へ落として、目印の真ん中に置く（0.6 秒）
T_SCAN_NG = (s('16-03', -0.2), e('16-03', 0.4))             # スマホ：枠は出るが、結果が出ない
def desk_plan():
    LATE.clear()
    p = mm.Plan(pos=D_PUT, heading=0, ground=0.0)
    at(p, T_DROP_BOX - 0.15, lambda q: q.nod(n=1, amp=18.0, label='頭の箱を前へ落とす'), 'd_drop')
    at(p, T_DROP_BOX + 0.9, lambda q: (q.walk_to(D_BACK, speed=1.1, label='離れる'), q.turn_to(toward=PHONE)), 'd_back')
    at(p, s('16-02b', 0.6), lambda q: q.look(0, 22, hold=2.0, body=True, label='スマホを見上げる'), 'd_phone')
    at(p, e('16-03', 0.2), lambda q: q.shake(amp=13.0), 'd_no')
    at(p, s('16-03.5', 1.0), lambda q: q.confused(label='読めない？'), 'd_conf')
    at(p, s('16-04', 0.6), lambda q: q.think(dur=2.4, label='考える'), 'd_think')
    at(p, s('16-04a', 0.4), lambda q: (q.walk_to(D_NEAR, speed=1.1, label='箱の近くへ'), q.turn_to(heading=0)), 'd_near')
    at(p, s('16-04a', 6.6), lambda q: q.look(0, -24, hold=1.6, body=True, label='箱の下の目印を見る'), 'd_lookbox')
    at(p, s('16-04b', 0.8), lambda q: q.look(-40, 18, hold=1.8, body=True, label='スマホの方を見る'), 'd_lookphone')
    at(p, s('16-05', 0.8), lambda q: q.nod(n=2, amp=8.0, label='うなずく'), 'd_nod')
    at(p, s('16-05b', 0.6), lambda q: q.nod(n=1, amp=10.0, label='うなずく'), 'd_nod2')
    p.wait(max(0.0, T_END + 0.5 - p.t))
    return p
def desk_frames():
    """卓上の予定（時刻は 2章の頭から。T_D0 より前は使わない）"""
    p = desk_plan(); fr = mm.simulate(p, fps=FPS, t_end=p.t + 0.5)
    return p, fr

if __name__ == '__main__':
    p, fr = frames(); print('frames', len(fr), 'LATE', LATE); print('WORLD', WORLD_RANGES); print('DESK', DESK_RANGES)
