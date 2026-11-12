# ナレーションの声（Gemini 3.8 Flash TTS・Achernar・「やさしく・おしとやかに」）を、台本 v2 の全文で作る
#   5文ずつまとめて読ませる（1日の回数の上限のため）→ stage/voice/achernar/batch_XX.wav と batch_XX.json（どの文か）
#   作ったまとめはとばす（途中で止まっても、同じコマンドで続きから）。回数の上限（429）では待ってやり直し、1日の上限なら止める
# 使い方: python3 make_narration.py [--only=3,7] [--n=5]
import sys, os, json, time, base64, wave, urllib.request
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"
OUT = SC + "/stage/voice/achernar"; os.makedirs(OUT, exist_ok=True)
L = json.load(open(SC + "/stage/script/script_v2_timed.json", encoding="utf-8"))
FIX = json.load(open(OUT + "/tts_text.json", encoding="utf-8")) if os.path.exists(OUT + "/tts_text.json") else {}   # 読み間違いを直す書き換え（文の番号 → 読ませる文）
NB = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--n=")), 5))
ONLY = [int(x) for x in next((a.split("=")[1] for a in sys.argv if a.startswith("--only=")), "").split(",") if x]
STYLE = open(SC + "/stage/voice_test/style_gentle.txt", encoding="utf-8").read().strip()     # 決めた声と同じ指示（2026-11-07、Achernar を選んでいただいた試し読みと同じ）
VOICE, MODEL = "Achernar", "gemini-3.8-flash-tts"


def tts(lines):
    prompt = STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(6):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=240))
            return base64.b64decode(res["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code == 429 and ("PerDay" in msg or "per day" in msg.lower()):
                print("DAILY LIMIT", msg[:300], flush=True); sys.exit(3)
            if e.code in (429, 500, 503):
                w = 30 * (k + 1); print("retry after", w, "s", e.code, msg[:160], flush=True); time.sleep(w); continue
            print("HTTP", e.code, msg[:400], flush=True); sys.exit(2)
        except Exception as e:
            w = 20 * (k + 1); print("retry after", w, "s", repr(e)[:160], flush=True); time.sleep(w)
    sys.exit(4)


groups = [L[i:i + NB] for i in range(0, len(L), NB)]
for gi, g in enumerate(groups):
    if ONLY and gi not in ONLY: continue
    wp, jp = OUT + "/batch_%02d.wav" % gi, OUT + "/batch_%02d.json" % gi
    if os.path.exists(wp) and os.path.exists(jp) and not ONLY: continue
    texts = [FIX.get(str(e["no"]), e["text"]) for e in g]
    raw = tts(texts)
    if raw[:4] == b"RIFF": open(wp, "wb").write(raw)
    else:
        with wave.open(wp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
    json.dump(dict(nos=[e["no"] for e in g], texts=[e["text"] for e in g], tts=texts), open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    with wave.open(wp) as w: d = w.getnframes() / w.getframerate()
    print("BATCH %02d  lines %s  %.1fs  %d chars" % (gi, [e["no"] for e in g], d, sum(len(t) for t in texts)), flush=True)
    time.sleep(7)                                                    # 1分に10回まで
print("ALL DONE", flush=True)
