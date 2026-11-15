import json,re,sys,time
sys.path.insert(0,sys.argv[0].rsplit('/',1)[0])
from yt_channel import subs
G="PTLLwlL9zF8 VWVqqyhlcu0 lAxKiwd1QLo 16zrEPOsIcI BmUZ2wp1lM8 iki5mL6JoEE t0tVQkIAfos AFEhHGzidNI 3YAEY6x5Bek Km5E4iTiqVY Y6cIu0-GAx4 m34ZZempdnc SBppLLdoglQ Ao2tY0J-xyE TwaZGejfmfc U0qllFgCu0Y W4VVvlokl7A znflTgK05Z8 jLeuqV4wt_o xj8am95rue0 1OJOhvQP-Zo 2EUIj9S5ygU Xisj5p-6A64 vvk7fAoWG_g E2UxQiPdscs NwLSnzQvXoY y7NQiNER6r4 Jv342zg_JAA I4d01OGywsg 8EXWSQPkSKQ 9VvtjkftZjQ Wtf_hRpigFw Z0_bm8JhrDw UkOFvDeXFpc".split()
C="0TbzQrCcyas EnnqAjtD6_U N0QlaCrcSww yyfUpAbGTek DSKv9baj6kI hCMDoJ8M2oM TA0KauyUS-M Rz2KDxjsHCM jlTclH5SGjk td4KVXduFks vNOVZHxP0D8 rFw546RBibA NbYxpZtz0Xc ZEuvGEY3y4E 9A_0QZnMHjo Sc40L7Uxh_8 W4VVvlokl7A K661LJ9J4CM o8euJbXSTV4 CEltM63yMYc".split()
NAMES={"UCS_EEYRtiF4Hl8aMjyu3xWA":"しくみの正体","UC0-ohwbMqL3qLTfMVlcHVQg":"しくみ物語"}
rec={}
for l in open("dl/chvids1.jsonl"):
    r=json.loads(l); r["chid"]=r["ch"]; r["chname"]=NAMES.get(r["ch"],r["ch"]); rec[r["id"]]=r
for l in open("dl/all_search.jsonl"):
    r=json.loads(l); r["chname"]=r["ch"]
    if r["id"] not in rec: rec[r["id"]]=r
def num(s):
    m=re.search(r"([\d\.,]+)\s*(万|億)?",s or "")
    if not m: return 0
    return int(float(m.group(1).replace(",",""))*{"万":1e4,"億":1e8,None:1}[m.group(2)])
chs={}
for vid in G+C:
    cid=rec[vid].get("chid")
    if cid and cid not in chs: chs[cid]=subs(cid); time.sleep(0.4)
out=[]
for grp,ids in [("genre",G),("control",C)]:
    for vid in ids:
        r=rec[vid]; s=chs.get(r.get("chid"),"?")
        out.append(dict(grp=grp,id=vid,title=r["title"],views=num(r["views"]),age=r["age"],ch=r["chname"],subs=s,subs_n=num(s)))
json.dump(out,open("dl/dataset.json","w"),ensure_ascii=False,indent=0)
for o in out: print(o["grp"][:3],o["id"],o["views"],o["subs"],round(o["views"]/o["subs_n"],2) if o["subs_n"] else "-",o["age"],o["ch"][:14],o["title"][:30])
