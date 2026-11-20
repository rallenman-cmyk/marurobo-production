import sys, json, re
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0] if '/' in sys.argv[0] else '.')
from yt_search import fetch, initial_data, walk
def subs2(chid):
    """チャンネルの見出し（pageHeaderViewModel）の中の登録者数だけを読む（おすすめのチャンネルの数を拾わない）"""
    d = initial_data(fetch(f"https://www.youtube.com/channel/{chid}?hl=ja&gl=JP"))
    if not d: return "?"
    for h in walk(d, "pageHeaderViewModel"):
        s = json.dumps(h, ensure_ascii=False)
        m = re.search(r'チャンネル登録者数\s*([\d\.,]+\s*[万億]?)人', s)
        if m: return m.group(1).replace(" ", "")
    for h in walk(d, "c4TabbedHeaderRenderer"):
        s = json.dumps(h, ensure_ascii=False)
        m = re.search(r'チャンネル登録者数\s*([\d\.,]+\s*[万億]?)人', s)
        if m: return m.group(1).replace(" ", "")
    return "?"
if __name__ == "__main__":
    for c in sys.argv[1:]: print(c, subs2(c))
