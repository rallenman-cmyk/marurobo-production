# 字幕 1 枚ぶんの声を書き起こして、その字幕の読みと合っているかを確かめる（7本目 v9。2026-11-21 ユーザー「なんでテロップのタイミングまだ治ってないの」）
#   字幕の長さ・速さの数だけでは、声とずれていても見つからなかった（v8 で 44 か所ずれていた）。
#   文の中で切り替わる字幕を 1 枚ずつ、その時刻の声だけ切り出して聞き取らせ、字幕の読み（台本の tts）と比べる。
#   切る所がずれていると、前の字幕の終わりの言葉や、次の字幕の頭の言葉が入る・抜けるので、似ている度が下がる。
#   MARU_WORK=<作業> python3 sub_hear.py [出力.json]   → 似ている度 0.8 未満の字幕を出す
import os, sys, json, wave, difflib, re, base64, io, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "..", "..", "skill", "marurobo-video-production", "scripts")); sys.path.insert(0, H)
import subs_jp as SJ, subs_one as SO
OUT = sys.argv[1] if len(sys.argv) > 1 else None
KEY = os.environ["GEMINI_API_KEY"]
P = json.load(open(os.path.join(H, "..", "voice", "placement.json"), encoding="utf-8"))
kata2hira = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
norm = lambda s: re.sub(r"[^ぁ-ゖー]", "", kata2hira(s))


def wav_bytes(x, sr):
    b = io.BytesIO()
    with wave.open(b, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return b.getvalue()


def hear(x, sr):
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(x, sr)).decode()}},
                                    {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください。漢字・カタカナ・英字は使わない（英字の読みもひらがなで）。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for k in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=120))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e: time.sleep(10 * (k + 1))
    return "（聞き取り失敗）"


jobs = []
for i, p in enumerate(P):
    nx = P[i + 1]["start"] - 0.05 if i + 1 < len(P) else p["end"] + 2
    wav = os.path.join(SJ.VOICE, "line_%03d.wav" % p["no"])
    ev = SO.events(p["start"], p["end"], p["text"], wav, SJ, speed=p.get("speed", 1.0), c_max=nx)
    if len(ev) < 2: continue
    tts = SO._SCRIPT.get(p["text"], {}).get("tts") or p["text"]
    # 字幕ごとの読み：句読点の区切りで合わせる（合わないときは文全体と比べる目安だけ）
    a_, b_ = SO._PH(p["text"]), SO._PH(tts)
    with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    pos = []; k = 0
    for y in a_: k += len(y); pos.append(k)
    k = 0; j0 = 0
    for m, (s0, s1, txt) in enumerate(ev):
        k += len(txt)
        if len(a_) == len(b_) and k in pos: j1 = pos.index(k) + 1; yomi = "".join(b_[j0:j1]); j0 = j1
        else: yomi = None
        t0 = s0 - p["start"]; t1 = (ev[m + 1][0] - p["start"]) if m + 1 < len(ev) else len(x) / sr
        jobs.append(dict(no=p["no"], at=round(s0, 2), text=txt, yomi=yomi, seg=x[int(max(0, t0) * sr):int(t1 * sr)], sr=sr))
print("聞き取る字幕", len(jobs), "枚", flush=True)
with ThreadPoolExecutor(4) as ex:
    heard = list(ex.map(lambda j: hear(j["seg"], j["sr"]), jobs))
bad = []; res = []
for j, h in zip(jobs, heard):
    ref = norm(j["yomi"]) if j["yomi"] else None
    sc = difflib.SequenceMatcher(None, ref, norm(h)).ratio() if ref else None
    res.append(dict(no=j["no"], at=j["at"], text=j["text"], yomi=j["yomi"], heard=h, score=sc))
    if sc is not None and sc < 0.8: bad.append(res[-1])
print("読みと合わない字幕（似ている度 0.8 未満）：", len(bad), "枚 ／ 読みが分からず比べられない：", sum(1 for r in res if r["score"] is None), "枚")
for r in bad: print(" ", r["at"], "%.2f" % r["score"], r["text"], "／ 読み", r["yomi"], "／ 聞こえた", r["heard"])
if OUT: json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
