# まるロボの声を、Gemini の「まとめて頼む方式（Batch API）」で1文ずつ作る（2026-11-25。料金がふつうの半分で、1日の回数の上限にも当たりにくい。恋愛の tools/tts_batch.py と同じ方式）
#   声・指示・型番は make_narration.py と同じ（Achernar・style_gentle.txt・gemini-3.8-flash-tts）。読み直しは tts_text.json（文の番号 → 読ませる文）
#   1文ずつ頼むので、読み違えた文だけを作り直せる（5文まとめて作り直さない）
#   できた声は stage/voice/achernar/line_NNN.wav（前後の無音を 40ms 残して切る）。lines.json に足す（split_narration.py と同じ形）。前の声は old/ に残す
# 使い方:
#   python3 tts_batch_maru.py submit [--only=3,7,12]   … 頼む（全部、または指定の文だけ）。頼んだ番号は batch_jobs.json に残る
#   python3 tts_batch_maru.py poll [--wait]            … 様子を見る。できていれば保存する。--wait は終わるまで1分ごとに見る（裏で動かす）
#   そのあと transcribe.py（gemini-3.5-flash-lite）で照合する
import sys, os, json, time, base64, wave, shutil, urllib.request, urllib.error
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from gemini_log import log
SC = os.environ.get("MARU_WORK", "."); OUT = SC + "/stage/voice/achernar"; os.makedirs(OUT, exist_ok=True)
VOICE, MODEL = "Achernar", "gemini-3.8-flash-tts"
API = "https://generativelanguage.googleapis.com/v1beta/"
JOBS = OUT + "/batch_jobs.json"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(4):                                               # 様子を見る（GET）ときだけ読み直す。頼む（POST）は読み直さない（二重に頼まないため）
        try:
            with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read().decode())
        except (ConnectionError, urllib.error.URLError, TimeoutError) as e:
            if method != "GET" or k == 3: raise
            print("つながりが切れたので30秒待つ", str(e)[:80], flush=True); time.sleep(30)


def find(d, k):
    if isinstance(d, dict):
        if k in d: return d[k]
        for v in d.values():
            r = find(v, k)
            if r is not None: return r
    elif isinstance(d, list):
        for v in d:
            r = find(v, k)
            if r is not None: return r


def submit(only):
    L = json.load(open(SC + "/stage/script/script_v2_timed.json", encoding="utf-8"))
    FIX = json.load(open(OUT + "/tts_text.json", encoding="utf-8")) if os.path.exists(OUT + "/tts_text.json") else {}
    STYLE = open(SC + "/stage/voice_test/style_gentle.txt", encoding="utf-8").read().strip()
    reqs, orig = [], {}
    for e in L:
        if only and e["no"] not in only: continue
        txt = FIX.get(str(e["no"]), e["text"]); orig[str(e["no"])] = e["text"]          # lines.json には元の文（字幕に使う）を残す
        reqs.append({"request": {"contents": [{"parts": [{"text": STYLE + "\n#### TRANSCRIPT\n" + txt}]}],
                                 "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}},
                     "metadata": {"key": str(e["no"])}})
    if not reqs: sys.exit("頼む文がない")
    d = call("POST", "models/%s:batchGenerateContent" % MODEL,
             {"batch": {"display_name": "maru-" + time.strftime("%Y%m%d%H%M%S"), "input_config": {"requests": {"requests": reqs}}}})
    name = d.get("name") or find(d, "name")
    jobs = json.load(open(JOBS)) if os.path.exists(JOBS) else []
    jobs.append({"name": name, "nos": [int(r["metadata"]["key"]) for r in reqs], "texts": orig, "done": False})
    json.dump(jobs, open(JOBS, "w"), ensure_ascii=False, indent=1)
    log(MODEL, "batch_submit", None, batch=name, lines=len(reqs))
    print("頼んだ：", name, len(reqs), "文")


def trim(pcm, sr, thr_db=-42.0, pad=0.04):
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0; n = int(0.01 * sr); m = len(x) // n
    if m == 0: return pcm
    db = 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9); loud = np.where(db >= thr_db)[0]
    if not len(loud): return pcm
    a = max(0, int((loud[0] * 0.01 - pad) * sr)); b = min(len(x), int(((loud[-1] + 1) * 0.01 + pad) * sr))
    return (x[a:b] * 32768.0).clip(-32768, 32767).astype(np.int16).tobytes()


def save(no, text, resp):
    c0 = (resp.get("candidates") or [{}])[0]
    if "content" not in c0: print(no, "声が返らなかった：", c0.get("finishReason")); return
    part = c0["content"]["parts"][0]["inlineData"]; raw = base64.b64decode(part["data"]); mt = part.get("mimeType", "")
    if raw[:4] == b"RIFF":
        import io
        with wave.open(io.BytesIO(raw)) as w: sr = w.getframerate(); raw = w.readframes(w.getnframes())
    else: sr = int(mt.split("rate=")[1].split(";")[0]) if "rate=" in mt else 24000
    y = trim(raw, sr); wp = OUT + "/line_%03d.wav" % no
    if os.path.exists(wp): os.makedirs(OUT + "/old", exist_ok=True); shutil.copy(wp, OUT + "/old/line_%03d_%s.wav" % (no, time.strftime("%Y%m%d%H%M%S")))
    with wave.open(wp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y)
    lp = OUT + "/lines.json"; lines = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
    dur = round(len(y) / 2 / sr, 3); lines[str(no)] = dict(no=no, text=text, dur=dur, batch="batchapi", t0=0.0, t1=dur)
    json.dump(lines, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    log(MODEL, "batch_result", resp, no=no, sec=dur)
    print("保存", no, dur, "秒", flush=True)


def poll(wait):
    jobs = json.load(open(JOBS))
    for j in jobs:
        if j.get("done"): continue
        while True:
            d = call("GET", j["name"]); st = find(d, "state") or ""; print(j["name"], st, flush=True)
            if any(s in st for s in ("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED")) or not wait: break
            time.sleep(60)
        if "SUCCEEDED" not in st:
            if any(s in st for s in ("FAILED", "CANCELLED", "EXPIRED")): j.update(done=True, state=st)
            continue
        items = find(d, "inlinedResponses")
        if isinstance(items, dict): items = items.get("inlinedResponses", [])
        for it in items or []:
            k = (it.get("metadata") or {}).get("key")
            if "error" in it: print(k, "失敗", it["error"]); continue
            save(int(k), j.get("texts", {}).get(k, ""), it.get("response", {}))
        j.update(done=True, state=st); json.dump(jobs, open(JOBS, "w"), ensure_ascii=False, indent=1)
    json.dump(jobs, open(JOBS, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    only = [int(x) for x in next((s.split("=")[1] for s in a if s.startswith("--only=")), "").split(",") if x]
    if a[0] == "submit": submit(only)
    elif a[0] == "poll": poll("--wait" in a)
