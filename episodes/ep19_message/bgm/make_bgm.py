# 19本目（メッセージの旅）の BGM を新しく作る（6・9・16・17本目と同じやり方。回ごとに新しい曲）。Gemini の作曲モデル Lyria（lyria-3.5、約 3 分の mp3）
# 使い方：MARU_WORK=<作業フォルダ> python3 make_bgm.py H,J,F   → <作業フォルダ>/stage/bgm/bgm_h.mp3 など
#   H（朝の部屋）：S01〜S03 友だちにスタンプを送る・一瞬で届く・時計が出る。ほのぼの、少し不思議
#   J（スマホの中）：S04〜S07 基板の町で、言葉が数字の粒になり、包みに入る。小さな冒険・好奇心、少しきらきら
#   F（空の旅）：S08 電波に乗って空へ → すぐ着く。わくわく、軽やか
import os, sys, json, base64, time, urllib.request

COMMON = ("Instrumental background music for a cute, gentle science explainer video for all ages, starring a small round robot. "
          "No vocals. Stays under a narrator: no busy lead melody, soft dynamics, steady groove, loopable, consistent energy from start to end. ")
PROMPTS = {
    "H": COMMON + "A calm sunny morning in a cozy room, a little robot hops on a big smartphone to send a cute sticker to a far-away friend; "
                  "soft electric piano, light glockenspiel, gentle plucked strings with a small curious motif, light brushed drums, warm round bass, "
                  "about 92 BPM, homey, warm and a little wondering, not scary.",
    "J": COMMON + "Tiny adventure inside a smartphone: a miniature robot walks through a circuit-board city of chips while words turn into glowing dots and get packed "
                  "into a little parcel; soft synth arpeggios, twinkling bells, gentle marimba, soft pulsing pad, clean light beat, major key, about 100 BPM, "
                  "curious, sparkly and friendly, a sense of small wonder, never scary.",
    "F": COMMON + "Flying over a town on a sunny day, riding a gentle radio wave: airy strings pad, light flute-like synth, soft whooshing texture, "
                  "bouncy pizzicato, light drums, major key, about 108 BPM, excited, light and adventurous, cartoon-like.",
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
