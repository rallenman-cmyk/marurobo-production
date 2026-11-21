# 字幕 1 枚ぶんの声を書き起こして、その字幕の読みと合っているかを確かめる（7本目 anim/sub_hear.py を 9本目用に。2026-11-21 v2 の点検）
#   関所（pre_upload_gate.py）が、字幕 1 枚ずつの聞き取りを求める。切る所がずれていると、前の字幕の終わりの言葉や、
#   次の字幕の頭の言葉が入る・抜けるので、似ている度が下がる。
#   9本目は組み立てが作った字幕（subs_events.json）をそのまま使う：声だけの音（文の声を placement の時刻に置いた物）から、
#   字幕の出ている間（次の字幕の始まりまで）を切り出して聞かせる。2 つの文にまたがる字幕もそのまま聞ける。
#   MARU_WORK=<作業> python3 sub_hear.py 出力.json [subs_events.json]
import os, sys, json, wave, difflib, re, base64, io, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
SUBP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(H, "subs_events.json")
KEY = os.environ["GEMINI_API_KEY"]
VD = os.path.join(os.environ["MARU_WORK"], "stage", "voice", "achernar")
P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
SC = {x["no"]: x for x in json.load(open(os.path.join(H, "..", "voice", "script_v1_0.json"), encoding="utf-8"))}
kata2hira = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
norm = lambda s: re.sub(r"[^ぁ-ゖー]", "", kata2hira(s))
MODEL = os.environ.get("HEAR_MODEL", "gemini-3.8-flash")


def wav_bytes(x, sr):
    b = io.BytesIO()
    with wave.open(b, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return b.getvalue()


def call(parts, js=False):
    body = {"contents": [{"parts": parts}]}
    if js: body["generationConfig"] = {"responseMimeType": "application/json"}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for k in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=180))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception: time.sleep(10 * (k + 1))
    return None


def hear(x, sr):
    return call([{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(x, sr)).decode()}},
                 {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください。漢字・カタカナ・英字は使わない（英字の読みもひらがなで）。書き起こしだけを出力。"}]) or "（聞き取り失敗）"


# 声だけの音
sr = None; tr = None
for p in P:
    with wave.open(os.path.join(VD, "line_%03d.wav" % p["no"])) as w:
        if sr is None:
            sr = w.getframerate(); tr = np.zeros(int((P[-1]["end"] + 5) * sr), np.int32)
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1).astype(np.int16)
    i0 = int(p["start"] * sr); tr[i0:i0 + len(x)] += x[:len(tr) - i0]
tr = np.clip(tr, -32768, 32767).astype(np.int16)
SUBS = sorted(tuple(s) for s in json.load(open(SUBP, encoding="utf-8")))
jobs = []
for m, (a, c, t) in enumerate(SUBS):
    nx = SUBS[m + 1][0] if m + 1 < len(SUBS) else c
    ls = [p for p in P if p["start"] < max(c, nx) and p["end"] > a]
    jobs.append(dict(at=round(a, 2), text=t.replace("\\N", ""), lines=[p["no"] for p in ls],
                     seg=tr[int(max(0, a - 0.05) * sr):int(min(nx, c + 0.3) * sr)]))
print("聞き取る字幕", len(jobs), "枚", flush=True)
CACHE = os.path.join(os.environ["MARU_WORK"], "sub_yomi_cache9.json")
YC = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
need = [j for j in jobs if j["text"] not in YC]
for k in range(0, len(need), 40):
    ch = need[k:k + 40]
    items = [dict(card=j["text"], line_tts="".join(SC[n]["tts"] for n in j["lines"])) for j in ch]
    for _ in range(3):
        r = call([{"text": "次の JSON の各項目について、card（字幕）を、ナレーターが読むとおりにすべてひらがなで書いてください。"
                   "line_tts は文全体の読み方の手がかりです（数字・英字の読みはこれに従う）。句読点・記号は書かない。"
                   "出力は、入力と同じ順のひらがなの文字列の JSON 配列だけ。\n" + json.dumps(items, ensure_ascii=False)}], js=True)
        try:
            r = json.loads(r)
            if len(r) == len(ch): break
        except Exception: r = None
    if not r: raise SystemExit("読みが作れない")
    for j, y in zip(ch, r): YC[j["text"]] = y
json.dump(YC, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with ThreadPoolExecutor(4) as ex:
    heard = list(ex.map(lambda j: hear(j["seg"], sr), jobs))
bad = []; res = []
for j, h in zip(jobs, heard):
    ref = norm(YC[j["text"]])
    sc = difflib.SequenceMatcher(None, ref, norm(h)).ratio() if ref else None
    for _ in range(2):                    # 合わないときは 2 回まで聞き直し、いちばん合う聞き取りを使う（聞き取りの言いまちがい「見張り→みひらき」を数えないため。v2 の点検）
        if sc is None or sc >= 0.8: break
        h2 = hear(j["seg"], sr); s2 = difflib.SequenceMatcher(None, ref, norm(h2)).ratio()
        if s2 > sc: h, sc = h2, s2
    res.append(dict(at=j["at"], text=j["text"], yomi=YC[j["text"]], heard=h, score=sc))
    if sc is not None and sc < 0.8: bad.append(res[-1])
print("読みと合わない字幕（似ている度 0.8 未満）：", len(bad), "枚 ／ 比べられない：", sum(1 for r in res if r["score"] is None), "枚")
for r in bad: print(" ", r["at"], "%.2f" % r["score"], r["text"], "／ 読み", r["yomi"], "／ 聞こえた", r["heard"])
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
