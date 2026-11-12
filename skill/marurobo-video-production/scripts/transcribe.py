import sys, os, json, base64, urllib.request
def tr(path, model):
    b = base64.b64encode(open(path, 'rb').read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえたとおりに日本語で書き起こしてください。句読点はそのまま。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    r = json.load(urllib.request.urlopen(req, timeout=120)); return r["candidates"][0]["content"]["parts"][0]["text"].strip()
model = sys.argv[1]
for p in sys.argv[2:]:
    try: print(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(p))))), os.path.basename(p), '|', tr(p, model).replace('\n', ' '))
    except Exception as e: print(p, 'ERR', str(e)[:200])
