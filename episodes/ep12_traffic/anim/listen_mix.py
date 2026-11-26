# 通しの音（mix.wav）を 30 秒ずつ聞かせて、読み・変な音・大きすぎる音を書き出す（7本目の道具を9本目用に。台詞の時刻は subs_events.json か LINES）
# MARU_WORK=<作業> python3 listen_mix.py mix.wav 出力.json [始め秒 終わり秒]
#   ① 区切りごとに、聞こえた言葉（ひらがな）と、気になる音（息・ノイズ・大きすぎる効果音・声と重なる音・途切れ）を書き起こさせる
#   ② 区切りごとに、声・効果音・BGM の大きさ（dB）を測る
import os, sys, json, wave, base64, io, urllib.request, time, re
import numpy as np
KEY = os.environ["GEMINI_API_KEY"]
src, out = sys.argv[1], sys.argv[2]
w = wave.open(src); sr = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
if ch > 1: x = x.reshape(-1, ch).mean(1)
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0; T1 = float(sys.argv[4]) if len(sys.argv) > 4 else len(x) / sr
HERE = os.path.dirname(os.path.abspath(__file__))
P = [dict(start=a, end=b, text=c) for a, b, c in json.load(open(os.environ.get("LINES", os.path.join(HERE, "subs_events.json")), encoding="utf-8"))]


def post(body):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % os.environ.get("HEAR_MODEL", "gemini-3-flash-preview"), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for k in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception as e: print("retry", repr(e)[:100], flush=True); time.sleep(20 * (k + 1))
    raise SystemExit("API 失敗")


def wavb(y, r=16000):
    y = np.interp(np.arange(int(len(y) * r / sr)) * sr / r, np.arange(len(y)), y).astype(np.float32)
    b = io.BytesIO()
    with wave.open(b, "wb") as o: o.setnchannels(1); o.setsampwidth(2); o.setframerate(r); o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    return b.getvalue()


ASK = ("これは解説動画の音です（やさしい女性のナレーション・小さな BGM・効果音）。\n"
       "1) 聞こえたナレーションを、すべてひらがなで書き起こしてください（数字や英字も聞こえた読みのまま）。\n"
       "2) 気になる音があれば、区切りの頭からの秒と一緒に書いてください：息の音・口の音・ノイズ・ぶつっと切れる音・"
       "声より大きく聞こえる効果音・声に重なって聞き取りにくい所・急に大きくなる／小さくなる所・不自然な間。なければ「なし」。\n"
       "JSON だけで答える：{\"kana\": \"…\", \"issues\": [{\"t\": 秒, \"what\": \"…\"}]}")
R = []
t = T0
while t < T1 - 1:
    a, b = int(t * sr), int(min(T1, t + 30) * sr)
    y = x[a:b]
    r = post({"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wavb(y)).decode()}}, {"text": ASK}]}],
              "generationConfig": {"responseMimeType": "application/json"}})
    txt = r["candidates"][0]["content"]["parts"][0]["text"]
    try: j = json.loads(txt)
    except Exception: j = {"raw": txt}
    lv = 20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9); pk = 20 * np.log10(np.abs(y).max() + 1e-9)
    lines = [p["text"] for p in P if p["start"] < min(T1, t + 30) and p["end"] > t]
    R.append(dict(t0=round(t, 1), t1=round(min(T1, t + 30), 1), rms_db=round(float(lv), 1), peak_db=round(float(pk), 1), heard=j, script=lines))
    print("%5.0f〜%5.0f  %s" % (t, min(T1, t + 30), json.dumps(j.get("issues", j), ensure_ascii=False)[:300]), flush=True)
    json.dump(R, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t += 29
