# 3章（読む）の確認用動画：絵コンテを声に合わせて並べる＋読み取りの図（ch3_overlays）を重ねる。1280×720・24fps
#   MARU_WORK=…/maru_ch3 python3 ch3_animatic.py        （CLEAN=c3 で通し用の「絵だけ」）
import os, sys, json, subprocess, wave
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
import narration as NA, overlay2d as O2, subs_jp as SJ
import ch3_overlays as OV
W_, H_, FPS = 1280, 720, 24
OUT = os.path.join(HERE, 'animatic'); os.makedirs(OUT, exist_ok=True)
V = json.load(open(WORK + '/stage/voice/achernar/lines.json')); L = json.load(open(WORK + '/stage/script/script_v2_timed.json'))
# 前の声からの間：話が変わる所 0.8、続き 0.45。4 の前は箱を運んで並べる（早回し）ぶん長め
GAP = {2: 0.8, 3: 0.6, 4: 3.4, 5: 1.0, 6: 0.45, 7: 0.9, 8: 1.0, 9: 1.2, 10: 1.4, 11: 0.6}
d = lambda no: V[str(no)]['dur']
ST = {1: 0.8}
for no in range(2, len(L) + 1): ST[no] = ST[no - 1] + d(no - 1) + GAP[no]
EN = {no: ST[no] + d(no) for no in ST}
T_END = EN[11] + 2.2
P = [dict(no=e['no'], start=ST[e['no']], end=round(EN[e['no']], 3), speed=1.0, slot=[ST[e['no']], EN[e['no']]], text=e['text']) for e in L]
json.dump(P, open(WORK + '/stage/voice/achernar/placement.json', 'w'), ensure_ascii=False, indent=0)
print('gaps<0.3', NA.report_gaps(P, 0.3), 'T_END', round(T_END, 2))
SRT = OUT + '/ch3.srt'; NA.srt(P, SRT)
s = lambda no: ST[no]; e = lambda no: EN[no]
# 読み取りの図の時刻（line_008 の H・E・L・L・O の声：0.05・1.16・2.13・3.09・4.05 秒、「ハロー」8.22 秒）
M = dict(a=s(5) - 0.2, b=s(6) + 0.1, c=s(7) + 0.2, d_letters=[s(8) + x for x in (0.05, 1.16, 2.13, 3.09, 4.05)], hello=s(8) + 8.1, e=s(9) + 0.3, end=e(9) + 0.9)
SHOTS = [(0.0, s(2), 'G1', 1.00, 1.05), (s(2), e(2) + 0.4, 'G2', 1.00, 1.05), (e(2) + 0.4, s(3) + 1.6, 'G3a', 1.00, 1.02), (s(3) + 1.6, e(3) + 0.5, 'G3', 1.02, 1.04),
         (e(3) + 0.5, e(3) + 2.2, 'G4', 1.00, 1.04), (e(3) + 2.2, s(4) + 4.4, 'G5', 1.00, 1.03), (s(4) + 4.4, s(4) + 6.4, 'G6a', 1.00, 1.02), (s(4) + 6.4, M['a'], 'G6', 1.02, 1.05),
         (M['a'], M['end'], 'G7', 1.00, 1.04), (M['end'], s(11) - 0.1, 'G8', 1.00, 1.04), (s(11) - 0.1, T_END, 'G9', 1.00, 1.05)]
IMG = {k: Image.open(os.path.join(HERE, 'sb', k + '.png')).convert('RGB').resize((W_, H_), Image.LANCZOS) for _, _, k, _, _ in SHOTS}
def kb(im, z):
    w, h = int(W_ / z), int(H_ / z); x = (W_ - w) // 2; y = (H_ - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def frame(t):
    for a, b, k, z0, z1 in SHOTS:
        if a <= t < b: break
    im = kb(IMG[k], z0 + (z1 - z0) * (t - a) / max(b - a, 1e-6))
    if M['a'] <= t < M['end']:
        im = im.convert('RGBA'); im.alpha_composite(OV.reading_frame(t, M, W_)); im = im.convert('RGB')
    return im
SR = 48000; n = int(T_END * SR)
sfx = np.zeros(n, np.float32)
def put(tt, x):
    i = int(tt * SR); m = min(len(x), n - i); sfx[i:i + m] += x[:m]
put(s(3) + 1.5, O2.thump(0.18, dur=0.09, f=140.0, click=0.3))                    # 箱ができた
for tt in (e(3) + 1.0, e(3) + 1.7): put(tt, O2.thump(0.14, dur=0.08, f=150.0, click=0.3))     # 箱を置く
for tt in M['d_letters']: put(tt + 0.02, O2.thump(0.08, dur=0.05, f=420.0, click=0.5))      # 文字が出る
if os.environ.get('CLEAN'):                       # 通しの確認用：絵だけ・効果音だけ・声の置き場所を書き出す（BGM と字幕は通しでまとめてつける）
    _tag = os.environ['CLEAN']
    np.save(os.path.join(OUT, _tag + '_sfx.npy'), sfx.astype(np.float32))
    json.dump([dict(p, wav=WORK + '/stage/voice/achernar/line_%03d.wav' % int(p['no'])) for p in P], open(os.path.join(OUT, _tag + '_P.json'), 'w'), ensure_ascii=False)
    _NF = int(round(T_END * FPS))
    _ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', os.path.join(OUT, _tag + '_clean.mp4')], stdin=subprocess.PIPE)
    for _i in range(_NF): _ff.stdin.write(frame(_i / FPS).tobytes())
    _ff.stdin.close(); _ff.wait(); print('clean done', _NF, round(T_END, 2)); sys.exit(0)
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768; music = np.tile(music, n // len(music) + 1)[:n]
music *= 0.06 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.38, duck_db=6)
with wave.open(OUT + '/ch3_audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ev = []
for k, p in enumerate(P):
    nxt = P[k + 1]['start'] if k + 1 < len(P) else p['end'] + 1.0
    ev += SJ.events(p['start'], min(max(p['end'] + 0.35, p['start'] + 1.0), nxt - 0.05), p['text'], wav=WORK + '/stage/voice/achernar/line_%03d.wav' % p['no'], speed=1.0)
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt) for a, c, txt in ev]
ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(0), O2.ts(4.0), '確認用 v1：3章　仮のまるロボの静止画（本番はPCの3D）'))
open(OUT + '/ch3.ass', 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
NF = int(round(T_END * FPS))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-i', OUT + '/ch3_audio.wav',
                       '-vf', 'ass=%s:fontsdir=/usr/share/fonts/opentype/noto' % (OUT + '/ch3.ass'), '-c:v', 'libx264', '-crf', '24', '-pix_fmt', 'yuv420p',
                       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-shortest', OUT + '/qr_ch3_animatic_v1.mp4'], stdin=subprocess.PIPE)
for i in range(NF): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('done', NF, round(T_END, 2))
