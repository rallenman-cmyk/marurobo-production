# 6本目（配膳ロボット）の BGM。v2 から、この回のために作った新しい曲（2026-11-15 ユーザー「bgm新しいの作ろう」）
#   曲は make_bgm.py で作る（Lyria。git には入れない）。作業フォルダの stage/bgm/bgm_h.mp3・bgm_m.mp3・bgm_t.mp3
#   H（基本・お昼のファミレス）：S01〜S13／S22 スープ／S26〜S30 顔・まとめ・オチ
#   M（先輩の目・なぞ）：S14〜S16 暗い中の点
#   T（ためす）：S17〜S21 低い物・高い物・子どもの飛び出し／S23〜S25 通路を狭くする
#   切り替え（前の曲を 2.5 秒で消し、次を 2 秒で入れ、2 秒重ねる）・大きさは 3本目の bgm_bus.py の make を使う。
#   曲は約 3 分なので、足りない所は 2 秒重ねてくり返す（3本目の「B の長い版」と同じやり方を、どの曲にも）
#   使い方：import bgm_bus; music = bgm_bus.make(END, SCST, sr, work)   SCST＝場面ごとの始まりの秒
import os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("H", "S01"), ("M", "S14"), ("T", "S17"), ("H", "S22"), ("T", "S23"), ("H", "S26")]
OFFSET = {("H", "S22"): 70.0, ("T", "S23"): 95.0, ("H", "S26"): 20.0}   # 同じ曲の 2 回目からは途中から
RMS = 0.012   # SKILL：新しい回は最初から 0.012（声より約 23 dB 下）
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
