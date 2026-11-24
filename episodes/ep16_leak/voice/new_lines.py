# 台本に文を足したとき、足した文の声を作る（16本目 2章 v6 のコメント「ここ展開早い、状況全然理解されない」→ 17-09 を 6 文に）
#   MARU_WORK=<作業> python3 new_lines.py <足す文の表.json> [1 文あたりの候補=4]
#   表：{"before": 前の文の番号, "after": 後の文の番号, "lines": [{"no": 番号, "id": "17-09", "text": 字幕の文, "tts": 読ませる文}, ...]}
#   1 文ずつ、前の文・その文・次の文の 3 文で読ませて、まん中だけを切り出す（retake_line.py と同じ作り。1 文だけだと調子が変わる）。
#   声はバッチで頼む（1 日の回数の上限が別）。候補は、書き起こし（漢字とひらがな）が台本にいちばん近く、速さがまわりに近い物を選ぶ。
#   line_NNN.wav を書き、lines.json に足す。前からある番号の声は line_NNN_before_retake.wav に残す
import os, sys, json, shutil, difflib, re
HERE = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(sys.argv[1], encoding="utf-8")); N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
src = open(os.path.join(HERE, "retake_line.py"), encoding="utf-8").read()
src = src[:src.index("PRE = {}")]                    # 関数と設定だけ使う（retake_line.py の本体は動かさない）
sys.argv = ["retake_line.py", str(spec["before"]), str(N)]
g = {"__name__": "rt"}; exec(src, g)
L, FIX, D, V = g["L"], g["FIX"], g["D"], g["V"]
tts_of = lambda no: FIX.get(str(no), L[no - 1]["tts"])
seq = [tts_of(spec["before"])] + [x["tts"] for x in spec["lines"]] + [tts_of(spec["after"])]
jobs, keys = [], []
for k, x in enumerate(spec["lines"]):
    ctx = seq[k:k + 3]
    for _ in range(N): jobs.append(ctx); keys.append(k)
import numpy as np, base64, io, wave, urllib.request
CACHE = os.path.join(g["W"], "stage", "voice", "new_lines_%s.npz" % os.path.basename(sys.argv[1]).split(".")[0])
def fetch(name):
    """前に頼んだバッチの結果を、もう一度取り出す（16本目：書き起こしの失敗で止まり、作った声を失いかけた）"""
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/" + name, headers={"x-goog-api-key": g["KEY"]}), timeout=120))
    out = {}
    for it in r["response"]["inlinedResponses"]["inlinedResponses"]:
        k = it.get("metadata", {}).get("key")
        try: dat = base64.b64decode(it["response"]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception: out[k] = None; continue
        if dat[:4] == b"RIFF":
            with wave.open(io.BytesIO(dat)) as w_: dat = w_.readframes(w_.getnframes())
        out[k] = np.frombuffer(dat, np.int16).astype(np.float32) / 32768
    return [out.get("k%03d" % i) for i in range(len(jobs))]
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True); outs = list(z["outs"])
elif os.environ.get("BATCH_NAME"):
    outs = fetch(os.environ["BATCH_NAME"])
else:
    outs = g["tts_batch"](jobs)
np.savez(CACHE, outs=np.array(outs, dtype=object))      # 作った声は、書き起こしの前に残す
def safe(fn, y):
    for _ in range(3):
        try: return fn(y)
        except Exception as ex: print("書き起こし失敗、やり直す", repr(ex)[:80], flush=True)
    return ""
norm = lambda s: re.sub(r'[、。？！「」…　 ・,.!?\s]', '', s)
res = {}
for k, x in zip(keys, outs):
    if x is None: continue
    y = g["pick_middle"](x, seq[k:k + 3])
    if y is None: continue
    e = spec["lines"][k]
    h = safe(g["heard"], y); hk = safe(g["heard_kana"], y)
    sc = difflib.SequenceMatcher(None, norm(e["text"]), norm(h)).ratio()
    sk = difflib.SequenceMatcher(None, norm(e.get("kana", "")), norm(hk)).ratio() if e.get("kana") else sc
    cps = len(e["text"]) / (len(y) / 24000)
    res.setdefault(k, []).append((sc + sk - 0.05 * abs(cps - 7.0), y, h + " ／ " + hk, sc, sk, cps))
    print(e["no"], e["id"], "一致 %.2f ひらがな %.2f 字/秒 %.1f" % (sc, sk, cps), h, "／", hk, flush=True)
for k, e in enumerate(spec["lines"]):
    if k not in res: print(e["no"], e["id"], "作れず"); continue
    best = max(res[k], key=lambda c: c[0])
    p = D + "/line_%03d.wav" % e["no"]
    if os.path.exists(p) and not os.path.exists(p.replace(".wav", "_before_retake.wav")): shutil.copy(p, p.replace(".wav", "_before_retake.wav"))
    open(p, "wb").write(g["wav_bytes"](best[1]))
    V[str(e["no"])] = dict(no=e["no"], text=e["text"], dur=round(len(best[1]) / 24000, 3), retake=True, added=True)
    print(e["no"], e["id"], "→ 選んだ：", best[2], "（一致 %.2f・ひらがな %.2f・%.1f 字/秒）" % (best[3], best[4], best[5]), flush=True)
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
