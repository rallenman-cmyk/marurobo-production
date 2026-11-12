# 冒頭の本番の組み立て：PC の絵（qrop_0001-0100.mp4 … 17 本）＋タイトル＋字幕＋声・足音・結果の音・BGM
#   python3 op_assemble.py DL_DIR OUT.mp4 [--preview]   （--preview：1280×720・15MB 以下の確認用）
import os, sys, json, glob, subprocess, wave, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
from op_timeline import *
import narration as NA, overlay2d as O2, subs_jp as SJ
DL, OUT = sys.argv[1], sys.argv[2]; PREV = '--preview' in sys.argv
FPS, SR = 24, 48000; W_, H_ = 1920, 1080
BGM = '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav'
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(OUT)))
# ---- 絵：PC の mp4 をつなぐ（コマ数を確かめる）
parts = sorted(glob.glob(os.path.join(DL, 'qrop2_*.mp4'))); assert parts, 'qrop2_*.mp4 がない'
nf = 0
for p in parts:
    a, b = map(int, os.path.basename(p).split('_')[-1][:-4].split('-')); n = int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip())
    assert n == b - a + 1, '%s のコマ数が %d（%d のはず）' % (p, n, b - a + 1); nf += n
lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(p) for p in parts))
body = os.path.join(tmp, 'body.mp4'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', body], check=True)
# ---- タイトル（最後のコマをぼかして、上に題）
last = os.path.join(tmp, 'last.png'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', body, '-frames:v', '1', last], check=True)
base = Image.open(last).convert('RGB').resize((W_, H_)); bl = base.filter(ImageFilter.GaussianBlur(9)); dk = Image.blend(bl, Image.new('RGB', (W_, H_), (14, 22, 34)), 0.55)
f1, f2 = ImageFont.truetype(FB, 96), ImageFont.truetype(FB, 126)
n_title = int(round((T_END - nf / FPS) * FPS)); tdir = os.path.join(tmp, 'title'); os.makedirs(tdir)
for i in range(n_title):
    t = i / FPS; u = min(1, t / 0.5); im = Image.blend(base, dk, min(1, t / 0.4)); d = ImageDraw.Draw(im)
    if u > 0:
        txt = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
        td.text((W_ / 2, H_ / 2 - 60), 'QRコードは', font=f1, fill=(255, 255, 255, int(255 * u)), anchor='mm')
        td.text((W_ / 2, H_ / 2 + 75), '欠けてもなぜ読める？', font=f2, fill=(255, 214, 64, int(255 * u)), anchor='mm')
        im = Image.alpha_composite(im.convert('RGBA'), txt).convert('RGB')
    im.save(os.path.join(tdir, 't_%04d.png' % i))
title = os.path.join(tmp, 'title.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tdir, 't_%04d.png'), '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', title], check=True)
# ---- 音：声（placement）・足音（PC の記録）・結果の音（画面が映っている 2 回）・BGM（声の間は 6dB 下げる）
P = json.load(open(WORK + '/stage/voice/achernar/placement.json'))
log = json.load(open(os.path.join(DL, 'qrop_log.json'))); n = int(T_END * SR)
sfx = np.zeros(n, np.float32)
for e in log['events']:
    if e['kind'] in ('step', 'step_turn', 'land'):
        s = O2.thump(0.22 * e.get('strength', 1.0), dur=0.07, f=170.0, click=0.45); i = int(e['t'] * SR); sfx[i:i + len(s)] += s[:max(0, n - i)]
for a, s in SCREEN:
    if s == 'hello' and 0 < a < 30:
        c = O2.chime(0.10); i = int(a * SR); sfx[i:i + len(c)] += c[:max(0, n - i)]
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', BGM, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32)[:n] / 32768; music = np.pad(music, (0, n - len(music)))
music *= 0.08 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2.0 * SR):] *= np.linspace(1, 0, int(2.0 * SR))
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.40, duck_db=6)
aw = os.path.join(tmp, 'audio.wav')
with wave.open(aw, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
# ---- 字幕
SRT = os.path.join(tmp, 'op.srt'); NA.srt(P, SRT)
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), t) for a, c, t in SJ.expand(O2.srt_lines(SRT))]
ap = os.path.join(tmp, 'op.ass'); open(ap, 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
# ---- 書き出し
vf = "ass=%s:fontsdir=/usr/share/fonts/opentype/noto" % ap
if PREV: vf = 'scale=1280:720,' + vf
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', body, '-i', title, '-i', aw,
       '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0,fps=24[v];[v]%s[o]' % vf, '-map', '[o]', '-map', '2:a',
       '-c:v', 'libx264', '-crf', '26' if PREV else '16', '-preset', 'medium', '-pix_fmt', 'yuv420p',
       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '160k', '-t', '%.3f' % T_END, OUT]
subprocess.run(cmd, check=True)
print('done', OUT, 'frames', nf, '+ title', n_title)
