# 1 文だけ声を作り直す（読み違い・聞き取りにくい・極端に遅い文）。何回か作って、書き起こしが台本にいちばん近く、
# 声の高さ・速さがまわりの文に近いものを選ぶ。前の声は line_NNN_before_retake.wav に残す
# MARU_WORK=<作業フォルダ> python3 retake_line.py 4,10,13 [回数=4] [必ず聞こえてほしい言葉=まる]
#   KANA=1 をつけると、ひらがなで書き起こして MUST（ひらがなで書く。例 そうじきが）を確かめる（5本目 v2「そうじが と読んでいる」）
#   前後の文も一緒に読ませて（3 文）、まん中の文だけを切り出す（1 文だけで読ませると調子が変わるため）
#   BATCH=1 をつけると、声は Gemini のバッチ（まとめて頼んで、数分後に受け取る）で作る。1 日の回数の上限が別なので、回数切れのときに使う（6本目 v3、ユーザー「バッチファイルでやってみて」）
import os, sys, json, wave, base64, urllib.request, difflib, re, shutil, time
import numpy as np
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
NOS = [int(x) for x in sys.argv[1].split(",")]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
MUST = sys.argv[3] if len(sys.argv) > 3 else ""
L = json.load(open(W + "/stage/script/script_v2_timed.json", encoding="utf-8"))
FIX = json.load(open(D + "/tts_text.json", encoding="utf-8")) if os.path.exists(D + "/tts_text.json") else {}
V = json.load(open(D + "/lines.json", encoding="utf-8"))
STYLE = open(W + "/stage/voice_test/style_gentle.txt", encoding="utf-8").read().strip()
KEY = os.environ["GEMINI_API_KEY"]


def post(model, body, timeout=240):
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    for k in range(5):
        try: return json.load(urllib.request.urlopen(req, timeout=timeout))
        except Exception as e:
            print("retry", repr(e)[:120], flush=True); time.sleep(20 * (k + 1))
    raise RuntimeError("API 失敗")


def tts(lines):
    body = {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Achernar"}}}}}
    r = post("gemini-3.8-flash-tts", body)
    return np.frombuffer(base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]), np.int16).astype(np.float32) / 32768


def tts_batch(jobs):
    """jobs：[文のリスト] → 声のリスト（同じ順）。バッチで頼んで、できるまで待つ"""
    reqs = [{"request": {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)}]}],
                         "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Achernar"}}}}},
             "metadata": {"key": "k%03d" % i}} for i, lines in enumerate(jobs)]
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:batchGenerateContent",
                                 data=json.dumps({"batch": {"display_name": "maru-retake", "input_config": {"requests": {"requests": reqs}}}}).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    name = json.load(urllib.request.urlopen(req, timeout=240))["name"]; print("バッチ", name, len(jobs), "本", flush=True)
    while True:
        time.sleep(20)
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/" + name, headers={"x-goog-api-key": KEY}), timeout=120))
        st = r.get("metadata", {}).get("state")
        if r.get("done"): break
    if st != "BATCH_STATE_SUCCEEDED": raise SystemExit("バッチ失敗 " + str(st))
    out = {}
    for it in r["response"]["inlinedResponses"]["inlinedResponses"]:
        k = it.get("metadata", {}).get("key")
        try:
            dat = base64.b64decode(it["response"]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception: out[k] = None; continue
        if dat[:4] == b"RIFF":   # バッチは WAV の形で返る（ふつうの呼び出しは中身だけ）
            import io
            with wave.open(io.BytesIO(dat)) as w_: dat = w_.readframes(w_.getnframes())
        out[k] = np.frombuffer(dat, np.int16).astype(np.float32) / 32768
    return [out.get("k%03d" % i) for i in range(len(jobs))]


def wav_bytes(x, sr=24000):
    import io
    b = io.BytesIO()
    with wave.open(b, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return b.getvalue()


def heard(x):
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(x)).decode()}}, {"text": "この音声を、聞こえたとおりに日本語で書き起こしてください。書き起こしだけを出力。"}]}]}
    return post("gemini-3.8-flash", body, 120)["candidates"][0]["content"]["parts"][0]["text"].strip()


def heard_kana(x):
    """ひらがなだけで書き起こす（漢字にすると「そうじが／そうじきが」の聞き違いが分からないため。KANA=1 のとき MUST をこれで確かめる）"""
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes(x)).decode()}}, {"text": "この音声を、聞こえた音のとおりに、すべてひらがなで書き起こしてください。漢字・カタカナは使わない。言いまちがいや抜けた音も、そのまま書く。書き起こしだけを出力。"}]}]}
    return post("gemini-3.8-flash", body, 120)["candidates"][0]["content"]["parts"][0]["text"].strip()


def runs(x, sr=24000, thr=-42, fr=0.01, min_sil=0.12):
    n = int(fr * sr); m = len(x) // n
    db = 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9); q = db < thr; out = []; i = 0
    while i < m:
        if q[i]:
            j = i
            while j < m and q[j]: j += 1
            if (j - i) * fr >= min_sil: out.append((i * fr, j * fr))
            i = j
        else: i += 1
    return out, db


def pick_first(x, texts, sr=24000):
    """1 本目の文（前の文がない）：2 文で読ませて、字数の割合に近い無音で切った前の文だけを取る（5本目 v2 で、2 文ともそのまま入っていた）"""
    sil, db = runs(x)
    tot = len(x) / sr; e1 = tot * len(texts[0]) / (len(texts[0]) + len(texts[1]))
    mids = [((a + b) / 2, b - a) for a, b in sil if a > 0.2 and b < tot - 0.2]
    if not mids: return None
    m = min(mids, key=lambda q: abs(q[0] - e1) - 0.8 * q[1])
    y = x[:int(m[0] * sr)]
    on = np.where(np.abs(y) > 0.01)[0]
    return y[max(0, on[0] - 960): on[-1] + 960] if len(on) else None


def pick_middle(x, texts, sr=24000):
    """3 文を読ませた声から、まん中の文を切り出す（字数の割合にいちばん合う、長い無音 2 つで切る）"""
    sil, db = runs(x)
    mids = [((a + b) / 2, b - a) for a, b in sil if a > 0.2 and b < len(x) / sr - 0.2]
    tot = len(x) / sr; c = [len(t) for t in texts]; e1 = tot * c[0] / sum(c); e2 = tot * (c[0] + c[1]) / sum(c)
    best = None
    for i in range(len(mids)):
        for j in range(i + 1, len(mids)):
            s = abs(mids[i][0] - e1) + abs(mids[j][0] - e2) - 0.8 * (mids[i][1] + mids[j][1])
            if best is None or s < best[0]: best = (s, mids[i][0], mids[j][0])
    if not best: return None
    a, b = int(best[1] * sr), int(best[2] * sr)
    y = x[a:b]
    on = np.where(np.abs(y) > 0.01)[0]
    return y[max(0, on[0] - 960): on[-1] + 960] if len(on) else None


PRE = {}
if os.environ.get("BATCH"):   # 先に全部の文の声をまとめて作っておく
    jobs, keys = [], []
    for no in NOS:
        i = no - 1
        ctx = [FIX.get(str(k + 1), L[k]["tts"]) for k in (i - 1, i, i + 1) if 0 <= k < len(L)]
        for k in range(N): jobs.append(ctx); keys.append(no)
    for no, x in zip(keys, tts_batch(jobs)): PRE.setdefault(no, []).append(x)
norm = lambda s: re.sub(r'[、。？！「」…　 ・,.!?\s]', '', s)
for no in NOS:
    i = no - 1; e = L[i]
    ctx = [FIX.get(str(k + 1), L[k]["tts"]) for k in (i - 1, i, i + 1) if 0 <= k < len(L)]
    mid = 1 if i > 0 else 0
    cands = []
    stop = False
    for k in range(N):
        try: x = PRE[no][k] if PRE else tts(ctx)
        except RuntimeError:   # 1 日の回数切れ：それまでの候補から選んで、ここで止める（6本目 v3：良い候補が残らず消えた）
            print("回数切れ。候補 %d 個から選ぶ" % len(cands), flush=True); stop = True; break
        if x is None: continue
        y = pick_middle(x, ctx) if len(ctx) == 3 else (pick_first(x, ctx) if mid == 0 and len(ctx) == 2 else x)
        if y is None: continue
        try: h = heard(y)
        except RuntimeError: print("書き起こし失敗", flush=True); stop = True; break
        sc = difflib.SequenceMatcher(None, norm(e["text"]), norm(h)).ratio()
        if os.environ.get("KANA"):
            try: hk = heard_kana(y)
            except RuntimeError: print("書き起こし失敗", flush=True); stop = True; break
            ok = MUST in hk; h = h + " ／ " + hk
        else:
            ok = (not MUST) or (MUST in h or MUST.replace("まる", "マル") in h)
        cps = len(e["text"]) / (len(y) / 24000)
        cands.append((sc + (0.3 if ok else 0) - 0.05 * abs(cps - 7.0), y, h, sc, cps))
        print(no, e["id"], "候補", k, "一致 %.2f" % sc, "字/秒 %.1f" % cps, h, flush=True)
    if not cands:
        print(no, "作れず")
        if stop: raise SystemExit("回数切れで止めた")
        continue
    best = max(cands, key=lambda c: c[0])
    p = D + "/line_%03d.wav" % no
    if not os.path.exists(p.replace(".wav", "_before_retake.wav")): shutil.copy(p, p.replace(".wav", "_before_retake.wav"))
    open(p, "wb").write(wav_bytes(best[1]))
    V[str(no)]["dur"] = round(len(best[1]) / 24000, 3); V[str(no)]["retake"] = True
    print(no, e["id"], "→ 選んだ：", best[2], "（一致 %.2f）" % best[3], flush=True)
    json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)   # 1 文ごとに残す
    if stop: raise SystemExit("回数切れで止めた（ここまでは保存した）")
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
