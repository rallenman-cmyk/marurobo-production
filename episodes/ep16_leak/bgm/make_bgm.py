# 16本目の BGM を新しく作る（6・9本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py H,M,S   → <作業フォルダ>/stage/bgm/bgm_h.mp3 など
#   H（家）：朝のまるロボの家。やわらかく、かわいい日常
#   M（調べる）：お城を調べる・裏口を見つける・数の図。好奇心のある、軽い探偵の感じ
#   S（影）：夜のお城の影・かくれた市場・脅し。ひそやか。こわすぎない
#   B（守る）：自分でできること・まとめ。明るく前向き（9章で使う）
#   N（夜に忍ぶ）：S12〜S15 夜のお城（影が忍びこむ・中を調べる）。v1 のコメントで S から替えた
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "H": COMMON + "A calm sunny morning in a cozy room: soft electric piano, light glockenspiel, gentle plucked guitar, light brushed drums, "
                  "warm round bass, major key, about 92 BPM, homey, cute and peaceful.",
    "M": COMMON + "A small robot curiously investigating a big castle gate and finding a hidden back door, like a light detective story: "
                  "pizzicato strings, soft marimba, light finger snaps, walking upright bass, about 100 BPM, curious and playful, not scary.",
    "S": COMMON + "A quiet night: a shadowy thief sneaks through a castle and a hidden market, sneaky and suspenseful but gentle for children: "
                  "muted plucked low strings, soft celesta, light ticking percussion, low warm synth pad, minor key, about 84 BPM, mysterious, never horror.",
    # N（夜に忍ぶ）：v1 のユーザー「このbgm違うのにしたい」（S12 夜の裏口）→ 選んだのは「そっと忍ぶ感じ」：ピチカートと低い音で、こっそり・ひそひそ。こわすぎず少しユーモア
    "N": COMMON + "Tiptoeing at night: a shadow quietly sneaks up to a castle back door and a little robot peeks from behind a wall. "
                  "Sneaky cartoon-like tiptoe music: soft staccato pizzicato strings in short steps, low bassoon-like plucks, light woodblock ticks, "
                  "brushed snare very soft, occasional celesta sparkle, minor key with a playful wink, about 96 BPM, secretive and a little humorous, never scary.",
    "B": COMMON + "A hopeful, bright resolution: the small robot changes all its door keys and feels safe again: soft piano, warm strings, "
                  "light claps, gentle ukulele, major key, about 104 BPM, uplifting and reassuring.",
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
