# 集めた検索結果をまとめて、当たり動画（ふだんの何倍か）を並べる
# python3 rank.py <channels.json> <origin.json> <出力.json> <検索結果.json…>
import json, re, sys
chans, origin, outp, *ins = sys.argv[1:]
C = json.load(open(chans)); O = json.load(open(origin))
JA = re.compile(r"[ぁ-んァ-ン一-龥]")
def secs(l):
    s = 0
    for x in (l or "0").split(":"):
        s = s * 60 + int(x)
    return s
V = {}
for f in ins:
    for q, vs in json.load(open(f))["queries"].items():
        for v in vs:
            if not v.get("views") or v["id"] in V:
                continue
            c = C.get(v.get("channel_id") or "", {})
            med = c.get("median")
            o = O.get(v["id"], {})
            V[v["id"]] = dict(v, q=q, subs=c.get("subs"), median=med, ratio=(round(v["views"] / med, 1) if med else None),
                              japanese=(o.get("japanese") if v["id"] in O else (True if JA.search(v["title"]) else False)), checked=v["id"] in O, secs=secs(v["length"]))
json.dump(list(V.values()), open(outp, "w"), ensure_ascii=False)
print("動画", len(V), "ふだんが分かる", sum(1 for v in V.values() if v["median"]), "海外と分かった", sum(1 for v in V.values() if v["checked"] and v["japanese"] is False))
