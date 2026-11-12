# 台本の直しを元の SRT に当てて、直した SRT を作る（声を作るとき・字幕を焼くときはこちらを使う）
#   使い方: python3 make_srt_rev.py 元.srt 直し.json 出力.srt
#   直し.json: [{"span": [始め, 終わり], "lines": [[始め, 終わり, "文"], ...], "why": "..."}, ...]（秒）。span の中で始まる元の文は消して、lines に入れ替える
import json, sys


def sec(x):
    hh, mm, rr = x.strip().split(":"); s_, ms = rr.split(","); return int(hh) * 3600 + int(mm) * 60 + int(s_) + int(ms) / 1000


def stamp(x):
    ms = int(round(x * 1000)); return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def read_srt(path):
    out = []
    for b in open(path, encoding="utf-8").read().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3 or " --> " not in L[1]: continue
        a, c = L[1].split(" --> "); out.append((sec(a), sec(c), " ".join(L[2:])))
    return out


def apply(lines, fixes):
    for fx in fixes:
        a0, a1 = fx["span"]
        lines = [l for l in lines if not (a0 <= l[0] < a1)] + [tuple(x) for x in fx["lines"]]
    return sorted(lines)


if __name__ == "__main__":
    src, fx, dst = sys.argv[1:4]
    L = apply(read_srt(src), json.load(open(fx, encoding="utf-8")))
    open(dst, "w", encoding="utf-8").write("\n\n".join("%d\n%s --> %s\n%s" % (i + 1, stamp(a), stamp(c), t) for i, (a, c, t) in enumerate(L)) + "\n")
    print(dst, len(L), "lines")
