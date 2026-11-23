# 強い聞き取り（gemini-3.1-pro-preview）で、ひらがなで 2 回聞き直す（聞き取りは毎回ぶれるので、何度も出る読み違いだけを直す。SKILL §2.5 I）
# MARU_WORK=<作業> python3 hear_pro.py 番号,番号…
import os, sys, json, base64, urllib.request
D = os.environ["MARU_WORK"] + "/stage/voice/achernar"
def tr(p):
    b = base64.b64encode(open(p, 'rb').read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください。言いまちがいや抜けた音・息の音（はぁ など）も、そのまま書く。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"]).strip()
for no in sys.argv[1].split(","):
    print(no, "|", tr(D + "/line_%03d.wav" % int(no)), "|", tr(D + "/line_%03d.wav" % int(no)), flush=True)
