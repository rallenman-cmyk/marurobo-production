# PC で描いた 3D（Blender の mp4）を、本番の組み立て（final_build.py）の 3D の所に差し込む
#   ・ドライブの marurobo_render から落とした章のフォルダ（qrop4・qrc1〜qrc5）を PC_RENDER（既定 /home/user/qr_plan/pc_render）に置く
#   ・ファイル名は「頭の名前 + 始めのコマ-終わりのコマ.mp4」（例 qrc5w_0327-0426.mp4）。コマは 1 から、t 秒 → int(round(t*24)) + 1
#   ・章ごとの決まり：どの絵（SHOTS の名前）を、どの頭の名前の描画で出すか。よその章の絵（使い回し）は、その章の同じ絵の頭から流し、足りなければ最後のコマで止める
#   ・図・札・字幕は今までどおり上に重ねる。描画が無い所は今までどおり絵コンテの静止画（足りない所は missing に記録）
import os, re, glob, subprocess, json
import numpy as np
from PIL import Image
FPS = 24
ROOT = os.environ.get('PC_RENDER', '/home/user/qr_plan/pc_render')
def fr_of(t): return int(round(t * FPS)) + 1
# ---------------------------------------------------------------- 絵の名前 → 描画の頭の名前（自分の章で描いたもの）
C2_DESK = {'K41', 'K42', 'K43'}
def c4_stage(k): return 'crates' if k[0] in 'CR' else ('factory' if k[0] == 'F' else ('reuse' if k[0] == 'T' else 'world'))
def own_prefix(tag, k, t):
    if tag == 'op': return None if k == 'poster' else 'qrop4_'          # 題（title）も 3D の上に重ねる（v11 #2）
    if tag == 'c1':
        if k == 'R_scan': return 'qrc1s2_'
        return 'qrc1t2_' if fr_of(t) <= 252 else 'qrc1w5_'
    if tag == 'c2': return 'qrc2t_' if k in C2_DESK else 'qrc2w_'
    if tag == 'c3': return 'qrc3w_'
    if tag == 'c4': return {'crates': 'qrc4c_', 'factory': 'qrc4f_', 'world': 'qrc4w_'}.get(c4_stage(k))
    if tag == 'c5': return 'qrc5w_' if k in ('W29', 'W30', 'W28', 'W31', 'W31b') else None
    return None
# よその章の絵（使い回し）：絵コンテの置き場所（chapters.py の IMG）で決まる
HOME = {'opening/sb2': 'op', 'ch1/sb': 'c1', 'ch2/sb': 'c2', 'ch3/sb': 'c3', 'ch4/sb': 'c4', 'c5/sb': 'c5'}
ALIAS = {('c4', 'T35'): ('op', 'S07_sh_step'), ('c4', 'T28'): ('op', 'S05_sh_hello'), ('c5', 'W30b'): ('c5', 'W30')}   # W30b：5章の終わりで「さきほどのインク」を 3D で      # 絵コンテが冒頭の絵と同じもの
# ---------------------------------------------------------------- 描画のファイル
class Src:
    """頭の名前ごとの mp4 のかたまり（コマの範囲 → ファイル）。読むのは ffmpeg で順に（飛んだら開き直す）"""
    def __init__(s, folder, prefix):
        s.chunks = []
        for p in glob.glob(os.path.join(folder, prefix + '*.mp4')):
            m = re.match(re.escape(prefix) + r'(\d+)-(\d+)\.mp4$', os.path.basename(p))
            if m: s.chunks.append((int(m.group(1)), int(m.group(2)), p))
        s.chunks.sort(); s.cur = None
    def has(s, f): return any(a <= f <= b for a, b, _ in s.chunks)
    def get(s, f, size):
        ch = next(((a, b, p) for a, b, p in s.chunks if a <= f <= b), None)
        if ch is None: return None
        a, b, p = ch
        if s.cur and s.cur['p'] == p and s.cur['next'] == f + 1 and s.cur['last'] is not None:      # 同じコマをもう一度（つなぎの重ね用）
            return Image.frombuffer('RGB', size, s.cur['last'], 'raw', 'RGB', 0, 1).copy()
        if s.cur is None or s.cur['p'] != p or s.cur['next'] > f or f - s.cur['next'] > 48:
            if s.cur: s.cur['proc'].kill()
            ss = (f - a) / FPS
            proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', '%.4f' % ss, '-i', p, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % size, '-'],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            s.cur = dict(p=p, proc=proc, next=f, last=None)
        n = size[0] * size[1] * 3
        while s.cur['next'] <= f:
            buf = s.cur['proc'].stdout.read(n)
            if len(buf) < n: break                     # ファイルの終わり（最後のコマを使う）
            s.cur['last'] = buf; s.cur['next'] += 1
        if s.cur['last'] is None: return None
        return Image.frombuffer('RGB', size, s.cur['last'], 'raw', 'RGB', 0, 1).copy()
class PC:
    def __init__(s, size=(1920, 1080)):
        s.size = size; s.srcs = {}; s.missing = {}; s.used = {}
        s.folders = {'qrop4_': 'qrop4', 'qrc1t2_': 'qrc1', 'qrc1w5_': 'qrc1', 'qrc1s2_': 'qrc1', 'qrc2w_': 'qrc2', 'qrc2t_': 'qrc2', 'qrc3w_': 'qrc3',
                     'qrc4c_': 'qrc4', 'qrc4f_': 'qrc4', 'qrc4w_': 'qrc4', 'qrc5w_': 'qrc5'}
    def src(s, prefix):
        if prefix not in s.srcs: s.srcs[prefix] = Src(os.path.join(ROOT, s.folders[prefix]), prefix)
        return s.srcs[prefix]
    def available(s):
        return {p: len(s.src(p).chunks) for p in s.folders}
    def frame(s, tag, k, t, a, b, chapters):
        """章 tag の t 秒（絵 k、区間 a〜b）の 3D の絵。無ければ None。使い回しなら (絵, True)"""
        reuse = False; src_tag, src_k, tt = tag, k, t
        home = chapters.home_of(tag, k)
        if (tag, k) in ALIAS: src_tag, src_k = ALIAS[(tag, k)]
        elif home and home != tag and not (tag == 'c1' and k == 'S10_low'): src_tag, src_k = home, k
        if src_tag != tag:
            reuse = True; sa, sb = chapters.first_span(src_tag, src_k)
            if sa is None: return None, reuse
            tt = min(sa + (t - a), sb - 1.0 / FPS)
        pre = own_prefix(src_tag, src_k, tt)
        if pre is None: return None, reuse
        f = fr_of(tt)
        if pre == 'qrc1s2_': f = fr_of(tt - chapters.c1_scan0())
        sr = s.src(pre); f = next((g for g in (f, f - 1, f + 1, f - 2, f + 2) if sr.has(g)), f)   # 区切りの端の 1〜2 コマは隣で
        im = sr.get(f, s.size) if sr.has(f) else None
        key = (tag, k, pre); s.last = (pre, f)
        if im is None: s.missing.setdefault(key, 0); s.missing[key] += 1
        else: s.used.setdefault(key, 0); s.used[key] += 1
        return im, reuse
    def report(s):
        return dict(root=ROOT, available=s.available(), used={'%s %s %s' % k: v for k, v in s.used.items()},
                    missing={'%s %s %s' % k: v for k, v in s.missing.items()})
