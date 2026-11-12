# 第7章・第8章の塔の部屋の、まるロボの予定（marumotion の Plan）。Blender の外でも同じ計算
#   第6章でまるロボは外で 06 を送り直している。第7章の前半（K1〜K5）はその同じ時間の「中」なので、まるロボはいない。
#   06 が届く（K6）と、手前の右から歩いて入ってきて、再生装置の右前で見守る：
#     K6  塔を見上げて、06 が間に合ったのでうなずく
#     K7  「…バッファです」：後ろへ下がりながら、光った札を見上げる（高い物を見るとき、人も一歩下がる）
#     K8  昇降機へ近づき、07 が上がるのを目で追う → 届いてうなずく
#     K9  再生装置の前へ戻り、曲に合わせて揺れる（K9b の終わりまで）→「…どうなるのでしょう？」で首をかしげる
#     K10 （後半）09 が来ない：「もっと遅れたら？」の間に昇降機の方を向き → 口の右前へ → のぞき込む → 塔の目盛りを見る → 待つ → もう一度のぞく
#         （口の真ん前に立つと、K10 のカメラから口の 6 割が隠れる。右前 (3.25, −0.95) なら隠れず、右前の柱も一直線でよけられる）
#     K11 残り一つ：再生装置と口の間を、早足で行ったり来たり
#     K12 最後の荷物が沈むのを見つめる → 音が止まった瞬間に驚く → 「ここで、音が途切れることがあります」で、がっくり
#   第8章の塔（C1〜C3）：空の塔を見上げて考える → 04 が届くのを見る → 鳴らし始めると小さく跳ねて、曲に合わせて揺れる
#   座標は部屋の座標（m）。再生装置は (0,0)（幅 1.8・奥行き 1.3）、昇降機の口は (1.8, 0)（前のふちは y=−0.5）。まるロボは高さ約 1.2m・胴の半径約 0.5m
import math
import marumotion as mm
import ch07_plan as p7

E_IN = (4.6, -3.4)            # 入ってくる所（K6 の画面の右の外）
H = (1.05, -1.48)             # 見守る所（再生装置の右前）
S_SIGN = (1.20, -2.45)        # 札を見上げる所（一歩下がって見る）
P_LIFT = (1.75, -1.75)        # 昇降機の少し手前（07 が上がるのを見る）
P_PIT = (3.25, -0.95)         # 口の右前（のぞき込む）。口は x 1.12〜2.48・y −0.48〜0.48、右前の柱は (2.46, −0.46)：行き帰りとも柱から 0.6m 以上
H2 = (0.80, -1.40)            # 再生装置のすぐ前（後半）
TOWER = (0.0, 0.0)
SIGN_W = (0.0, -0.475, 4.66)  # 札の位置（部屋の座標）
EYE_Z = 0.76                  # 目の高さ（ルートから）
BPM = 78.0                    # 揺れ：曲（約 156 BPM）の 2拍に 1回


def heading_to(src, dst): return math.degrees(math.atan2(-(dst[0] - src[0]), dst[1] - src[1]))


def look_at(pl, src, dst, hold=0.6):
    hd = heading_to(src, dst[:2]); yaw = (hd - math.degrees(pl._psi) + 180) % 360 - 180
    z = dst[2] if len(dst) > 2 else EYE_Z
    pitch = math.degrees(math.atan2(z - EYE_Z, math.hypot(dst[0] - src[0], dst[1] - src[1])))
    pl.look(yaw=max(-60, min(60, yaw)), pitch=max(-30, min(45, pitch)), hold=hold)


def until(pl, t_abs, t0, shifts=False):
    """本編の秒 t_abs まで待つ（予定の秒 ＝ 本編の秒 − t0）"""
    pl.idle(max(t_abs - t0 - pl.t, 0.05), shifts=shifts, glance=False)


def at_word(n, word):
    a, b = p7.L(n), p7.LE(n); txt = p7.PLC[n]["text"]
    return a + (b - a) * txt.index(word) / len(txt)


T_ENTER = 781.0               # 歩き出す（06 が塔の上へ押し出されているころ。カメラが下りてくる前に画面へ入る）
T_SHOW = 780.4                # ここまでは見えない（大きさ 0）


def plan_ch7(t0):
    """第7章（予定の 0 秒 ＝ 本編 t0）。どの動きも、台本の言葉の前に終わるように頭の時刻を決める（遅れが次へたまらない）"""
    pl = mm.Plan(pos=E_IN, heading=heading_to(E_IN, H), seed=17)
    until(pl, T_ENTER, t0)
    pl.walk_to(H, speed=mm.V_WALK, label="06 と一緒に入ってくる")
    pl.turn_to(heading_to(H, TOWER))
    look_at(pl, H, (0.0, 0.0, 3.2), hold=0.8)                                   # 塔を見上げる（06 が積み重なりの上に落ちたところ）
    until(pl, p7.L(138) + 1.6, t0)
    pl.nod(n=1, amp=10.0, label="間に合った")                                    # 「五番が終わる前に間に合えば…」
    until(pl, p7.L(139) + 0.2, t0, shifts=True)
    pl.back_to(S_SIGN, step=0.30, sw=0.26, gap=0.04, look=True, label="札を見るために下がる")   # 「この、先に受け取ったデータを…」
    until(pl, at_word(139, "バッファ") - 0.1, t0)
    pl.awe(dur=3.0, pitch=38.0, label="札を見上げる")                            # 「…バッファです」で札が光る
    a7 = p7.ARR["07A"]
    until(pl, p7.L(140) + 0.1, t0, shifts=True)
    pl.walk_to(P_LIFT, speed=mm.V_WALK, label="昇降機へ")                         # K8：07 が上がって、塔の上の扉から落ちる
    pl.turn_to(heading_to(P_LIFT, (1.8, 0.0)))
    look_at(pl, P_LIFT, (1.5, 0.0, 4.0), hold=max(a7["t_land"] - t0 - pl.t - 0.6, 0.5))
    until(pl, a7["t_land"] + 0.15, t0)
    pl.nod(n=2, amp=7.0, label="届いた")
    until(pl, p7.L(142) + 0.1, t0, shifts=True)
    pl.walk_to(H, speed=mm.V_WALK, label="再生装置の前へ")                         # K9：曲は続く
    pl.turn_to(heading_to(H, TOWER))
    pl.groove(dur=max(p7.L(145) + 0.3 - t0 - pl.t, 1.0), bpm=BPM, amp=0.008, label="曲に合わせて揺れる")
    pl.confused(label="もっと遅れたら？")                                         # 「…どうなるのでしょう？」
    pl.turn_to(heading_to(H, P_PIT), step=0.22, gap=0.03, label="昇降機の方を向く")   # 問いかけの間に、荷物の来る方を向く
    look_at(pl, H, (1.8, 0.0, 1.2), hold=0.4)
    until(pl, p7.T_B + 0.25, t0)
    pl.walk_to(P_PIT, speed=mm.V_BRISK, label="口へ")                            # K10：09 が来ない（右前の柱の外を通る）
    pl.turn_to(heading_to(P_PIT, (1.8, 0.0)), step=0.22, gap=0.03)
    pl.peer(dur=1.4, label="のぞき込む")
    until(pl, p7.L(148) - 0.1, t0)                                                # 「先に届いていた分は、少しずつ減っていきます」
    look_at(pl, P_PIT, (-0.65, -0.42, 2.0), hold=1.0)                            # 塔の目盛りを見る（減っていく）
    pl.idle(max(p7.L(148) + 3.4 - t0 - pl.t, 0.5), shifts=True, glance=True, label="足踏みして待つ")
    pl.peer(dur=1.2, label="もう一度のぞく")
    until(pl, p7.L(149) + 0.05, t0, shifts=True)
    pl.turn_to(heading_to(P_PIT, H2), step=0.22, gap=0.03, label="再生装置へ急ぐ")   # K11：残り一つ
    pl.run_to(H2)
    pl.turn_to(heading_to(H2, TOWER), step=0.22, gap=0.03)
    look_at(pl, H2, (0.0, 0.0, 1.15), hold=0.6)
    look_at(pl, H2, (1.8, 0.0, 0.3), hold=0.5)                                   # そわそわ：口をふり返る
    look_at(pl, H2, (0.0, 0.0, 1.15), hold=0.6)
    look_at(pl, H2, (1.8, 0.0, 0.3), hold=0.4)
    look_at(pl, H2, (0.0, 0.0, 1.10), hold=max(p7.T_STOP - t0 - pl.t - 0.6, 0.5))     # K12：最後の荷物が沈むのを見つめる
    until(pl, p7.T_STOP, t0)
    pl.surprise(label="音が止まる")
    until(pl, p7.L(152) + 0.9, t0)
    pl.sigh(label="がっくり")
    pl.idle(4.0, shifts=False, glance=False)
    return pl


def plan_ch8(t0):
    """第8章の塔（予定の 0 秒 ＝ 本編 t0）"""
    pl = mm.Plan(pos=H, heading=heading_to(H, TOWER), seed=19)
    until(pl, p7.L(158) + 0.2, t0)
    look_at(pl, H, (0.0, 0.0, 3.4), hold=1.0)                                   # 空の塔を見上げる
    pl.think(dur=2.6, label="もっとためれば？")
    a4 = p7.ARR["04C"]
    until(pl, a4["t_rise0"] + 1.0, t0)
    pl.turn_to(heading_to(H, (1.8, 0.0)))
    look_at(pl, H, (1.8, 0.0, 3.8), hold=max(a4["t_land"] - t0 - pl.t, 0.5))     # 04 が上がって届くのを見る
    pl.turn_to(heading_to(H, TOWER))
    until(pl, p7.T_START_C + 0.15, t0)
    pl.hops(n=2, height=0.05, spin=12.0, label="鳴り始めた")
    pl.groove(dur=max(p7.T2_8 + 0.5 - t0 - pl.t, 1.0), bpm=BPM, amp=0.008, label="曲に合わせて揺れる")
    return pl
