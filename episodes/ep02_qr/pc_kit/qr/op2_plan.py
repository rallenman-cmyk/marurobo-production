# 冒頭のまるロボの予定（台本 v2.0）。動きは v1.2（op_plan）と同じ順番で、時刻だけ v2.0 の声に合わせる
import math
import marumotion as mm
from op2_timeline import *

def plan():
    hd = math.degrees(math.atan2(-(LENS[0] - START[0]), LENS[1] - START[1]))
    p = mm.Plan(pos=START, heading=hd)
    p.idle(1.0)
    p.look(yaw=0, pitch=22, hold=5.0, label='スマホを見る')
    p.wait(max(0.0, T_WALK - p.t))
    p.walk_to(STAND, speed=1.0, label='スマホをのぞこうと歩いて、右下に乗ってしまう')
    plan.t_on = p.t
    p.wait(max(0.0, T_LOOKUP2 - p.t))
    p.look(yaw=0, pitch=34, hold=2.6, label='結果を見上げる')
    p.wait(max(0.0, T_LOOKDOWN - p.t))
    p.look(yaw=0, pitch=-38, hold=1.4, label='足もとを見る')
    p.surprise(label='乗っていたことに気づく')
    p.wait(max(0.0, T_POSTER_UP - p.t))
    p.look(yaw=0, pitch=30, hold=2.2, label='スマホを見上げる')
    p.wait(max(0.0, T_POSTER_DOWN - p.t))
    p.look(yaw=-15, pitch=-30, hold=1.2, label='足もとを見る')
    p.look(yaw=0, pitch=0, hold=0.3)
    p.wait(max(0.0, T_STEPIN - p.t))
    plan.t_step = p.t
    p.walk_to(STEP, speed=1.2, label='慌てて、逆に奥へ踏み込む')
    p.turn_to(toward=LENS[:2], label='スマホの方へ向き直る')
    p.wait(max(0.0, T_FREEZE - p.t))
    p.look(yaw=0, pitch=30, hold=2.6, label='固まって見上げる')
    p.wait(max(0.0, T_OFF - p.t))
    plan.t_off = p.t
    p.walk_to(OFF, speed=0.6, label='そっと降りる')
    p.turn_to(toward=(0.0, 0.0), label='QRを見る')
    p.idle(max(0.0, T_FACE - p.t))
    p.turn_to(toward=(3.4, -4.4), label='こちらを向く')
    p.nod(n=1, label='うなずく')
    p.wait(max(0.0, T_END - p.t))
    return p

def screen():
    """スマホの画面：読めた（hello）／探している（scan）。乗った・踏み込んだ・降りた時刻は予定から"""
    plan()
    return [(0.0, 'scan'), (T_HELLO1, 'hello'), (plan.t_on - 0.6, 'scan'), (T_HELLO2, 'hello'), (plan.t_step + 0.6, 'scan'), (plan.t_off + 2.3, 'hello')]

if __name__ == '__main__':
    p = plan(); fr = mm.simulate(p, fps=24)
    print('plan length %.2fs frames %d  T_END %.2f' % (p.t, len(fr), T_END))
    for lb in p.labels: print(lb)
    print('screen', [(round(a, 2), k) for a, k in screen()])
    print('shots', [(round(a, 2), round(b, 2), v) for a, b, v, *_ in SHOTS])
