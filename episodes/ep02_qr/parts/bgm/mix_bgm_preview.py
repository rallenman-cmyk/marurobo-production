# 試しのBGMを冒頭の確認用動画（v2）に入れて、声・足音と一緒に聞けるようにする
#   python3 mix_bgm_preview.py bgm.wav out.mp4
#   BGMはくり返して冒頭の長さに。声の間は6dB下げる（EP01と同じ）。曲の大きさは効果音より少し小さく
import sys, os, json, subprocess, wave
import numpy as np
WORK = os.environ['MARU_WORK']; sys.path.insert(0, WORK + '/tools'); sys.path.insert(0, '/home/user/qr_plan/parts/opening')
import narration as NA, overlay2d as O2, marumotion as mm, op_plan
from op_timeline import *
SR = 48000; n = int(T_END * SR)
def load(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
bgm = load(sys.argv[1]); reps = int(np.ceil(n / len(bgm))) + 1
fade = int(0.03 * SR); x = bgm.copy(); x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
music = np.tile(x, reps)[:n]; music[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
music *= 0.16 / (np.sqrt(np.mean(music ** 2)) + 1e-9) * 0.5          # 曲の大きさ（RMS 0.08）
sfx = np.zeros(n, np.float32); pl = op_plan.plan(); mm.simulate(pl, fps=24)
for e in pl.events:
    if e['kind'] in ('step', 'step_turn', 'land'):
        s = O2.thump(0.22 * e.get('strength', 1.0), dur=0.07, f=170.0, click=0.45); i = int(e['t'] * SR); sfx[i:i + len(s)] += s[:max(0, n - i)]
for a, s in SCREEN:
    if s == 'hello' and 0 < a < 40:
        c = O2.chime(0.10); i = int(a * SR); sfx[i:i + len(c)] += c[:max(0, n - i)]
P = json.load(open(WORK + '/stage/voice/achernar/placement.json'))
bus = music + sfx
mix = NA.mix_voice(bus, 0.0, P=P, bus_peak=0.40, duck_db=6)
tmp = sys.argv[2] + '.wav'
with wave.open(tmp, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.environ.get('MARU_ANIM', '/home/user/qr_plan/parts/opening/animatic/qr_opening_animatic_v3.mp4'), '-i', tmp,
                '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-af', 'loudnorm=I=-16:TP=-1.5', sys.argv[2]], check=True)
os.remove(tmp); print('ok', sys.argv[2])
