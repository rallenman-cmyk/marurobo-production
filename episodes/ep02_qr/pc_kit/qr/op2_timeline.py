# 冒頭（台本 v2.0・2026-11-12）の時刻の決まり。場所・スマホ・カメラの位置は op_timeline（v1.2）と同じ。時刻だけ v2.0 の声に合わせる
#   声の時刻は本番の組み立て（chapters.py op）と同じもの（op_v20_times.json）。秒は冒頭の頭から（24fps）
#   v1.2 で描いた冒頭（qrop2_・qrop3_）は声の時刻が 0.4〜7 秒ずれるので、v2.0 では qrop4_ として全部描き直す
import json, os
from op_timeline import MOD, N, QZ, rc, STAND, STEP, START, OFF, LENS, AIM, PHONE_SIZE
FPS = 24
_J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'op_v20_times.json'), encoding='utf-8'))
V = {k: tuple(v) for k, v in _J['lines'].items()}
def s(i, d=0.0): return V[i][0] + d
def e(i, d=0.0): return V[i][1] + d
T_END = _J['T_END']
T_LINES = (s('01-01'), s('01-01', 6.4))                    # 見ている範囲の線（最初の読み取りだけ）
T_HELLO1 = s('01-01', 6.5)                                 # 「読み取ってみると……」の間（声の 5.8〜7.2 秒）で結果が出る
T_WALK = s('02-01', 0.15)                                  # 「あっ、スマホをのぞこうとして」歩き出す → 右下に乗る
T_HELLO2 = s('02-02', 0.55)                                # 「（間）……読めました」：「読めました」の直前
T_LOOKUP2 = s('02-02', -0.25)                              # 結果を見上げる
T_LOOKDOWN = s('02-03', 0.3)                               # 「あれ？」で足もとを見る → 気づく
T_POSTER_UP, T_POSTER_DOWN = s('02-03.5', 0.4), s('02-03.5', 4.4)   # 「汚れたポスターでも…」：見上げて、足もとを見る（ほとんどポスターの図が重なる）
T_STEPIN = s('03-01', 0.5)                                 # 「慌てて降りようとして」→ 逆に奥へ踏み込む
T_FREEZE = s('03-02', -0.6)                                # 「……今度は、読めません」：固まって見上げる
T_OFF = s('04-01b', 0.1)                                   # 「そして、どこまで隠したら…」でそっと降りる（S09_off の引きの絵で。寄りの絵で歩くと体しか映らない）
T_FACE = s('04-04')                                        # 「まるロボと一緒に…」こちらを向いて、うなずく
T_TITLE = (e('04-04', 0.6), T_END)
# カット（始め・終わり・カメラ・寄る量の始め・終わり）。絵の区切りは組み立て（絵コンテ）と同じ
CAMOF = {'S01_wide_lines': 'wide', 'S02_sh_hello': 'shoulder', 'S03_walk': 'wide2', 'S04_sh_scan': 'shoulder', 'S05_sh_hello': 'shoulder', 'S06_close': 'close',
         'poster': 'wide2', 'S07_sh_step': 'shoulder', 'S08_med': 'med', 'S09_off': 'wide', 'S10_low': 'low', 'S11_face': 'face', 'title': 'face'}
SHOTS = []; _seen = set()
for a, b, k in _J['shots']:
    v = CAMOF[k]
    if k == 'S06_close' and k in _seen: v = 'shoulder'        # 2回目（03-01 奥へ踏み込む）は肩ごし。寄りだと歩く体で画面がふさがる
    _seen.add(k)
    if SHOTS and SHOTS[-1][2] == v:      # 同じカメラが続く所はつなぐ
        a0, _, _, d0, d1 = SHOTS[-1]; SHOTS[-1] = (a0, b, v, d0, d1 + 0.03); continue
    SHOTS.append((a, b, v, 0.0, 0.05 if v != 'low' else 0.30))
SCREEN = [(0.0, 'scan'), (T_HELLO1, 'hello')]             # （歩いて乗った所で 'scan' に戻す：op2_plan で時刻を決める）
