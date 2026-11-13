# 声を書き起こして、台本の文と比べる（読み間違い・読みとばしを見つける）
# MARU_WORK=<作業フォルダ> python3 check_reading.py [モデル=gemini-3.8-flash]
import os, sys, json, re, base64, urllib.request, difflib
from concurrent.futures import ThreadPoolExecutor
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.8-flash"
L = json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))


def tr(path):
    b = base64.b64encode(open(path, 'rb').read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえたとおりに日本語で書き起こしてください。数字は漢数字やかなでなく、聞こえた読みをひらがなで書いてもよい。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120)); return r["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            err = str(e)
    return "ERR " + err


norm = lambda s: re.sub(r'[、。？！「」…　 ・,.!?\s]', '', s)
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(lambda e: tr(D + "/line_%03d.wav" % e["no"]), L))
out = []
for e, t in zip(L, res):
    r1 = difflib.SequenceMatcher(None, norm(e["text"]), norm(t)).ratio()
    r2 = difflib.SequenceMatcher(None, norm(e["tts"]), norm(t)).ratio()
    out.append(dict(no=e["no"], id=e["id"], text=e["text"], heard=t, score=round(max(r1, r2), 3)))
json.dump(out, open(D + "/heard.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for o in sorted(out, key=lambda o: o["score"])[:30]:
    if o["score"] < 0.9:
        print("%.2f %s\n  台本: %s\n  声　: %s" % (o["score"], o["id"], o["text"], o["heard"]))
print("done", len(out))
