# v10 のコメントで分かった読み間違い・声の違いを、その文だけ作り直す（2026-11-13）
#   1 文ずつ 2 回読ませ → Gemini で文字起こし → 読みが合っている方を選ぶ → master_voice と同じ仕上げ（無音 0.06 秒・-18 dB・山 -1.5 dB）
#   元の master/ID.wav は master_before_v11/ に残す。声の置き場所の表（v2_voice_map.json）の dur も書き換える
import os, sys, json, base64, wave, time, shutil, urllib.request, urllib.error, io
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SP = '/tmp/claude-0/-home-user/8cc26183-437c-5f90-a7e9-3b23d7f91ab2/scratchpad'
STYLE = open(SP + '/v2gen/stage/voice_test/style_gentle.txt', encoding='utf-8').read().strip()
KEY = os.environ['GEMINI_API_KEY']
# ID → (読ませる文, 文字起こしに入っていてほしい言葉, 入っていてはいけない言葉)
LINES = {
    '07-04':   ('ここには、もじは、はいっていません。', ['ここには'], ['えっ']),
    '16-05':   ('予備で直せるのは、キューアールコードを見つけたあとに読む、箱の中身だけ。', ['予備'], []),
    '19-01c':  ('このやっつの、ゼロといちの並びで、数字がひとつ、表されています。箱ひとつに、数字がひとつ、入っているんです。', ['やっつ|八つ|8つ'], ['はっつ']),
    '19-04':   ('箱の中身を順番に並べると、エイチ、イー、エル、エル、オー。「ハロー」になりました。', ['ハロー|HELLO|はろー'], []),
    '25-06':   ('そして、すり替わった数字は、本当より、に、大きくなっていました。', ['2|に'], ['4|よん']),
    '32-09b':  ('読み取るアプリによっても、粘り強さは、少しずつ、ちがいます。', ['違います|ちがいます'], ['ちがうます']),
}
def post(model, body):
    req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % model, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'x-goog-api-key': KEY})
    for k in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=240))
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8', 'replace')
            if e.code in (429, 500, 503): time.sleep(20 * (k + 1)); continue
            raise RuntimeError(msg[:300])
    raise RuntimeError('retry over')
def tts(text):
    r = post('gemini-3.8-flash-tts', {'contents': [{'parts': [{'text': STYLE + '\n#### TRANSCRIPT\n' + text}]}],
         'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Achernar'}}}}})
    return np.frombuffer(base64.b64decode(r['candidates'][0]['content']['parts'][0]['inlineData']['data']), np.int16).astype(np.float32) / 32768, 24000
def wav_bytes(x, sr):
    b = io.BytesIO()
    with wave.open(b, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return b.getvalue()
def transcribe(x, sr):
    r = post('gemini-3.8-flash', {'contents': [{'parts': [{'text': 'この音声を、聞こえたとおりにひらがなと数字で書き起こしてください。文字起こしだけを出力。'},
                                                          {'inlineData': {'mimeType': 'audio/wav', 'data': base64.b64encode(wav_bytes(x, sr)).decode()}}]}]})
    return r['candidates'][0]['content']['parts'][0]['text'].strip()
def master(x, sr):
    h = int(sr * 0.01); n = len(x) // h; db = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12))
    act = db > db.max() - 30; on = np.where(act)[0]
    a = max(0, on[0] * h - int(0.06 * sr)); b = min(len(x), (on[-1] + 1) * h + int(0.06 * sr)); y = x[a:b].copy()
    lv = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h)[act] ** 2).mean()) + 1e-9); pk = 20 * np.log10(np.abs(y).max() + 1e-9)
    y *= 10 ** (min(-18.0 - lv, -1.5 - pk) / 20); f = int(0.01 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y
import re
M = json.load(open(SP + '/v2_voice_map.json', encoding='utf-8'))
os.makedirs(HERE + '/master_before_v11', exist_ok=True); os.makedirs(HERE + '/takes_v11', exist_ok=True)
ONLY = sys.argv[1:] or list(LINES)
rep = {}
for i in ONLY:
    text, want, bad = LINES[i]; best = None
    for take in range(3):
        x, sr = tts(text); y = master(x, sr); tr = transcribe(y, sr)
        ok = all(re.search(w, tr) for w in want) and not any(re.search(w, tr) for w in bad)
        open(HERE + '/takes_v11/%s_%d.wav' % (i, take), 'wb').write(wav_bytes(y, sr))
        print(i, take, 'OK' if ok else 'NG', round(len(y) / sr, 2), tr, flush=True)
        if ok: best = (y, sr, tr); break
    if best is None: print(i, 'NO GOOD TAKE'); continue
    y, sr, tr = best; dst = M[i]['wav']
    if not os.path.exists(HERE + '/master_before_v11/' + i + '.wav'): shutil.copy(dst, HERE + '/master_before_v11/' + i + '.wav')
    open(dst, 'wb').write(wav_bytes(y, sr)); rep[i] = dict(old=M[i]['dur'], new=round(len(y) / sr, 3), heard=tr)
    M[i]['dur'] = round(len(y) / sr, 3)
json.dump(M, open(SP + '/v2_voice_map.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(rep, open(HERE + '/regen_v11_report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('done', rep)
