# 説明書き（# のあと）の中に、動きや音の指示が入ってしまった行を探す（16本目 2章の 2 回目の点検）
#   行の終わりに説明書きを足したまま、その行の後ろに「; ev(...)」「; sh_key(...)」をつないだため、2 か所で扉の音と影の動きが効いていなかった。
#   python3 comment_code_check.py <ファイル.py> ...   見つけた行を出す。0 行になるまで直す（描く前に必ず通す）
import re, sys
CALLS = r";\s*(sh_key|key|ev|door_key|light_key|hide_key|M\.\w+|pop_lock|track|add|L\.append|cube|cyl)\("
n = 0
for p in sys.argv[1:]:
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        q = None; ins = None
        for j, ch in enumerate(l):
            if ins is None and ch in "\"'": ins = ch
            elif ins is not None and ch == ins: ins = None
            elif ch == "#" and ins is None: q = j; break
        if q is not None and re.search(CALLS, l[q:]):
            print("%s:%d  説明書きの中に指示：%s" % (p, i, l[q:q + 160].rstrip())); n += 1
print("説明書きの中の指示：%d 行" % n)
sys.exit(1 if n else 0)
