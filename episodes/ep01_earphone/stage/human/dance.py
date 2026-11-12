# 踊り（第1・2章）：曲の拍に合わせた体の動き
#   K7「たまたま、みんな同じ曲を？」（想像）：曲の盛り上がり（21.798〜29.494秒・5小節）に合わせて、全員が同じ振りで踊る
#     1小節目 首でリズム → 2小節目 体を左右に → 3小節目 空いた手を突き上げる（拍ごとに）→ 4小節目 スマホを頭の上へ、左右に振る
#     → 5小節目の4拍目 決めポーズ（体を少し反らし、腕をもう一段上へ）→ K8 のカット（29.878秒）まで止まる
#   K8「……そんなわけないですよね」（現実）：ほかの人は踊っていない。主人公だけが続けていて、スマホを下ろし、
#     K9 では小さくうなずき・右手で太ももを拍ごとに叩く → 38.2秒に音が途切れると、ピタッと止まる
#   曲の拍：1拍 0.3848秒（156BPM）。盛り上がり（21.8〜33.6秒）の拍と、静かな部分の拍は 0.31拍ずれている（曲を調べて決めた）
#   動きの形：拍の直後にすばやく動き、ゆっくり戻る（u/τ·e^(1−u/τ)）。始まり・終わりは躍度最小（なめらかに）
import math

T_B = 0.3848
G0 = 21.798            # 盛り上がりの最初の拍（1小節目の頭）
N_BEATS = 20           # 盛り上がりは5小節
T_FANT1 = 29.878       # K8 のカット（ここから現実）
OFF_CALM = 0.31        # 静かな部分の拍のずれ（拍の単位）
T_DROP = 38.20         # 曲が途切れる


def mj(t, t0, d):
    u = min(max((t - t0) / d, 0.0), 1.0); return u * u * u * (10 - 15 * u + 6 * u * u)


def beat_count(t):
    """拍の数（なめらかにつながる実数）。盛り上がりでは G0 の拍に、静かな部分では 0.31拍 遅い拍に合う"""
    off = OFF_CALM * (1 - mj(t, 21.62, 0.16)) + OFF_CALM * mj(t, 33.55, 0.6)
    return (t - G0) / T_B - off


def kick(dt, tau):
    """拍から dt 秒たったときの動き（0〜1）。tau 秒で最大、そのあとゆっくり戻る"""
    if dt < 0: return 0.0
    u = dt / tau; return u * math.exp(1.0 - u)


def pulses(t, tau=0.07, every=1):
    """拍ごと（every＝2 なら2拍ごと）の動き。直前の2回ぶんを足す（尾が次の拍にかかる）"""
    b = beat_count(t); k = math.floor(b / every) * every; out = 0.0
    for j in (k, k - every):
        out += kick((b - j) * T_B, tau)
    return out


ZERO = dict(on=0.0, head_x=0.0, neck_x=0.0, spine_x=0.0, chest_x=0.0, spine_z=0.0, chest_z=0.0, head_z=0.0,
            arm_up=0.0, pump=0.0, lift=0.0, phones_up=0.0, wave=0.0, final=0.0, tap=0.0)


def crowd(t):
    """想像の場面（K7）で、全員が同じ振りで踊る。範囲の外は None"""
    if t < G0 - 0.05 or t >= T_FANT1: return None
    b = beat_count(t); d = dict(ZERO); d["on"] = 1.0
    ramp = mj(t, G0 - 0.03, 0.30)
    nod = pulses(t, 0.12, 2); bp = pulses(t, 0.07, 1)
    fin = mj(t, G0 + 19 * T_B - 0.06, 0.20)                       # 5小節目の4拍目：決めポーズ
    hold = 1.0 - fin                                               # 決めポーズでは拍の動きを止める
    d["head_x"] = 15.0 * nod * ramp * hold; d["neck_x"] = 6.0 * nod * ramp * hold
    d["spine_x"] = 4.0 * bp * ramp * hold - 6.0 * fin; d["chest_x"] = 2.5 * bp * ramp * hold - 3.5 * fin
    s_on = mj(t, G0 + 4 * T_B - 0.20, 0.40)                         # 2小節目から左右に揺れる（1小節で1往復）
    sw = math.sin(2 * math.pi * b / 4.0) * s_on
    swf = sw * hold + math.sin(2 * math.pi * (19.0 + 0.10) / 4.0) * fin   # 決めポーズは傾いたまま止まる
    d["spine_z"] = 10.0 * swf; d["chest_z"] = 5.0 * swf; d["head_z"] = -4.0 * swf
    d["arm_up"] = mj(t, G0 + 8 * T_B - 0.15, 0.32)                  # 3小節目：空いた手を突き上げ、拍ごとに押し上げる
    d["tap"] = ramp * (1 - d["arm_up"])                             # 1〜2小節目：空いた手で太ももを拍ごとに叩く
    d["pump"] = bp * hold
    p_on = mj(t, G0 + 12 * T_B - 0.20, 0.42)                         # 4小節目：スマホを頭の上へ
    d["lift"] = d["arm_up"] * (1 - p_on)                            # 両手で持つ人は、3小節目は顔の高さまで上げる
    d["phones_up"] = p_on; d["wave"] = swf                           # 揺れ（−1〜1）。腕・スマホの横の振りは、使う側で上げた量を掛ける
    d["final"] = fin
    return d


def hero(t):
    """主人公：想像の場面ではみんなと同じ。現実（K8〜）では一人で続け、スマホを下ろし、小さくノリ続ける → 曲が途切れると止まる"""
    stop = 1.0 - mj(t, T_DROP + 0.12, 0.22)
    if t < G0 - 0.05:                                              # 盛り上がりの前：小さくうなずく（静かな部分の拍）
        d = dict(ZERO); d["on"] = 0.0; nod = pulses(t, 0.14, 2)
        d["head_x"] = 2.5 * nod; d["neck_x"] = 1.0 * nod; d["spine_x"] = 0.6 * pulses(t, 0.08, 1); return d
    if t < T_FANT1: return crowd(t)
    d = dict(ZERO); d["on"] = 0.0
    b = beat_count(t); nod = pulses(t, 0.12, 2); bp = pulses(t, 0.07, 1)
    rel = 1.0 - mj(t, T_FANT1 + 0.05, 0.40)                          # 決めポーズから揺れに戻る
    down = mj(t, 31.25, 0.90)                                       # スマホを下ろす（31.25〜32.15秒）
    calm = mj(t, 31.20, 1.00)                                       # 曲が静かになるのに合わせて、動きも小さく
    amp_nod = 15.0 - 8.0 * calm
    d["head_x"] = amp_nod * nod * stop; d["neck_x"] = (6.0 - 3.5 * calm) * nod * stop
    d["spine_x"] = ((4.0 - 2.2 * calm) * bp - 6.0 * rel) * stop; d["chest_x"] = ((2.5 - 1.4 * calm) * bp - 3.5 * rel) * stop
    sw0 = math.sin(2 * math.pi * (19.0 + 0.10) / 4.0)
    sw = (math.sin(2 * math.pi * b / 4.0) * (1 - rel) + sw0 * rel) * (1.0 - 0.6 * calm)
    d["spine_z"] = 10.0 * sw * stop; d["chest_z"] = 5.0 * sw * stop; d["head_z"] = -4.0 * sw * stop
    d["arm_up"] = 1.0 - mj(t, 31.05, 0.85)                          # 右手を下ろす（31.05〜31.9秒）
    d["pump"] = bp * (1 - rel)
    d["phones_up"] = 1.0 - down; d["wave"] = math.sin(2 * math.pi * b / 4.0) * (1 - rel) + sw0 * rel
    d["final"] = rel
    d["tap"] = mj(t, 31.85, 0.45) * stop                            # 右手で太ももを拍ごとに叩く（強さ。動きは拍の位相から）
    d["pump"] *= stop; d["wave"] *= stop
    return d
