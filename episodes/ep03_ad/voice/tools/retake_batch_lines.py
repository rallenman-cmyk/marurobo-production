# 高すぎる文を、最初に声を作ったときと同じ「まとめ（batch_XX：5 文ずつ）」で読ませ直して差し替える（3本目 v11。2026-11-20 ユーザー「声はバッチファイルつかってやって」）
#   頼み方は Gemini のバッチ（batchGenerateContent：まとめて頼んで、できたら受け取る。ふつうの頼み方の 1 日 100 回の上限とは別。7本目 gen_batch.py と同じ）
#   ・1 文ずつ作るより、まわりの文と同じ流れ・調子で読まれる。声の AI の 1 日の上限（100 回）も、5 文で 1 回なので足りる
#   ・機械で高さを下げない（v10 の「声おかしすぎる」）。伸び縮みは 8% まで
#   MARU_WORK=<作業> python3 retake_batch_lines.py <元の声.wav> <出.wav> <作業フォルダ> 文ID…   （N=回数 既定 3）
#   流れ：文が入っているまとめを N 回読ませる（作ったものはとばす）→ split_narration と同じやり方で 1 文ずつに分ける
#     → 選ぶ文ごとに ①書き起こしが合う ②雑音なし ③高さが全体の中央値＋15Hz 以内 ④長さが元の枠の 0.92〜1.08 倍 の中から、高さが中央値に近いもの
#     → 枠ちょうどに伸び縮みして、元の文と同じ大きさで置く。合うものがない文は元の声のまま。結果は <作業>/result_batch.json
import base64, difflib, json, os, re, subprocess, sys, time, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE)
SK = os.path.join(V, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
sys.path.insert(0, HERE); sys.path.insert(0, SK)
from line_pitch import f0_track, measure
os.environ.setdefault("MARU_WORK", ".")
import split_narration as SN
src, out, W = sys.argv[1:4]; ids = sys.argv[4:]; N = int(os.environ.get("N", "3"))
os.makedirs(W, exist_ok=True)
D = os.environ["MARU_WORK"] + "/stage/voice/achernar"
WT = json.load(open(os.path.join(V, "word_times.json")))
SCR = {x["id"]: x for x in json.load(open(os.path.join(V, "script_v1_0.json")))}
NO2ID = {x["no"]: x["id"] for x in SCR.values()}
STYLE = open(os.path.join(V, "style_gentle_ad.txt"), encoding="utf-8").read().strip()   # 最初に作ったときと同じ指示（voice_test/style_gentle.txt と同じ中身）
med = float(np.median(list(measure(src, os.path.join(V, "word_times.json")).values())))
with wave.open(src) as w: sr = w.getframerate(); X = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

batches = {}
for fn in sorted(f for f in os.listdir(D) if f.startswith("batch_") and f.endswith(".json") and "take" not in f):
    j = json.load(open(os.path.join(D, fn), encoding="utf-8"))
    for no in j["nos"]:
        if NO2ID.get(no) in ids: batches[fn[:-5]] = j

def tts(lines, path):
    if os.path.exists(path): return True
    body = {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Achernar"}}}}}
    for k in range(6):
        try:
            res = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent",
                  data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]}), timeout=240))
            raw = base64.b64decode(res["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
            return True
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code == 429 and "per_day" in msg.lower().replace("perday", "per_day").replace("_per_model_per_day", "per_day"): print("1 日の上限：", path); return False
            time.sleep(15 * (k + 1))
        except Exception: time.sleep(10)
    return False

def tr(p):
    b = base64.b64encode(open(p, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえたとおりに日本語で書き起こしてください。書き起こしだけを出力。"}]}]}
    for _ in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]}), timeout=120))
            return r["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception: pass
    return ""
norm = lambda s: re.sub(r"[\s、。！？!?…「」（）・,.ー]", "", s)
def rms(v): v = v[np.abs(v) > 0.01]; return float(np.sqrt((v ** 2).mean())) if len(v) else 1e-3
def wr(p, x, r):
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(r); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

# ① まとめを N 回読ませる（バッチで一度に頼む。できているものはとばす）
def tts_batch(items):
    """items：[(文のリスト, 書く場所)] → バッチで頼んで、できるまで待って書く"""
    KEY = os.environ["GEMINI_API_KEY"]
    reqs = [{"request": {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)}]}],
                         "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Achernar"}}}}},
             "metadata": {"key": "k%03d" % i}} for i, (lines, _) in enumerate(items)]
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:batchGenerateContent",
                                 data=json.dumps({"batch": {"display_name": "maru-ep03-v11", "input_config": {"requests": {"requests": reqs}}}}).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    name = json.load(urllib.request.urlopen(req, timeout=240))["name"]; print("バッチ", name, len(items), "本", flush=True)
    t0 = time.time()
    while True:
        time.sleep(30)
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/" + name, headers={"x-goog-api-key": KEY}), timeout=120))
        if r.get("done"): break
        if time.time() - t0 > 3 * 3600: raise SystemExit("バッチが 3 時間で終わらない：" + name)
    st = r.get("metadata", {}).get("state")
    if st != "BATCH_STATE_SUCCEEDED": raise SystemExit("バッチ失敗 " + str(st))
    n = 0
    for it in r["response"]["inlinedResponses"]["inlinedResponses"]:
        k = int(it.get("metadata", {}).get("key", "k-1")[1:])
        try: dat = base64.b64decode(it["response"]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception: continue
        path = items[k][1]
        if dat[:4] == b"RIFF": open(path, "wb").write(dat)
        else:
            with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(dat)
        n += 1
    print("できた", n, "/", len(items), flush=True)
todo = [(j["tts"], os.path.join(W, "%s_take%d.wav" % (b, i))) for b, j in batches.items() for i in range(1, N + 1)]
todo = [x for x in todo if not os.path.exists(x[1])]
if todo: tts_batch(todo)
# ② 1 文ずつに分けて、選ぶ文を測る
cands = {k: [] for k in ids}
jobs = []
for b, j in batches.items():
    for i in range(1, N + 1):
        p = os.path.join(W, "%s_take%d.wav" % (b, i))
        if not os.path.exists(p): continue
        x, r = SN.load(p); segs = SN.split(x, r, j["tts"])
        if segs is None: print("分けられなかった：", p); continue
        for no, (a, e) in zip(j["nos"], segs):
            k = NO2ID[no]
            if k not in ids: continue
            y = x[int(max(0, a - SN.PAD) * r):int((e + SN.PAD) * r)]; q = os.path.join(W, "%s_take%d_%s.wav" % (b, i, k)); wr(q, y, r)
            jobs.append((k, q, y, r))
def meas(job):
    k, q, y, r = job
    f = f0_track(y, r); heard = tr(q)
    noise = subprocess.run([sys.executable, os.path.join(SK, "voice_noise.py"), "check", q], capture_output=True, text=True).stdout
    return k, dict(file=q, pitch=round(float(np.median(f))) if len(f) > 10 else 0, dur=round(len(y) / r, 2), heard=heard,
                   sim=round(difflib.SequenceMatcher(None, norm(WT[k]["text"]), norm(heard)).ratio(), 2), noise_ok=("雑音のあるファイル 0" in noise))
with ThreadPoolExecutor(6) as ex:
    for k, c in ex.map(meas, jobs): cands[k].append(c)
# ③ 選んで置く
Y = X.copy(); rep = {}
for k in ids:
    slot = WT[k]["end"] - WT[k]["start"]
    ok = [c for c in cands[k] if c["sim"] >= 0.85 and c["noise_ok"] and c["pitch"] and c["pitch"] <= med + 15 and 0.92 <= c["dur"] / slot <= 1.08]
    rep[k] = dict(slot=round(slot, 2), cands=[{a: c[a] for a in ("file", "pitch", "dur", "sim", "noise_ok", "heard")} for c in cands[k]])
    if not ok: rep[k]["chosen"] = None; continue
    c = min(ok, key=lambda c: abs(c["pitch"] - med) / 10 + abs(c["dur"] / slot - 1) * 20)
    fit = c["file"][:-4] + "_fit.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["file"], "-af", "rubberband=tempo=%.5f:pitchq=quality:formant=preserved" % (c["dur"] / slot), "-ar", str(sr), "-ac", "1", fit], check=True)
    with wave.open(fit) as w: z = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = int((WT[k]["start"] - 0.04) * sr); b = int((WT[k]["end"] + 0.04) * sr)
    z = z * rms(X[a:b]) / rms(z); Y[a:b] = 0; Y[a:a + len(z)] = z[:len(Y) - a]
    rep[k]["chosen"] = dict(file=c["file"], pitch=c["pitch"], tempo=round(c["dur"] / slot, 3), heard=c["heard"])
wr(out, Y, sr)
json.dump(dict(median=round(med), batches=sorted(batches), lines=rep), open(os.path.join(W, "result_batch.json"), "w"), ensure_ascii=False, indent=1)
print("中央値 %.0f Hz・まとめ %d 個 × %d 回" % (med, len(batches), N))
for k, r in rep.items(): print(k, "→", ("作り直し %sHz・伸び縮み %.3f" % (r["chosen"]["pitch"], r["chosen"]["tempo"])) if r["chosen"] else "元のまま（合うものなし：%s）" % [(c["pitch"], c["dur"], c["sim"]) for c in r["cands"]])
