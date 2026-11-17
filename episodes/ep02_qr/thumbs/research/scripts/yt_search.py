import sys, json, re, urllib.parse, subprocess
def fetch(url):
    return subprocess.run(["curl","-sS","-L","-H","Accept-Language: ja-JP,ja;q=0.9","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",url],capture_output=True,text=True).stdout
def initial_data(html):
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html, re.S)
    if not m: m = re.search(r'ytInitialData"\]\s*=\s*(\{.*?\});', html, re.S)
    return json.loads(m.group(1)) if m else None
def walk(o, key):
    if isinstance(o, dict):
        for k,v in o.items():
            if k==key: yield v
            yield from walk(v,key)
    elif isinstance(o, list):
        for x in o: yield from walk(x,key)
def txt(t):
    if not t: return ""
    if "simpleText" in t: return t["simpleText"]
    return "".join(r.get("text","") for r in t.get("runs",[]))
def search(q, sp=None):
    url="https://www.youtube.com/results?hl=ja&gl=JP&search_query="+urllib.parse.quote(q)
    if sp: url+="&sp="+sp
    d=initial_data(fetch(url)); out=[]
    if not d: return out
    for v in walk(d,"videoRenderer"):
        ch=v.get("ownerText",{}).get("runs",[{}])[0]
        out.append(dict(id=v.get("videoId"),title=txt(v.get("title")),views=txt(v.get("viewCountText")),age=txt(v.get("publishedTimeText")),len=txt(v.get("lengthText")),ch=ch.get("text"),chid=ch.get("navigationEndpoint",{}).get("browseEndpoint",{}).get("browseId")))
    return out
if __name__=="__main__":
    for q in sys.argv[1:]:
        for r in search(q):
            print(json.dumps(dict(q=q,**r),ensure_ascii=False))
