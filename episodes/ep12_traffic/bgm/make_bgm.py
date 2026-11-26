# 12本目（渋滞）の BGM を新しく作る（6・9・16・17本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py D,Q,K,S,F   → <作業フォルダ>/stage/bgm/bgm_d.mp3 など
#   D（夕方のドライブ）：S01〜S03 休みの日の夕方、助手席のまるロボ。あたたかく、少しわくわく
#   Q（疑問がふくらむ）：S04〜S04の2 誰が測っている？ 先まで分かるのはなぜ？ 不思議・好奇心
#   K（数えてみる）：S05〜S06 歩道橋の上で車を数える。軽く、せわしなく、おかしみ
#   S（感知器のしくみ）：S07〜S09 道の上の機械と情報の流れ。すっきりした好奇心
#   F（町はずれ）：S10 畑の横の道。ひろびろ、少し首をかしげる感じ
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "D": COMMON + "A warm late-afternoon weekend drive through a friendly city, golden sunset light, a little robot riding in the passenger seat: "
                  "soft electric piano, light acoustic guitar strums, gentle shaker, warm round bass, major key, about 96 BPM, cozy, hopeful and a little excited.",
    "Q": COMMON + "Wondering about a mystery: who is measuring the traffic jam on the map? Questions grow one by one: soft plucked strings, "
                  "light celesta, gentle pulsing synth, soft low drum, about 92 BPM, curious and intriguing, slightly mysterious but never scary.",
    "K": COMMON + "A small robot on a pedestrian bridge trying to count cars rushing below and getting dizzy: bouncy pizzicato, light woodblock, "
                  "playful xylophone runs, quick hi-hat, about 120 BPM, busy, comical and lighthearted.",
    "S": COMMON + "Learning how a roadside sensor and an information network work: clean light synth arpeggios, soft bells, gentle plucks, "
                  "steady soft beat, major key, about 102 BPM, smart, clear and curious, like a friendly science lesson.",
    "F": COMMON + "A quiet open country road beside green fields under a big sky, a little robot looking around puzzled: soft acoustic guitar, "
                  "light flute-like pad, gentle marimba, relaxed beat, about 88 BPM, spacious, calm and a little wondering.",
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
