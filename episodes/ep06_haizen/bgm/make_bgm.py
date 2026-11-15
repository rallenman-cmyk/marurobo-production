# 6本目の BGM を新しく作る（2026-11-15 ユーザー「bgm新しいの作ろう」）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py H,M,T   → <作業フォルダ>/stage/bgm/bgm_h.mp3 など
#   H（基本）：お昼のファミレス。あたたかく、かわいく、軽い
#   M（なぞ）：先輩の目で見た暗い店（点の雲）
#   T（ためす）：低い物・高い物・子どもの飛び出し・狭い通路
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "H": COMMON + "Cozy family restaurant at lunchtime: light bossa nova feel, nylon guitar, soft electric piano, ukulele, gentle brushed drums, "
                  "warm upright bass, a few bright glockenspiel touches, major key, about 98 BPM, friendly, warm and a little playful.",
    "M": COMMON + "Looking through a robot's eyes in the dark: soft synth pads, slow arpeggiated celesta, gentle sonar-like pings, airy, "
                  "curious and calm, not scary, about 84 BPM, minor key turning warm.",
    "T": COMMON + "Playful experiment in a busy restaurant: pizzicato strings, marimba, light hand claps, bouncy bass, toy piano accents, "
                  "about 112 BPM, curious and cheerful, a little sneaky.",
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
