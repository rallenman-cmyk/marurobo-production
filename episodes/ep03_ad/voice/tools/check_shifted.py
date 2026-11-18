# 下げた文の声を切り出して、書き起こし（台本と合うか）と、音のゆがみ（金属っぽい・こもる・雑音）を AI に聞いてもらう（元の声と並べて比べる）
#   python3 check_shifted.py 元.wav 直した.wav word_times.json 文ID…
import base64, difflib, json, os, re, sys, tempfile, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
A, B, WT = sys.argv[1:4]; ids = sys.argv[4:]; d = json.load(open(WT)); tmp = tempfile.mkdtemp()

def cut(src, k, tag):
    with wave.open(src) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    y = x[int((d[k]["start"] - 0.1) * sr):int((d[k]["end"] + 0.1) * sr)]; p = os.path.join(tmp, "%s_%s.wav" % (k, tag))
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
    return p

def ask(parts):
    body = {"contents": [{"parts": parts}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for _ in range(4):
        try: return json.load(urllib.request.urlopen(req, timeout=120))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e: err = e
    return "ERR %s" % err

def au(p): return {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(open(p, "rb").read()).decode()}}

def one(k):
    pa, pb = cut(A, k, "a"), cut(B, k, "b")
    t = ask([au(pb), {"text": "この音声を、聞こえたとおりに日本語で書き起こしてください。書き起こしだけを出力。"}])
    q = ask([au(pa), au(pb), {"text": "1つ目は元の声、2つ目は高さだけを下げた声です。2つ目に、元にない音のゆがみ（金属っぽい響き・ロボットのような声・こもり・ぶつぶつ切れる・雑音）がありますか。最初に「なし」「少し」「目立つ」のどれかを書き、そのあと理由を短く。"}])
    n = lambda s: re.sub(r"[\s、。！？!?…「」・,.]", "", s)
    sim = difflib.SequenceMatcher(None, n(d[k]["text"]), n(t)).ratio()
    return k, sim, t, q.replace("\n", " ")[:90]

with ThreadPoolExecutor(6) as ex:
    for k, sim, t, q in ex.map(one, ids): print("%-7s 合う %.2f | %s | %s" % (k, sim, t, q))
