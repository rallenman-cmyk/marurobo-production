# 9本目（エスカレーター）の BGM。この回のために作った新しい曲（make_bgm.py。git には入れない）。作業フォルダの stage/bgm/bgm_h.mp3・bgm_n.mp3・bgm_k.mp3
#   H（基本・昼の駅）：S01〜S08（冒頭・1章）／S15〜S27（3〜5章）／S39〜S40（まとめ・オチ）
#   N（床の下）：S09〜S14（夜の点検・床の下）
#   K（挑戦）：S28〜S38（見張りに挑戦）
#   切り替え・大きさ・くり返しは 6本目の bgm_bus.py と同じ（3本目の make を使う）
import os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("H", "S01"), ("N", "S09"), ("H", "S15"), ("K", "S28"), ("H", "S39")]
OFFSET = {("H", "S15"): 60.0, ("H", "S39"): 120.0}   # 同じ曲の 2 回目からは途中から
RMS = 0.0076   # 7本目と同じ（声 -24 dB に合わせた大きさ）   # 7本目 v6：声を 4 dB 下げたので、曲も 4 dB 下げて差をそのままに（v5 まで 0.012）   # SKILL：新しい回は最初から 0.012（声より約 23 dB 下）
_load0 = B3.load


def _looped(path, sr):
    """曲を 1 本の長い流れにする：頭はそのまま、5 秒〜(終わり-8 秒) を 2 秒重ねながら 4 回くり返す"""
    x = _load0(path, sr)
    a, e, k = int(5 * sr), len(x) - int(8 * sr), int(2 * sr)
    body = x[a:e]; out = x[:e].copy()
    for _ in range(4):
        o = out.copy(); o[-k:] = o[-k:] * np.linspace(1, 0, k) + body[:k] * np.linspace(0, 1, k)
        out = np.concatenate([o, body[k:]])
    return out


def make(END, SCST, sr, work):
    B3.SRC = os.path.join(work, "stage", "bgm")
    B3.PLAN, B3.OFFSET, B3.RMS = PLAN, OFFSET, RMS
    B3.load = _looped
    return B3.make(END, SCST, sr)
