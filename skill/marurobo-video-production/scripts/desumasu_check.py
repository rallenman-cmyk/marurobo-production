# 台本の台詞の語尾を調べる：「です・ます」で終わる文が何本続いているかを出す。
# python3 desumasu_check.py 台本.md [続いてよい本数=2]
# 台詞の行は「**番号** 文」の形。章（## ）をまたいでも続けて数える（声は続くので）。
import re, sys
path = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
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
