# 高すぎる文の声を下げてそろえる（3本目 v10「8分あたりから声がずっと高い」）。長さ・時刻は変えない（rubberband の高さだけを変える。声の質＝フォルマントは保つ）
#   python3 even_pitch.py voice.wav word_times.json out.wav [上げ幅の上限 Hz=12]
#   全体の中央値より 20Hz 以上高い文を、中央値＋上限 まで下げる。前後 0.03 秒は元の声と重ねてつなぐ
import json, os, subprocess, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from line_pitch import measure

#   文ごとに上限を変える：k=Hz（例 07-05b=26。下げすぎて聞き取りにくくなった文は、書き起こしで確かめて上限を上げる）
args = [a for a in sys.argv[1:] if "=" not in a]; CAPS = {a.split("=")[0]: float(a.split("=")[1]) for a in sys.argv[1:] if "=" in a}
src, wt, out = args[:3]; cap = float(args[3]) if len(args) > 3 else 12.0
with wave.open(src) as w:
    sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
d = json.load(open(wt)); r = measure(src, wt); med = float(np.median(list(r.values())))
y = x.copy(); tmp = tempfile.mkdtemp(); done = []
for k, f in r.items():
    if f - med < 20: continue
    ratio = (med + CAPS.get(k, cap)) / f
    if ratio > 0.995: continue
    a = max(0, int((d[k]["start"] - 0.05) * sr)); b = min(len(x), int((d[k]["end"] + 0.05) * sr))
    pi, po = os.path.join(tmp, "i.wav"), os.path.join(tmp, "o.wav")
    with wave.open(pi, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x[a:b] * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pi, "-af", "rubberband=pitch=%.5f:formant=preserved:pitchq=quality" % ratio, "-ar", str(sr), "-ac", "1", po], check=True)
    with wave.open(po) as w: z = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    z = np.pad(z, (0, max(0, (b - a) - len(z))))[:b - a]
    n = int(0.03 * sr); fade = np.ones(b - a); fade[:n] = np.linspace(0, 1, n); fade[-n:] = np.linspace(1, 0, n)
    y[a:b] = x[a:b] * (1 - fade) + z * fade
    done.append((k, round(f), round(f * ratio)))
with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
print("中央値 %.0f Hz。下げた文：" % med, done)
