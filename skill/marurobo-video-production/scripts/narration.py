# ナレーションの声を時間軸に置く（2026-11-07、Achernar・やさしく）
#   決まり：各文は台本 v2 の仮の時刻どおりに始める（絵の時刻はそのまま）。声が次の文の始まりにかかるときだけ、
#     ① 前の文との間が空いていれば、少し早く始める（前の声の終わりから 0.15 秒あける）
#     ② それでもかかるときは、少し詰める（速さ 1.08 倍まで。高さは変えない）
#     ③ それでも無理なら、置けない文として知らせる（その文から後の絵の時刻を直す必要がある）
#   作るもの：stage/voice/achernar/placement.json（文ごとの始め・終わり・速さ）、narration_full.wav（本編の全部、48kHz）、
#             stage/script/bluetooth_voice_rev3.srt（声に合わせた字幕）
# 使い方: python3 narration.py   ／ ほかのスクリプトから: import narration; narration.track(t0, t1, sr)
import os, json, wave, subprocess, tempfile
import numpy as np
SC = os.environ.get("MARU_WORK", "."); D = os.environ.get("MARU_VOICE") or SC + "/stage/voice/achernar"   # 作業フォルダ・声の置き場所
GAP_MIN, SPEED_MAX, SR = 0.15, 1.08, 48000
SCRIPT_JSON = os.environ.get("MARU_SCRIPT") or SC + "/stage/script/script_v2_timed.json"      # 台本（文ごとの no・start・end・text、任意で gap_before）
SRT_OUT = os.environ.get("MARU_SRT") or SC + "/stage/script/bluetooth_voice_rev3.srt"          # 声に合わせた字幕の書き出し先
GAP_TOPIC = 0.78                                                     # 話が変わる文の前の間（EP01 で 11 か所「切り替わりが早い」と直された。0.75〜0.8 秒）
TARGET_DB = -20.0                                                    # 声のある所だけの平均の大きさ（dBFS）。文ごとにそろえる


def _load(p, sr=SR):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ac", "1", "-ar", str(sr), tf.name], check=True)
        with wave.open(tf.name) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0


def _speed(p, f, sr=SR):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tf:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", "atempo=%.4f" % f, "-ac", "1", "-ar", str(sr), tf.name], check=True)
        with wave.open(tf.name) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0


def level_db(x, sr=SR):
    n = int(0.02 * sr); m = len(x) // n
    if m == 0: return -90.0
    r = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)); v = r[r > 10 ** (-40 / 20)]
    return float(20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-12)) if len(v) else -90.0


def place():
    L = json.load(open(SCRIPT_JSON, encoding="utf-8"))
    V = json.load(open(D + "/lines.json", encoding="utf-8"))
    out = []; prev_end = -1.0; problems = []
    for i, e in enumerate(L):
        v = V.get(str(e["no"]))
        if v is None: problems.append((e["no"], "声がない")); continue
        nxt = L[i + 1]["start"] if i + 1 < len(L) else e["start"] + v["dur"] + 5
        gap = max(GAP_MIN, float(e.get("gap_before", 0.0)))              # 台本に gap_before（例 0.78：話が変わる文）があれば、前の声からその分あける
        start, dur, sp = max(e["start"], prev_end + gap), v["dur"], 1.0       # 前の文がはみ出していたら、その分だけ遅らせる
        limit = nxt - GAP_MIN
        if start + dur > limit and start <= e["start"] + 1e-6:
            early = max(prev_end + gap, start - 0.6)                      # ① 前の声との間を使って、最大 0.6 秒早く
            start = min(start, max(early, limit - dur))
        if start + dur > limit:
            sp = min(SPEED_MAX, dur / max(limit - start, 0.1))           # ② 少し詰める（1.08 倍まで）
            dur = dur / sp
        if start + dur > limit + 1e-3: problems.append((e["no"], "次の文を %.2f 秒遅らせる" % (start + dur - limit)))   # ③ 次の文へ送る
        out.append(dict(no=e["no"], start=round(start, 3), end=round(start + dur, 3), speed=round(sp, 4), slot=[e["start"], e["end"]], text=e["text"]))
        prev_end = start + dur
    json.dump(out, open(D + "/placement.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return out, problems


def track(t0, t1, sr=SR, P=None):
    """本編の t0〜t1 秒のナレーション（モノラル float32）。文ごとに大きさをそろえる"""
    P = P or json.load(open(D + "/placement.json", encoding="utf-8"))
    y = np.zeros(int(round((t1 - t0) * sr)), np.float32)
    for p in P:
        if p["end"] <= t0 or p["start"] >= t1: continue
        wp = p.get("wav") or D + "/line_%03d.wav" % p["no"]                          # 差し替えた声（例：第4章 6:24 の②）は "wav" で指す
        x = _speed(wp, p["speed"], sr) if abs(p["speed"] - 1.0) > 1e-3 else _load(wp, sr)
        x = x * (10 ** ((TARGET_DB - level_db(x, sr)) / 20))
        i0 = int(round((p["start"] - t0) * sr))
        a = max(0, -i0); b = min(len(x), len(y) - i0)
        if b > a: y[i0 + a:i0 + b] += x[a:b]
    return y


def voiced(t0, t1, sr=SR, P=None):
    """声が鳴っている所（音楽・効果音を下げる「ダッキング」用）：0〜1 のなめらかな包絡（上がり 0.12 秒・下がり 0.35 秒）。100Hz で計算して引き伸ばす"""
    P = P or json.load(open(D + "/placement.json", encoding="utf-8"))
    fr = 100; n = int(round((t1 - t0) * fr)) + 1; g = np.zeros(n, np.float32)
    for p in P:
        a = int(round((p["start"] - 0.12 - t0) * fr)); b = int(round((p["end"] + 0.10 - t0) * fr))
        g[max(0, a):max(0, min(n, b))] = 1.0
    env = np.zeros_like(g); v = 0.0; ku, kd = 0.12 * fr, 0.35 * fr
    for i in range(n):                                               # 一次の追従（上がりは速く、下がりはゆっくり）
        tgt = g[i]; v += (tgt - v) / (ku if tgt > v else kd); env[i] = v
    m = int(round((t1 - t0) * sr))
    return np.interp(np.arange(m) / sr, np.arange(n) / fr, env).astype(np.float32)


def report_gaps(P, thr=0.5):
    """文と文の間が thr 秒より短い所の一覧（話が変わる文なら 0.75〜0.8 秒にする。同じ話の続きなら短くてよい）"""
    out = []
    for a, b in zip(P, P[1:]):
        g = b["start"] - a["end"]
        if g < thr: out.append((b["no"], round(g, 2), b["text"][:24]))
    return out


def srt(P, path):
    def ts(x):
        x = max(0.0, x); h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; ms = int(round((s - int(s)) * 1000))
        if ms == 1000: ms = 999
        return "%02d:%02d:%02d,%03d" % (h, m, int(s), ms)
    lines = []
    for k, p in enumerate(P):
        nxt = P[k + 1]["start"] if k + 1 < len(P) else p["end"] + 1.0
        end = min(max(p["end"] + 0.35, p["start"] + 1.0), nxt - 0.05)        # 字幕は声の終わりの少しあとまで（次の字幕の前まで）
        lines.append("%d\n%s --> %s\n%s\n" % (k + 1, ts(p["start"]), ts(end), p["text"]))
    open(path, "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    P, problems = place()
    sped = [p for p in P if p["speed"] > 1.0001]; moved = [p for p in P if abs(p["start"] - p["slot"][0]) > 1e-3]
    print("placed", len(P), "| 詰めた文", len(sped), [(p["no"], p["speed"]) for p in sped], "| 早めた文", len(moved), [(p["no"], round(p["start"] - p["slot"][0], 2)) for p in moved])
    print("置けない文", problems)
    srt(P, SRT_OUT)
    if "--gaps" in __import__("sys").argv:                              # 声の前の間が短い文（話が変わる所なら gap_before を台本に書いて置き直す）
        for no, g, t in report_gaps(P): print("  gap %.2fs before %s  %s" % (g, no, t))
    if "--full" in __import__("sys").argv:
        y = track(0.0, P[-1]["end"] + 1.0)
        with wave.open(D + "/narration_full.wav", "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
        print("WROTE narration_full.wav %.1fs" % (len(y) / SR))


def mix_voice(bus, t0, sr=SR, bus_peak=0.45, duck_db=4.0, P=None):
    """効果音・音楽（bus：モノラル (n,) か ステレオ (n,2)）に声を足す。bus は山を bus_peak にそろえ、声の間は duck_db だけ下げる。
    t0：bus の頭が本編の何秒か。最後に山が 0.97 を超えないようにする"""
    n = len(bus); t1 = t0 + n / sr
    b = bus * (bus_peak / max(float(np.abs(bus).max()), 1e-9))
    env = voiced(t0, t1, sr, P)[:n]; g = 1.0 - (1.0 - 10 ** (-duck_db / 20.0)) * env
    v = track(t0, t1, sr, P)[:n]                                               # P：声の置き場所（省くと placement.json）
    out = b * (g[:, None] if b.ndim == 2 else g) + (v[:, None] if b.ndim == 2 else v)
    pk = float(np.abs(out).max())
    return out * (0.97 / pk) if pk > 0.97 else out
