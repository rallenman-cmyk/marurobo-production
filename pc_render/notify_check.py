#!/usr/bin/env python3
# 🖥PC描画の係のセッションだけが使う：終わった依頼のうち、まだ頼んだセッションに知らせていないものを出す
#   python3 pc_render/notify_check.py          … 一覧を出す（JSON の行）。描画係の様子も出す
#   python3 pc_render/notify_check.py --mark <id> … 知らせ終えた印を付ける（pc_render/知らせ済み.txt。commit・push は呼ぶ側）
import subprocess, sys, json, os
os.chdir(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True).stdout.decode().strip())
F = "pc_render/知らせ済み.txt"
told = set(open(F).read().split()) if os.path.exists(F) else set()
if len(sys.argv) > 2 and sys.argv[1] == "--mark":
    told.add(sys.argv[2]); open(F, "w").write("\n".join(sorted(told)) + "\n"); sys.exit(0)
def sh(*a):
    r = subprocess.run(a, capture_output=True); return r.returncode, r.stdout.decode(errors="replace")
if sh("git", "fetch", "-q", "origin", "pc-render-status")[0]: sys.exit("印の枝を取れません")
def show(p):
    c, o = sh("git", "show", "FETCH_HEAD:" + p); return json.loads(o.lstrip("﻿")) if c == 0 and o.strip() else None
print("描画係", json.dumps(show("agent.json"), ensure_ascii=False))
for extra in ("pc_workers.json", "agent_error.json"):
    d = show(extra)
    if d: print(extra, json.dumps(d, ensure_ascii=False))
_, ls = sh("git", "ls-tree", "--name-only", "FETCH_HEAD", "done/")
for x in sorted(ls.split()):
    jid = os.path.basename(x)[:-5]
    if jid in told: continue
    d = show(x); q = "pc_render/queue/%s.json" % jid
    req = json.load(open(q)) if os.path.exists(q) else {}
    print("未連絡", json.dumps(dict(id=jid, state=d["state"], minutes=d["minutes"], session=req.get("session", ""), name=req.get("name", ""), tail=d.get("tail", [])[-6:]), ensure_ascii=False))
