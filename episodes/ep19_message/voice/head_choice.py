# 文の頭の音が、にごっていないかを「どちらに聞こえるか」を選ばせて 4 回聞く（SKILL §3 の 16本目：書き起こしはゆれるので、選ばせて 4 回）
#   head_voicing.py で割合が大きかった文に使う。頭の言葉（例 ところで）と、にごらせた言葉（どころで）を並べて、どちらかを答えさせる（A/B の順は回ごとに入れかえる）
# MARU_WORK=<作業フォルダ> python3 head_choice.py 番号,番号…
import os, sys, json, base64, urllib.request, time, re
import pykakasi
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
L = {e["no"]: e for e in json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))}
kk = pykakasi.kakasi()
VO = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))


def ask(path, a, b):
    d = base64.b64encode(open(path, "rb").read()).decode()
    q = "この音声のいちばん最初の言葉は、次のどちらに聞こえますか。A：%s　B：%s　A か B の 1 文字だけで答えてください。" % (a, b)
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": d}}, {"text": q}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))["candidates"][0]["content"]["parts"][0]["text"].strip()
            return r[:1].upper()
        except Exception as e:
            time.sleep(10 * (k + 1))
    return "?"


for no in [int(x) for x in sys.argv[1].split(",")]:
    e = L[no]
    h = "".join(x["hira"] for x in kk.convert(re.split(r"[、。？！]", e["tts"].lstrip("…「"))[0]))[:5]
    v = VO.get(h[0], h[0]) + h[1:]
    votes = []
    for k in range(4):
        a, b = (h, v) if k % 2 == 0 else (v, h)
        r = ask(D + "/line_%03d.wav" % no, a, b)
        votes.append("正" if (r == "A") == (k % 2 == 0) else ("濁" if r in "AB" else "?"))
    print(no, e["id"], h, "/", v, " ".join(votes), "← 作り直す候補" if votes.count("濁") >= 2 else "", flush=True)
