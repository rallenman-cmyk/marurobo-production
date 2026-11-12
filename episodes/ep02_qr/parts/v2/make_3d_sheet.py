# 3D の描き直し用の時刻表：今の組み立て（台本 v2.0・本番の組み立て）で、3D の場面ごとに
#   通しの時刻・長さ・その間の声・寄りの量・3D の中の字の扱い をまとめる → /home/user/qr_plan/3D描き直し用_時刻表.md と .csv
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import final_build as FB, fig_anim as FA
I = json.load(open(os.path.join(HERE, 'final', 'qr_ep02_final_test_index.json'))); off = I['offsets']
FIGK = set(FB.FAMILY) | set(FB.SINGLE) | {f[:-4] for f in os.listdir(os.path.join(HERE, 'fig'))}
NAMES = {'op': '冒頭', 'c1': '1章', 'c2': '2章', 'c3': '3章', 'c4': '4章', 'c5': '5章', 'end': '結び'}
# 3D の中に字がある場面：本番では 3D の字を消し、2D の札（字幕より大きい）で見せる
TEXT3D = {'K09': '浮かぶ「HELLO」→ 3D の字は消す（2D で重ねるなら札で）', 'R_number': '「46」の板 → 3D の字は消す（2D の札「計算した数字（たとえば 46）」あり）',
          'K21': '比率の数字 1 1 3 1 1 → 消す（2D の札「1 : 1 : 3 : 1 : 1」あり）', 'K21a': '比率の数字 1 1 3 1 1 → 消す（2D の札「1 : 1 : 3 : 1 : 1」あり）', 'K22': '比率の数字 1 1 3 1 1 → 消す（2D の札あり）',
          'K30': 'マスの番号 1〜5 → 消す（次の 2D の図「定規」で見せる）', 'K32': '「予備の量」の板 → 消す（2D の札「予備の箱の数」あり）',
          'K33': '「予備の量」「柄の番号」の板 → 消す（2D の札あり）', 'K34': '「4マス」→ 消す（2D の札「まわりに 4マス以上の余白」あり）',
          'G6': '0と1のカード → 3D の字は消し、カードの白黒だけ残す（2D の札「0 0 1 0 0 0 0 0」あり）',
           'R1': '目盛りの数字 0・64・192・255 → 消す（2D の札「箱の数字：0 〜 255」あり）',
          'R3': '「リード・ソロモン符号」の看板 → 消す（2D の札あり）', 'B28d': '浮かぶ「HELLO」→ 3D の字は消す',
          'C1': '箱の数字 → 残すなら今の1.5倍以上の大きさで（2D のメモでも同じ数字を出している）', 'C2': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C2a': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C3': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C4': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C6a': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C6': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）',
          'C7': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C8': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C9': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C10': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C11': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C12a': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）', 'C12': '箱の数字 → 残すなら今の1.5倍以上（2D のメモでも同じ数字を出している）',
          'T28': 'スマホの画面の「HELLO」→ 画面いっぱいに大きく'}
fmt = lambda t: '%d:%04.1f' % (t // 60, t % 60)
rows = []
for tag in ['op', 'c1', 'c2', 'c3', 'c4', 'c5', 'end']:
    ch = FB.CH.build(tag); o = off[tag]; P = ch.P() if hasattr(ch, 'P') else []
    SH = ch.SHOTS; ends = [sh[0] for sh in SH[1:]] + [ch.T_END]
    for sh, b in zip(SH, ends):
        a, k = sh[0], sh[2]
        if k in FIGK or b - a < 0.05: continue
        z0, z1 = (sh[3], sh[4]) if len(sh) > 4 else (1.0, 1.0)
        lines = [p for p in P if p['start'] < b - 0.1 and p['end'] > a + 0.1]
        rows.append(dict(章=NAMES[tag], 絵=k, 始め=fmt(o + a), 終わり=fmt(o + b), 秒=round(b - a, 1), コマ=int(round((b - a) * 24)),
                         寄り='%.2f→%.2f' % (z0, z1) if z1 != z0 else 'なし', 声=' / '.join('%s「%s」' % (p['id'], p['text'][:22] + ('…' if len(p['text']) > 22 else '')) for p in lines),
                         字=(('看板の「1994」→ 消す（2D の札あり）') if (k == 'F1' and tag in ('c4', 'end')) else TEXT3D.get(k, ''))))
out = '/home/user/qr_plan/3D描き直し用_時刻表'
with open(out + '.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
tot = {}; 
for r in rows: tot[r['章']] = tot.get(r['章'], 0) + r['秒']
md = ['# 3D の描き直し用の時刻表（台本 v2.0・本番の組み立ての時刻）', '',
      '- 時刻は本番の組み立ての試し（全体 %s）の通しの時刻。3D の場面だけを並べた（2D の図・札の場面は入れていない）。' % fmt(I['total']),
      '- 「コマ」は 24 コマ/秒で数えた長さ。「寄り」は組み立てでゆっくり寄る量（描く側で寄らなくてよい）。',
      '- 「3D の中の字」：決まり「3D の中に字を入れない。数字・式・名前は 2D の札で、字幕より大きく」に合わせる所。PC で描くときに、この字を消す。',
      '- PC に送るのは、言われてから（この表はその準備）。', '',
      '## 章ごとの 3D の長さ', '', '| 章 | 3D の場面 | 合計 |', '|---|---|---|']
md += ['| %s | %d | %s |' % (c, sum(1 for r in rows if r['章'] == c), fmt(s)) for c, s in tot.items()]
md += ['', '## 3D の中の字を消す場面（%d 場面）' % sum(1 for r in rows if r['字']), '', '| 章 | 絵 | 時刻 | 3D の中の字 |', '|---|---|---|---|']
seen = set()
for r in rows:
    if r['字'] and r['絵'] not in seen: seen.add(r['絵']); md.append('| %s | %s | %s | %s |' % (r['章'], r['絵'], r['始め'], r['字']))
for c in tot:
    md += ['', '## %s' % c, '', '| 絵 | 始め | 終わり | 秒 | コマ | 寄り | 声 |', '|---|---|---|---|---|---|---|']
    md += ['| %s | %s | %s | %s | %d | %s | %s |' % (r['絵'], r['始め'], r['終わり'], r['秒'], r['コマ'], r['寄り'], r['声'].replace('|', '｜')) for r in rows if r['章'] == c]
open(out + '.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print(len(rows), tot)
