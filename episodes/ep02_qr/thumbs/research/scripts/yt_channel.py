import sys, json, re
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
from yt_search import fetch, initial_data, walk, txt
def subs(chid):
    html=fetch(f"https://www.youtube.com/channel/{chid}?hl=ja&gl=JP")
    m=re.search(r'チャンネル登録者数\s*([\d\.,]+\s*[万億]?)人',html)
    if not m: m=re.search(r'([\d\.,]+\s*[万]?)\s*(?:人|subscribers)',html)
    return m.group(1).replace(" ","") if m else "?"
def videos(chid, sort=None):
    url=f"https://www.youtube.com/channel/{chid}/videos?hl=ja&gl=JP"
    d=initial_data(fetch(url)); out=[]
    for v in walk(d,"videoRenderer"):
        out.append(dict(id=v.get("videoId"),title=txt(v.get("title")),views=txt(v.get("viewCountText")),age=txt(v.get("publishedTimeText"))))
    if not out:
        for v in walk(d,"lockupViewModel"):
            md=v.get("metadata",{}).get("lockupMetadataViewModel",{})
            parts=[p.get("accessibilityLabel") or p.get("text",{}).get("content") for row in md.get("metadata",{}).get("contentMetadataViewModel",{}).get("metadataRows",[]) for p in row.get("metadataParts",[])]
            out.append(dict(id=v.get("contentId"),title=md.get("title",{}).get("content"),views=parts[0] if parts else "",age=parts[1] if len(parts)>1 else ""))
    return out
if __name__=="__main__":
    mode=sys.argv[1]
    for c in sys.argv[2:]:
        if mode=="subs": print(c, subs(c))
        else:
            for r in videos(c): print(json.dumps(dict(ch=c,**r),ensure_ascii=False))
