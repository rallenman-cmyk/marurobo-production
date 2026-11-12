# 通しの確認用動画（冒頭＋1章＋2章…）：章ごとの「絵だけ」の確認用動画をつなぎ、声・効果音・字幕を通しの時刻に置き、BGM を通しで 1 本流す
#   1. 各章の確認用スクリプトを CLEAN=名前 で走らせる → animatic/名前_clean.mp4・名前_sfx.npy・名前_P.json
#   2. python3 through_review.py OUT.mp4 章のフォルダ:名前 …（順に）
#   BGM は止めない（章のつなぎ目でも続ける）。最後の 2.5 秒だけ消していく。字幕は声の間で分ける（subs_jp.events に声のファイルを渡す）
import os, sys, json, subprocess, wave
import numpy as np
SP = '/tmp/claude-0/-home-user/8cc26183-437c-5f90-a7e9-3b23d7f91ab2/scratchpad'
sys.path.insert(0, SP + '/maru/tools')
import narration as NA, overlay2d as O2, subs_jp as SJ
OUT = sys.argv[1]; PARTS = [a.split(':') for a in sys.argv[2:]]
SR, FPS = 48000, 24
# 台本の ID（足した文・分けた文）
EXTRA_IDS = {'maru': {4.5: '02-03.5'}, 'maru_ch1': {2.5: '05-02.5', 14.5: '07-01.7b', 16.3: '07-02.6', 16.5: '07-02.6b', 16.7: '07-02.6c', 23.3: '07-04.3', 23.5: '07-04.5', 23.7: '07-04.7'}}
BGM = '/home/user/qr_plan/parts/bgm/A_marimba_bed_180s.wav'
tmp = os.path.splitext(OUT)[0] + '_work'; os.makedirs(tmp, exist_ok=True)
def vdur(p): return float(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'csv=p=0', p]).strip())
# ---- 章ごとの長さと置き場所
offs, P, sfx_parts, clips = [], [], [], []
t = 0.0
for d, tag in PARTS:
    clip = os.path.join(d, tag + '_clean.mp4'); D = vdur(clip); clips.append(clip); offs.append(t)
    for p in json.load(open(os.path.join(d, tag + '_P.json'), encoding='utf-8')):
        ws = p['wav'].split('/stage/voice/')[0]
        ids = {float(x['no']): x['id'] for x in json.load(open(ws + '/stage/script/script_v2_timed.json', encoding='utf-8'))}
        ids.update(EXTRA_IDS.get(os.path.basename(ws), {}))
        p = dict(p, id=ids.get(float(p['no']), str(p['no'])))
        q = dict(p); q['start'] = p['start'] + t; q['end'] = p['end'] + t; q['slot'] = [q['start'], q['end']]; q['chapter'] = tag; P.append(q)
    sfx_parts.append((t, np.load(os.path.join(d, tag + '_sfx.npy'))))
    t += D
T = t; n = int(round(T * SR))
print('parts', [(tag, round(o, 2)) for (d, tag), o in zip(PARTS, offs)], 'total', round(T, 2))
# ---- 音：効果音（章ごと）＋ BGM（通しで 1 本）→ 声を置いて、声の間は BGM を 6dB 下げる
sfx = np.zeros(n, np.float32)
for o, x in sfx_parts:
    i = int(round(o * SR)); m = min(len(x), n - i); sfx[i:i + m] += x[:m]
r = subprocess.run(['ffmpeg', '-v', 'error', '-i', BGM, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
bed = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
music = np.tile(bed, n // len(bed) + 1)[:n]
music *= 0.07 / (np.sqrt(np.mean(music ** 2)) + 1e-9); music[-int(2.5 * SR):] *= np.linspace(1, 0, int(2.5 * SR))
mix = NA.mix_voice(music + sfx, 0.0, P=P, bus_peak=0.38, duck_db=6)
aw = os.path.join(tmp, 'audio.wav')
with wave.open(aw, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
# ---- 字幕：文ごとに、声のファイルの間で分ける。表示は声の終わりの少しあとまで（次の字幕の前まで）
ev = []
for k, p in enumerate(P):
    nxt = P[k + 1]['start'] if k + 1 < len(P) else p['end'] + 1.0
    end = min(max(p['end'] + 0.35, p['start'] + 1.0), nxt - 0.05)
    ev += SJ.events(p['start'], end, p['text'], wav=p.get('wav'), speed=1.0)
ass = O2.ASS_HEAD[:] + ['Dialogue: 0,%s,%s,Main,,0,0,0,,%s' % (O2.ts(a), O2.ts(c), txt) for a, c, txt in ev]
labels = {'op': '冒頭', 'c1': '1章', 'c2': '2章', 'c3': '3章', 'c4': '4章'}
VER = os.environ.get('VER', 'v5')
for (d, tag), o in zip(PARTS, offs):
    ass.append('Dialogue: 1,%s,%s,Shot,,0,0,0,,%s' % (O2.ts(o), O2.ts(o + 4.0), '確認用 通し %s：%s（仮のまるロボの静止画・本番はPCの3D）' % (VER, labels.get(tag, tag))))
ap = os.path.join(tmp, 'subs.ass'); open(ap, 'w', encoding='utf-8').write('\n'.join(ass) + '\n')
json.dump(dict(offsets={tag: o for (d, tag), o in zip(PARTS, offs)}, total=T, subs=[dict(id=p.get('id', str(p['no'])), text=p['text'], t0=round(p['start'], 2), t1=round(p['end'], 2), chapter=p['chapter']) for p in P]),
          open(os.path.splitext(OUT)[0] + '_index.json', 'w'), ensure_ascii=False, indent=0)
# ---- 絵：つないで字幕を焼く（音は映像の長さで切る）
lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join("file '%s'\n" % os.path.abspath(c) for c in clips))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', aw, '-vf', 'ass=%s:fontsdir=/usr/share/fonts/opentype/noto' % ap,
                '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '24', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-g', '48',
                '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '128k', '-t', '%.3f' % T, '-movflags', '+faststart', OUT], check=True)
print('done', OUT, round(T, 2))
