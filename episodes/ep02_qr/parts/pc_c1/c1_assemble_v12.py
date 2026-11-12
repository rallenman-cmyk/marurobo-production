# 1章の本番の組み立て：PC の絵（卓上 qrc1t_*.mp4 → 中の世界 qrc1w_*.mp4）＋ URL の図 ＋ 字幕 ＋ 声・効果音・BGM
#   MARU_WORK=…/maru_ch1 python3 c1_assemble.py DL_DIR OUT.mp4 [--preview]
#   卓上 → 中の世界のつなぎ目は、白く光ってつなぐ（画面の中へ入る）。声の置き場所は c1_timeline の V（「見つかりました」の前を 5 秒のばした版）
import os, sys, json, glob, subprocess, wave, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
from c1_timeline import *
import narration as NA, overlay2d as O2, subs_jp as SJ
DL, OUT = sys.argv[1], sys.argv[2]; PREV = '--preview' in sys.argv
SR = 48000
BGM = '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav'
URL_PNG = '/home/user/qr_plan/parts/ch1/sb/URL.png'
tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(OUT)))
def frames_of(p): return int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip())
def join(prefix, f_a, f_b):
    parts = sorted(glob.glob(os.path.join(DL, prefix + '*.mp4'))); assert parts, prefix + '*.mp4 がない'
    got = []
    for p in parts:
        a, b = map(int, os.path.basename(p)[len(prefix):-4].split('-')); n = frames_of(p)
        assert n == b - a + 1, '%s のコマ数が %d（%d のはず）' % (p, n, b - a + 1); got += list(range(a, b + 1))
    assert got == list(range(f_a, f_b + 1)), '%s のコマが %d〜%d にそろっていない' % (prefix, f_a, f_b)
    lst = os.path.join(tmp, prefix + 'list.txt'); open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(p) for p in parts))
    out = os.path.join(tmp, prefix + 'body.mp4'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
    return out
tab = join('qrc1t_', 1, F_TABLE_END); wld = join('qrc1w2_', F_TABLE_END + 1, F_END)   # v1.2 の中の世界は qrc1w2_
TL = json.load(open(os.path.join(DL, 'qrc1t_log.json'))); WL = json.load(open(os.path.join(DL, 'qrc1w_log.json')))

# ---- 声の置き場所（c1_timeline の V。文は placement.json から）
P0 = {p['no']: p for p in json.load(open(WORK + '/stage/voice/achernar/placement.json'))}
VD = WORK + '/stage/voice/achernar'
P = []
for k in sorted(V):
    p = dict(no=k, start=V[k][0], end=V[k][1], speed=1.0, slot=[V[k][0], V[k][1]], text=TEXT.get(k) or P0[k]['text'])
    if k in WAV: p['wav'] = VD + '/' + WAV[k]
    wp = p.get('wav') or VD + '/line_%03d.wav' % k
    with wave.open(wp) as w: du = w.getnframes() / w.getframerate()
    assert abs(du - (p['end'] - p['start'])) < 0.03, '声の長さが違う：%s（%.2f と %.2f）' % (k, du, p['end'] - p['start'])
    P.append(p)
print('gaps<0.4', NA.report_gaps(P, 0.4))

# ---- 効果音
n = int(T_END * SR); sfx = np.zeros(n, np.float32)
def put(t, x):
    i = int(t * SR)
    if 0 <= i < n: sfx[i:i + len(x)] += x[:n - i]
for e in TL['events'] + WL['events']:
    if e['kind'] in ('step', 'step_turn'): put(e['t'], O2.thump(0.16 * e.get('strength', 1.0), dur=0.06, f=190.0, click=0.45))
    if e['kind'] == 'land': put(e['t'], O2.thump(0.30, dur=0.09, f=120.0, click=0.35))
    if e['kind'] == 'takeoff': put(e['t'], O2.tone(300, 700, 0.18, 0.05))
put(TL['t_cross'], O2.tone(900, 260, 0.35, 0.10)); put(TL['t_cross'] + 0.05, O2.chime(0.05))                   # 画面に飛び込む（ぽちゃん）
put(T_TABLE_END - 0.2, O2.tone(400, 1400, 0.6, 0.05))                                                         # 画面の中へ（ひゅーん）
for k, tb in enumerate(WL['beams']): put(tb, O2.tone(1200 + 200 * k, 1800 + 200 * k, 0.25, 0.05))            # 目の光
for b, (a, c) in WL['fold'].items():                                                                          # たたむ：板が起き上がるかたかた・ふたがかぽっ
    amp = 0.10 if int(b) == 14 else 0.025
    for i in range(8): put(a + (c - a) * (0.15 + 0.08 * i), O2.thump(amp * 0.7, dur=0.04, f=320.0, click=0.6))
    put(c - 0.05, O2.thump(amp, dur=0.07, f=210.0, click=0.5))
put(WL['marks']['catch'], O2.thump(0.22, dur=0.08, f=160.0, click=0.4)); put(WL['toss_land'], O2.thump(0.26, dur=0.09, f=140.0, click=0.4))
put(WL['t_open8'], O2.chime(0.10)); put(T_HELLO, O2.chime(0.08, notes=((1318, 1.0, 0.35), (1760, 0.8, 0.3), (2637, 0.5, 0.25))))
for k in range(8): put(T_SPREAD[0] + (T_SPREAD[1] - T_SPREAD[0]) * k / 7, O2.tone(1400 + 90 * k, 1600 + 90 * k, 0.12, 0.03))
put(T_SHADOW, O2.tone(180, 120, 0.9, 0.06)); put(WL['t_open20'], O2.thump(0.10, dur=0.07, f=200.0, click=0.5))
put(T_BLUE, O2.chime(0.05)); put(T_ORANGE, O2.chime(0.05, notes=((1046, 1.0, 0.3), (1318, 0.7, 0.25))))
for b, (a, c) in WL['unfold'].items(): put(a + 0.2, O2.thump(0.02, dur=0.04, f=300.0, click=0.6))
# ---- BGM（中の世界は少し小さめ。声の間は 6dB 下げる）
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', BGM, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
music = np.tile(music, int(np.ceil(n / len(music))) + 1)[:n]
music *= 0.06 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2.5 * SR):] *= np.linspace(1, 0, int(2.5 * SR))
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.38, duck_db=6)
aw = os.path.join(tmp, 'audio.wav')
with wave.open(aw, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
# ---- 字幕
SRT = os.path.join(tmp, 'c1.srt'); NA.srt(P, SRT)
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), t) for a, c, t in SJ.expand(O2.srt_lines(SRT))]
ap = os.path.join(tmp, 'c1.ass'); open(ap, 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
# ---- 書き出し：卓上の終わり 0.25 秒を白へ、中の世界のはじめ 0.35 秒を白から。URL の図はふわっと重ねる
tt = F_TABLE_END / FPS; u0, u1 = URL_INSERT
fc = ('[0:v]fade=t=out:st=%.3f:d=0.25:color=white[a];[1:v]fade=t=in:st=0:d=0.35:color=white[b];[a][b]concat=n=2:v=1:a=0,fps=24,format=yuv420p[v];'
      '[2:v]scale=1920:1080,format=rgba,fade=t=in:st=%.3f:d=0.3:alpha=1,fade=t=out:st=%.3f:d=0.3:alpha=1[u];'
      '[v][u]overlay=0:0:enable=\'between(t,%.3f,%.3f)\'[w];[w]ass=%s:fontsdir=/usr/share/fonts/opentype/noto%s[o]'
      % (tt - 0.25, u0, u1 - 0.3, u0, u1, ap, ',scale=1280:720' if PREV else ''))
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', tab, '-i', wld, '-loop', '1', '-framerate', '24', '-t', '%.3f' % T_END, '-i', URL_PNG, '-i', aw,
       '-filter_complex', fc, '-map', '[o]', '-map', '3:a', '-c:v', 'libx264', '-crf', '26' if PREV else '16', '-preset', 'medium', '-pix_fmt', 'yuv420p',
       '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '160k', '-t', '%.3f' % (F_END / FPS), OUT]
subprocess.run(cmd, check=True)
print('done', OUT, 'frames', F_END, 'sec', round(F_END / FPS, 2))
