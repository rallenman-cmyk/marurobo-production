# 2章（見つける）の確認用動画：絵コンテを声に合わせて並べる。1280×720・24fps
#   MARU_WORK=…/maru_ch2 python3 ch2_animatic.py
import os, sys, json, subprocess, wave
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
import narration as NA, overlay2d as O2, subs_jp as SJ
W_, H_, FPS = 1280, 720, 24
OUT = os.path.join(HERE, 'animatic'); os.makedirs(OUT, exist_ok=True)
V = json.load(open(WORK + '/stage/voice/achernar/lines.json')); L = json.load(open(WORK + '/stage/script/script_v2_timed.json'))
# 文ごとの「前の声からの間」：話が変わる所 0.8、続き 0.45、動きを見せる所は長め（数字は秒）
GAP = {2: 0.6, 3: 1.0, 4: 1.6, 5: 1.4, 6: 0.6, 7: 0.9, 8: 0.45, 9: 0.6, 10: 0.6, 11: 0.45, 12: 1.4, 13: 0.3, 14: 0.45, 15: 1.0, 16: 0.3, 17: 0.45,
       18: 0.9, 19: 0.45, 20: 0.6, 21: 0.9, 22: 0.3, 23: 0.6, 24: 0.45, 25: 0.6, 26: 0.6, 27: 0.45, 28: 0.9, 29: 0.3, 30: 0.9, 31: 0.6, 32: 0.6,
       33: 1.4, 34: 0.9, 35: 0.45, 36: 0.3, 37: 1.0, 38: 1.0, 39: 1.6, 40: 0.8, 41: 0.3, 42: 0.45, 43: 0.9, 44: 0.3, 45: 0.45}
d = lambda no: V[str(no)]['dur']
ST = {1: 0.6}
for no in range(2, len(L) + 1): ST[no] = ST[no - 1] + d(no - 1) + GAP[no]
EN = {no: ST[no] + d(no) for no in ST}
T_END = EN[45] + 2.0
P = [dict(no=e['no'], start=ST[e['no']], end=round(EN[e['no']], 3), speed=1.0, slot=[ST[e['no']], EN[e['no']]], text=e['text']) for e in L]
json.dump(P, open(WORK + '/stage/voice/achernar/placement.json', 'w'), ensure_ascii=False, indent=0)
print('gaps<0.3', NA.report_gaps(P, 0.3), 'T_END', round(T_END, 2))
SRT = OUT + '/ch2.srt'; NA.srt(P, SRT)
s = lambda no: ST[no]; e = lambda no: EN[no]
SHOTS = [(0.0, s(1) + 2.6, 'ZOOM19', 1.00, 3.0), (s(1) + 2.6, s(2), 'K20', 1.00, 1.04), (s(2), s(2) + 2.4, 'K21a', 1.00, 1.02), (s(2) + 2.4, s(3) - 0.3, 'K21', 1.00, 1.03), (s(3) - 0.3, s(4) - 0.6, 'K21', 1.03, 1.06), (s(4) - 0.6, s(5), 'K22', 1.00, 1.04),
         (s(5), s(6), 'K23', 1.00, 1.04), (s(6), s(7), 'K24', 1.00, 1.05),
         (s(7), s(8), 'D1', 1.00, 1.03), (s(8), s(9), 'K25a', 1.00, 1.02), (s(9), s(10), 'K25', 1.00, 1.02), (s(10), s(10) + 4.6, 'K26a', 1.00, 1.02), (s(10) + 4.6, s(11), 'K26b', 1.00, 1.02),
         (s(11), s(12) - 0.8, 'D1', 1.00, 1.03),
         (s(12) - 0.8, s(15), 'K27', 1.00, 1.06), (s(15), s(18), 'K28', 1.00, 1.05), (s(18), s(20), 'K29', 1.00, 1.05), (s(20), s(21), 'K30', 1.00, 1.04),
         (s(21), s(25), 'K31a', 1.00, 1.05), (s(25), s(26), 'K32', 1.00, 1.03), (s(26), s(28), 'K33', 1.00, 1.04), (s(28), s(30), 'K31', 1.00, 1.04),
         (s(30), s(31), 'K40', 1.00, 1.03), (s(31), s(32), 'K38', 1.00, 1.03), (s(32), s(32) + 4.0, 'K39', 1.00, 1.02), (s(32) + 4.0, s(33), 'K40', 1.02, 1.03), (s(33), s(34), 'K39', 1.00, 1.02),
         (s(34), s(37), 'K34', 1.00, 1.06), (s(37), s(37) + 4.0, 'K41', 1.00, 1.03), (s(37) + 4.0, s(39) - 0.2, 'K42', 1.00, 1.04), (s(39) - 0.2, s(40), 'K43', 1.00, 1.04),
         (s(40), s(43), 'K42', 1.04, 1.08), (s(43), T_END, 'K37', 1.00, 1.04)]
IMG = {k: Image.open(os.path.join(HERE, 'sb', k + '.png')).convert('RGB').resize((W_, H_), Image.LANCZOS) for _, _, k, _, _ in SHOTS if k != 'ZOOM19'}
IMG['K19'] = Image.open(os.path.join(HERE, 'sb', 'K19.png')).convert('RGB').resize((W_, H_), Image.LANCZOS)
def kb(im, z):
    w, h = int(W_ / z), int(H_ / z); x = (W_ - w) // 2; y = (H_ - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def kbc(im, z, cx, cy):
    w, h = int(W_ / z), int(H_ / z); x = int(min(max(cx * W_ - w / 2, 0), W_ - w)); y = int(min(max(cy * H_ - h / 2, 0), H_ - h))
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def frame(t):
    for a, b, k, z0, z1 in SHOTS:
        if a <= t < b: break
    if k == 'ZOOM19':                                  # 全体（真上）から左上の目印へ寄る：1.2 秒見せてから寄る
        u = min(1.0, max(0.0, (t - 1.2) / 1.8)); u = u * u * (3 - 2 * u)
        return kbc(IMG['K19'], 1.0 + 2.0 * u, 0.5 + (0.355 - 0.5) * u, 0.5 + (0.22 - 0.5) * u)
    return kb(IMG[k], z0 + (z1 - z0) * (t - a) / max(b - a, 1e-6))
SR = 48000; n = int(T_END * SR)
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768; music = np.tile(music, n // len(music) + 1)[:n]
music *= 0.06 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))
sfx = np.zeros(n, np.float32)
for tt, a in ((s(3) - 0.3, 0.05), (s(4) - 0.2, 0.05), (s(12) - 0.7, 0.2), (s(37) + 2.0, 0.15)):
    x = O2.thump(a * 2, dur=0.09, f=140.0, click=0.3); i = int(tt * SR); sfx[i:i + len(x)] += x
if os.environ.get('CLEAN'):                       # 通しの確認用：絵だけ・効果音だけ・声の置き場所を書き出す（BGM と字幕は通しでまとめてつける）
    _tag = os.environ['CLEAN']
    np.save(os.path.join(OUT, _tag + '_sfx.npy'), sfx.astype(np.float32))
    json.dump([dict(p, wav=p.get('wav') or WORK + '/stage/voice/achernar/line_%03d.wav' % int(p['no'])) for p in P], open(os.path.join(OUT, _tag + '_P.json'), 'w'), ensure_ascii=False)
    _NF = int(round(T_END * FPS))
    _ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', os.path.join(OUT, _tag + '_clean.mp4')], stdin=subprocess.PIPE)
    for _i in range(_NF): _ff.stdin.write(frame(_i / FPS).tobytes())
    _ff.stdin.close(); _ff.wait(); print('clean done', _NF); sys.exit(0)
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.38, duck_db=6)
with wave.open(OUT + '/ch2_audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt) for a, c, txt in SJ.expand(O2.srt_lines(SRT))]
ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(0), O2.ts(T_END), '確認用 v3：2章　仮のまるロボの静止画（本番はPCの3D）'))
open(OUT + '/ch2.ass', 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
NF = int(round(T_END * FPS))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-i', OUT + '/ch2_audio.wav',
                       '-vf', 'ass=%s:fontsdir=/usr/share/fonts/opentype/noto' % (OUT + '/ch2.ass'), '-c:v', 'libx264', '-crf', '24', '-pix_fmt', 'yuv420p',
                       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-shortest', OUT + '/qr_ch2_animatic_v3.mp4'], stdin=subprocess.PIPE)
for i in range(NF): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('done', NF, round(T_END, 2))
