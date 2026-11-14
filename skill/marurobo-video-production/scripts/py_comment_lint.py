# Python の行の途中の説明（#）のあとに、処理らしきもの（; のあとに代入や呼び出し）が続いていないかを探す
import sys, io, tokenize, re
bad = 0
for p in sys.argv[1:]:
    try: toks = list(tokenize.generate_tokens(io.StringIO(open(p, encoding='utf-8').read()).readline))
    except Exception as e: print(p, 'tokenize error', e); continue
    for t in toks:
        if t.type == tokenize.COMMENT and re.search(r';\s*[A-Za-z_][\w\.\[\]\'"]*\s*(=|\.\w+\(|\()', t.string):
            print('%s:%d: %s' % (p, t.start[0], t.string[:120])); bad += 1
print('NG' if bad else 'OK', bad)
