# 冒頭の確認用動画（絵コンテを声の時刻に並べたもの）。1280×720・24fps
#   絵：sb/F01〜F11（仮のまるロボの静止画）＋スマホの画面の小窓＋タイトル。声：Achernar。字幕：subs_jp。足音：まるロボの予定の step
import os, sys, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools')
from op_timeline import *
import narration as NA, overlay2d as O2, subs_jp as SJ, marumotion as mm, op_plan
W_, H_, FPS = 1280, 720, 24
OUT = os.path.join(HERE, 'animatic'); os.makedirs(OUT, exist_ok=True)
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(px): return ImageFont.truetype(FB, px)
# ---- 声の置き場所（冒頭の時刻表から）
V = json.load(open(WORK + '/stage/voice/achernar/lines.json'))
L = json.load(open(WORK + '/stage/script/script_v2_timed.json'))
P = []
for e in L:
    s = VOICE_START[e['no']]; d = V[str(e['no'])]['dur']
    P.append(dict(no=e['no'], start=s, end=round(s + d, 3), speed=1.0, slot=[s, s + d], text=e['text']))
    if e['no'] == 4:      # 台本 v1.2：02-03.5（汚れたポスター）
        a, b = VOICE_4B; P.append(dict(no=4.5, start=a, end=round(b, 3), speed=1.0, slot=[a, b], text='そういえば、少し汚れたポスターのQRコードでも、ちゃんと読めることがありますよね。', wav=WORK + '/stage/voice/achernar/line_004b.wav'))
json.dump(P, open(WORK + '/stage/voice/achernar/placement.json', 'w'), ensure_ascii=False, indent=0)
SRT = OUT + '/op.srt'; NA.srt(P, SRT)
print('gaps', NA.report_gaps(P, 0.6))
# ---- スマホの画面（小窓）
def phone_ui(preview, state):
    w, h = 300, 540; im = Image.new('RGBA', (w + 24, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w + 23, h + 23], 42, fill=(28, 32, 38, 255))
    pv = Image.open(preview).convert('RGB'); s = h / pv.height; pv = pv.resize((int(pv.width * s), h))
    x0 = (pv.width - w) // 2; pv = pv.crop((x0, 0, x0 + w, h))
    scr = Image.new('RGBA', (w, h)); scr.paste(pv, (0, 0)); sd = ImageDraw.Draw(scr)
    cx, cy, k = w // 2, h // 2 + 10, 120                        # 読み取りの枠（角だけ）
    col = (255, 214, 64) if state == 'scan' else (120, 220, 140)
    for sx in (-1, 1):
        for sy in (-1, 1):
            X, Y = cx + sx * k, cy + sy * k
            sd.line([(X, Y), (X - sx * 34, Y)], fill=col, width=6); sd.line([(X, Y), (X, Y - sy * 34)], fill=col, width=6)
    if state == 'hello':
        sd.rounded_rectangle([18, 22, w - 18, 92], 18, fill=(248, 248, 246, 240))
        sd.text((36, 34), 'テキスト', font=font(18), fill=(110, 116, 124)); sd.text((36, 54), 'HELLO', font=font(28), fill=(30, 34, 40))
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 32, fill=255)
    im.paste(scr, (12, 12), mask); return im
PV = {'plain': 'sb/T_top_plain.png', 'stand': 'sb/F04.png', 'step': 'sb/F07.png'}
UI = {}
def preview_at(t): return 'plain' if t < 10.1 else ('stand' if t < 28.6 else ('step' if t < 39.6 else 'plain'))
def screen_at(t):
    st = 'scan'
    for a, s in SCREEN:
        if t >= a: st = s
    return st
# ---- カット（静止画・ゆっくり寄る）
SHOTS = [(a, b, {'wide': 'S01_wide_lines', 'shoulder': None, 'wide2': 'S03_walk', 'close': 'S06_close', 'med': 'S08_med', 'low': 'S10_low', 'face': 'S11_face'}[v] or
          {7.7: 'S02_sh_hello', 13.6: 'S04_sh_scan', S(32.5): 'S07_sh_step'}[a], 1.0 + d0, 1.0 + d1) for a, b, v, d0, d1 in SHOTS]
SHOTS.insert(4, (23.6, 26.4, 'S05_sh_hello', 1.10, 1.12)); SHOTS[3] = (13.6, 23.6, 'S04_sh_scan', 1.04, 1.10)
SHOTS = [(a, b, ('S09_off' if (k == 'S01_wide_lines' and a > 40) else ('S06_close' if a == 32.5 else k)), z0, z1) for a, b, k, z0, z1 in SHOTS]
POSTER = Image.open(os.path.join(HERE, '..', 'inserts', 'poster_dirty.png')).convert('RGB').resize((W_, H_), Image.LANCZOS)
IMG = {k: Image.open(os.path.join(HERE, 'sb2', k + '.png')).convert('RGB').resize((W_, H_), Image.LANCZOS) for _, _, k, _, _ in SHOTS}
def kb(im, z):
    w, h = int(W_ / z), int(H_ / z); x, y = (W_ - w) // 2, (H_ - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def title_frame(t):
    base = IMG['S10_low'].filter(ImageFilter.GaussianBlur(6)); dk = Image.new('RGB', (W_, H_), (14, 22, 34))
    im = Image.blend(base, dk, 0.55); d = ImageDraw.Draw(im)
    a = min(1, (t - T_TITLE[0]) / 0.5)
    d.text((W_ / 2, H_ / 2 - 40), 'QRコードは', font=font(64), fill=(255, 255, 255), anchor='mm')
    d.text((W_ / 2, H_ / 2 + 50), '欠けてもなぜ読める？', font=font(84), fill=(255, 214, 64), anchor='mm')
    return Image.blend(Image.blend(base, dk, 0.55), im, a)
def frame(t):
    if t >= T_TITLE[0]: return title_frame(t)
    for a, b, k, z0, z1 in SHOTS:
        if a <= t < b: im = kb(IMG[k], z0 + (z1 - z0) * (t - a) / (b - a)); break
    else: im = IMG['S11_face'].copy()
    if T_POSTER[0] <= t < T_POSTER[1]:      # 02-03.5：汚れたポスターの図をふわっと重ねる
        al = min(1.0, (t - T_POSTER[0]) / 0.3, (T_POSTER[1] - t) / 0.3); im = Image.blend(im, POSTER, max(0.0, al))
    if False:
        ui = UI[(preview_at(t), screen_at(t))]; al = min(1, (t - 1.0) / 0.4, (40.6 - t) / 0.4)
        ui2 = ui.resize((int(ui.width * 0.62), int(ui.height * 0.62)))
        if al < 1: a_ = ui2.split()[3].point(lambda v: int(v * al)); ui2.putalpha(a_)
        im = im.convert('RGBA'); im.alpha_composite(ui2, (W_ - ui2.width - 28, 24)); im = im.convert('RGB')
        d = ImageDraw.Draw(im); d.text((W_ - ui2.width // 2 - 28, 24 + ui2.height + 16), 'スマホの画面', font=font(20), fill=(255, 255, 255), anchor='mm', stroke_width=3, stroke_fill=(20, 26, 34))
    return im
# ---- 音：足音（予定の step）・結果が出る小さな音・声
SR = 48000; n = int(T_END * SR); bus = np.zeros(n, np.float32)
pl = op_plan.plan(); _ = mm.simulate(pl, fps=24)
for e in pl.events:
    if e['kind'] in ('step', 'step_turn', 'land'):
        x = O2.thump(0.22 * e.get('strength', 1.0), dur=0.07, f=170.0, click=0.45); i = int(e['t'] * SR); bus[i:i + len(x)] += x[:max(0, n - i)]
for a, s in SCREEN:
    if s == 'hello' and 0 < a < 40:
        x = O2.chime(0.10); i = int(a * SR); bus[i:i + len(x)] += x[:max(0, n - i)]
if os.environ.get('CLEAN'):                       # 通しの確認用：絵だけ・効果音だけ・声の置き場所を書き出す（BGM と字幕は通しでまとめてつける）
    _tag = os.environ['CLEAN']
    np.save(os.path.join(OUT, _tag + '_sfx.npy'), bus.astype(np.float32))
    json.dump([dict(p, wav=p.get('wav') or WORK + '/stage/voice/achernar/line_%03d.wav' % int(p['no'])) for p in P], open(os.path.join(OUT, _tag + '_P.json'), 'w'), ensure_ascii=False)
    _NF = int(round(T_END * FPS))
    _ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', os.path.join(OUT, _tag + '_clean.mp4')], stdin=subprocess.PIPE)
    for _i in range(_NF): _ff.stdin.write(frame(_i / FPS).tobytes())
    _ff.stdin.close(); _ff.wait(); print('clean done', _NF); sys.exit(0)
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
music = np.frombuffer(r.stdout, np.int16).astype(np.float32)[:n] / 32768; music = np.pad(music, (0, n - len(music)))
music *= 0.08 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2.0 * SR):] *= np.linspace(1, 0, int(2.0 * SR))
mix = NA.mix_voice(music + bus, 0.0, P=P, bus_peak=0.40, duck_db=6)
with wave.open(OUT + '/op_audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
# ---- 字幕（ASS）
ass = O2.ASS_HEAD[:]
for a, c, txt in SJ.expand(O2.srt_lines(SRT)):
    ass.append('Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt))
ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(0), O2.ts(T_END), '確認用 v4（台本v1.2）：仮のまるロボの静止画（本番はPCの3D）'))
open(OUT + '/op.ass', 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
# ---- 書き出し
NF = int(round(T_END * FPS))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W_, H_), '-r', str(FPS), '-i', '-',
                       '-i', OUT + '/op_audio.wav', '-vf', "ass=%s:fontsdir=/usr/share/fonts/opentype/noto" % (OUT + '/op.ass'),
                       '-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-shortest',
                       OUT + '/qr_opening_animatic_v4.mp4'], stdin=subprocess.PIPE)
for i in range(NF): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('done', NF)
