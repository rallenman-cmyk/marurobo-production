# 台本の md（台本_vX_Y.md）から、台本レビューツール（https://claude.ai/artifact/3kj4tZtaZWwbvig7GmEs4c）に入れる版のデータを作る
# python3 build_from_md.py <台本.md> <PID> <番号> <ラベル> <based_on または -> <作った時刻 UTC> "<変えた所>"
# 出力：version_<ラベル>.json（collection versions、doc_id = <PID>-v<番号の形>）
import json, hashlib, re, sys, os

md_path, PID, NUM, LABEL, BASED, AT, NOTE = sys.argv[1:8]
here = os.path.dirname(os.path.abspath(__file__))
txt = open(md_path, encoding='utf-8').read()
blocks = []
n = 0


def c(ch, raw):
    global n
    n += 1
    blocks.append({'i': len(blocks), 'k': 'c', 'id': 'N%03d' % n, 'ch': ch, 'raw': raw})


lines = txt.split('\n')
# 見出しの下の説明（最初の --- まで）
head = []
i = 1
while i < len(lines) and lines[i].strip() != '---':
    if lines[i].strip():
        head.append(lines[i].rstrip().rstrip(' '))
    i += 1
ch = '冒頭'
c(ch, '\n'.join(h.strip() for h in head))
scene = None


def flush():
    global scene
    if scene:
        c(ch, scene[0] + ('\n' + '\n'.join(scene[1]) if scene[1] else ''))
        scene = None


tail = []
in_tail = False
for ln in lines[i:]:
    s = ln.strip()
    if s.startswith('## '):
        flush()
        title = s[3:].strip()
        if title.startswith('確認すること') or title.startswith('決めたこと') or title.startswith('決めてほしいこと'):
            in_tail = True
            tail.append(title)
            continue
        in_tail = False
        ch = re.split(r'[（　]', title)[0] or title
        c(ch, title)
    elif in_tail:
        if s and not re.match(r'^\|\s*-', s):
            tail.append(s)
    elif s.startswith('### '):
        flush()
        scene = [s[4:].strip(), []]
    elif s.startswith('- ') and scene is not None:
        scene[1].append(s[2:])
    else:
        m = re.match(r'^\*\*(\d\d-\d\d[0-9a-z.]*)\*\*\s*(.*?)\s*$', s)
        if m:
            flush()
            bid, body = m.group(1), m.group(2)
            tags_full = re.findall(r'【([^】]*)】', body)
            text = re.sub(r'【[^】]*】', '', body).strip()
            tags = sorted({t.split('：')[0] for t in tags_full})
            note = '　'.join(t for t in tags_full if '：' in t)
            blocks.append({'i': len(blocks), 'k': 'd', 'id': bid, 'ch': ch, 'sp': 'ナレーション', 'tags': tags, 'note': note, 'text': text})
flush()
if tail:
    c('付記', '\n'.join(tail))

d = [b for b in blocks if b['k'] == 'd']
ids = [b['id'] for b in d]
assert len(ids) == len(set(ids)), 'ID がかぶっている'
for b in d:
    assert len(b['text']) <= 50, ('50字こえ', b['id'], len(b['text']))
sha = hashlib.sha256(txt.encode()).hexdigest()
vid_suffix = 'v' + LABEL.split('（')[0].lstrip('v').replace('.', '_')
VID = f'{PID}-{vid_suffix}'
ver = {'project': PID, 'number': int(NUM), 'label': LABEL, 'based_on': None if BASED == '-' else BASED, 'created_at': AT, 'created_by': 'ai',
       'dialogue_count': len(d), 'chapter_count': len({b['ch'] for b in blocks}), 'blocks': blocks, 'change_note': NOTE,
       'file': 'episodes/ep04_robot/' + os.path.basename(md_path), 'sha256': sha}
out = os.path.join(here, f'version_{vid_suffix[1:]}.json')
json.dump(ver, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(VID, 'lines', len(d), 'blocks', len(blocks), 'chars', sum(len(b['text']) for b in d), out)
