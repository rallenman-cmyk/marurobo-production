# v11 の置き場所・言葉の時刻・声に、gaps.py の時間を足して v12 にする（1 回だけ走らせる。v11 の物は *_v11 に残す）
#   python3 apply_gaps.py <v11 の声.wav> <v12 の声.wav>
import json, os, sys, wave, shutil
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from gaps import G, GAPS
for name in ("placement.json", "word_times.json"):
    src = os.path.join(HERE, name.replace(".json", "_v11.json"))
    if not os.path.exists(src): shutil.copy(os.path.join(HERE, name), src)
P = json.load(open(os.path.join(HERE, "placement_v11.json"), encoding="utf-8"))
for p in P:
    p["start"], p["end"] = round(G(p["start"]), 3), round(G(p["end"]), 3); p["slot"] = [round(G(v), 3) for v in p["slot"]]
json.dump(P, open(os.path.join(HERE, "placement.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
W = json.load(open(os.path.join(HERE, "word_times_v11.json"), encoding="utf-8"))
for k, v in W.items():
    v["start"], v["end"] = round(G(v["start"]), 3), round(G(v["end"]), 3)
json.dump(W, open(os.path.join(HERE, "word_times.json"), "w", encoding="utf-8"), ensure_ascii=False)
with wave.open(sys.argv[1]) as w: pr = w.getparams(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
sr = pr.framerate; out, last = [], 0
for t, g in GAPS:
    i = int(t * sr); out += [x[last:i], np.zeros(int(round(g * sr)), np.int16)]; last = i
out.append(x[last:])
with wave.open(sys.argv[2], "wb") as w: w.setparams(pr); w.writeframes(np.concatenate(out).tobytes())
print("足した時間 %.1f 秒（%d か所）" % (sum(g for _, g in GAPS), len(GAPS)))
