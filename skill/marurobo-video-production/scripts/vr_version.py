"""動画レビュー: 区切った版の登録データ(JSON)を作り、検証する。
使い方:
  split   SRC.mp4 OUTDIR [秒=30]    … 原本を再エンコードせず約○秒ごとに区切る
  build   SRC.mp4 OUTDIR uploaded.txt PROJECT_ID VERSION_ID NUMBER LABEL OUT.json
uploaded.txt は「ファイル名 アセットID」を1行ずつ。
"""
import hashlib, json, os, subprocess, sys

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def probe_dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).strip())

def split(src, out, secs='30'):
    os.makedirs(out, exist_ok=True)
    subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-c', 'copy', '-f', 'hls', '-hls_time', str(secs),
        '-hls_segment_type', 'fmp4', '-hls_fmp4_init_filename', 'init.mp4',
        '-hls_segment_filename', os.path.join(out, 'seg%03d.mp4'), '-hls_playlist_type', 'vod', os.path.join(out, 'index.m3u8')])
    big = [f for f in os.listdir(out) if os.path.getsize(os.path.join(out, f)) > 19 * 1024 * 1024]
    if big: sys.exit('20MiB を超える区切りがあります: %s' % big)
    print('ok', len(os.listdir(out)) - 1, 'files')

def build(src, out, up, pid, vid, num, label, dst):
    ids = dict(l.split() for l in open(up) if l.strip())
    segs, t, name_dur = [], 0.0, None
    for l in open(os.path.join(out, 'index.m3u8')):
        l = l.strip()
        if l.startswith('#EXTINF:'): name_dur = float(l[8:].rstrip(','))
        elif l and not l.startswith('#'):
            p = os.path.join(out, l)
            if l not in ids: sys.exit('未登録の区切り: ' + l)
            segs.append({'i': len(segs), 'file': l, 'url': '/_blob/' + ids[l], 'id': ids[l], 'start': round(t, 6),
                         'dur': name_dur, 'size': os.path.getsize(p), 'sha256': sha(p)})
            t += name_dur
    total = probe_dur(src)
    if abs(t - total) > 0.1: sys.exit('区切りの合計 %.3f 秒が原本 %.3f 秒と合いません' % (t, total))
    doc = {'project_id': pid, 'number': int(num), 'label': label, 'status': 'validating', 'duration': round(total, 3),
           'segment_count': len(segs), 'segments': segs,
           'init': {'url': '/_blob/' + ids['init.mp4'], 'id': ids['init.mp4'], 'sha256': sha(os.path.join(out, 'init.mp4'))},
           'source': {'filename': os.path.basename(src), 'sha256': sha(src), 'size': os.path.getsize(src), 'duration': round(total, 3)}}
    json.dump(doc, open(dst, 'w'), ensure_ascii=False, indent=1)
    print('ok', vid, len(segs), 'segments', '%.3f s' % total, 'sum %.3f' % t)

if __name__ == '__main__':
    {'split': split, 'build': build}[sys.argv[1]](*sys.argv[2:])
