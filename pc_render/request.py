#!/usr/bin/env python3
# PC の描画係に、描画を頼む（クラウドの各回のセッションが使う）
#   python3 pc_render/request.py <一式の zip> --ps1 run_pc_render_ep05.ps1 --name ep05_v3 [--only S10a,S11a] [--order 5] [--workers 3] [--samples 24]
#   やること：1) zip を GitHub の枝 pc-kit/<id> に 1 つだけ入れて push（main の枝は重くしない）
#             2) 依頼票 pc_render/queue/<id>.json を作って commit・fetch・rebase・push
#   --only を付けると「短い直し」（先に描かれる）。付けないと「全部描き」。順番：短い直し → --order の小さい順 → 受付の順
#   終わったかどうかは python3 pc_render/status.py <id>。動画は今までどおり Google ドライブ marurobo_render（scripts/drive_watch.py）
#   zip は各回の pc_kit/make_kit.sh で作る（PC では C:\marurobo に広げ、--ps1 の手順をそのまま走らせる）
import argparse, subprocess, os, sys, json, datetime, re, time

def sh(*a, inp=None, check=True):
    r = subprocess.run(a, input=inp, capture_output=True)
    if check and r.returncode: sys.exit("失敗：%s\n%s" % (" ".join(a), r.stderr.decode(errors="replace")))
    return r.stdout.decode().strip()

ap = argparse.ArgumentParser()
ap.add_argument("zip"); ap.add_argument("--ps1", required=True); ap.add_argument("--name", required=True, help="回と版。例 ep05_v3")
ap.add_argument("--only", default=""); ap.add_argument("--order", type=int, default=0)
ap.add_argument("--workers", type=int, default=0); ap.add_argument("--samples", type=int, default=0)
ap.add_argument("--fresh", action="store_true", help="同じ出力フォルダに残っている前の絵を捨ててから描く（同じ版の名前で描き直すときは必ず付ける）")
ap.add_argument("--replace", default="", help="置きかえる前の依頼の id（その依頼票を消す。描いている途中なら止まる）")
ap.add_argument("--session", default="", help="頼んだセッションの名前（記録用）")
A = ap.parse_args()
ok = re.compile(r"^[A-Za-z0-9_.-]+$")
zname = os.path.basename(A.zip)
for v, what in ((A.name, "--name"), (A.ps1, "--ps1"), (zname, "zip の名前")):
    if not ok.match(v): sys.exit("%s は半角の英数字と _ . - だけにしてください：%s" % (what, v))
if A.order < 0: sys.exit("--order は 1 以上")
if A.only and not re.match(r"^[A-Za-z0-9_,.-]+$", A.only): sys.exit("--only はカットの名前をカンマで区切る（空白なし）")
if not os.path.isfile(A.zip): sys.exit("zip がありません：" + A.zip)
mb = os.path.getsize(A.zip) / 1e6
if mb > 90: sys.exit("zip が大きすぎます（%.0f MB）。動画や声を入れていないか確かめてください" % mb)
root = sh("git", "rev-parse", "--show-toplevel"); os.chdir(root)
branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
now = datetime.datetime.now(datetime.timezone.utc)
jid = "%s-%s" % (now.strftime("%Y%m%d-%H%M%S"), A.name)
kb = "pc-kit/" + jid
# 1) zip だけの枝（親なしの 1 コミット）
blob = sh("git", "hash-object", "-w", A.zip)
tree = sh("git", "mktree", inp=("100644 blob %s\t%s\n" % (blob, zname)).encode())
com = sh("git", "commit-tree", tree, "-m", "PC の一式 " + jid)
for i in range(4):
    r = subprocess.run(["git", "push", "-q", "origin", "%s:refs/heads/%s" % (com, kb)])
    if r.returncode == 0: break
    time.sleep(2 ** (i + 1))
else: sys.exit("一式の枝を push できませんでした")
# 頼む量（コマ数）を、zip の中の手順（JOBS）から数える。描画係が「小さな直しだけ割り込ませる」のに使う
frames = 0; outdir = ""
try:
    import zipfile
    z = zipfile.ZipFile(A.zip)
    nm = [n for n in z.namelist() if n.endswith("/" + A.ps1) or n == A.ps1]
    txt = z.read(nm[0]).decode("utf-8-sig", "replace") if nm else ""
    jobs = {a: int(b) for a, b in re.findall(r'@\("([A-Za-z0-9_]+)",\s*(\d+),', txt)}
    want = [c for c in A.only.split(",") if c] if A.only else list(jobs)
    miss = [c for c in want if c not in jobs]
    if A.only and jobs and miss: sys.exit("--only のカットが手順にありません：" + ",".join(miss))
    frames = sum(jobs.get(c, 0) for c in want)
    m = re.search(r'\$out = Join-Path \$root "([A-Za-z0-9_.-]+)"', txt); outdir = m.group(1) if m else ""
except SystemExit: raise
except Exception: frames = 0
# 歯止め：同じ出力フォルダを使う依頼が前にあるのに --fresh が無い（古い絵が混ざる）／同じ名前の依頼がまだ待ち行列にある（二重）
import glob
sh("git", "fetch", "-q", "origin", "pc-render-status", check=False)
fin = set(os.path.basename(x)[:-5] for x in subprocess.run(["git", "ls-tree", "--name-only", "FETCH_HEAD", "done/"], capture_output=True).stdout.decode().split())
for f in sorted(glob.glob("pc_render/queue/*.json")):
    try: o = json.load(open(f))
    except Exception: continue
    if o.get("id") == jid: continue
    waiting = o.get("id") not in fin
    if waiting and o.get("name") == A.name and A.replace != o.get("id"):
        sys.exit("同じ名前の依頼がまだ待っています：%s\n出し直すなら --replace %s を付ける（前の依頼を取り消して置きかえる）" % (o["id"], o["id"]))
    same_out = outdir and (o.get("out") == outdir or (not o.get("out") and o.get("ps1") == A.ps1 and o.get("name") == A.name))
    if same_out and not A.fresh:
        sys.exit("出力フォルダ %s は、前の依頼（%s）でも使っています。同じフォルダで描き直すなら --fresh を付ける（前の絵を捨ててから描く）。付けないと古い絵が混ざります" % (outdir, o["id"]))
if A.replace:
    rp = "pc_render/queue/%s.json" % A.replace
    if os.path.exists(rp): sh("git", "rm", "-q", rp)
# 2) 依頼票
job = dict(id=jid, name=A.name, kit_branch=kb, zip=zname, ps1=A.ps1, only=A.only, kind="fix" if A.only else "full",
           order=A.order, frames=frames, fresh=A.fresh, out=outdir, workers=A.workers, samples=A.samples, session=A.session, created=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
p = "pc_render/queue/%s.json" % jid
os.makedirs("pc_render/queue", exist_ok=True)
json.dump(job, open(p, "w"), ensure_ascii=True, indent=1)
sh("git", "add", p); sh("git", "commit", "-q", "-m", "PC 描画の依頼：%s%s" % (A.name, "（" + A.only + "）" if A.only else ""))
for i in range(4):
    sh("git", "fetch", "-q", "origin", branch); sh("git", "rebase", "-q", "origin/" + branch)
    if subprocess.run(["git", "push", "-q", "origin", branch]).returncode == 0: break
    time.sleep(2 ** (i + 1))
else: sys.exit("依頼票を push できませんでした（一式の枝は push 済み）")
print("頼みました：%s（%s・一式 %.1f MB）\n終わったかどうか：python3 pc_render/status.py %s" % (jid, "短い直し" if A.only else "全部描き", mb, jid))
