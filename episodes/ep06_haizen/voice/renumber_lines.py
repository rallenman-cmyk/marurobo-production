# 文を足したとき、後ろの声の番号をずらす（6本目 v2→v3：12-02 を 4 文に分けた）
# MARU_WORK=<作業フォルダ> python3 renumber_lines.py 開始番号 ずらす数
#   開始番号より後ろ（開始番号を含む）の line_NNN*.wav・lines.json・heard.json・tts_text.json の番号を +ずらす数。
#   前の状態は achernar_before_renumber/ に丸ごと残す（2 回目からは上書きしない）
import os, sys, json, re, shutil
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
start, k = int(sys.argv[1]), int(sys.argv[2])
bk = D + "_before_renumber"
if not os.path.exists(bk): shutil.copytree(D, bk)
fs = [f for f in os.listdir(D) if re.match(r"line_(\d{3})", f)]
fs.sort(key=lambda f: -int(f[5:8]))      # 大きい番号から動かす（上書きしないため）
for f in fs:
    n = int(f[5:8])
    if n >= start: os.rename(os.path.join(D, f), os.path.join(D, "line_%03d%s" % (n + k, f[8:])))
for name in ("lines.json", "heard.json", "tts_text.json"):
    p = os.path.join(D, name)
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding="utf-8"))
    if not isinstance(d, dict): continue
    out = {}
    for key, v in d.items():
        n = int(key) if key.isdigit() else None
        nn = n + k if n is not None and n >= start else n
        if isinstance(v, dict) and "no" in v and nn is not None: v["no"] = nn
        out[str(nn) if nn is not None else key] = v
    json.dump(dict(sorted(out.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)), open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ずらした：%d 番から +%d" % (start, k))
