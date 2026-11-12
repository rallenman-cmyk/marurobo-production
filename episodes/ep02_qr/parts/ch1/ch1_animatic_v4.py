# 1章（中に入る）の確認用動画：絵コンテを声に合わせて並べる。1280×720・24fps
import os, sys, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
import narration as NA, overlay2d as O2, subs_jp as SJ
W_, H_, FPS = 1280, 720, 24
OUT = os.path.join(HERE, 'animatic'); os.makedirs(OUT, exist_ok=True)
V = json.load(open(WORK + '/stage/voice/achernar/lines.json')); L = json.load(open(WORK + '/stage/script/script_v2_timed.json'))
# 文ごとの「前の声からの間」（話が変わる所は0.8秒、続きは0.45秒、動きを見せる所は長め）。台本 v0.9 の1章 28文
GAP = {2: ('dive', 4.3), 3: 0.8, 4: 0.8, 5: 0.8, 6: 0.8, 7: 0.8, 8: 0.6, 9: 0.45, 10: 3.0, 11: 0.8, 12: 0.8, 13: 0.45, 14: 0.6, 15: 0.8, 16: 0.5,
       17: 0.8, 18: 0.45, 19: 0.8, 20: 0.5, 21: 0.8, 22: 0.45, 23: 1.8, 24: 0.8, 25: 0.8, 26: 0.6, 27: 0.45, 28: 0.8}
d = lambda no: V[str(no)]['dur']
START = [0.6]
for no in range(2, len(L) + 1):
    g = GAP[no]; pe = START[-1] + d(no - 1)
    START.append(pe + 0.15 + g[1] if isinstance(g, tuple) else pe + g)
ST = {no: s for no, s in zip(range(1, len(L) + 1), START)}
T_END = ST[28] + d(28) + 2.8
T_IN = ST[1] + d(1) + 0.15                                            # 言い終えてから飛び込む
T_FOLD = ST[9] + d(9) + 0.1
P = []
for e, s in zip(L, START):
    du = V[str(e['no'])]['dur']; P.append(dict(no=e['no'], start=s, end=round(s + du, 3), speed=1.0, slot=[s, s + du], text=e['text']))
json.dump(P, open(WORK + '/stage/voice/achernar/placement.json', 'w'), ensure_ascii=False, indent=0)
print('gaps<0.4', NA.report_gaps(P, 0.4))
SRT = OUT + '/ch1.srt'; NA.srt(P, SRT)
OPEN = '/home/user/qr_plan/parts/opening/sb2/S02_sh_hello.png'
SHOTS = [(0.0, T_IN, 'OPN', 1.00, 1.04), (T_IN, T_IN + 0.9, 'D1', 1.00, 1.03), (T_IN + 0.9, T_IN + 1.6, 'D2', 1.03, 1.08), (T_IN + 1.6, T_IN + 2.8, 'ZOOM', 1, 1),
         (T_IN + 2.8, T_IN + 3.6, 'K02a', 1.00, 1.03), (T_IN + 3.6, ST[3], 'K02', 1.00, 1.05),
         (ST[3], ST[3] + 0.15, 'K03', 1.00, 1.00), (ST[3] + 0.15, ST[3] + 2.2, 'K03v', 1.00, 1.01), (ST[3] + 2.2, ST[3] + 4.7, 'K03h', 1.01, 1.02), (ST[3] + 4.7, ST[5] + 2.0, 'K03', 1.02, 1.08),
         (ST[5] + 2.0, ST[5] + 3.4, 'K04b', 1.00, 1.03), (ST[5] + 3.4, ST[6], 'K04', 1.08, 1.10),
         (ST[6], ST[7], 'K05', 1.00, 1.04), (ST[7], T_FOLD, 'K05b', 1.00, 1.05), (T_FOLD, T_FOLD + 0.7, 'F1', 1.00, 1.01), (T_FOLD + 0.7, T_FOLD + 1.4, 'F2', 1.01, 1.02), (T_FOLD + 1.4, T_FOLD + 2.1, 'F3', 1.02, 1.03), (T_FOLD + 2.1, ST[10], 'F4', 1.03, 1.04), (ST[10], ST[11], 'K07', 1.00, 1.03), (ST[11], ST[12], 'K06', 1.04, 1.06),
         (ST[12], ST[15], 'K08', 1.00, 1.06), (ST[15], ST[15] + 2.6, 'K09a', 1.00, 1.04), (ST[15] + 2.6, ST[16], 'K09', 1.00, 1.05), (ST[16], ST[18], 'K10', 1.00, 1.04), (ST[18], ST[19], 'URL', 1.00, 1.02),
         (ST[19], ST[21], 'K11', 1.00, 1.06), (ST[21], ST[23] - 1.6, 'K09', 1.05, 1.08), (ST[23] - 1.6, ST[24] + 2.0, 'K12', 1.00, 1.05), (ST[24] + 2.0, ST[25], 'K13', 1.00, 1.06),
         (ST[25], ST[28] + d(28) + 0.4, 'K14', 1.00, 1.10), (ST[28] + d(28) + 0.4, ST[28] + d(28) + 1.4, 'K15', 1.00, 1.02), (ST[28] + d(28) + 1.4, T_END, 'K16', 1.02, 1.04)]
IMG = {k: Image.open(os.path.join(HERE, 'sb', k + '.png')).convert('RGB').resize((W_, H_), Image.LANCZOS) for _, _, k, _, _ in SHOTS if k not in ('ZOOM', 'OPN')}
OPN = Image.open(OPEN).convert('RGB').resize((W_, H_), Image.LANCZOS)
def kb(im, z, cx=0.5, cy=0.5):
    w, h = int(W_ / z), int(H_ / z); x = int(min(max(cx * W_ - w / 2, 0), W_ - w)); y = int(min(max(cy * H_ - h / 2, 0), H_ - h))
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def frame(t):
    for a, b, k, z0, z1 in SHOTS:
        if a <= t < b: break
    if k == 'OPN': return kb(OPN, z0 + (z1 - z0) * (t - a) / (b - a))
    if k == 'ZOOM':                                            # 画面の中へ（画面のQRに寄っていく）
        u = (t - a) / (b - a); return kb(IMG['D2'], 1.08 + 6.0 * u ** 2.0, 0.615, 0.27)
    im = kb(IMG[k], z0 + (z1 - z0) * (t - a) / (b - a))
    
    return im
SR = 48000; n = int(T_END * SR)
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32)[:n] / 32768; music = np.pad(music, (0, n - len(music)))
music *= 0.06 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))
sfx = np.zeros(n, np.float32)
for tt, a in ((T_IN + 0.85, 0.2), (T_IN + 3.6, 0.35), (T_FOLD + 0.15, 0.25), (T_FOLD + 1.2, 0.12), (T_FOLD + 1.6, 0.12), (T_FOLD + 2.0, 0.15), (ST[10] + 0.3, 0.2), (ST[23] - 1.4, 0.15)):                    # 着地・箱を載せる・ふたが開く
    x = O2.thump(a, dur=0.09, f=120.0, click=0.3); i = int(tt * SR); sfx[i:i + len(x)] += x
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.38, duck_db=6)
with wave.open(OUT + '/ch1_audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt) for a, c, txt in SJ.expand(O2.srt_lines(SRT))]
ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(0), O2.ts(T_END), '確認用 v4：1章　仮のまるロボの静止画（本番はPCの3D）'))
open(OUT + '/ch1.ass', 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
NF = int(round(T_END * FPS))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-i', OUT + '/ch1_audio.wav',
                       '-vf', 'ass=%s:fontsdir=/usr/share/fonts/opentype/noto' % (OUT + '/ch1.ass'), '-c:v', 'libx264', '-crf', '24', '-pix_fmt', 'yuv420p',
                       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-shortest', OUT + '/qr_ch1_animatic_v4.mp4'], stdin=subprocess.PIPE)
for i in range(NF): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('done', NF)
