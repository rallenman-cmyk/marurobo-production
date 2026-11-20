# 試し：字幕の 1 行ずつの区切りが、声のどこで始まるかを聞き取らせる
import os, sys, json, wave, re
import numpy as np
_NOS = sys.argv[1]; sys.argv = [sys.argv[0], "1"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retake_line.py"), encoding="utf-8").read().split("norm = lambda")[0]
exec(src)
import base64
def starts(x, pieces):
    q = "この音声は次の文を読んだものです。次の各部分を読み始める時刻（秒、小数2けた）を、JSON の配列だけで出力してください。\n" + "\n".join("%d: %s" % (i + 1, p) for i, p in enumerate(pieces))
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(x)).decode()}}, {"text": q}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    return json.loads(post("gemini-3.8-flash", body, 120)["candidates"][0]["content"]["parts"][0]["text"])
for item in _NOS.split(";"):
    no, ps = item.split(":", 1)
    x = np.frombuffer(wave.open(D + "/line_%03d.wav" % int(no)).readframes(10 ** 8), np.int16).astype(np.float32) / 32768
    print(no, len(x) / 24000, starts(x, ps.split("|")), flush=True)
