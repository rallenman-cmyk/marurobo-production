# 声のファイルの途中に無音を足す（7本目 v9：字幕を声の切れ目で替えると 2 秒に足りない 1 枚の所。ユーザー「声のあとに間を足す」）
#   MARU_WORK=<作業> python3 add_pause.py <番号> <足す所（秒）> <足す長さ（秒）> …（3 つずつ）
#   前の声は line_NNN_before_pause.wav に残す（もう残っていれば、そこから作り直す＝何度動かしても同じ）。lines.json の dur も直す
import os, sys, json, wave, shutil
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
V = json.load(open(D + "/lines.json", encoding="utf-8"))
a = sys.argv[1:]
for k in range(0, len(a), 3):
    no, at, add = int(a[k]), float(a[k + 1]), float(a[k + 2])
    p = D + "/line_%03d.wav" % no; b = p.replace(".wav", "_before_pause.wav")
    if not os.path.exists(b): shutil.copy(p, b)
    with wave.open(b) as w: pr = w.getparams(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    sr = pr.framerate; i = int(at * sr)
    y = np.concatenate([x[:i], np.zeros(int(add * sr), np.int16), x[i:]])
    with wave.open(p, "wb") as w: w.setparams(pr); w.writeframes(y.tobytes())
    V[str(no)]["dur"] = round(len(y) / sr, 3)
    print(no, "に", at, "秒の所で", add, "秒の間を足した →", V[str(no)]["dur"], "秒")
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
