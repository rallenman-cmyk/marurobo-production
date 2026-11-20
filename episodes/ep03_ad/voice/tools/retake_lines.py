# 高すぎる文を、高さを機械で変えずに声を作り直して差し替える（3本目 v11。v10 で高さを下げた文が「声おかしすぎる・スローになってる」と言われたため）
#   python3 retake_lines.py <元の声.wav> <出.wav> <作業フォルダ> 文ID…
#   文ごとに候補を N 本作り（gemini_tts2.py・Achernar・style_gentle_ad.txt）、前後の無音を切って、
#     ①書き起こしが台本と合う ②雑音なし ③高さが全体の中央値＋15Hz 以内 ④長さが元の枠の 0.92〜1.08 倍
#   の候補から、高さが中央値に近く長さが枠に近いものを選ぶ。枠ちょうどに伸び縮み（8% 以内）させ、元の文と同じ大きさにして置く。
#   合う候補がない文は、元の声のまま（高さを機械で変えない）。結果は <作業フォルダ>/result.json
import json, os, re, subprocess, sys, wave, base64, difflib, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(HERE)
SK = os.path.join(V, "..", "..", "..", "skill", "marurobo-video-production", "scripts")
sys.path.insert(0, HERE); from line_pitch import f0_track, measure
src, out, W = sys.argv[1:4]; ids = sys.argv[4:]; N = int(os.environ.get("N", "4"))
os.makedirs(W, exist_ok=True)
WT = json.load(open(os.path.join(V, "word_times.json")))
TTS = {x["id"]: x["tts"] for x in json.load(open(os.path.join(V, "script_v1_0.json")))}
med = float(np.median(list(measure(src, os.path.join(V, "word_times.json")).values())))
with wave.open(src) as w: sr = w.getframerate(); X = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

def rd(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, w.getframerate()
def wr(p, x, r):
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(r); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
def trim(x, r):
    h = r // 100; n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9); on = np.where(db > db.max() - 38)[0]
    return x[max(0, on[0] * h - int(.04 * r)):min(len(x), (on[-1] + 1) * h + int(.04 * r))]
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
norm = lambda s: re.sub(r"[\s、。！？!?…「」・,.ー]", "", s)
def rms(v): v = v[np.abs(v) > 0.01]; return float(np.sqrt((v ** 2).mean())) if len(v) else 1e-3

def cand(k, i):
    d = os.path.join(W, k); os.makedirs(d, exist_ok=True); t = os.path.join(d, "t.txt"); open(t, "w").write(TTS[k])
    raw = os.path.join(d, "c%d.wav" % i)
    for _ in range(0 if os.environ.get("NOGEN") else 5):                # 混んでいて失敗したら、少し待って作り直す（NOGEN=1：作らず、できている候補だけで選ぶ）
        if os.path.exists(raw): break
        subprocess.run([sys.executable, os.path.join(SK, "gemini_tts2.py"), raw, "Achernar", t, os.path.join(V, "style_gentle_ad.txt")], capture_output=True)
        if not os.path.exists(raw): import time; time.sleep(20)
    if not os.path.exists(raw): return None
    x, r = rd(raw); y = trim(x, r); p = os.path.join(d, "c%d_t.wav" % i); wr(p, y, r)
    f = f0_track(y, r); pitch = float(np.median(f)) if len(f) > 10 else 0
    heard = tr(p); sim = difflib.SequenceMatcher(None, norm(WT[k]["text"]), norm(heard)).ratio()
    noise = subprocess.run([sys.executable, os.path.join(SK, "voice_noise.py"), "check", p], capture_output=True, text=True).stdout
    return dict(file=p, pitch=round(pitch), dur=round(len(y) / r, 2), sim=round(sim, 2), heard=heard, noise_ok=("雑音のあるファイル 0" in noise), sr=r)

res = {}
with ThreadPoolExecutor(int(os.environ.get("PAR", "3"))) as ex:
    futs = {(k, i): ex.submit(cand, k, i) for k in ids for i in range(1, N + 1)}
    for (k, i), fu in futs.items(): res.setdefault(k, []).append(fu.result())
Y = X.copy(); report = {}
for k in ids:
    slot = WT[k]["end"] - WT[k]["start"]
    cs = [c for c in res[k] if c and c["sim"] >= 0.85 and c["noise_ok"] and c["pitch"] and c["pitch"] <= med + 15 and 0.92 <= c["dur"] / slot <= 1.08]
    report[k] = dict(slot=round(slot, 2), cands=[{a: c[a] for a in ("pitch", "dur", "sim", "noise_ok", "heard")} for c in res[k] if c])
    if not cs: report[k]["chosen"] = None; continue
    c = min(cs, key=lambda c: abs(c["pitch"] - med) / 10 + abs(c["dur"] / slot - 1) * 20)
    fit = os.path.join(W, k, "fit.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["file"], "-af", "rubberband=tempo=%.5f:pitchq=quality:formant=preserved" % (c["dur"] / slot), "-ar", str(sr), "-ac", "1", fit], check=True)
    z, _ = rd(fit); a = int((WT[k]["start"] - 0.04) * sr); b = int((WT[k]["end"] + 0.04) * sr)
    z = z * rms(X[a:b]) / rms(z); Y[a:b] = 0; Y[a:a + len(z)] = z[:len(Y) - a]
    report[k]["chosen"] = dict(file=c["file"], pitch=c["pitch"], tempo=round(c["dur"] / slot, 3), heard=c["heard"])
wr(out, Y, sr)
json.dump(dict(median=round(med), lines=report), open(os.path.join(W, "result.json"), "w"), ensure_ascii=False, indent=1)
print("中央値 %.0f Hz" % med)
for k, r in report.items(): print(k, "→", ("作り直し %sHz・伸び縮み %.3f" % (r["chosen"]["pitch"], r["chosen"]["tempo"])) if r["chosen"] else "元のまま（合う候補なし：%s）" % [(c["pitch"], c["dur"], c["sim"]) for c in r["cands"]])
