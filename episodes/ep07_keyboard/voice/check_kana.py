# 声をひらがなで書き起こす（漢字で書き起こすと聞き違いを直してしまう。SKILL §3「読み違いの点検はひらがなで」）
# MARU_WORK=<作業フォルダ> python3 check_kana.py → heard_kana.json（文ごとに、読ませた文 tts と、聞こえたひらがな）
import os, sys, json, base64, urllib.request
from concurrent.futures import ThreadPoolExecutor
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
L = json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))
def tr(p):
    b = base64.b64encode(open(p, 'rb').read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえたとおりに、すべてひらがなとカタカナだけで書き起こしてください。漢字・数字・英字は使わず、英字の名前はカタカナで（例：エー、ビー）。のばす音は「ー」。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(4):
        try: return json.load(urllib.request.urlopen(req, timeout=120))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e: err = str(e)
    return "ERR " + err
with ThreadPoolExecutor(4) as ex: R = list(ex.map(lambda e: tr(D + "/line_%03d.wav" % e["no"]), L))
json.dump([dict(no=e["no"], id=e["id"], tts=e["tts"], kana=r) for e, r in zip(L, R)], open(D + "/heard_kana.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for e, r in zip(L, R): print(e["id"], r)
