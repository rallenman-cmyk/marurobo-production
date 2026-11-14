# 台本の台詞の語尾を調べる：「です・ます」で終わる文が何本続いているかを出す。
# 使い分けの決まりは SKILL.md §4（説明は です・ます、反応はくだけて）。これは続きすぎを見つける手助けだけ。
# python3 desumasu_check.py 台本.md [続いてよい本数=5]
# もう一つ：同じ語尾の形（〜でしょう・〜ました など）が 3 本続く所も出す（ロボットではありません回 v0.3「しょうの語尾が3連続」）。
# 台詞の行は「**番号** 文」の形。章（## ）をまたいでも続けて数える（声は続くので）。
import re, sys
path = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
POLITE = re.compile(r'(です|ます|でした|ました|ません|でしょう|ましょう|ください)(か|ね|よ|けど|けどね|よね)?[。？！?!]*$')
rows = []
for ln in open(path, encoding='utf-8'):
    m = re.match(r'\*\*(\S+)\*\*\s*(.+)', ln.strip())
    if not m:
        continue
    text = re.sub(r'【[^】]*】', '', m.group(2)).strip()
    last = re.split(r'(?<=[。？！])', text)
    last = [s for s in last if s.strip()][-1].strip() if text else ''
    rows.append((m.group(1), text, bool(POLITE.search(last))))
run = []
bad = 0
total_p = sum(r[2] for r in rows)
for r in rows + [(None, '', False)]:
    if r[2]:
        run.append(r)
        continue
    if len(run) > limit:
        bad += 1
        print('%d 本続く: %s 〜 %s' % (len(run), run[0][0], run[-1][0]))
        for x in run:
            print('   ', x[0], x[1])
    run = []
print('台詞 %d 本のうち、です・ますで終わる文 %d 本（%d%%）。%d 本より長く続く所 %d か所' % (
    len(rows), total_p, 100 * total_p // max(1, len(rows)), limit, bad))

# 同じ語尾の音が 3 本続く所（耳で聞くので、文の最後の 2 文字で比べる：「でしょう」「ましょう」は同じ「ょう」、「ました」「でした」は同じ「した」）
def ending(t):
    t = re.sub(r'[。？！?!」』…\s]+$', '', t)
    return t[-2:] if len(t) >= 2 else None
same = 0
for i in range(len(rows) - 2):
    es = [ending(r[1]) for r in rows[i:i + 3]]
    if es[0] and es[0] == es[1] == es[2]:
        same += 1
        print('同じ語尾「%s」が 3 本: %s %s %s' % (es[0], rows[i][0], rows[i + 1][0], rows[i + 2][0]))
print('同じ語尾が 3 本続く所 %d か所' % same)

# 「しょう」の音（〜でしょう？・〜ましょう）は、2 本続いただけで耳に残る（5本目 台本 v0.1「しょうの語尾が連続してる」）。2 本続く所も出す。
shou = 0
for i in range(len(rows) - 1):
    a, b = ending(rows[i][1]), ending(rows[i + 1][1])
    if a == b == 'ょう':
        shou += 1
        print('「しょう」が 2 本続く: %s %s' % (rows[i][0], rows[i + 1][0]))
print('「しょう」が 2 本続く所 %d か所' % shou)
