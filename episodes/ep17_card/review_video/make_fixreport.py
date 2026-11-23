# 16本目（7本目から写した）：直しの対応表（fixreports）を作る。コメントの時刻を、字幕の id を手がかりに新しい版の時刻へ置きかえる
# 使い方：python3 make_fixreport.py OLD_VERSION.json NEW_VERSION.json COMMENTS_DIR EXPLAIN.json OUT.json FROM_ID TO_ID 作った日時
#   EXPLAIN.json：{"コメントid": "直したこと", ...}
import json, os, sys, glob
old, new, cdir, exf, out, fr, to, at = sys.argv[1:9]
O = json.load(open(old, encoding="utf-8"))["subs"]; N = {s["id"]: s for s in json.load(open(new, encoding="utf-8"))["subs"]}
EX = json.load(open(exf, encoding="utf-8"))


def remap(t):
    if t is None: return None
    prev = [s for s in O if s["t0"] <= t]
    if not prev: return round(t, 1)
    s = prev[-1]
    if s["id"] not in N: return round(t, 1)
    n = N[s["id"]]; k = min(t - s["t0"], n["t1"] - n["t0"] + 0.8)   # 文の中の何秒目か（文のあとの間は少しまで）
    return round(n["t0"] + k, 1)


items = []
for f in sorted(glob.glob(os.path.join(cdir, "*.json"))):
    c = json.load(open(f, encoding="utf-8")); c = c.get("data", c); cid = os.path.basename(f)[:-5]
    items.append(dict(action="fixed", comment_id=cid, comment_rev=c.get("rev", 1), explain=EX[cid], new_t=remap(c.get("t")), new_t_end=remap(c.get("t_end")),
                      new_version_id=to, original_t=c.get("t"), original_t_end=c.get("t_end"), original_text=c.get("text"), reason=""))
items.sort(key=lambda x: (x["original_t"] is not None, x["original_t"] or 0))
json.dump(dict(created_at=at, created_by="ai", from_version=fr, to_version=to, project_id=fr.rsplit("-", 1)[0], items=items),
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out, len(items))
