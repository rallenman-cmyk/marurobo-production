#!/usr/bin/env python3
# PC の描画係の様子と、頼んだ描画が終わったかを見る（クラウドの各回のセッションが使う）
#   python3 pc_render/status.py            … 描画係の様子と、待ち行列・終わった依頼の一覧
#   python3 pc_render/status.py <id>       … その依頼だけ。終了コード：0＝終わった、1＝まだ、2＝そろわなかった（tail を読む）
import subprocess, sys, json, os

def sh(*a):
    r = subprocess.run(a, capture_output=True); return r.returncode, r.stdout.decode(errors="replace")

os.chdir(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True).stdout.decode().strip())
c, _ = sh("git", "fetch", "-q", "origin", "pc-render-status")
if c: sys.exit("印の枝 pc-render-status を取れません")
def show(path):
    c, o = sh("git", "show", "FETCH_HEAD:" + path); return json.loads(o.lstrip("\ufeff")) if c == 0 and o.strip() else None
ag = show("agent.json")
print("描画係：" + ("%s（%s 時点・PC の時計）%s" % (ag["state"], ag["at"], " いま：" + ag["job"] if ag.get("job") else "") if ag else "まだ一度も動いていません"))
if ag and ag.get("waiting"): print("待ち：" + "、".join(ag["waiting"]))
_, ls = sh("git", "ls-tree", "--name-only", "FETCH_HEAD", "done/")
done = {os.path.basename(x)[:-5]: x for x in ls.split() if x.endswith(".json")}
if len(sys.argv) > 1:
    jid = sys.argv[1]
    if jid not in done: print("%s：まだ終わっていません" % jid); sys.exit(1)
    d = show(done[jid]); print("%s：%s（%s・%s 分）" % (jid, "終わりました" if d["state"] == "done" else "そろいませんでした", d["finished"], d["minutes"]))
    if d["state"] != "done": print("\n".join(d.get("tail", []))); sys.exit(2)
    sys.exit(0)
for jid in sorted(done):
    d = show(done[jid]); print("  %s：%s（%s）" % (jid, "終わり" if d["state"] == "done" else "そろわず", d["finished"]))
