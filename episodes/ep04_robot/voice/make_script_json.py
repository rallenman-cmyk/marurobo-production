# 台本 v1.0（md）→ 声づくり用の台本 json（make_narration.py・split_narration.py・narration.py が読む形）
# python3 make_script_json.py <台本.md> <出力 json>
#   no（1 から）・id（台本の番号）・scene・text（字幕に出す元の台詞）・tts（読ませる文）・start/end（仮の時刻）・gap_before（場面が変わる文は 0.78）
import sys, re, json
from yomi_robot import yomi
md, out = sys.argv[1], sys.argv[2]
L, scene, prev_scene, t = [], None, None, 0.0
for ln in open(md, encoding='utf-8'):
    s = ln.strip()
    if s.startswith('### '):
        scene = s[4:].split('　')[0]
    m = re.match(r'^\*\*(\d\d-\d\d[0-9a-z]*)\*\*\s*(.*?)\s*$', s)
    if not m:
        continue
    text = re.sub(r'【[^】]*】', '', m.group(2)).strip()
    gap = 0.78 if scene != prev_scene and L else 0.0
    t += gap + 0.35
    dur = 0.17 * len(text) + 0.4
    L.append(dict(no=len(L) + 1, id=m.group(1), scene=scene, text=text, tts=yomi(text), start=round(t, 2), end=round(t + dur, 2), **({'gap_before': gap} if gap else {})))
    t += dur
    prev_scene = scene
json.dump(L, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(L), '文', '仮の長さ %.0f 秒' % t)
