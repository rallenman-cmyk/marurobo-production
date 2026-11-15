# 7本目の BGM を新しく作る（6本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py H,P,M   → <作業フォルダ>/stage/bgm/bgm_h.mp3 など
#   H（基本）：夜の机。まるロボがキーボードの上を跳ねる。やわらかく、かわいく
#   P（昔）：1860〜90年代の作業場・工場・教室。古いピアノの軽い曲
#   M（なぞ）：タイプライターの中・電信・なぞの説
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "H": COMMON + "A cozy night at a desk with a big computer keyboard: soft lo-fi electric piano, gentle plucked synth, light brushed drums, "
                  "warm round bass, a few toy-like key-click percussion touches, major key, about 92 BPM, calm, cute and curious.",
    "P": COMMON + "Old workshop in the 1870s, inventors building the first typewriter: light vintage upright piano in a gentle ragtime-like rhythm (not too fast), "
                  "soft clarinet, pizzicato strings, warm and nostalgic, about 100 BPM, playful but calm.",
    "M": COMMON + "A friendly mystery: investigating clues inside an old machine and a telegraph office: muted pizzicato strings, soft marimba, "
                  "low clarinet, light ticking percussion like a telegraph sounder, about 96 BPM, curious, a little suspenseful but never scary.",
}


def make(k, out):
    body = {"contents": [{"parts": [{"text": PROMPTS[k]}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/lyria-3.5:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for t in range(4):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=600)); break
        except Exception as e:
            print("retry", k, repr(e)[:160], flush=True); time.sleep(30 * (t + 1))
    else:
        raise SystemExit("失敗 " + k)
    for p in r["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            open(out, "wb").write(base64.b64decode(p["inlineData"]["data"])); print(k, out, os.path.getsize(out), p["inlineData"].get("mimeType")); return
    raise SystemExit("音が返らない " + json.dumps(r)[:300])


if __name__ == "__main__":
    d = os.path.join(os.environ["MARU_WORK"], "stage", "bgm"); os.makedirs(d, exist_ok=True)
    for k in sys.argv[1].split(","):
        make(k, os.path.join(d, "bgm_%s.mp3" % k.lower()))
