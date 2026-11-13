# 確認用動画（台本 v2.0）の章を組む共通の仕組み。章ごとの設定（chN.py）から呼ぶ
#   ・声は台本の ID で並べる（line_wav で前の声の使い回し／新しい声）
#   ・文と文の間は GAP（ID → 秒）。決めていない所は：場面が変わる 1.2／話が変わる（前の文が「？」で終わる・次が「では」「ところが」で始まる）0.8／続き 0.45
#   ・絵は SHOTS：(きっかけ, 絵の名前, 寄り始め, 寄り終わり[, 寄る中心x, y])。きっかけ＝('ID', 's'|'e', 秒のずれ)。次のきっかけまで続く
#   ・寄る動きは 1 ピクセルより細かく（整数で切り出すと左右に揺れて見える）
#   ・OVER：(きっかけ, きっかけ, 関数(t, t0, t1) → RGBA 1280×720)。図や大きな文字を重ねる
#   ・CLEAN=タグ で、通し用の「絵だけ」＋効果音＋声の置き場所を書き出す
import os, sys, json, subprocess, wave, re
import numpy as np
from PIL import Image
W_, H_, FPS, SR = 1280, 720, 24, 48000
SP = '/tmp/claude-0/-home-user/8cc26183-437c-5f90-a7e9-3b23d7f91ab2/scratchpad'
VOICE = json.load(open(SP + '/v2_voice_map.json', encoding='utf-8'))     # ID → {text, wav, dur}
def wav_dur(p):
    with wave.open(p) as w: return w.getnframes() / w.getframerate()
_LP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_lock.json')
LOCK = json.load(open(_LP, encoding='utf-8'))['lock'] if os.path.exists(_LP) else {}
def timeline(ids, GAP, scene_of, lead=0.8, tail=2.0):
    ST, EN = {}, {}; t = lead; prev = None
    for i in ids:
        v = VOICE[i]
        if prev is not None:
            g = GAP.get(i)
            if g is None:
                pt, nt = VOICE[prev]['text'], v['text']
                if scene_of(i) != scene_of(prev): g = 1.2
                elif pt.endswith('？') or nt.startswith(('では', 'ところが', 'それでは', 'まず', '次に', 'そして今', 'ここで')): g = 0.8
                else: g = 0.45
            t = EN[prev] + g
            if i in LOCK and LOCK[i] >= EN[prev] + 0.25: t = LOCK[i]      # 作り直した声の次の文は前と同じ時刻（voice_lock.json）
        ST[i] = t; EN[i] = t + v['dur']; prev = i
    return ST, EN, EN[ids[-1]] + tail
_YM = None
def _ylen(t):
    global _YM
    if _YM is None:
        import importlib.util
        sp = importlib.util.spec_from_file_location('yomi_qr', '/home/user/qr_plan/parts/voice_v2/yomi.py'); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); _YM = m.yomi
    return sum(1 for ch in _YM(t) if ch not in '、。？！…「」（）・ 　')
def _segments(wav, gap=0.12):
    import numpy as np
    with wave.open(wav) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    h = int(sr * 0.01); n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12)); on = db > db.max() - 38
    segs = []; j = 0
    while j < n:
        if on[j]:
            q = j
            while q < n and on[q]: q += 1
            if segs and j * 0.01 - segs[-1][1] < gap: segs[-1] = (segs[-1][0], q * 0.01)
            else: segs.append((j * 0.01, q * 0.01))
            j = q
        else: j += 1
    return [g for g in segs if g[1] - g[0] >= 0.05]
_WT = {}
def word_time(i, frag):
    """文 i の声の中で、言葉 frag を言い始める時刻（声の頭からの秒）。
    文を読点・句点のまとまりに分け、声の出ている区間（0.12 秒以上の間で区切る）に順に当てはめる（読みの長さと区間の長さが合うように）。QR回 v11"""
    import re, math
    v = VOICE[i]; t = v['text']; k = t.find(frag)
    if k < 0: raise KeyError('%s に「%s」がない' % (i, frag))
    if i not in _WT:
        cut = [0] + [m.end() for m in re.finditer(r'[、。？！]+|……', t)] + [len(t)]
        ch = []
        for a, b in zip(cut, cut[1:]):
            if b > a and _ylen(t[a:b]) > 0: ch.append((a, b))
            elif ch and b > a: ch[-1] = (ch[-1][0], b)
        segs = _segments(v['wav']); L = [max(1, _ylen(t[a:b])) for a, b in ch]
        rate = sum(g1 - g0 for g0, g1 in segs) / sum(L); nC, nS = len(ch), len(segs); INF = 1e18
        if nS < nC:
            _WT[i] = None
        else:
            D = [[INF] * (nS + 1) for _ in range(nC + 1)]; B = [[None] * (nS + 1) for _ in range(nC + 1)]; D[0][0] = 0
            for c in range(1, nC + 1):
                for sj in range(c, nS - (nC - c) + 1):
                    for sp in range(c - 1, sj):
                        if D[c - 1][sp] >= INF: continue
                        dur = segs[sj - 1][1] - segs[sp][0]; cost = D[c - 1][sp] + math.log(max(dur, 0.05) / (L[c - 1] * rate)) ** 2
                        if cost < D[c][sj]: D[c][sj] = cost; B[c][sj] = sp
            asg = []; sj = nS
            for c in range(nC, 0, -1): sp = B[c][sj]; asg.append((segs[sp][0], segs[sj - 1][1])); sj = sp
            _WT[i] = (ch, asg[::-1])
    if _WT[i] is None: return v['dur'] * _ylen(t[:k]) / max(1, _ylen(t))
    ch, asg = _WT[i]
    for (a, b), (g0, g1) in zip(ch, asg):
        if a <= k < b: return g0 + (g1 - g0) * _ylen(t[a:k]) / max(1, _ylen(t[a:b]))
    return asg[-1][0]
class Chapter:
    def __init__(s, tag, ids, GAP, IMG, SHOTS, OVER=(), SFX=(), scene_of=lambda i: i.split('-')[0], lead=0.8, tail=2.0):
        s.tag, s.ids = tag, ids
        s.ST, s.EN, s.T_END = timeline(ids, GAP, scene_of, lead, tail)
        s.IMG = {k: Image.open(p).convert('RGB').resize((W_, H_), Image.LANCZOS) for k, p in IMG.items()}
        def cue(c):
            if isinstance(c, (int, float)): return float(c)
            i, se, off = c
            if se == 'w': frag, o2 = off if isinstance(off, tuple) else (off, 0.0); return s.ST[i] + word_time(i, frag) + o2      # w(ID, 言葉, ずらし)
            return (s.ST if se == 's' else s.EN)[i] + off
        s.cue = cue
        sh = sorted([(cue(x[0]),) + tuple(x[1:]) for x in SHOTS], key=lambda x: x[0])
        s.SHOTS = [(a, (sh[k + 1][0] if k + 1 < len(sh) else s.T_END)) + tuple(x[1:]) for k, x in enumerate(sh) for a in [x[0]]]
        s.OVER = [(cue(a), cue(b), f) for a, b, f in OVER]
        for _a, _b, _f in s.OVER:
            if hasattr(_f, 'bind'): _f.bind(cue)          # 声の中の言葉の時刻（w()）を、重ね絵に渡す
        s.SFX = [(cue(c), x) for c, x in SFX]
    def kb(s, im, z, cx=0.5, cy=0.5):
        w, h = W_ / z, H_ / z; x = min(max(cx * W_ - w / 2, 0), W_ - w); y = min(max(cy * H_ - h / 2, 0), H_ - h)
        return im.transform((W_, H_), Image.AFFINE, (w / W_, 0, x, 0, h / H_, y), resample=Image.BICUBIC)
    def frame(s, t):
        sh = s.SHOTS[0]
        for x in s.SHOTS:
            if x[0] <= t < x[1]: sh = x; break
        a, b, k, z0, z1 = sh[:5]; cx, cy = (sh[5], sh[6]) if len(sh) > 6 else (0.5, 0.5)
        u = (t - a) / max(b - a, 1e-6); u = min(max(u, 0), 1)
        im = s.kb(s.IMG[k], z0 + (z1 - z0) * u, cx, cy)
        ov = [(a, b, f) for a, b, f in s.OVER if a <= t < b]
        if ov:
            im = im.convert('RGBA')
            for a, b, f in ov: im.alpha_composite(f(t, a, b))
            im = im.convert('RGB')
        return im
    def P(s):
        return [dict(no=k + 1, id=i, start=round(s.ST[i], 3), end=round(s.EN[i], 3), speed=1.0, slot=[s.ST[i], s.EN[i]], text=VOICE[i]['text'], wav=VOICE[i]['wav']) for k, i in enumerate(s.ids)]
    def run(s, outdir):
        os.makedirs(outdir, exist_ok=True); tag = os.environ.get('CLEAN', s.tag)
        n = int(s.T_END * SR); sfx = np.zeros(n, np.float32)
        for t, x in s.SFX:
            i = int(t * SR); m = min(len(x), n - i)
            if m > 0: sfx[i:i + m] += x[:m]
        np.save(os.path.join(outdir, tag + '_sfx.npy'), sfx)
        json.dump(s.P(), open(os.path.join(outdir, tag + '_P.json'), 'w'), ensure_ascii=False)
        NF = int(round(s.T_END * FPS))
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', os.path.join(outdir, tag + '_clean.mp4')], stdin=subprocess.PIPE)
        for i in range(NF): ff.stdin.write(s.frame(i / FPS).tobytes())
        ff.stdin.close(); ff.wait(); print('clean', tag, NF, round(s.T_END, 2))
    def sheet(s, path, n=16):
        ts = [s.T_END * (k + 0.5) / n for k in range(n)]; sh = Image.new('RGB', (320 * 4, 180 * ((n + 3) // 4)))
        for k, t in enumerate(ts): sh.paste(s.frame(t).resize((320, 180)), ((k % 4) * 320, (k // 4) * 180))
        sh.save(path)
# ---- 図の部品（2D）
from PIL import ImageDraw, ImageFont
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
_F = {}
def F(n):
    if n not in _F: _F[n] = ImageFont.truetype(FB, n)
    return _F[n]
INK = (40, 46, 52); BLUE = (63, 134, 221); ORANGE = (240, 149, 58); RED = (217, 71, 90); TEAL = (20, 163, 180); GRAY = (150, 158, 166); WHITE = (255, 255, 255)
def ease(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def panel(items, box=(80, 40, 1200, 300), fade=0.3):
    """items：[(出る秒（区間の頭から）, 関数(draw, alpha))]。上の白い板に順に描く"""
    def f(t, a, b):
        im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); al = min(1.0, (t - a) / fade, (b - t) / fade)
        if al <= 0: return im
        d = ImageDraw.Draw(im); d.rounded_rectangle(box, 22, fill=(250, 250, 248, int(238 * al)))
        for t0, g in items:
            u = ease((t - a - t0) / 0.3)
            if u > 0: g(d, al * u)
        return im
    return f
def big(text, xy=(640, 170), size=72, col=INK, box=None):
    """大きな文字1つ（字幕より大きく）。box を渡すと白い板つき"""
    def g(d, al):
        if box: d.rounded_rectangle(box, 22, fill=(250, 250, 248, int(238 * al)))
        d.text(xy, text, font=F(size), fill=(*col, int(255 * al)), anchor='mm')
    return g
def label(text, xy, size=56, col=INK):
    return lambda d, al: d.text(xy, text, font=F(size), fill=(*col, int(255 * al)), anchor='mm')
def card(text, xy=(640, 150), size=60, col=INK, pad=28):
    """白い札に大きな文字（それだけで出す）"""
    def f(t, a, b):
        im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); al = min(1.0, (t - a) / 0.3, (b - t) / 0.3)
        if al <= 0: return im
        d = ImageDraw.Draw(im); x0, y0, x1, y1 = d.textbbox(xy, text, font=F(size), anchor='mm')
        d.rounded_rectangle((x0 - pad, y0 - pad * 0.7, x1 + pad, y1 + pad * 0.7), 20, fill=(250, 250, 248, int(240 * al)))
        d.text(xy, text, font=F(size), fill=(*col, int(255 * al)), anchor='mm'); return im
    return f
