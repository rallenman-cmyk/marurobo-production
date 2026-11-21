# 声のファイルの途中に無音を足す（7本目 v9：字幕を声の切れ目で替えると 2 秒に足りない 1 枚の所。ユーザー「声のあとに間を足す」）
#   MARU_WORK=<作業> python3 add_pause.py <番号> <足す所（秒）> <足す長さ（秒）> <間の前の字> …（4 つずつ）
#   前の声は line_NNN_before_pause.wav に残す（もう残っていれば、そこから作り直す＝何度動かしても同じ）。lines.json の dur も直す
#   v9：足した間を voice/pauses.json に書く。timing.py の w()（札・3D の言葉の時刻）は、これを見て間のあとの言葉を遅らせる
#   （書かないと、17-08 のように「もっと速く！」の札が声より 0.8 秒早く出る）
import os, sys, json, wave, shutil
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
V = json.load(open(D + "/lines.json", encoding="utf-8"))
H = os.path.dirname(os.path.abspath(__file__))
S = {x["no"]: x for x in json.load(open(os.path.join(H, "script_v1_0.json"), encoding="utf-8"))}
PZ = json.load(open(os.path.join(H, "pauses.json"), encoding="utf-8")) if os.path.exists(os.path.join(H, "pauses.json")) else {}
a = sys.argv[1:]
assert len(a) % 4 == 0, "番号・秒・長さ・間の前の字 の 4 つずつ"
for k in range(0, len(a), 4):
    no, at, add, pre = int(a[k]), float(a[k + 1]), float(a[k + 2]), a[k + 3]
    assert S[no]["text"].startswith(pre), "間の前の字が、文の頭と合わない：" + pre
    PZ[S[no]["id"]] = [[at, add, pre]]          # 前の声（_before_pause）から作り直すので、1 文 1 か所
    p = D + "/line_%03d.wav" % no; b = p.replace(".wav", "_before_pause.wav")
    if not os.path.exists(b): shutil.copy(p, b)
    with wave.open(b) as w: pr = w.getparams(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    sr = pr.framerate; i = int(at * sr)
    y = np.concatenate([x[:i], np.zeros(int(add * sr), np.int16), x[i:]])
    with wave.open(p, "wb") as w: w.setparams(pr); w.writeframes(y.tobytes())
    V[str(no)]["dur"] = round(len(y) / sr, 3)
    print(no, "に", at, "秒の所で", add, "秒の間を足した →", V[str(no)]["dur"], "秒")
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(PZ, open(os.path.join(H, "pauses.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
