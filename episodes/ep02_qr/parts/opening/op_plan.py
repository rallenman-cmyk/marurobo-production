# 冒頭のまるロボの予定（marumotion）。PC の本番（marurig で本物のモデルに当てる）とこちらの確認用で同じものを使う
import math
import marumotion as mm
from op_timeline import *

def plan():
    hd = math.degrees(math.atan2(-(LENS[0] - START[0]), LENS[1] - START[1]))
    p = mm.Plan(pos=START, heading=hd)               # スマホの方を向いて立つ
    p.idle(1.0)
    p.look(yaw=0, pitch=22, hold=5.5, label='スマホを見る')              # 1文目：手前のスマホを見る
    p.wait(max(0.0, 9.6 - p.t))
    p.walk_to(STAND, speed=1.0, label='スマホをのぞこうと歩いて、右下に乗ってしまう')
    p.wait(max(0.0, 23.4 - p.t))
    p.look(yaw=0, pitch=34, hold=2.6, label='結果を見上げる')
    p.wait(max(0.0, 26.9 - p.t))
    p.look(yaw=0, pitch=-38, hold=1.4, label='足もとを見る')
    p.surprise(label='乗っていたことに気づく')
    p.wait(max(0.0, 33.4 - p.t))                                        # 02-03.5「汚れたポスターでも…」の間（v1.2）：スマホを見上げて、足もとを見る
    p.look(yaw=0, pitch=30, hold=2.2, label='スマホを見上げる')
    p.wait(max(0.0, 37.4 - p.t))
    p.look(yaw=-15, pitch=-30, hold=1.2, label='足もとを見る')
    p.look(yaw=0, pitch=0, hold=0.3)
    p.wait(max(0.0, S(32.6) - p.t))
    p.walk_to(STEP, speed=1.2, label='慌てて、逆に奥へ踏み込む')
    p.turn_to(toward=LENS[:2], label='スマホの方へ向き直る')
    p.wait(max(0.0, S(40.0) - p.t))
    p.look(yaw=0, pitch=30, hold=2.6, label='固まって見上げる')
    p.wait(max(0.0, S(45.2) - p.t))
    p.walk_to(OFF, speed=0.6, label='そっと降りる')
    p.turn_to(toward=(0.0, 0.0), label='QRを見る')
    p.idle(max(0.0, S(69.7) - p.t))
    p.turn_to(toward=(3.4, -4.4), label='こちらを向く')
    p.nod(n=1, label='うなずく')
    p.wait(max(0.0, T_END - p.t))
    return p

if __name__ == '__main__':
    p = plan(); fr = mm.simulate(p, fps=24)
    print('plan length %.2fs frames %d' % (p.t, len(fr)))
    for lb in p.labels: print(lb)
    import json
    json.dump([dict(t=f['t'], root=f['root'], psi=f['psi'], pitch=f['pitch'], roll=f['roll'], twist=f['twist'],
                    feet=[list(map(float, x)) if not isinstance(x, dict) else x for x in f['feet']] if 'feet' in f else None,
                    gaze=[f.get('gaze_yaw', 0), f.get('gaze_pitch', 0)]) for f in fr], open('op_frames.json', 'w'), default=float)
    ev = [e for e in p.events if e['kind'] in ('step', 'step_turn', 'takeoff', 'land')]
    print('steps', len(ev), [round(e['t'], 2) for e in ev][:40])
