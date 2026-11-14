# 作り直した声の候補を、前後の無音を切って、ひらがなで書き起こし、言ってほしい読みが入っているか・長さを並べる（3本目 v4）
#   python3 retake_check.py <読み（ひらがな、例 ときしかもんを）> 候補1.wav 候補2.wav …   → 切った声は <候補>_t.wav
#   読みは、書き起こしから空白・句読点を除いた中に入っているかで見る。3 回書き起こして、何回入っていたかを出す
import sys, os, json, base64, wave, re, urllib.request
import numpy as np
want = sys.argv[1]; files = sys.argv[2:]


def trim(p, o):
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    h = sr // 100; n = len(x) // h; f = x[:n * h].reshape(n, h).astype(float) / 32768
    db = 20 * np.log10(np.sqrt((f ** 2).mean(1)) + 1e-12); on = np.where(db > db.max() - 38)[0]
    a = max(0, on[0] * h - int(.06 * sr)); b = min(len(x), (on[-1] + 1) * h + int(.06 * sr)); y = x[a:b]
    with wave.open(o, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())
    return len(y) / sr


def tr(p):
    b = base64.b64encode(open(p, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください（漢字やカタカナは使わない）。のばす音は「ー」。書き起こしだけを出力。"}]}]}
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]}), timeout=120))
    return r["candidates"][0]["content"]["parts"][0]["text"].strip()


for p in files:
    o = p[:-4] + "_t.wav"; d = trim(p, o); hs = [tr(o) for _ in range(3)]
    ok = sum(want in re.sub(r"[\s、。，．,.！？!?ー]", "", h).replace("ー", "") for h in hs)
    print("%s  %.2f 秒  %d/3  %s" % (os.path.basename(o), d, ok, hs[0]))
