# 会話と広告の回の BGM：曲B を基本に、場面に合わせて曲C・曲D に切り替える（2026-11-12 ユーザー「Bをメインに内容に合わせてCDも使って」）
#   B（30 秒の短い曲）：2.6 秒から 25.01 秒（40 拍・96 BPM）を継ぎ目なくくり返す。頭の 2.6 秒は最初の 1 回だけ
#   C（抜き足差し足）：S10〜S12 データの箱・広告の売り場（にぎやかに調べる所）
#   D（ジャズの探偵）：S07〜S08 スマホの中の門・見張り番を試す（はらはらする所）、S17〜S18 新しい容疑者・会社を調べる
#   切り替えは場面の境目で、前の曲を 2.5 秒かけてなめらかに消し（境目の 1 秒あとに消えきる）、次の曲を 2 秒かけて入れる
#   （境目の 1 秒前から）。消えかけと入りかけが 2 秒、大きさの合計が変わらないように重なる。v5「BGM 急に途切れるのやめて、フェードアウトで自然に」(6:36)。
#   前（v4）は 0.8 秒で消して 0.8 秒で入れていて、ぶつっと切れて聞こえた。大きいまま重ねるのは v4「2 つ重なってる？」でだめ。最後は 3 秒で消える
#   曲の大きさは RMS でそろえる（声の下に入れる。声の間はさらに下げるのは組み立ての側）
#   使い方：import bgm_bus; music = bgm_bus.make(END, SCST, sr)   SCST＝場面ごとの始まりの秒（assemble.py と同じ）
#   曲の mp3 は review_page/bgm_b.mp3・bgm_c.mp3・bgm_d.mp3（git には入れない）
import os, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "review_page")
PLAN = [("B", "S00"), ("D", "S07"), ("B", "S09"), ("C", "S10"), ("B", "S13"), ("D", "S17"), ("B", "S19")]
OFFSET = {("D", "S17"): 40.0}           # 2 回目の D は 40 秒目から（1 回目と同じ所を聞かせない）
B_LOOP = (2.6, 25.01)
FOUT, FOUT_POST = 2.5, 1.0      # 前の曲が消える長さ・境目のあと何秒で消えきるか（v5）
FIN, FIN_PRE = 2.0, 1.0          # 次の曲が入る長さ・境目の何秒前から入るか（v5）
RMS = 0.024          # v4「BGM が大きい」（2:39）→ さらに 2 dB 下げた（声より約 17 dB 下。声の間はさらに 6 dB 下げる）


def load(p, sr):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


B_LONG = os.environ.get("BGM_B", "")      # "B1"・"B3"：B の長い版（3 分）を使う（確認ページで選ばれたら）


def b_long(n, sr, first):
    # 長い版：頭の 0〜5 秒は最初の 1 回だけ、5 秒〜(終わり-12 秒) を 2 秒かけて重ねながらくり返す
    x = load(os.path.join(SRC, "bgm_%s.mp3" % B_LONG.lower()), sr)
    a, e, k = int(5 * sr), len(x) - int(12 * sr), int(2 * sr)
    body = x[a:e]; out = x[:e].copy() if first else body.copy()
    while len(out) < n:
        o = out.copy(); o[-k:] = o[-k:] * np.linspace(1, 0, k) + body[:k] * np.linspace(0, 1, k)
        out = np.concatenate([o, body[k:]])
    return out[:n]


def b_stream(n, sr, first):
    if B_LONG: return b_long(n, sr, first)
    x = load(os.path.join(SRC, "bgm_b.mp3"), sr)
    a, L = int(B_LOOP[0] * sr), int(round(B_LOOP[1] * sr))
    # 継ぎ目：ループの終わりの 40ms を、頭の 40ms と重ねる
    k = int(0.04 * sr); loop = x[a:a + L].copy()
    tail = x[a + L:a + L + k]
    loop[:k] = loop[:k] * np.linspace(0, 1, k) + tail * np.linspace(1, 0, k)
    head = x[:a] if first else np.zeros(0, np.float32)
    out = np.concatenate([head] + [loop] * (n // L + 2))
    return out[:n]


def lead_in(x, sr, win=0.25):
    """曲の頭の、ほぼ無音の所の長さ（サンプル）。曲のふつうの大きさの 2 割に届く少し前まで"""
    h = int(win * sr); e = np.sqrt(np.mean(x[:len(x) // h * h].reshape(-1, h) ** 2, 1))
    on = np.nonzero(e > 0.2 * np.median(e))[0]
    return max(0, int(on[0]) * h - int(0.1 * sr)) if len(on) else 0


def make(END, SCST, sr):
    n = int(END * sr)
    music = np.zeros(n, np.float32)
    starts = [SCST[s] for _, s in PLAN] + [END]
    for i, (k, sc) in enumerate(PLAN):
        a = starts[i] - (FIN_PRE if i else 0.0)                                     # 次の曲は境目の少し前から入り始める
        b = min(END, starts[i + 1] + (FOUT_POST if i + 1 < len(PLAN) else 0.0))   # 前の曲は境目の少しあとに消えきる
        m = int((b - a) * sr)
        if k == "B":
            x = b_stream(m, sr, first=(i == 0))
        else:
            src = load(os.path.join(SRC, "bgm_%s.mp3" % k.lower()), sr)
            o = int(OFFSET.get((k, sc), 0.0) * sr)
            o = max(o, lead_in(src, sr))          # v5：曲の頭のほぼ無音（C は 4.7 秒）は飛ばす。前は切り替わりで BGM が途切れて聞こえた (6:36)
            x = src[o:o + m]
            if len(x) < m: raise SystemExit("曲%s が場面 %s に足りない（%.1f 秒）" % (k, sc, (m - len(x)) / sr))
        x = x * (RMS / (np.sqrt(np.mean(x ** 2)) + 1e-9))
        if i:
            f = int(FIN * sr); x[:f] *= np.sin(np.linspace(0, np.pi / 2, f))       # なめらかに入る
        if i + 1 < len(PLAN):
            f = int(FOUT * sr); x[-f:] *= np.cos(np.linspace(0, np.pi / 2, f))     # なめらかに消える
        else:
            g = int(3.0 * sr); x[-g:] *= np.linspace(1, 0, g)
        j = int(a * sr); music[j:j + len(x)] += x[:n - j]
    return music
