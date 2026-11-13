# Google ドライブの marurobo_render（リンク共有）を見張り、指定の章がそろったら dl_pc/<章>/ に落として確かめる
#   使い方: python3 -I drive_watch.py ch07:35 ch08:6 ch06:20   （章:mp4 の本数）  → そろった章ごとに dl_pc/<章>.ok
#   ファイル名に / や先頭の . があるものは落とさない。各 mp4 は ffprobe で 1920×1080 とコマ数を確かめる
import sys, os, re, time, html, json, subprocess
ROOT_ID = "1thcAROo3WmIhr6hKVZxydPrw-X9ACjrk"
D = os.environ.get("MARU_DL") or os.path.join(os.environ.get("MARU_WORK", "."), "dl_pc")
want = dict((a.split(":")[0], int(a.split(":")[1])) for a in sys.argv[1:])
def listing(fid):
    r = subprocess.run(["curl", "-sSL", "--max-time", "60", "https://drive.google.com/embeddedfolderview?id=%s#list" % fid], capture_output=True, text=True)
    s = r.stdout
    files = re.findall(r'href="https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)/view[^"]*"[^>]*>.*?<div class="flip-entry-title">([^<]+)</div>', s, re.S)
    folders = re.findall(r'href="https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)"[^>]*>.*?<div class="flip-entry-title">([^<]+)</div>', s, re.S)
    return [(html.unescape(t), i) for i, t in files], [(html.unescape(t), i) for i, t in folders]
def frames(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=width,height,nb_read_packets", "-of", "csv=p=0", p], capture_output=True, text=True)
    return r.stdout.strip()
t_end = time.time() + float(os.environ.get("MARU_WATCH_SEC", "6600"))                # 見張る長さ（秒）
while want and time.time() < t_end:
    _, folders = listing(ROOT_ID); fmap = dict(folders)
    for ch, need in list(want.items()):
        if ch not in fmap: continue
        files, _ = listing(fmap[ch])
        mp4 = [f for f in files if f[0].endswith(".mp4")]
        if len(mp4) < need: print(time.strftime("%H:%M"), ch, "mp4", len(mp4), "/", need, flush=True); continue
        os.makedirs(os.path.join(D, ch), exist_ok=True); bad = []
        for name, fid in files:
            if "/" in name or name.startswith("."): continue
            dst = os.path.join(D, ch, name)
            if not (os.path.exists(dst) and os.path.getsize(dst) > 1000):
                subprocess.run(["curl", "-sSL", "--max-time", "600", "-o", dst, "https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t" % fid])
            if name.endswith(".mp4"):
                m = re.search(r"_(\d{4,})-(\d{4,})\.mp4$", name); info = frames(dst)
                if not m or not info.startswith("1920,1080,") or int(info.split(",")[2]) != int(m.group(2)) - int(m.group(1)) + 1: bad.append((name, info))
        if bad:
            print(time.strftime("%H:%M"), ch, "BAD", bad[:5], flush=True)
            for name, _ in bad: os.remove(os.path.join(D, ch, name))
            continue
        open(os.path.join(D, ch + ".ok"), "w").write(json.dumps([n for n, _ in files], ensure_ascii=False))
        print(time.strftime("%H:%M"), ch, "OK", len(files), "files", flush=True); del want[ch]
    if want: time.sleep(120)
print("WATCH END", "left:", list(want), flush=True)
