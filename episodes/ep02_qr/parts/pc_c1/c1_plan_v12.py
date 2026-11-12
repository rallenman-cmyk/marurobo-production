# 1章のまるロボの予定（marumotion）。中の世界（21×21 の大地）。座標は世界座標（m）、1マス 1.5m
#   各動きは「声のこの時刻にこの動きの山が来る」ように、前もって長さを測って（Plan を複製して試す）始める時刻を決める
import math, json, os, copy
import numpy as np
import marumotion as mm
from c1_timeline import *
HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, 'qr_assets.json'), encoding='utf-8'))
N, MOD, TILE_TOP = 21, 1.5, 0.24
def xy(r, c): return (-(N * MOD) / 2 + (c + 0.5) * MOD, (N * MOD) / 2 - (r + 0.5) * MOD)
def box_c(b):
    cs = A['boxes'][str(b)]; p = np.mean([xy(r, c) for r, c in cs], axis=0); return (float(p[0]), float(p[1]))
DATA = A['symbols']['HELLO_H']['data_boxes']; SPARE = A['symbols']['HELLO_H']['spare_boxes']
FOLD_B = 14            # たたんで見せる箱（予備）
PEEK0 = 14             # 「ひとつずつのぞいて」：たたんだ箱をそのままのぞく
PEEK = [14, 11]        # 「ここは違うみたい」（さっきのぞいた 14）「こっちも違う」（右どなり 11）：同じ所から左・右に見える
OPEN_DATA = 8          # 「見つかりました」：開ける中身の箱（11 の右どなり）
OPEN_SPARE = 20        # 「開けてもらいましょう」：予備の箱
def hd(a, b): return math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1]))
P_LAND = xy(17, 16); P_BEAM = xy(13, 13)          # 目印 3 つが左前〜右前に収まる所（向きを変える角度が小さい）
BEAM_ORDER = ('TR', 'TL', 'BL')                     # 右から左へ順に照らす
FIN = {'TL': xy(3, 3), 'TR': xy(3, 17), 'BL': xy(17, 3)}
cells14 = A['boxes'][str(FOLD_B)]; C14 = box_c(FOLD_B); E14 = xy(*cells14[0])          # 端のマス（読む順の最初）
P_PRE = (E14[0], E14[1] - 1.25)                 # 端のマスの手前（となりの箱 13 のマスの上。まだたたまれていない）
P_HOLD = (C14[0] + 0.35, C14[1] - 2.1)                # たたんだ箱のすぐ手前（箱 14 の跡の中。ほかの箱がたたまれても足元は空く）
S1 = ((box_c(PEEK[0])[0] + box_c(PEEK[1])[0]) / 2, box_c(PEEK[0])[1] - 2.45)  # 14 と 11 の間の手前：左前に 14、右前に 11（向きを変えるのは 68°）
_d7 = np.array(box_c(OPEN_DATA)) - np.array(S1); S2 = tuple((np.array(box_c(OPEN_DATA)) - _d7 / np.linalg.norm(_d7) * 1.35).tolist())   # 7 へまっすぐ向かって止まる所
C20 = box_c(OPEN_SPARE); S3 = (C20[0] + 1.3, C20[1] - 1.25)        # 予備の箱 20 の右手前
WP_A = (6.75, -3.75)   # 箱 8 → 箱 20：箱 11 と 10 の間を抜ける
WP_B = (0.8, 3.0)      # 箱 20 → 左上の目印：箱 20・19 をよける
P_FIN_END = FIN['TL']
CARRY_LAND = T_CARRY[0] + 0.55   # 箱が頭に着く瞬間
LATE = []              # 間に合わなかった動き（秒）
MARK = {}              # 動きの名前 → 実際に始まった時刻（3D の箱・ふたの動きをこれに合わせる）

def dur(p, fn):
    """fn を複製の Plan で試して、何秒かかるか"""
    q = copy.deepcopy(p); t0 = q.t; fn(q); return q.t - t0

def at(p, t_key, fn, lead=0.0, name=''):
    """fn の始まりから lead 秒の所（動きの山）が t_key に来るように待ってから fn。間に合わなければ記録してすぐ始める"""
    t0 = t_key - lead
    if t0 < p.t - 1e-6: LATE.append((name, round(p.t - t0, 2)))
    gap = t0 - p.t
    if gap > 3.2: p.idle(gap - 0.4, shifts=True, glance=True)        # 長く待つ間は、重心を移したり、ちらっと見回したり（止まって見えないように）
    p.wait(max(0.0, t0 - p.t))
    if name: MARK[name] = p.t
    fn(p)

def ends(p, t_end, fn, name=''):
    """fn が t_end に終わるように始める"""
    at(p, t_end, fn, lead=dur(p, fn), name=name)

def hop_back(p, target, label=None):
    """向きを変えずに後ろへ跳びのく（驚いて）：しゃがむ→後ろへ 1.5m ほど→着く"""
    lid = p._lb(label); t0 = p.t
    p._neutral(t0, 0.12)
    dv = np.array(target, float) - p._p
    seg = p._jumps(t0 + 0.05, [0.32], dxy=tuple(dv), crouch=0.04, T_c=0.16, ext=0.06, depth=0.045, zeta=0.6, settle=0.6, T_l=0.25)
    f = seg.flights[0]
    p.layer(t0, seg.t1, lambda t, f=f: {"pitch": -9.0 * mm.hump(t, f["t0"] - 0.1, f["t1"] - f["t0"] + 0.3)})
    p.tracks["iris"].set(t0, 0.06, 0.25); p.tracks["iris"].set(seg.t1, 0.6, 0.0)
    p.event(t0, "beep_surprise", 0.8)
    p.t = seg.t1; p._lb_end(lid); return p

def peek_no(p, label=None):
    """のぞいて（0.7秒で前へかがむ）→ 起き上がりながら首を振る"""
    lid = p._lb(label); t0 = p.t
    p.peer(dur=0.3); p.t = t0 + 0.95; p.shake(amp=13.0); p.t = t0 + 0.95 + 1.3
    p._lb_end(lid); return p

def world_plan():
    LATE.clear(); MARK.clear()
    p = mm.Plan(pos=P_LAND, heading=hd(P_LAND, P_BEAM), ground=TILE_TOP)
    p.wait(T_LAND); p.surprise(label='着地')
    at(p, V[2.5][0] + 0.3, lambda q: (q.look(0, -32, hold=1.1, body=True, label='足もとの大きなマスを見る'), q.look_around(label='見回す（壮大）')), name='tile')
    # 「この441マスは、役割ごとに」：真ん中へ走り、最初の目印の方を向いて止まる
    ends(p, T_BEAM[0] - 0.9, lambda q: q.run_to(P_BEAM, label='真ん中へ走る'), name='run')
    for k, key in enumerate(BEAM_ORDER):                                # 目の光で目印を照らす（光は向き終わった瞬間）
        ends(p, T_BEAM[k] - 0.05, lambda q, key=key: q.turn_to(toward=FIN[key], step=0.24, gap=0.03, label='目印%sの方を向く' % key), name='beam%s' % key)
    at(p, V[6][0] + 0.6, lambda q: q.look_around(label='どこに書いてある？'))
    # 「まるロボに、8マスをたたんで」：端のマスの手前へ。言い終わりに端のマスへ跳び乗る
    ends(p, V[9][0] + 1.0, lambda q: (q.walk_to(P_PRE, speed=1.6, label='端のマスの手前へ'), q.turn_to(toward=E14)), name='to_pre')
    at(p, V[9][0] + 2.2, lambda q: q.look(0, -20, hold=1.2, body=True, label='足元のマスを見る'))
    ends(p, T_STEP + 0.9, lambda q: q.jump_to(E14, z1=TILE_TOP, label='端のマスに跳び乗る'), name='step')   # jump_to は着いてから 0.9 秒おさまる
    at(p, T_STEP + 0.95, lambda q: hop_back(q, P_PRE, label='マスが動き出して跳びのく'), name='hop')
    p.turn_to(toward=C14, step=0.24, gap=0.03)
    # 箱が頭に跳び乗る（T_CARRY[0]）→ 箱を載せて、たたんだ場所の手前まで運ぶ → 箱が前へ跳んで元の場所へ（T_CARRY[1]）
    at(p, T_CARRY[0] - 0.35, lambda q: q.look(0, 25, hold=0.3, body=False, label='箱が跳ぶのを見上げる'), name='lookup')
    at(p, CARRY_LAND, lambda q: (q.layer(q.t, q.t + 0.6, lambda t, a=q.t: {"lift": -0.035 * mm.hump(t, a, 0.5)}), q.wait(0.45)), name='catch')
    ends(p, T_CARRY[1] - 0.25, lambda q: q.walk_to(P_HOLD, speed=1.1, label='箱を運ぶ'), name='carry')
    at(p, T_CARRY[1] - 0.1, lambda q: (q.layer(q.t, q.t + 0.5, lambda t, a=q.t: {"lift": -0.03 * mm.hump(t, a, 0.45), "pitch": 6.0 * mm.hump(t, a, 0.45)}), q.wait(0.5)), name='toss')
    at(p, T_WAVE[0] + 0.2, lambda q: (q.look(-28, 6, hold=0.7, label='ほかの箱がたたまれていく'), q.look(0, 0, hold=0.1)), name='wave_look')
    # 「ひとつずつのぞいて」：たたんだ箱 14 をのぞく
    at(p, T_PEEK0, lambda q: q.peer(dur=0.9, label='箱14をのぞく'), name='peek0')
    # 「どの箱に？」：13 と 12 の間へ歩き、13 の方を向く
    ends(p, T_PEEK[0] - 0.3, lambda q: (q.back_to(S1, step=0.36, sw=0.26, gap=0.04, look=False, label='右へカニ歩き（14と11の間へ）'), q.turn_to(toward=box_c(PEEK[0]), step=0.24, gap=0.03)), name='to_s1')
    at(p, T_PEEK[0], lambda q: peek_no(q, label='のぞく：違う（14）'), name='peek1')
    ends(p, T_PEEK[1] - 0.02, lambda q: q.turn_to(toward=box_c(PEEK[1]), step=0.22, gap=0.03), name='turn12')
    at(p, T_PEEK[1], lambda q: peek_no(q, label='のぞく：違う（11）'), name='peek2')
    # 「見つかりました」：となりの青い箱 7 へ急いで、頭でふたを押し上げる
    at(p, p.t, lambda q: q.run_to(S2, label='となりの青い箱へ急ぐ'), name='to_s2')
    at(p, T_OPEN_DATA - 0.35, lambda q: q.nod(n=1, amp=16.0, label='頭でふたを押し上げる（8）'), name='open7')
    at(p, T_SPREAD[0] + 0.2, lambda q: q.hops(n=2, label='見つけた'), name='hops')
    at(p, T_HELLO + 0.3, lambda q: q.awe(dur=2.6, pitch=22.0, label='HELLO を見上げる'), name='awe')
    # 「残りの17個には？」「開けてもらいましょう」：予備の箱 20 へ
    ends(p, T_OPEN_SPARE - 0.15, lambda q: (q.run_to(WP_A, label='予備の箱20へ'), q.run_to(S3), q.turn_to(toward=C20)), name='to_s3')
    at(p, T_OPEN_SPARE, lambda q: q.nod(n=1, amp=16.0, label='頭でふたを押し上げる（20）'), name='open20')
    at(p, T_OPEN_SPARE + 1.2, lambda q: q.peer(dur=1.4, label='空っぽをのぞく'), name='peer20')
    at(p, V[23][0] + 4.6, lambda q: q.confused(label='首をかしげる'), name='conf')
    # 「どうやって取り戻す？」→「見つける」：左上の目印へ走る（2章へ）
    at(p, V[26][0] + 0.8, lambda q: q.think(dur=2.4, label='考える'), name='think')
    at(p, V[28][0] + 3.5, lambda q: (q.run_to(WP_B, label='左上の目印へ走る（2章へ）'), q.run_to((P_FIN_END[0] + 2.6, P_FIN_END[1] - 2.6))), name='run_fin')
    p.wait(max(0.0, T_END - p.t))
    return p

def world_frames():
    p = world_plan(); fr = mm.simulate(p, fps=FPS, t_end=T_END + 0.5)
    for f in fr:                                     # 着地の前は、空から落ちてくる（自由落下）
        if f['t'] < T_LAND:
            dt = T_LAND - f['t']; dz = min(14.0, 0.5 * 9.81 * dt * dt)
            f['root'][2] += dz
            for ft in f['feet']: ft['ankle'][2] += dz
    return p, fr

if __name__ == '__main__':
    p = world_plan()
    print('plan end', round(p.t, 2), 'T_END', round(T_END, 2))
    for lb in p.labels: print([round(lb[0], 2), round(lb[1], 2), lb[2]])
    print('LATE', LATE)
    print('P_PRE', P_PRE, 'P_HOLD', P_HOLD, 'S1', S1, 'S2', S2, 'S3', S3)

# ======================================================================== 卓上（冒頭の机）：画面の前へ走り、画面に飛び込む
import op_timeline as OPT
def _phone():
    L = np.array(OPT.LENS); Am = np.array(OPT.AIM); back = (Am - L) / np.linalg.norm(Am - L)
    px = np.cross(back, [0, 0, 1]); px /= np.linalg.norm(px); py = np.cross(-back, px); py /= np.linalg.norm(py)
    PW, PH, PT = OPT.PHONE_SIZE; cph = L - back * PT / 2 - py * (PH / 2 - 0.35); scr = cph - back * (PT / 2 + 0.005)
    return back, py, scr
BACK, PY, SCR = _phone(); SCR_N = -BACK                 # 画面の向き（手前・上向き）
T_START = (float(_phone()[2][0]), -6.75)                 # 1章のはじめ：スマホの画面の正面、少し離れた所（タイトルの間に回り込んでいた）
T_STANDPT = (float(SCR[0]), -5.05)                       # 画面の下の前（画面の下の端は高さ1.69m・y=-4.36）
T_DIVE_TO = (float(SCR[0]), -3.4)                        # 跳ぶ先（ルート）。画面は上を向いて斜めに立っているので、高く跳んで上から飛び込む
T_DIVE_DZ = 1.2; T_DIVE_APEX = 2.2
def screen_d(x):                                         # 画面の面からの距離（手前が＋）
    return float(np.dot(np.array(x) - SCR, SCR_N))

def table_plan():
    p = mm.Plan(pos=T_START, heading=0.0, ground=0.0)
    p.wait(V[1][0] + 1.2); p.look(0, 22, hold=1.4, body=True, label='画面を見上げる')
    p.wait(max(0.0, V[1][1] - 2.4 - p.t)); p.walk_to(T_STANDPT, speed=1.3, label='画面の下へ')
    p.look(0, 32, hold=0.3, body=True, label='画面を見上げる')
    t0 = max(p.t, T_JUMP - 0.55); p.wait(t0 - p.t)
    lid = p._lb('画面に飛び込む'); p._neutral(p.t, 0.12)
    dv = np.array(T_DIVE_TO) - p._p
    seg = p._jumps(p.t, [T_DIVE_APEX], dxy=tuple(dv), dz=T_DIVE_DZ, crouch=0.045, T_c=0.36, ext=0.09, ext_ld=0.06, depth=0.045, zeta=0.6, settle=0.6, T_l=0.2)
    f = seg.flights[0]
    p.layer(f['t0'] - 0.3, f['t1'] + 0.6, lambda t, f=f: {"pitch": 8.0 * mm.env(t, f['t0'] - 0.36, 0.3, 0.0, 0.1) + 70.0 * mm.mj(t, f['t0'] + 0.35, 0.40)})
    p.event(f['t0'], 'beep_happy', 1.0)
    p.t = seg.t1; p._lb_end(lid)
    p.wait(max(0.0, T_TABLE_END + 0.2 - p.t))
    return p, f

def table_frames():
    """卓上の毎コマ。胴の中心が画面の面を 0.7m 越えたら、まるロボを消す（それまでは画面とスマホの体が隠す）"""
    p, f = table_plan(); fr = mm.simulate(p, fps=FPS, t_end=T_TABLE_END + 0.5)
    t_cross = t_gone = None
    for k in fr:
        if k['t'] < f['t0'] + 0.5 * (f['t1'] - f['t0']): continue      # 頂上を過ぎて、上から画面へ
        c = np.array(k['root']) + np.array([0, 0, mm.TORSO_Z]); d = screen_d(c)
        if t_cross is None and d < 0: t_cross = k['t']; p_cross = c
        if t_gone is None and d < -0.40: t_gone = k['t']
    return p, fr, dict(t_takeoff=f['t0'], t_cross=t_cross, p_cross=p_cross.tolist() if t_cross else None, t_gone=t_gone)
