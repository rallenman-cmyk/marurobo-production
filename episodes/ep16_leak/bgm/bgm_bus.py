# 16本目（情報流出）の BGM。この回のために作った新しい曲（make_bgm.py。git には入れない）。作業フォルダの stage/bgm/bgm_h/m/s/b.mp3
#   H（家）：S01〜S05（冒頭）／S30〜S32（家に戻る）／S40（オチ）
#   M（調べる）：S06〜S11（お城を調べる・裏口・数の図）／S18〜S21（市場）／S27〜S29（ほかのドア）
#   N（夜に忍ぶ）：S12〜S15（v2 から）／S（影）：S16〜S17（錠をかける・脅し）／S22〜S26（市場・つながる）／S33〜S35（輪）
#   B（守る）：S36〜S39（自分でできること・まとめ）
#   切り替え・大きさ・くり返しは 6本目の bgm_bus.py と同じ（3本目の make を使う）
import os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("H", "S01"), ("M", "S06"), ("N", "S12"), ("S", "S16"), ("C1", "S18"), ("S", "S19"), ("C3", "S22"), ("S", "22-05"), ("C2", "S28"), ("S", "S29"), ("H", "S30"), ("S", "S33"), ("B", "S36"), ("H", "S40")]   # v2：S12〜S15（夜に忍びこむ・中を調べる）を N（そっと忍ぶ）に。v1 のユーザー「このbgm違うのにしたい」
# v10（ユーザー「案1、2と3はどこか合いそうなところにつけて」）：追いかける S18＝C1（コミカルな追いかけっこ）、走って取り返す S22〜22-04＝C3（夜の冒険）、鍵を次々に試す S28＝C2（ドキドキの追跡）
OFFSET = {("S", "S19"): 30.0, ("S", "22-05"): 70.0, ("S", "S29"): 110.0, ("H", "S30"): 50.0, ("S", "S33"): 60.0, ("H", "S40"): 100.0}   # 同じ曲の 2 回目からは途中から
RMS = 0.00375   # 16本目 3章 v11「bgmまだ大きい」→ 19・21・23 dB 下を聞きくらべても「23 でも大きい」→ 声より約 26 dB 下（ユーザーが選んだ）。 ／ 16本目 3章 v10「BGMが大きい」：声より約 13 dB 下は大きい → 約 17 dB 下に（-4 dB）。v9 の 24 dB 下は「聞こえない」だった。 ／ 16本目 3章 v9「bgm全然聞こえない」：声より約 24 dB 下で聞こえなかった → 約 13 dB 下に（0.0076 から +7 dB。下げ幅も 6→3 dB）。#  # 7本目と同じ（声 -24 dB に合わせた大きさ）   # 7本目 v6：声を 4 dB 下げたので、曲も 4 dB 下げて差をそのままに（v5 まで 0.012）   # SKILL：新しい回は最初から 0.012（声より約 23 dB 下）
_load0 = B3.load


def _looped(path, sr):
    """曲を 1 本の長い流れにする：頭はそのまま、5 秒〜(終わり-8 秒) を 2 秒重ねながら 6 回くり返す（16本目：S は S12〜S29 と長く、4 回では 7 秒足りなかった）"""
    x = _load0(path, sr)
    a, e, k = int(5 * sr), len(x) - int(8 * sr), int(2 * sr)
    body = x[a:e]; out = x[:e].copy()
    for _ in range(6):
        o = out.copy(); o[-k:] = o[-k:] * np.linspace(1, 0, k) + body[:k] * np.linspace(0, 1, k)
        out = np.concatenate([o, body[k:]])
    return out


def make(END, SCST, sr, work):
    B3.SRC = os.path.join(work, "stage", "bgm")
    plan, off = list(PLAN), dict(OFFSET)
    # 聞きくらべ用：MARU_BGM_TRY=C1 で、3章の追いかける場面（S18）だけを候補の曲にし、S19 から元の S に戻す（v9 のユーザー「bgm臨場感あるやつとか何個か作って聞かせてほしい」）
    k_try = os.environ.get("MARU_BGM_TRY")   # （案1を S18 に決めたので、いまは使わない。ほかの場面で試すとき用）
    if k_try:
        plan = sorted(plan + [(k_try, "S18"), ("S", "S19")], key=lambda q: SCST[q[1]]); off[("S", "S19")] = 30.0
    B3.PLAN, B3.OFFSET, B3.RMS = plan, off, RMS
    B3.load = _looped
    return _even(B3.make(END, SCST, sr), sr)


def _even(x, sr):
    """曲の大きさのむらを半分にする（16本目 3章 v9「途切れ途切れに聞こえる」：はじく弦の曲は音と音の間がへこみ、声の下で途切れて聞こえた）。
    0.3 秒の大きさに合わせて、静かな所を上げる（上げは +9 dB まで・下げは -4 dB まで）。曲の切り替わりの消える所はそのまま（もとが無音に近い所は上げない）"""
    k = int(0.3 * sr); p = np.pad(x.astype(np.float64) ** 2, (k // 2, k - k // 2), mode="edge"); c = np.concatenate([[0.0], np.cumsum(p)])
    env = np.sqrt(np.maximum((c[k:] - c[:-k]) / k, 0))[:len(x)]
    gain = np.clip((RMS / (env + 1e-9)) ** 0.5, 10 ** (-4 / 20), 10 ** (9 / 20))
    gain[env < RMS * 0.03] = 1.0   # 切り替わりの無音は上げない
    k2 = int(0.15 * sr); gp = np.pad(gain, (k2 // 2, k2 - k2 // 2), mode="edge"); c2 = np.concatenate([[0.0], np.cumsum(gp)])
    return (x * ((c2[k2:] - c2[:-k2]) / k2)[:len(x)]).astype(np.float32)
