# 全部の文の声を 1 文ずつ切り出して、AI に聞き取らせる（3本目 v11：ユーザー「声おかしすぎるとこあるんだけど全部みなおして」）
#   python3 check_all_lines.py <声.wav> <出.json> [文ID…]
#   ① 書き起こしが台本と合うか（合う割合）② 聞いた感じ：速さ（遅い・速い）・機械っぽさ・抑揚の変さ・雑音を「なし／少し／目立つ」で
#   ③ 高さ（Hz）と、1 秒あたりの字の数。3 回聞かせて、2 回以上「目立つ」なら挙げる
import base64, difflib, json, os, re, sys, tempfile, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from line_pitch import f0_track
src, out = sys.argv[1:3]; only = sys.argv[3:]
WT = json.load(open(os.path.join(os.path.dirname(HERE), "word_times.json")))
with wave.open(src) as w: sr = w.getframerate(); X = np.frombuffer(w.readframes(w.getnframes()), np.int16)
tmp = tempfile.mkdtemp()
Q = ("これは日本語のナレーションの 1 文です。台本は「%s」。次を JSON だけで答えてください："
     "{\"heard\": 聞こえたとおりの書き起こし, \"slow\": 不自然に遅い・間延びしているか（なし/少し/目立つ）, \"robot\": 機械っぽい・金属っぽい・こもった声か（なし/少し/目立つ）, "
     "\"intonation\": 抑揚や高さが不自然か（なし/少し/目立つ）, \"noise\": 雑音・ぶつ切れがあるか（なし/少し/目立つ）, \"note\": 気になる所を短く}")
def ask(p, text):
    b = base64.b64encode(open(p, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": Q % text}]}], "generationConfig": {"responseMimeType": "application/json"}}
    for _ in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]}), timeout=120))
            return json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
        except Exception: pass
    return {}
norm = lambda s: re.sub(r"[\s、。！？!?…「」（）・,.ー]", "", s)
def one(k):
    v = WT[k]; seg = X[int((v["start"] - 0.08) * sr):int((v["end"] + 0.08) * sr)]
    p = os.path.join(tmp, k + ".wav")
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(seg.tobytes())
    f = f0_track(seg.astype(np.float32) / 32768, sr); pitch = float(np.median(f)) if len(f) > 10 else 0
    talk = sum(b - a for a, b in v["wt"][1]) if v.get("wt") else v["end"] - v["start"]
    rs = [ask(p, v["text"]) for _ in range(3)]
    flags = {}
    for key in ("slow", "robot", "intonation", "noise"):
        n = sum(1 for r in rs if str(r.get(key, "")).startswith("目立"))
        if n >= 2: flags[key] = n
    sims = [difflib.SequenceMatcher(None, norm(v["text"]), norm(r.get("heard", ""))).ratio() for r in rs if r]
    return k, dict(pitch=round(pitch), cps=round(len(norm(v["text"])) / max(talk, 0.1), 1), sim=round(max(sims) if sims else 0, 2),
                   flags=flags, notes=[r.get("note", "") for r in rs if r], heard=rs[0].get("heard", "") if rs and rs[0] else "")
ids = only or sorted(WT, key=lambda k: WT[k]["start"])
R = {}
with ThreadPoolExecutor(6) as ex:
    for k, r in ex.map(one, ids): R[k] = r
json.dump(R, open(out, "w"), ensure_ascii=False, indent=1)
pm = float(np.median([r["pitch"] for r in R.values() if r["pitch"]]))
print("高さのまん中 %.0f Hz" % pm)
for k in ids:
    r = R[k]; why = []
    if r["sim"] < 0.85: why.append("聞き取り %.2f（%s）" % (r["sim"], r["heard"]))
    if r["pitch"] - pm >= 20: why.append("高い +%d" % (r["pitch"] - pm))
    if r["flags"]: why.append("聞いた感じ：" + "・".join("%s %d/3" % (a, b) for a, b in r["flags"].items()))
    if why: print(k, " / ".join(why), "|", WT[k]["text"][:24])
