# 声の読み方を確かめる：①台本の各文の正しい読み（ひらがな）を文章用モデルで作る（readings.json、一度だけ）
#   ②各文の声（line_NNN.wav）をひらがなで書き起こす（heard.json）③二つを比べ、違う文を出す（check.json）
#   書き起こしは声の回数の枠を使わない（文章用モデル gemini-3.8-flash）
# 使い方: python3 check_readings.py [--only=12,40]
import os, sys, json, base64, time, difflib, unicodedata, urllib.request
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; D = SC + "/stage/voice/achernar"
L = json.load(open(SC + "/stage/script/script_v2_timed.json", encoding="utf-8"))
ONLY = [int(x) for x in next((a.split("=")[1] for a in sys.argv if a.startswith("--only=")), "").split(",") if x]
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"


def ask(parts, as_json=False):
    body = {"contents": [{"parts": parts}]}
    if as_json: body["generationConfig"] = {"responseMimeType": "application/json"}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=240))["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e: print("retry", repr(e)[:120], flush=True); time.sleep(15 * (k + 1))
    raise SystemExit("ask failed")


def kana(s):
    s = unicodedata.normalize("NFKC", s); out = []
    for ch in s:
        o = ord(ch)
        if 0x30A1 <= o <= 0x30F6: ch = chr(o - 0x60)                                  # カタカナ → ひらがな
        if 0x3041 <= o <= 0x309F or 0x30A1 <= o <= 0x30F6 or ch == "ー": out.append(ch)
        elif 0x3041 <= ord(ch) <= 0x309F: out.append(ch)
    return "".join(out)


rp = os.path.join(D, "readings.json")
if not os.path.exists(rp):
    items = [dict(no=e["no"], text=e["text"]) for e in L]
    prompt = ("次の日本語のナレーション台本の各文について、ふつうに読み上げたときの読みを、すべてひらがなで書いてください。"
              "記号は書かず、英字（Bluetooth など）はカタカナの読み（ブルートゥース）をひらがなにしてください。"
              "JSON の配列で、[{\"no\": 番号, \"yomi\": \"ひらがな\"}, ...] の形だけを返してください。\n" + json.dumps(items, ensure_ascii=False))
    R = json.loads(ask([{"text": prompt}], as_json=True)); json.dump({str(r["no"]): r["yomi"] for r in R}, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
READ = json.load(open(rp, encoding="utf-8"))
hp = os.path.join(D, "heard.json"); HEARD = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
for e in L:
    no = str(e["no"]); wp = os.path.join(D, "line_%03d.wav" % e["no"])
    if not os.path.exists(wp) or (no in HEARD and not ONLY) or (ONLY and e["no"] not in ONLY): continue
    data = base64.b64encode(open(wp, "rb").read()).decode()
    HEARD[no] = ask([{"inlineData": {"mimeType": "audio/wav", "data": data}},
                     {"text": "この音声で話されている言葉を、聞こえたとおりに、すべてひらがなで書き起こしてください。漢字・カタカナ・記号は使わず、ひらがなだけを返してください。"}]).strip()
    json.dump(HEARD, open(hp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
res = []
for e in L:
    no = str(e["no"])
    if no not in HEARD: continue
    a, b = kana(READ.get(no, "")), kana(HEARD[no]); r = difflib.SequenceMatcher(None, a, b).ratio()
    diffs = [(a[i1:i2], b[j1:j2]) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if tag != "equal"]
    res.append(dict(no=e["no"], ratio=round(r, 3), text=e["text"], expect=a, heard=b, diffs=diffs))
json.dump(res, open(os.path.join(D, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
bad = [r for r in res if r["ratio"] < 0.97 or r["diffs"]]
print("checked", len(res), "with differences", len(bad))
for r in bad: print(r["no"], r["ratio"], r["diffs"][:6], "|", r["text"])
