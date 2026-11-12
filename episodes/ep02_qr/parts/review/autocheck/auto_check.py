# 動画を見なくてもできる点検（v7 確認用・本番の試しの両方）
#   A 効果音と声の重なり  B 長い間  C 字幕（短すぎ・速すぎ）  D 図の字と字幕の重なり  E 図の字の大きさ
import os, sys, json, wave, re
import numpy as np
V2 = '/home/user/qr_plan/parts/v2'; sys.path.insert(0, V2); sys.path.insert(0, '/home/user/qr_plan/parts/sfx_qr')
OUT = os.path.dirname(os.path.abspath(__file__)); SR = 48000
TAGS = ['op', 'c1', 'c2', 'c3', 'c4', 'c5', 'end']
fmt = lambda t: '%d:%04.1f' % (t // 60, t % 60)
R = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}
def voice_iv(P):
    out = []
    for p in P:
        try:
            with wave.open(p['wav']) as w: d = w.getnframes() / w.getframerate()
        except Exception: d = p['end'] - p['start']
        out.append((p['start'], p['start'] + d / p.get('speed', 1.0), p.get('id', '?'), p.get('text', '')))
    return out
def sfx_events(x, thr=0.03):
    """効果音の鳴っている所（20ms ごとの大きさで切り出す）。[(始め, 終わり, 最大)]"""
    hop = int(0.02 * SR); n = len(x) // hop; e = np.abs(x[:n * hop]).reshape(n, hop).max(1); on = e > thr; ev = []; i = 0
    while i < n:
        if on[i]:
            j = i
            while j < n and (on[j] or (j + 5 < n and on[j:j + 5].any())): j += 1
            ev.append((i * 0.02, j * 0.02, float(e[i:j].max()))); i = j
        else: i += 1
    return ev
for kind, d, idx in ([] if os.environ.get("ONLY_DE") else (('v7', V2 + '/animatic', '/home/user/qr_plan/parts/review/qr_review_v7_index.json'), ('final', V2 + '/final', V2 + '/final/qr_ep02_final_test_index.json'))):
    off = json.load(open(idx))['offsets']; off = dict(off) if isinstance(off, list) else off
    for tag in TAGS:
        P = json.load(open(os.path.join(d, tag + '_P.json'))); iv = voice_iv(P); o = off[tag]
        x = np.load(os.path.join(d, tag + '_sfx.npy'), mmap_mode='r')
        for a, b, pk in sfx_events(np.asarray(x)):
            if pk < 0.08: continue                               # ごく小さい音（足音・目盛りの小さいピッ）は数えない
            hit = [v for v in iv if a < v[1] - 0.05 and b > v[0] + 0.05]
            near = [v for v in iv if not hit and (0 <= v[0] - b < 0.3 or 0 <= a - v[1] < 0.15)]
            if hit or near:
                v = (hit or near)[0]
                R['A'].append(dict(kind=kind, ch=tag, t=round(o + a, 2), at=fmt(o + a), dur=round(b - a, 2), peak=round(pk, 2), how='重なり' if hit else '近すぎ', line=v[2], text=v[3][:30]))
        for (a0, b0, i0, t0), (a1, b1, i1, t1) in zip(iv, iv[1:]):
            g = a1 - b0
            if g > 2.2 and kind == 'v7': R['B'].append(dict(ch=tag, t=round(o + b0, 2), at=fmt(o + b0), gap=round(g, 2), after=i0, before=i1, text=t1[:30]))
# C 字幕：短すぎ（1.0秒未満）・速すぎ（1秒に9文字より多い）
for kind, idx in (('v7', '/home/user/qr_plan/parts/review/qr_review_v7_index.json'),):
    for s in json.load(open(idx))['subs']:
        n = len(re.sub(r'[\s、。！？…「」（）・]', '', s['text'])); du = s['t1'] - s['t0']
        if du < 1.0 or n / max(du, 0.01) > 9.0: R['C'].append(dict(id=s['id'], at=fmt(s['t0']), dur=round(du, 2), cps=round(n / max(du, 0.01), 1), text=s['text']))
# D・E 図の字：本番の組み立て（1080）で、字幕が出ている時刻ごとに図を描き、字の位置と大きさを記録する
import fig_anim as FA
LOG = []
_t = FA.D.text
def text_log(self, xy, t, size, col, a=1.0, anchor='mm'):
    if a > 0.05: LOG.append((xy[0], xy[1], size, t, anchor))
    return _t(self, xy, t, size, col, a, anchor)
FA.D.text = text_log
import final_build as FB
fidx = json.load(open(V2 + '/final/qr_ep02_final_test_index.json')); foff = fidx['offsets']
subs = fidx['subs']; seenE = {}
for tag in TAGS:
    ch = FB.build(tag); segs = FB.fig_segments(ch); o = foff[tag]
    for a, b, name, cue in segs:
        for t in np.arange(a + 0.3, b, 0.5):
            LOG.clear(); FA.FIG[name](t - a, b - a, cue)
            T = o + t; on = [s for s in subs if s['t0'] <= T <= s['t1']]
            lines = max([len(s['text']) // 21 + 1 for s in on] or [0])
            top = 720 - 40 - 64 * min(lines, 2)                       # 字幕の上の端（1280 基準）
            for x, y, size, txt, anc in LOG:
                key = (name, txt, size)
                if key not in seenE: seenE[key] = (name, txt, size, fmt(T))
                bottom = y + (size / 2 if anc[1] == 'm' else size)
                if on and bottom > top and txt.strip():
                    R['D'].append(dict(fig=name, at=fmt(T), text=txt, y=y, size=size, sub=on[0]['text'][:24]))
    for x, y, f in ch.OVER:                                          # 札やメモ（重ねる絵）も、字幕の帯にかからないか
        for t in np.arange(x + 0.3, y, 1.0):
            T = o + t; on = [s for s in subs if s['t0'] <= T <= s['t1']]
            if not on: continue
            im = f(t, x, y); al = np.asarray(im.split()[3])[int(1080 * 0.74):, :]
            if (al > 40).mean() > 0.002: R['D'].append(dict(fig='重ねる札/メモ（%s）' % tag, at=fmt(T), text='（字幕の帯に重なる絵）', y=None, size=None, sub=on[0]['text'][:24])); break
# E：数字・式は字幕（56）以上、ほかの字は 44 以上を目安に
for name, txt, size, at in seenE.values():
    has_num = bool(re.search(r'[0-9０-９×＋=＝→]', txt))
    if (has_num and size < 56) or size < 44: R['E'].append(dict(fig=name, text=txt, size=size, first=at, kind='数字・式' if has_num else '字'))
# D の重複をまとめる
seen = set(); D = []
for r in R['D']:
    k = (r['fig'], r['text'])
    if k in seen: continue
    seen.add(k); D.append(r)
R['D'] = D
json.dump(R, open(os.path.join(OUT, 'auto_check.json'), 'w'), ensure_ascii=False, indent=1)
for k in R: print(k, len(R[k]))
