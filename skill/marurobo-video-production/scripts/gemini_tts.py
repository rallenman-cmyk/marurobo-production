# Gemini の TTS で、一文を WAV（24kHz・16bit・モノラル）にする。キーは環境変数 GEMINI_API_KEY（ヘッダーで送る。表示しない）
# 使い方: python3 gemini_tts.py 出力.wav 声の名前 "読む文" ["読み方の指示（任意）"] [--model gemini-3.8-flash-tts]
import sys, os, json, base64, wave, urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("--model")]
model = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--model=")), "gemini-3.8-flash-tts")
out, voice, text = args[0], args[1], args[2]
style = args[3] if len(args) > 3 else ""
prompt = (style + "：" + text) if style else text
body = {"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model,
                             data=json.dumps(body).encode("utf-8"),
                             headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
try:
    res = json.load(urllib.request.urlopen(req, timeout=120))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "replace")[:400]); sys.exit(1)
part = res["candidates"][0]["content"]["parts"][0]["inlineData"]
raw = base64.b64decode(part["data"]); mt = part.get("mimeType", "")
if raw[:4] == b"RIFF":                                              # WAV がそのまま返る型（3.8）：そのまま書く
    open(out, "wb").write(raw)
else:                                                               # 生の PCM（audio/L16;rate=24000）：WAV の頭を付ける
    rate = int(mt.split("rate=")[1].split(";")[0]) if "rate=" in mt else 24000
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(raw)
with wave.open(out, "rb") as w:
    print("WROTE", out, "%.2fs" % (w.getnframes() / w.getframerate()), "%dHz %dch" % (w.getframerate(), w.getnchannels()), mt)
