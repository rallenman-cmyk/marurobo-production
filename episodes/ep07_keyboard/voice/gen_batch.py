# 声をまとめて頼んで作る（7本目 v8。ふつうの頼み方が「混み合い（429）」で止まるときに使う。6本目 retake_line.py の BATCH と同じ考え）
#   MARU_WORK=<作業> python3 gen_batch.py jobs.json [回数=4]
#   jobs.json：[{"no": 40, "ctx": ["前の文", "この文", "次の文"], "text": "字幕の文", "must": "ひらがなで必ず聞こえてほしい言葉"}, …]
#     ctx は声に読ませる文（かな直し済み）。3 文で読ませて、まん中の文だけを切り出す（1 文だけだと調子が変わる）
#   いちばん台本に近く、must が聞こえる候補を line_NNN.wav に書く（前の声は line_NNN_before_retake.wav に残す）。lines.json の dur も直す
import os, sys, json, wave, base64, urllib.request, difflib, re, shutil, time, io
import numpy as np
_JOBS = json.load(open(sys.argv[1], encoding="utf-8")); _N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
sys.argv = [sys.argv[0], "1"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retake_line.py"), encoding="utf-8").read().split("norm = lambda")[0]
exec(src)


def tts_batch(jobs):
    """jobs：[文のリスト] → 声のリスト（同じ順）。バッチで頼んで、できるまで待つ"""
    reqs = [{"request": {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + "\n".join(lines)}]}],
                         "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Achernar"}}}}},
             "metadata": {"key": "k%03d" % i}} for i, lines in enumerate(jobs)]
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:batchGenerateContent",
                                 data=json.dumps({"batch": {"display_name": "maru-ep07", "input_config": {"requests": {"requests": reqs}}}}).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    name = json.load(urllib.request.urlopen(req, timeout=240))["name"]; print("バッチ", name, len(jobs), "本", flush=True)
    while True:
        time.sleep(20)
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/" + name, headers={"x-goog-api-key": KEY}), timeout=120))
        if r.get("done"): break
    st = r.get("metadata", {}).get("state")
    if st != "BATCH_STATE_SUCCEEDED": raise SystemExit("バッチ失敗 " + str(st))
    out = {}
    for it in r["response"]["inlinedResponses"]["inlinedResponses"]:
        k = it.get("metadata", {}).get("key")
        try: dat = base64.b64decode(it["response"]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception: out[k] = None; continue
        if dat[:4] == b"RIFF":
            with wave.open(io.BytesIO(dat)) as w_: dat = w_.readframes(w_.getnframes())
        out[k] = np.frombuffer(dat, np.int16).astype(np.float32) / 32768
    return [out.get("k%03d" % i) for i in range(len(jobs))]


norm = lambda s: re.sub(r'[、。？！「」…　 ・,.!?\s]', '', s)
flat = [j for j in _JOBS for _ in range(_N)]
xs = tts_batch([j["ctx"] for j in flat])
res = {}
for j, x in zip(flat, xs):
    if x is None: continue
    y = pick_middle(x, j["ctx"])
    if y is None: continue
    hk = heard_kana(y); h = heard(y)
    sc = difflib.SequenceMatcher(None, norm(j["text"]), norm(h)).ratio(); ok = j.get("must", "") in hk
    cps = len(j["text"]) / (len(y) / 24000)
    print(j["no"], "候補 一致 %.2f 字/秒 %.1f %s" % (sc, cps, "○" if ok else "×"), h, "／", hk, flush=True)
    res.setdefault(j["no"], []).append((sc + (1.0 if ok else 0) - 0.05 * abs(cps - 7.0), ok, y, h, hk))
for j in _JOBS:
    c = res.get(j["no"], [])
    good = [x for x in c if x[1]]
    if not good: print(j["no"], "→ must が聞こえる候補なし（書かない）"); continue
    best = max(good, key=lambda x: x[0])
    p = D + "/line_%03d.wav" % j["no"]
    if os.path.exists(p) and not os.path.exists(p.replace(".wav", "_before_retake.wav")): shutil.copy(p, p.replace(".wav", "_before_retake.wav"))
    open(p, "wb").write(wav_bytes(best[2]))
    V.setdefault(str(j["no"]), {"no": j["no"], "text": j["text"]})
    V[str(j["no"])]["dur"] = round(len(best[2]) / 24000, 3); V[str(j["no"])]["retake"] = True
    print(j["no"], "→ 選んだ：", best[3], "／", best[4], flush=True)
json.dump(V, open(D + "/lines.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
