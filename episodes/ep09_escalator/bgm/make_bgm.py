# 9本目の BGM を新しく作る（6・9本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py H,N,K   → <作業フォルダ>/stage/bgm/bgm_h.mp3 など
#   H（基本）：昼の駅。まるロボがエスカレーターに乗る。やわらかく、かわいく
#   N（床の下）：夜の点検・床の下の機械の部屋・歯車と鎖。少しふしぎで、こわくない
#   K（挑戦）：見張りに挑戦する夜。軽くてちょっとおどけた感じ
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "H": COMMON + "A bright, friendly train station with an escalator gently moving: soft electric piano, light marimba, gentle plucked synth, "
                  "light brushed drums, warm round bass, major key, about 96 BPM, calm, cute and curious.",
    "N": COMMON + "A quiet night inspection under the floor, inside the machine room of an escalator with big gears and chains: muted pizzicato strings, "
                  "soft mallets, low warm synth pad, light mechanical ticking percussion, about 90 BPM, mysterious and curious but never scary.",
    "K": COMMON + "A playful little challenge at night: a small robot tries to outsmart safety sensors and keeps getting stopped: light bassoon and pizzicato, "
                  "soft woodblock, gentle staccato piano, about 104 BPM, comedic, light and warm.",
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
