# 台本 v2.0 の声の仕上げ：①頭と終わりの無音を 0.06 秒に ②途中の 1.2 秒を超える間は 0.75 秒に（「……」「（間）」のある文はそのまま）
#   ③声の部分の大きさを -18 dB にそろえる（山は -1.5 dB まで）④頭と終わりに 10ms のフェード。元の声は残し、master/ID.wav に書く
import json, wave, os, numpy as np
SP = '/tmp/claude-0/-home-user/8cc26183-437c-5f90-a7e9-3b23d7f91ab2/scratchpad'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'master')
M = json.load(open(SP + '/v2_voice_map.json'))
json.dump(M, open(SP + '/v2_voice_map_before_master.json', 'w'), ensure_ascii=False, indent=0)
TARGET, PEAK, PAD, MAXGAP, NEWGAP = -18.0, -1.5, 0.06, 1.2, 0.75
rep = []
for i, m in M.items():
    with wave.open(m['wav']) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    h = int(sr * 0.01); n = len(x) // h; r = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12); db = 20 * np.log10(r)
    act = db > db.max() - 30; on = np.where(act)[0]
    a = max(0, on[0] * h - int(PAD * sr)); b = min(len(x), (on[-1] + 1) * h + int(PAD * sr)); y = x[a:b]
    if '……' not in m['text'] and '（間）' not in m['text']:
        sil = db < db.max() - 38; k = on[0]; cuts = []
        while k < on[-1]:
            if sil[k]:
                j = k
                while j < on[-1] and sil[j]: j += 1
                if (j - k) * 0.01 > MAXGAP: cuts.append((k * h - a, j * h - a))
                k = j
            else: k += 1
        for c0, c1 in reversed(cuts):
            keep = int(NEWGAP * sr); mid0 = c0 + keep // 2; mid1 = c1 - keep // 2
            y = np.concatenate([y[:mid0], y[mid1:]])
    act_lv = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h)[act] ** 2).mean()) + 1e-9)
    g = TARGET - act_lv; pk = 20 * np.log10(np.abs(y).max() + 1e-9)
    g = min(g, PEAK - pk); y = y * (10 ** (g / 20))
    f = int(0.01 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    p = os.path.join(OUT, i + '.wav')
    with wave.open(p, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    rep.append((i, round(m['dur'], 2), round(len(y) / sr, 2), round(g, 1)))
    m.update(wav=p, dur=round(len(y) / sr, 3), raw=m.get('raw', m['wav']) if False else m['wav'])
for m in M.values(): pass
json.dump(M, open(SP + '/v2_voice_map.json', 'w'), ensure_ascii=False, indent=0)
d0 = sum(r[1] for r in rep); d1 = sum(r[2] for r in rep)
print('lines', len(rep), 'voice %.1f s -> %.1f s' % (d0, d1), 'gain range', min(r[3] for r in rep), max(r[3] for r in rep))
