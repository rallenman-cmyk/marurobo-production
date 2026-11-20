# 声を 1 文ずつ聞かせて、「遅すぎる・引きのばした感じ・変な抑揚・ノイズ・途中で声が変わる」を探す
# （2026-11-20 ユーザー「声おかしすぎる、スローになってるのかなんなのか」「全部みなおして」。3本目 v10）
# 使い方：python3 voice_listen.py <声のフォルダ（line_001.wav …）> <台本 json（no・text の並び）> [出力 json]
#   GEMINI_API_KEY が要る。結果は「おかしい」と言われた文だけ表示する。速さは、声のある所だけで測った 1 秒あたりの字数も並べる。
import os, sys, json, re, base64, urllib.request, wave
import numpy as np
from concurrent.futures import ThreadPoolExecutor

D, SJ = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(D, "listen.json")
MODEL = os.environ.get("LISTEN_MODEL", "gemini-3.8-flash")
L = json.load(open(SJ, encoding="utf-8"))
if isinstance(L, dict): L = list(L.values())

ASK = ("あなたは日本語ナレーションの音声チェック係です。この音声（台本：「%s」）を聞いて、"
       "自然な女性ナレーションとして変な所がないか厳しく見てください。"
       "見る点：(1) 遅すぎる・音を引きのばしたような声 (2) 速すぎる (3) 不自然な抑揚・機械っぽい声 (4) 途中で声の高さや声質が変わる "
       "(5) ノイズ・切れ・二重の声 (6) 読み間違い。"
       "次の JSON だけを出力：{\"ok\": true か false, \"speed\": \"遅い\" か \"普通\" か \"速い\", \"score\": 1〜5（5 が自然）, \"issue\": \"変な所を短く。なければ空\"}")


def ask(e):
    path = os.path.join(D, "line_%03d.wav" % e["no"])
    b = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": ASK % e["text"]}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL,
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    err = ""
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))
            return json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as ex:
            err = str(ex)
    return {"ok": None, "issue": "ERR " + err}


def rate(e):
    with wave.open(os.path.join(D, "line_%03d.wav" % e["no"])) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    h = int(sr * 0.02); m = len(x) // h
    v = (np.abs(x[:m * h]).reshape(m, h).max(1) > 0.02).sum() * 0.02
    n = len(re.sub(r"[、。？！…「」\s・（）?!]", "", e["text"]))
    return round(n / max(v, 0.1), 2), round(len(x) / sr, 2)


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(ask, L))
out = []
for e, r in zip(L, res):
    cps, dur = rate(e)
    out.append(dict(no=e["no"], id=e.get("id", ""), text=e["text"], cps=cps, dur=dur, **r))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
bad = [o for o in out if o.get("ok") is not True or o.get("speed") != "普通" or (o.get("score") or 5) <= 3]
for o in sorted(bad, key=lambda o: (o.get("score") or 0)):
    print("%s %s 点%s %s 字/秒%.1f  %s\n    → %s" % (o["no"], o["id"], o.get("score"), o.get("speed"), o["cps"], o["text"], o.get("issue")))
print("全 %d 文、気になる文 %d" % (len(out), len(bad)))
