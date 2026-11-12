# 4章（直す）の確認用動画：絵コンテを声に合わせて並べる。1280×720・24fps
#   MARU_WORK=…/maru_ch4 python3 ch4_animatic.py        （CLEAN=c4 で通し用の「絵だけ」）
import os, sys, json, subprocess, wave
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
import narration as NA, overlay2d as O2, subs_jp as SJ
W_, H_, FPS = 1280, 720, 24
OUT = os.path.join(HERE, 'animatic'); os.makedirs(OUT, exist_ok=True)
V = json.load(open(WORK + '/stage/voice/achernar/lines.json')); L = json.load(open(WORK + '/stage/script/script_v2_timed.json'))
# 前の声からの間：話が変わる所 0.8〜1.4、続き 0.45。動きを見せる所（布をかける・汚れが落ちる・メモが出る・組み上がる）は長め
GAP = {2: 0.45, 3: 0.8, 4: 0.45, 5: 1.4, 6: 0.6, 7: 0.6, 8: 0.9, 9: 1.3, 10: 0.6, 11: 1.2, 12: 0.6, 13: 0.6, 14: 0.8, 15: 1.9, 16: 0.6,
       17: 1.0, 18: 0.6, 19: 1.0, 20: 1.3, 21: 0.45, 22: 0.8, 23: 1.0, 24: 0.8, 25: 1.0, 26: 1.4, 27: 0.6, 28: 0.9, 29: 0.9, 30: 0.6,
       31: 1.4, 32: 0.8, 33: 0.8, 34: 0.45, 35: 1.6, 36: 0.9, 37: 0.6, 38: 1.6, 39: 1.4}
d = lambda no: V[str(no)]['dur']
ST = {1: 0.8}
for no in range(2, len(L) + 1): ST[no] = ST[no - 1] + d(no - 1) + GAP[no]
EN = {no: ST[no] + d(no) for no in ST}
T_END = EN[39] + 2.4
P = [dict(no=e['no'], start=ST[e['no']], end=round(EN[e['no']], 3), speed=1.0, slot=[ST[e['no']], EN[e['no']]], text=e['text']) for e in L]
json.dump(P, open(WORK + '/stage/voice/achernar/placement.json', 'w'), ensure_ascii=False, indent=0)
print('gaps<0.3', NA.report_gaps(P, 0.3), 'T_END', round(T_END, 2))
s = lambda no: ST[no]; e = lambda no: EN[no]
SHOTS = [(0.0, s(3), 'F1', 1.00, 1.06), (s(3), s(5) - 0.3, 'F2', 1.00, 1.06),
         (s(5) - 0.3, s(7), 'C1', 1.00, 1.04), (s(7), s(7) + 4.6, 'C2a', 1.00, 1.02), (s(7) + 4.6, e(8) + 0.2, 'C2', 1.00, 1.03),
         (e(8) + 0.2, s(9) + 6.4, 'C3', 1.00, 1.03), (s(9) + 6.4, s(11) - 0.3, 'C4', 1.00, 1.03),
         (s(11) - 0.3, s(12), 'C2', 1.00, 1.02), (s(12), s(13), 'W23', 1.00, 1.05), (s(13), e(14) + 0.2, 'C2', 1.02, 1.04),
         (e(14) + 0.2, e(14) + 0.9, 'C6a', 1.00, 1.01), (e(14) + 0.9, s(15) - 0.1, 'C6', 1.00, 1.01), (s(15) - 0.1, s(17) + 2.0, 'C7', 1.00, 1.05),
         (s(17) + 2.0, e(19) + 0.3, 'C8', 1.00, 1.04), (e(19) + 0.3, s(22) + 5.4, 'C9', 1.00, 1.04), (s(22) + 5.4, s(23), 'C10', 1.00, 1.02),
         (s(23), s(24), 'C11', 1.00, 1.04), (s(24), s(24) + 2.6, 'C10', 1.02, 1.03), (s(24) + 2.6, s(25) + 1.6, 'C12a', 1.00, 1.03), (s(25) + 1.6, s(26) - 0.3, 'C12', 1.00, 1.04),
         (s(26) - 0.3, s(27), 'D5a', 1.00, 1.01), (s(27), s(28), 'D5b', 1.00, 1.02), (s(28), s(29), 'W26', 1.00, 1.04), (s(29), s(30), 'D5c', 1.00, 1.02), (s(30), s(31) - 0.3, 'D5d', 1.00, 1.02),
         (s(31) - 0.3, s(32), 'R1', 1.00, 1.04), (s(32), s(33), 'R2', 1.00, 1.03), (s(33), s(35) - 0.3, 'R3', 1.00, 1.05),
         (s(35) - 0.3, s(36), 'T35', 1.00, 1.04), (s(36), s(37) + 1.2, 'B28a', 1.00, 1.03), (s(37) + 1.2, s(37) + 5.4, 'B28b', 1.00, 1.03), (s(37) + 5.4, s(38) - 0.1, 'B28c', 1.00, 1.03),
         (s(38) - 0.1, s(39) - 0.3, 'B28d', 1.00, 1.03), (s(39) - 0.3, T_END, 'T28', 1.00, 1.05)]
IMG = {k: Image.open(os.path.join(HERE, 'sb', k + '.png')).convert('RGB').resize((W_, H_), Image.LANCZOS) for _, _, k, _, _ in SHOTS}
def kb(im, z):
    w, h = int(W_ / z), int(H_ / z); x = (W_ - w) // 2; y = (H_ - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def frame(t):
    for a, b, k, z0, z1 in SHOTS:
        if a <= t < b: break
    return kb(IMG[k], z0 + (z1 - z0) * (t - a) / max(b - a, 1e-6))
SR = 48000; n = int(T_END * SR)
sfx = np.zeros(n, np.float32)
def put(tt, x):
    i = int(tt * SR); m = min(len(x), n - i); sfx[i:i + m] += x[:m]
put(e(8) + 0.25, O2.thump(0.16, dur=0.12, f=110.0, click=0.15))        # 布をかける
put(e(14) + 0.9, O2.thump(0.22, dur=0.10, f=90.0, click=0.4))          # 汚れが落ちる
for tt in (e(19) + 0.35, s(22) + 5.45, s(17) + 2.05): put(tt, O2.thump(0.10, dur=0.06, f=380.0, click=0.5))   # メモ・数字が出る
put(s(25) + 1.65, O2.thump(0.12, dur=0.06, f=520.0, click=0.5))         # 5 に戻る
put(s(37) + 5.45, O2.thump(0.14, dur=0.08, f=300.0, click=0.4))         # 組み上がる
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
with wave.open(OUT + '/ch4_audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ev = []
for k, p in enumerate(P):
    nxt = P[k + 1]['start'] if k + 1 < len(P) else p['end'] + 1.0
    ev += SJ.events(p['start'], min(max(p['end'] + 0.35, p['start'] + 1.0), nxt - 0.05), p['text'], wav=WORK + '/stage/voice/achernar/line_%03d.wav' % p['no'], speed=1.0)
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt) for a, c, txt in ev]
ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(0), O2.ts(4.0), '確認用 v1：4章　仮のまるロボの静止画（本番はPCの3D）'))
open(OUT + '/ch4.ass', 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
NF = int(round(T_END * FPS))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-i', OUT + '/ch4_audio.wav',
                       '-vf', 'ass=%s:fontsdir=/usr/share/fonts/opentype/noto' % (OUT + '/ch4.ass'), '-c:v', 'libx264', '-crf', '24', '-pix_fmt', 'yuv420p',
                       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-shortest', OUT + '/qr_ch4_animatic_v1.mp4'], stdin=subprocess.PIPE)
for i in range(NF): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('done', NF, round(T_END, 2))
