# 会話と広告の回：声だけの通し（animatic_tmp/voice.wav）を作り直す。声を 1 文だけ差し替えたときに使う（絵は作らない）
#   中身は animatic.py の「声」の所と同じ（-20 dBFS にそろえる・合言葉の所の「ピー」）
#   MARU_WORK=<作業フォルダ> python3 make_voice_mix.py
import os, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["MARU_WORK"]; V = W + "/stage/voice/achernar"
P = json.load(open(os.path.join(HERE, "..", "voice", "placement.json"), encoding="utf-8"))
ID = {e["no"]: e["id"] for e in json.load(open(os.path.join(HERE, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
END = P[-1]["end"] + 2.0; sr = 24000
tmp = W + "/animatic_tmp"; os.makedirs(tmp, exist_ok=True)
mix = np.zeros(int(END * sr), np.float32)
for p in P:
    with wave.open(V + "/line_%03d.wav" % p["no"]) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    r = np.sqrt((x ** 2)[np.abs(x) > 0.01].mean() + 1e-12); x *= 10 ** (-20 / 20) / r
    i = int(p["start"] * sr); mix[i:i + len(x)] += x[:len(mix) - i]
for p in P:
    if ID[p["no"]] in ("08-08", "08-11"):
        i = int((p["start"] - 1.6 + 0.3) * sr); n = int(0.7 * sr)
        b = 0.12 * np.sin(2 * np.pi * 1000 * np.arange(n) / sr); f = int(0.01 * sr); b[:f] *= np.linspace(0, 1, f); b[-f:] *= np.linspace(1, 0, f)
        mix[i:i + n] += b
mix /= max(1.0, np.abs(mix).max() / 0.89)
with wave.open(tmp + "/voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", tmp + "/voice.wav", "%.1f 秒" % END)
