# YouTube の検索結果ページ（日本向け）から、動画の題・再生回数・公開時期・長さ・チャンネルを抜き出す（ネタの需要調べ用）
# python3 yt_search.py <出力.json> "<検索語1>" "<検索語2>" ... [--sort views]
# 公開ページを少しずつ読む（1 件ごとに 1.5 秒あける）。数字は取った日のスナップショット
import json, re, sys, time, urllib.parse, datetime
import requests

H = {"Accept-Language": "ja", "User-Agent": "Mozilla/5.0"}
SP_VIEWS = "CAM%253D"  # 再生回数の多い順


def parse_views(t):
    if not t:
        return None
    t = t.replace(",", "").replace("回視聴", "").replace("視聴", "").strip()
    m = re.match(r"([\d.]+)\s*(万|億)?", t)
    if not m:
        return None
    v = float(m.group(1))
    return int(v * {"万": 1e4, "億": 1e8}.get(m.group(2), 1))


def age_days(t):
    if not t:
        return None
    m = re.search(r"(\d+)\s*(秒|分|時間|日|週間|か月|ヶ月|年)", t)
    if not m:
        return None
    n = int(m.group(1))
    return n * {"秒": 0, "分": 0, "時間": 0, "日": 1, "週間": 7, "か月": 30, "ヶ月": 30, "年": 365}[m.group(2)]


def walk(o):
    if isinstance(o, dict):
        if "videoRenderer" in o:
            yield o["videoRenderer"]
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def txt(x):
    if not x:
        return ""
    if "simpleText" in x:
        return x["simpleText"]
    return "".join(r.get("text", "") for r in x.get("runs", []))


def search(q, sort=None):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&hl=ja&gl=JP"
    if sort == "views":
        url += "&sp=" + SP_VIEWS
    html = requests.get(url, headers=H, timeout=30).text
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        return []
    data = json.loads(m.group(1))
    out = []
    for v in walk(data):
        out.append({
            "id": v.get("videoId"),
            "title": txt(v.get("title")),
            "channel": txt(v.get("ownerText")),
            "channel_id": (v.get("ownerText", {}).get("runs", [{}])[0].get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId")),
            "views": parse_views(txt(v.get("viewCountText"))),
            "published": txt(v.get("publishedTimeText")),
            "age_days": age_days(txt(v.get("publishedTimeText"))),
            "length": txt(v.get("lengthText")),
        })
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sort = "views" if "--sort" in sys.argv else None
    outp, qs = args[0], args[1:]
    res = {"fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sort": sort, "queries": {}}
    for q in qs:
        res["queries"][q] = search(q, sort)
        time.sleep(1.5)
    json.dump(res, open(outp, "w"), ensure_ascii=False, indent=1)
    for q, vs in res["queries"].items():
        print(q, len(vs))
