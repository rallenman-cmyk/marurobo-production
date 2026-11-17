import json,sys,glob
from PIL import Image,ImageDraw,ImageFont
D=json.load(open("dl/dataset.json"))
fonts=glob.glob("/usr/share/fonts/**/NotoSansCJK-Bold.ttc",recursive=True)+glob.glob("/usr/share/fonts/**/NotoSerifCJK-Bold.ttc",recursive=True)
F=ImageFont.truetype(fonts[0],20,index=0); F2=ImageFont.truetype(fonts[0],17,index=0)
def fmt(n):
    return f"{n/1e4:.1f}万" if n>=1e4 else str(n)
def tile(o,idx):
    im=Image.open(f"thumbs/{o['id']}.jpg").convert("RGB")
    w,h=im.size; th=w*9//16
    if h>th: im=im.crop((0,(h-th)//2,w,(h-th)//2+th))
    im=im.resize((480,270))
    t=Image.new("RGB",(480,330),"white"); t.paste(im,(0,0))
    d=ImageDraw.Draw(t)
    title=o["title"]; s=title[:22]+("…" if len(title)>22 else "")
    ratio=f"x{o['views']/o['subs_n']:.1f}" if o["subs_n"] else "x?"
    d.text((6,272),f"{idx}. {s}",font=F2,fill="black")
    d.text((6,298),f"{fmt(o['views'])}回 / 登録{o['subs']}  {ratio}  {o['age']}  {o['ch'][:10]}",font=F2,fill=(170,0,0))
    return t
def sheet(items,name,start=1):
    cols=4; rows=(len(items)+3)//4
    S=Image.new("RGB",(cols*480+(cols+1)*8,rows*330+(rows+1)*8),(60,60,60))
    for i,o in enumerate(items):
        S.paste(tile(o,start+i),(8+(i%4)*488,8+(i//4)*338))
    S.save(name,quality=88)
g=[o for o in D if o["grp"]=="genre"]; c=[o for o in D if o["grp"]=="control"]
sheet(g[:12],"sheet_genre_1.jpg",1); sheet(g[12:24],"sheet_genre_2.jpg",13); sheet(g[24:],"sheet_genre_3.jpg",25)
sheet(c[:12],"sheet_genre_4_control_shikumi_a.jpg",101); sheet(c[12:],"sheet_genre_5_control_shikumi_b.jpg",113)
