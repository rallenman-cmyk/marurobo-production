# YouTube のチャンネルの「動画」ページから、登録者数と、最近の動画の再生回数（ふだんの再生＝中央値）を取る
# python3 yt_channel.py <入力：検索結果.json…> <出力.json>
import json, re, sys, time, statistics
import requests
from yt_search import H, parse_views, txt

def walk_any(o):
    if isinstance(o, dict):
        if "videoRenderer" in o:
            yield o["videoRenderer"]
        for v in o.values():
            yield from walk_any(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_any(v)

def channel(cid):
    html = requests.get(f"https://www.youtube.com/channel/{cid}/videos?hl=ja&gl=JP", headers=H, timeout=30).text
    subs = None
    m = re.search(r"チャンネル登録者数\s*([\d.]+)\s*(万|億)?人", html)
    if m:
        subs = int(float(m.group(1)) * {"万": 1e4, "億": 1e8}.get(m.group(2), 1))
    # 今のページは lockupViewModel の形。題と「N回視聴」を順に拾う
    titles = re.findall(r'"lockupMetadataViewModel":\{"title":\{"content":"(.*?)"\}', html)
    views = [int(x.replace(",", "")) for x in re.findall(r'"accessibilityLabel":"([\d,]+)\s*回視聴"', html)]
    vids = [{"title": a, "views": b} for a, b in zip(titles, views)]
    return {"subs": subs, "recent": vids[:30], "median": statistics.median(views[:30]) if views else None}

if __name__ == "__main__":
    *ins, outp = sys.argv[1:]
    try:
        cache = json.load(open(outp))
    except Exception:
        cache = {}
    ids = set()
    for f in ins:
        d = json.load(open(f))
        for vs in d["queries"].values():
            for v in vs:
                if v.get("channel_id"):
                    ids.add(v["channel_id"])
    todo = [c for c in ids if c not in cache]
    for i, c in enumerate(todo):
        try:
            cache[c] = channel(c)
        except Exception as e:
            cache[c] = {"error": str(e)}
        if i % 10 == 9:
            json.dump(cache, open(outp, "w"), ensure_ascii=False)
        time.sleep(1.2)
    json.dump(cache, open(outp, "w"), ensure_ascii=False)
    print("channels", len(cache), "new", len(todo))
