# 動画の元の題（何語の動画か）を取る。公開の窓口（oembed）だけを使う
# 日本語のページでは、海外の動画の題が日本語に訳されて出る。「日本語の題＝日本の動画」とは限らない。
# 元の題に日本語が無ければ、その再生回数は世界ぜんぶの数（日本の人だけの数ではない）。
# python3 yt_origin.py <検索結果.json…> <出力：origin.json> [--min 再生回数]
import json, re, sys, time
import requests

JA = re.compile(r"[ぁ-んァ-ン一-龥]")


def original_title(vid):
    try:
        r = requests.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        if r.status_code == 200:
            return r.json().get("title")
    except Exception:
        pass
    return None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mn = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 30000
    if "--min" in sys.argv:
        args.remove(str(mn))
    *ins, outp = args
    try:
        cache = json.load(open(outp))
    except Exception:
        cache = {}
    ids = {}
    for f in ins:
        for vs in json.load(open(f))["queries"].values():
            for v in vs:
                if v.get("views") and v["views"] >= mn:
                    ids[v["id"]] = v["title"]
    todo = [i for i in ids if i not in cache]
    for n, i in enumerate(todo):
        t = original_title(i)
        cache[i] = {"original": t, "japanese": (bool(JA.search(t)) if t else None)}
        if n % 20 == 19:
            json.dump(cache, open(outp, "w"), ensure_ascii=False)
        time.sleep(0.4)
    json.dump(cache, open(outp, "w"), ensure_ascii=False)
    print("調べた動画", len(cache), "新しく", len(todo), "海外", sum(1 for c in cache.values() if c["japanese"] is False))
