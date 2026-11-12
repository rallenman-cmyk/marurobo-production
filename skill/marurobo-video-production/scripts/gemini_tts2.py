# Gemini TTS（人物・場面・演出の指示つき）：指示は「台本」と分けて書き、台本だけを読ませる。キーは GEMINI_API_KEY（ヘッダー）
# 使い方: python3 gemini_tts2.py 出力.wav 声の名前 台本.txt 指示.txt [--model=gemini-3.8-flash-tts]
import sys, os, json, base64, wave, urllib.request
out, voice, tpath, spath = sys.argv[1:5]
model = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--model=")), "gemini-3.8-flash-tts")
script = open(tpath, encoding="utf-8").read().strip(); style = open(spath, encoding="utf-8").read().strip()
prompt = style + "\n#### TRANSCRIPT\n" + script
body = {"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model, data=json.dumps(body).encode("utf-8"),
                             headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
try: res = json.load(urllib.request.urlopen(req, timeout=180))
except urllib.error.HTTPError as e: print("HTTP", e.code, e.read().decode("utf-8", "replace")[:400]); sys.exit(1)
part = res["candidates"][0]["content"]["parts"][0]["inlineData"]; raw = base64.b64decode(part["data"])
if raw[:4] == b"RIFF": open(out, "wb").write(raw)
else:
    with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
with wave.open(out, "rb") as w: print("WROTE", out, "%.2fs" % (w.getnframes() / w.getframerate()))
