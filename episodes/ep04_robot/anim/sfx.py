# ロボットではありません回の効果音（3本目の sfx.py に、この回の音を足す）
#   click：マウスのカチッ／down：しょんぼり（下がる電子音）／そのほか（step・jump・land・pi・pop_ui など）は 3本目と同じ
import os, importlib.util
import numpy as np
_sp = importlib.util.spec_from_file_location("sfx_ep03", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ep03_ad", "anim", "sfx.py"))
S3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S3)


def make(kind, sr=48000):
    if kind == "click":   # 乾いた短い 2 つの音（押す・離す）
        a = S3._mx(S3._noise(0.025, sr, 2000, 9000, a=0.0005, d=0.004), 0.5 * S3._tone(2600, 2400, 0.02, sr, a=0.0005, d=0.004))
        return 0.5 * np.concatenate([a, np.zeros(int(0.07 * sr)), 0.6 * a])
    if kind == "down":
        return 0.22 * S3._tone(700, 350, 0.45, sr, a=0.02, d=0.3)
    return S3.make(kind, sr)
