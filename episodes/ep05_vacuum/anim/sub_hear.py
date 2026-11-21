# 字幕 1 枚ぶんの声を書き起こして、その字幕の読みと合っているかを確かめる（5本目の本番。7本目 anim/sub_hear.py と同じ考え）
#   字幕（.ass の Main）を 1 枚ずつ、その時刻の文の声（line_NNN.wav）から切り出して聞き取らせ、字幕の読み（台本の tts を手がかりにひらがなにしたもの）と比べる。
#   切り替わりがずれていると、前の字幕の終わりの言葉や次の字幕の頭の言葉が入る・抜けるので、似ている度が下がる。
#   MARU_WORK=<作業> python3 sub_hear.py <字幕.ass> <声のフォルダ> <出力.json>   → 似ている度 0.8 未満の字幕を出す
import os, sys, json, wave, difflib, re, base64, io, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
ASS, VD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
KEY = os.environ["GEMINI_API_KEY"]
P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
SC = {d["no"]: d for d in json.load(open(os.path.join(H, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
kata2hira = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
norm = lambda s: re.sub(r"[^ぁ-ゖー]", "", kata2hira(s))
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"


def call(body, timeout=180):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for k in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=timeout))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception: time.sleep(10 * (k + 1))
    return None


def subs(ass):
    L = []
    for l in open(ass, encoding="utf-8"):
        if not l.startswith("Dialogue"): continue
        p = l.split(",", 9)
        if p[3] != "Main": continue
        f = lambda x: sum(float(v) * m for v, m in zip(x.split(":"), (3600, 60, 1)))
        L.append((f(p[1]), f(p[2]), re.sub(r"\{.*?\}", "", p[9].strip()).replace("\\N", "")))
    return sorted(L)


def wav_bytes(x, sr):
    b = io.BytesIO()
    with wave.open(b, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return b.getvalue()


L = subs(ASS); jobs = []
for i, (a, b, t) in enumerate(L):
    p = next((q for q in P if q["start"] - 0.25 <= a <= q["end"] + 0.05), None)
    if p is None: continue
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as w:
        sr, ch = w.getframerate(), w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    if ch > 1: x = x.reshape(-1, ch).mean(1).astype(np.int16)
    sp = p.get("speed", 1.0)
    t0 = max(0.0, (a + 0.05 - p["start"]) * sp); t1 = min(len(x) / sr, (b + 0.05 - p["start"]) * sp)
    # 次の字幕が同じ文なら、そこまで（字幕の終わりは次の字幕の始まり）
    if i + 1 < len(L) and L[i + 1][0] <= p["end"] + 0.05: t1 = min(t1, (L[i + 1][0] + 0.05 - p["start"]) * sp)
    else: t1 = len(x) / sr
    jobs.append(dict(no=p["no"], at=round(a, 2), text=t, tts=SC.get(p["no"], {}).get("tts", p["text"]), seg=x[int(t0 * sr):int(t1 * sr)], sr=sr))
print("聞き取る字幕", len(jobs), "枚 ／ 字幕", len(L), "枚", flush=True)
CACHE = os.path.join(os.environ["MARU_WORK"], "sub_yomi_cache05.json")
YC = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
need = [j for j in jobs if j["text"] + "|" + str(j["no"]) not in YC]
for k in range(0, len(need), 40):
    ch_ = need[k:k + 40]
    body = {"contents": [{"parts": [{"text": "次の JSON の各項目について、card（字幕の一部）を、ナレーターが読むとおりにすべてひらがなで書いてください。"
            "line_tts は文全体の読み方の手がかりです（数字・英字の読みはこれに従う）。句読点・記号は書かない。"
            "出力は、入力と同じ順のひらがなの文字列の JSON 配列だけ。\n" + json.dumps([dict(card=j["text"], line_tts=j["tts"]) for j in ch_], ensure_ascii=False)}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    r = json.loads(call(body) or "[]")
    if len(r) != len(ch_): raise SystemExit("読みが作れない")
    for j, y in zip(ch_, r): YC[j["text"] + "|" + str(j["no"])] = y
json.dump(YC, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def hear(j):
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(j["seg"], j["sr"])).decode()}},
                                    {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください。漢字・カタカナ・英字は使わない（英字や数字の読みもひらがなで）。書き起こしだけを出力。"}]}]}
    return call(body, 120) or "（聞き取り失敗）"


with ThreadPoolExecutor(4) as ex:
    heard = list(ex.map(hear, jobs))
res = []; bad = []
for j, h in zip(jobs, heard):
    ref = norm(YC[j["text"] + "|" + str(j["no"])])
    sc = difflib.SequenceMatcher(None, ref, norm(h)).ratio() if ref else None
    res.append(dict(no=j["no"], at=j["at"], text=j["text"], yomi=ref, heard=h, score=sc))
    if sc is not None and sc < 0.8: bad.append(res[-1])
print("読みと合わない字幕（似ている度 0.8 未満）：", len(bad), "枚")
for r in bad: print(" ", r["at"], "%.2f" % r["score"], r["text"], "／ 読み", r["yomi"], "／ 聞こえた", r["heard"])
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
