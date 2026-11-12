# 音声（WAV）を Gemini で書き起こす（声が台本どおりか確かめる）。使い方: python3 transcribe.py a.wav [b.wav …]
import sys, os, json, base64, urllib.request
for path in sys.argv[1:]:
    data = base64.b64encode(open(path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": data}},
                                    {"text": "この音声で話されている日本語を、そのまま書き起こしてください。書き起こしだけを返してください。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180)); print(os.path.basename(path), "->", r["candidates"][0]["content"]["parts"][0]["text"].strip())
    except urllib.error.HTTPError as e:
        print(os.path.basename(path), "HTTP", e.code, e.read().decode("utf-8", "replace")[:300])
