# 声をひらがなで書き起こす（漢字で書き起こすと聞き違いを直してしまう。SKILL §3「読み違いの点検はひらがなで」）
# 12本目（17本目から写した）：聞き取りのモデルが混んで返事が来ない（2026-11-26：時間切れ・503）ので、
#   ①1 本ずつ結果を保存して、止まっても続きから ②混んでいたら別のモデルに切り替える ③時間切れは 60 秒、に直した
# MARU_WORK=<作業フォルダ> python3 check_kana.py [番号,…] → heard_kana.json（文ごとに、読ませた文 tts と、聞こえたひらがな）
import os, sys, json, base64, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
L = json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))
OUT = D + "/heard_kana.json"
MODELS = ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3-flash-preview"]   # 2026-11-26：3.8・3.5 は混んで返事なし、2.5 はもう使えない（404）
PROMPT = "この音声を、聞こえたとおりに、すべてひらがなとカタカナだけで書き起こしてください。漢字・数字・英字は使わず、英字の名前はカタカナで（例：エー、ビー）。のばす音は「ー」。書き起こしだけを出力。"
done = {str(r["no"]): r for r in json.load(open(OUT, encoding="utf-8"))} if os.path.exists(OUT) else {}
ONLY = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else None


def tr(p):
    b = base64.b64encode(open(p, 'rb').read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": PROMPT}]}]}
    err = ""
    for k in range(8):
        m = MODELS[k % len(MODELS)]
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % m, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))["candidates"][0]["content"]["parts"][0]["text"].strip(), m
        except Exception as e:
            err = "%s %s" % (m, e); time.sleep(3 + 2 * k)
    return "ERR " + err, ""


def one(e):
    k = str(e["no"])
    if ONLY is None and k in done and not done[k]["kana"].startswith("ERR"): return
    r, m = tr(D + "/line_%03d.wav" % e["no"])
    done[k] = dict(no=e["no"], id=e["id"], tts=e["tts"], kana=r, model=m)
    json.dump(sorted(done.values(), key=lambda x: x["no"]), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(e["id"], m, r, flush=True)


with ThreadPoolExecutor(4) as ex:
    list(ex.map(one, [e for e in L if ONLY is None or e["no"] in ONLY]))
print("のこり ERR", sum(1 for r in done.values() if r["kana"].startswith("ERR")), "／", len(done))
