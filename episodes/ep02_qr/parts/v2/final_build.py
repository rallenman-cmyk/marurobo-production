# 本番の組み立て（章ごと・1920×1080）：chapters.py の並び（声の ID がきっかけ）をそのまま使い、
#   ・図の静止画 → fig_anim の動く図（同じ図が続く所は1つの動きにつなぐ）
#   ・札・メーター → fig_anim の札・メーター（1080 で描く）
#   ・効果音 → sfx_qr の部品（札が出る・メーターの目盛り・あふれる・たたむ・しずく など）
#   ・3D の所 → PC の描画（pc_render.py：PC_RENDER のフォルダの mp4）。無い所は絵コンテの静止画を拡大（PC=0 で全部静止画）
#   CLEAN=タグ python3 final_build.py TAG → final/TAG_clean.mp4・TAG_sfx.npy・TAG_P.json（通しは through_review.py で FINAL=1）
import os, sys, json, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'sfx_qr'))
import anim2 as A
A.W_, A.H_ = 1920, 1080
import fig_anim as FA, sfx_qr as SX
import chapters as CH
from PIL import Image
W, H, FPS, SR = 1920, 1080, 24, 48000
import pc_render as PCR
PCX = PCR.PC((W, H)) if os.environ.get('PC', '1') != '0' else None
class _Info:
    """章ごとの絵の置き場所（使い回しの元の章）と、絵の最初の区間"""
    def __init__(s): s.c = {}
    def get(s, tag):
        if tag not in s.c:
            cap = {}; orig = A.Chapter
            class Cap(orig):
                def __init__(self, tag_, ids, GAP, IMG, SHOTS, *a, **k): cap['img'] = dict(IMG); orig.__init__(self, tag_, ids, GAP, IMG, SHOTS, *a, **k)
            A.Chapter = Cap
            try: ch = CH.build(tag)
            finally: A.Chapter = orig
            ch.IMG = {}; s.c[tag] = (ch, cap['img'])
        return s.c[tag]
    def home_of(s, tag, k):
        p = s.get(tag)[1].get(k)
        if not p: return None
        rel = os.path.relpath(os.path.dirname(p), CH.P).replace(os.sep, '/')
        return PCR.HOME.get(rel)
    def first_span(s, tag, k):
        for x in s.get(tag)[0].SHOTS:
            if x[2] == k: return x[0], x[1]
        return None, None
    def c1_scan0(s): return s.get('c1')[0].ST['09-03'] - 0.3       # c1_timeline.T_SCAN[0]
INFO = _Info()
STEPS = json.load(open(os.path.join(HERE, 'robot_events.json'))) if os.path.exists(os.path.join(HERE, 'robot_events.json')) else {}
# 札・メーターを 1080 版に（chapters.py の card/meter を差し替えてから組む）
_cards, _meters = [], []
def card(text, size=60, xy=(640, 150), col=None, pad=None):
    f = FA.card(text, size, xy); g = lambda t, a, b: f(t - a, b - a); _cards.append(g); return g
def meter(n):
    f = FA.meter(n); g = lambda t, a, b: f(t - a, b - a); _meters.append((g, n)); return g
CH.card = card; CH.meter = meter
FAMILY = {'c3_alnum': ('c3_alnum', None), 'c3_alnum_hl': ('c3_alnum', 'hl'), 'c4_bits0': ('c4_bits', None), 'c4_bits1': ('c4_bits', 'flip'),
          'D5a': ('c4_summary', None), 'D5b': ('c4_summary', 'row2'), 'D5c': ('c4_summary', 'bar'), 'D5d': ('c4_summary', 'pairs'),
          'c5_logo': ('c5_logo', None), 'c5_logo_drop': ('c5_logo', 'drop'), 'c5_two': ('c5_two', None), 'c5_two_box': ('c5_two', 'box'),
          'c5_balance0': ('c5_balance', None), 'c5_balance1': ('c5_balance', 'tilt'),
          'D1': ('c2_finder', None), 'K25a': ('c2_print', None), 'K25': ('c2_print', 'scan'), 'K26a': ('c2_chart', None), 'K26b': ('c2_chart', 'mark'),
          'c2_mask': ('c2_mask', None), 'c2_mask_fake': ('c2_mask', 'fake'), 'c2_mask_pats': ('c2_mask', 'pats'), 'c2_mask_over': ('c2_mask', 'over')}
SINGLE = ['c1_url', 'c1_bigger', 'c2_nearfar', 'c2_ruler', 'c2_times21', 'c2_three', 'c2_manual', 'c2_shop', 'c3_toc', 'c4_bignum', 'c5_drops', 'c5_thirty', 'end_world']
def fig_segments(ch):
    """SHOTS の図の所を、動く図の区間 [(a, b, 図の名前, cue)] にまとめる"""
    segs = []; cur = None
    for sh in ch.SHOTS:
        a, b, k = sh[:3]
        fam = FAMILY.get(k, (k, None) if k in SINGLE else None)
        if fam is None: cur = None; continue
        name, role = fam
        if cur and cur[2] == name and abs(cur[1] - a) < 1e-6 and role:
            cur[1] = b
            if role == 'hl': cur[3].update(H=a - cur[0], E=a - cur[0] + 0.6, L=a - cur[0] + 1.2, O=a - cur[0] + 1.8)
            elif role == 'bar': cur[3].update(bar=a - cur[0])
            elif role == 'box': cur[3].update(box=a - cur[0], result=a - cur[0] + 1.6)
            else: cur[3][role] = a - cur[0]
        else:
            cue = {}
            if role == 'row2': cue = {'row2': 0.0}
            if role == 'bar': cue = {'row2': 0.0, 'bar': 0.3}
            if role == 'pairs': cue = {'row2': 0.0, 'bar': 0.0, 'pairs': 0.3}
            if role == 'drop': cue = {'logo': -1.0, 'drop': 0.4}
            if role == 'tilt': cue = {'tilt': 0.3}
            if role == 'flip': cue = {'flip': 0.3}
            if name == 'c5_logo' and role is None and segs and any(s[2] == 'c5_logo' for s in segs): cue = {'logo': -1.0}
            cur = [a, b, name, cue]; segs.append(cur)
    return segs
def build(tag):
    _cards.clear(); _meters.clear(); ch = CH.build(tag); segs = fig_segments(ch)
    base_frame = ch.frame
    def frame(t):
        for a, b, name, cue in segs:
            if a <= t < b:
                im = FA.FIG[name](t - a, b - a, cue)
                ov = [(x, y, f) for x, y, f in ch.OVER if x <= t < y]
                for x, y, f in ov: im.alpha_composite(f(t, x, y))
                return im.convert('RGB')
        if PCX:
            sh = next((x for x in ch.SHOTS if x[0] <= t < x[1]), ch.SHOTS[-1])
            a, b, k, z0, z1 = sh[:5]; cx, cy = (sh[5], sh[6]) if len(sh) > 6 else (0.5, 0.5)
            im, reuse = PCX.frame(tag, k, t, a, b, INFO)
            if im is not None:
                if reuse:                                           # 使い回し：絵コンテと同じくゆっくり寄る（止まったコマでも動きが出る）
                    u = min(max((t - a) / max(b - a, 1e-6), 0), 1); im = ch.kb(im, z0 + (z1 - z0) * u, cx, cy)
                ov = [(x, y, f) for x, y, f in ch.OVER if x <= t < y]
                if ov:
                    im = im.convert('RGBA')
                    for x, y, f in ov: im.alpha_composite(f(t, x, y))
                    im = im.convert('RGB')
                return im
        return base_frame(t)
    ch.frame = frame
    # 効果音：札が出る（ポン）・メーター（ピッ／ブブー）・元の効果音
    sfx = []
    for x, y, f in ch.OVER:
        if f in _cards: sfx.append((x + 0.02, SX.chime()))
        for g, n in _meters:
            if f is g:
                for j in range(min(n, 9)): sfx.append((x + 0.4 + 0.18 * j, SX.meter_tick()))
                if n > 8: sfx.append((x + 0.4 + 0.18 * 8 + 0.05, SX.overflow()))
    for a, b, name, cue in segs:
        if name == 'c5_drops': sfx += [(a + 0.3, SX.drop(0.2)), (a + 0.8, SX.drops())]
        if name == 'c4_bits' and 'flip' in cue: sfx.append((a + cue['flip'], SX.drop(0.22)))
        if name == 'c2_mask':
            if 'pats' in cue: sfx.append((a + cue['pats'] + 1.6, SX.chime(0.14, 1046.5)))
            if 'over' in cue: sfx.append((a + cue['over'] + 0.6, SX.beam(1.6)))
        if name == 'c1_url': sfx += [(a + 0.5 + 0.09 * k, SX.meter_tick(0.06)) for k in range(22)]
    for sh in ch.SHOTS:
        if sh[2] == 'F1': sfx.append((sh[0] + 0.1, SX.fold()))
        if sh[2] == 'R_open8': sfx.append((sh[0], SX.lid_open()))
        if sh[2] in ('C6a',): sfx.append((sh[1] - 0.05, SX.drop()))
        if sh[2] == 'B28b': sfx.append((sh[0] + 0.2, SX.gather()))
        if sh[2] == 'B28c': sfx.append((sh[0], SX.assemble()))
    # まるロボの足音（3D と同じ予定の一歩ずつ。robot_events.json）：その描画が映っている所だけ。小さく（声の下でも邪魔にならない）
    if PCX:
        for t, kind, pre in STEPS.get(tag, []):
            if any(a <= t < b for a, b, *_ in segs): continue
            sh = next((x for x in ch.SHOTS if x[0] <= t < x[1]), None)
            if sh is None or PCR.own_prefix(tag, sh[2], t) != pre: continue
            if kind == 'land': sfx.append((t, SX.hop_land(0.07)))
            elif kind != 'takeoff': sfx.append((t, SX.step(0.05 if kind == 'step' else 0.04)))
    ch.SFX = sfx
    return ch
if __name__ == '__main__':
    tag = sys.argv[1]; ch = build(tag); out = os.path.join(HERE, 'final'); os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == 'sheet':
        ts = [ch.T_END * (k + 0.5) / 12 for k in range(12)]; sh = Image.new('RGB', (480 * 4, 270 * 3))
        for k, t in enumerate(ts): sh.paste(ch.frame(t).resize((480, 270)), ((k % 4) * 480, (k // 4) * 270))
        sh.save(A.SP + '/final_sheet_%s.png' % tag); print('sheet', tag)
    else:
        os.environ.setdefault('CLEAN', tag); ch.run(out)
        if PCX: json.dump(PCX.report(), open(os.path.join(out, tag + '_pc.json'), 'w'), ensure_ascii=False, indent=1); print('pc', tag, PCX.report()['used'], 'missing', PCX.report()['missing'])
