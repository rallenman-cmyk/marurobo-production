# 17本目（カード）の BGM を新しく作る（6・9・16本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py N,H,M,T,C   → <作業フォルダ>/stage/bgm/bgm_n.mp3 など
#   N（夜のカード）：S01 はじめてのカードを金庫にしまう夜。やさしく、少しわくわく
#   H（朝の家・あれ？）：S02〜S03 知らせが来て、金庫を開ける。軽い不思議
#   M（探偵）：S04〜S09 探偵の帽子で 3 か所を調べる。軽い探偵の感じ
#   T（なぞ解き）：S10〜S12 番号の決まり。ひらめき・好奇心
#   C（お店）：S13〜S14 ネットのお店で打ってみる。明るく、少し楽しい
#   B（影の部屋）：S15 暗い部屋の機械が番号の札を作る。なぞめいて、こわくない
#   K（試す）：S16〜S17 お店の門で何度も試す。一定の刻みで、少しずつ張りつめる。こわくない
#   R（正体）：S18〜S19 まるロボの番号だった・手口の正体。考えこむ、落ち着いた感じ（こわがらせない）
#   L（台帳）：S20〜S22 なぜ使っていないカードも？ 塔の中の台帳を調べる。好奇心・落ち着いた説明
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "N": COMMON + "A quiet cozy night in a small room: a little robot carefully puts its very first card into a small safe. Soft music box, gentle "
                  "celesta, warm pad, soft brushed drums, major key with a dreamy feeling, about 78 BPM, tender and a little excited.",
    "H": COMMON + "A calm sunny morning that turns a little puzzling: soft electric piano, light glockenspiel, plucked strings with a curious question-like "
                  "motif, light brushed drums, warm round bass, about 92 BPM, homey and gently mysterious, not scary.",
    "M": COMMON + "A small robot detective in a deerstalker hat searching a room for clues with a magnifying glass: pizzicato strings, soft marimba, "
                  "light finger snaps, walking upright bass, about 100 BPM, curious and playful detective mood, never scary.",
    "T": COMMON + "Discovering a hidden rule in a row of numbers, little 'aha' moments: light synth arpeggios, soft bells, gentle plucks, "
                  "clean steady beat, major key, about 104 BPM, smart, bright and curious, like solving a puzzle.",
    "C": COMMON + "A bright friendly shop front on a sunny day, a little robot pressing big buttons on a register: ukulele, light handclaps, "
                  "glockenspiel, bouncy bass, major key, about 108 BPM, cheerful and a bit playful.",
    "B": COMMON + "Peeking into a dim little room at night where a gray box machine quietly prints number slips: soft muted plucks, low warm pad, "
                  "light ticking clock-like percussion, mellow bass, minor-ish but cute, about 90 BPM, mysterious and curious, never scary or dark.",
    "K": COMMON + "Number slips being tried again and again at a shop gate, steady repetitive pulse that slowly builds a little tension: "
                  "pizzicato ostinato, soft synth pulse, light shaker, gentle low drum, about 112 BPM, focused and suspenseful but cartoon-like, never scary.",
    "R": COMMON + "Realizing how a puzzle works, calm and thoughtful wrap-up: soft piano, warm strings pad, gentle bells, light brushed beat, "
                  "about 84 BPM, reflective and reassuring, a little serious but kind, not sad and not scary.",
    "L": COMMON + "Exploring a bright, tidy hall full of softly glowing lamps to understand why something happened: gentle marimba and celesta, "
                  "soft warm pad, light pizzicato, steady soft beat, about 92 BPM, curious, calm and clear like a friendly explanation, never scary.",
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
