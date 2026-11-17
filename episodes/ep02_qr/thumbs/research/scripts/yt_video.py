import sys, json, re
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from yt_search import fetch, initial_data, walk, txt
from concurrent.futures import ThreadPoolExecutor
def info(vid):
    h=fetch(f"https://www.youtube.com/watch?v={vid}&hl=ja&gl=JP")
    d=initial_data(h) or {}
    o=next(walk(d,"videoOwnerRenderer"),{})
    m=re.search(r'"viewCount":"(\d+)"',h); views=int(m.group(1)) if m else None
    m=re.search(r'"publishDate":"([^"]+)"',h); pub=m.group(1)[:10] if m else ""
    m=re.search(r'<meta name="title" content="([^"]*)"',h); title=m.group(1) if m else ""
    m=re.search(r'"lengthSeconds":"(\d+)"',h); ln=int(m.group(1)) if m else 0
    return dict(id=vid,title=title,views=views,pub=pub,len=ln,ch=txt(o.get("title")),subs=txt(o.get("subscriberCountText")))
if __name__=="__main__":
    ids=sys.argv[1:]
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(info,ids): print(json.dumps(r,ensure_ascii=False))
