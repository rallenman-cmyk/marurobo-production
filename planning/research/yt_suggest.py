# YouTube の検索の「予測候補」（みんながよく打つ言葉）を集める。公開の窓口を使う
# python3 yt_suggest.py <出力.json> "<もとの言葉1>" "<もとの言葉2>" ...
# もとの言葉の後ろに、あ〜わ の一文字を足して広げる（例：「仕組み あ」「仕組み か」…）
import json, sys, time
import requests

KANA = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわ")


def suggest(q):
    r = requests.get("https://suggestqueries.google.com/complete/search", params={"client": "firefox", "ds": "yt", "hl": "ja", "gl": "jp", "q": q}, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.encoding = "utf-8"
    try:
        return json.loads(r.text)[1]
    except Exception:
        return []


if __name__ == "__main__":
    outp, seeds = sys.argv[1], sys.argv[2:]
    res = {}
    for s in seeds:
        got = []
        for k in [""] + KANA:
            for w in suggest((s + " " + k).strip()):
                if w not in got:
                    got.append(w)
            time.sleep(0.25)
        res[s] = got
        print(s, len(got))
    json.dump(res, open(outp, "w"), ensure_ascii=False, indent=1)
