# YouTube のチャンネルの「動画」ページ（新しい順）から、登録者数と、最近の動画（最大 30 本）の題・再生回数を取る
# ふだん＝最近の動画の再生回数の中央値。
# 2026-11-17 直した：前の版は「1.6万回視聴」「33万回視聴」の形を読めず、1万回未満の動画だけで中央値を出していた
#   （大きめのチャンネルで「ふだん」が低く出て、「倍」が高く出ていた）。題と再生の組み合わせもずれることがあった。
# python3 yt_channel.py <入力：検索結果.json…> <出力.json> [--min 再生回数]   （その再生回数以上の動画のチャンネルだけ調べる）
import json, re, sys, time, statistics
from concurrent.futures import ThreadPoolExecutor
import requests

H = {"Accept-Language": "ja", "User-Agent": "Mozilla/5.0"}
LABEL = re.compile(r'"accessibilityLabel":\s*"([\d,.]+)\s*(万|億)?\s*回視聴"')


def _walk(o, key, out):
    if isinstance(o, dict):
        if key in o:
            out.append(o[key])
        for v in o.values():
            _walk(v, key, out)
    elif isinstance(o, list):
        for v in o:
            _walk(v, key, out)


def channel(cid):
    html = requests.get(f"https://www.youtube.com/channel/{cid}/videos?hl=ja&gl=JP", headers=H, timeout=30).text
    subs = None
    m = re.search(r"チャンネル登録者数\s*([\d.]+)\s*(万|億)?人", html)
    if m:
        subs = int(float(m.group(1)) * {"万": 1e4, "億": 1e8}.get(m.group(2), 1))
    name = re.search(r'<meta property="og:title" content="(.*?)"', html)
    vids = []
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if m:
        locks = []
        _walk(json.loads(m.group(1)), "lockupViewModel", locks)
        for l in locks:
            md = l.get("metadata", {}).get("lockupMetadataViewModel", {})
            title = md.get("title", {}).get("content")
            lab = LABEL.search(json.dumps(md, ensure_ascii=False))
            if not (title and lab):
                continue
            views = int(float(lab.group(1).replace(",", "")) * {"万": 1e4, "億": 1e8}.get(lab.group(2), 1))
            age = re.search(r'"content":\s*"(\d+\s*(?:秒|分|時間|日|週間|か月|ヶ月|年)前)"', json.dumps(md, ensure_ascii=False))
            vids.append({"id": l.get("contentId"), "title": title, "views": views, "published": age.group(1) if age else None})
    views = [v["views"] for v in vids[:30]]
    return {"name": name.group(1) if name else None, "subs": subs, "recent": vids[:30], "median": statistics.median(views) if views else None, "v": 2}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mn = 0
    if "--min" in sys.argv:
        mn = int(sys.argv[sys.argv.index("--min") + 1]); args.remove(str(mn))
    *ins, outp = args
    try:
        cache = json.load(open(outp))
    except Exception:
        cache = {}
    ids = set()
    for f in ins:
        for vs in json.load(open(f))["queries"].values():
            for v in vs:
                if v.get("channel_id") and (v.get("views") or 0) >= mn:
                    ids.add(v["channel_id"])
    todo = [c for c in ids if cache.get(c, {}).get("v") != 2]

    def work(c):
        try:
            r = channel(c)
        except Exception as e:
            r = {"error": str(e), "v": 2}
        time.sleep(1.0)
        return c, r

    with ThreadPoolExecutor(3) as ex:
        for n, (c, r) in enumerate(ex.map(work, todo)):
            cache[c] = r
            if n % 30 == 29:
                json.dump(cache, open(outp, "w"), ensure_ascii=False)
    json.dump(cache, open(outp, "w"), ensure_ascii=False)
    print("チャンネル", len(ids), "新しく調べた", len(todo))
