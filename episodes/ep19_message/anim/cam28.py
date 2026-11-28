# 17本目 v8：札の下のはし yb は、組んだ動画の一覧で測る（1 段 0.18・2 段 0.29・3 段 0.39・4 段 0.62。最初は 0.44 と見積もってかぶった）。4 段のときは広い角度（16〜22）・低いカメラも入れて探す。28（家の大きなスマホ）のカメラを、右上の一覧（段の数ごとの下のはし yb）と 28-04 の左上の小窓をよけて、まるロボとスマホが大きく映るように探す
import os
import math,itertools,sys
sys.argv=["x","[]"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"proj.py")).read().split("cases=")[0])
REST=(1.50,1.20); PRESS=(1.43,1.31)
def maru_pts(c):
    x,y=c; return {"hat":(x,y,0.69),"feet":(x,y,0.0),"right":(x+0.2,y-0.05,0.4),"left":(x-0.2,y+0.05,0.4),"lens":(x-0.11,y+0.18,0.34),"back":(x+0.1,y-0.18,0.4)}
phone={"tl":(1.06,1.52,0.62),"tr":(1.34,1.52,0.62),"bl":(1.06,1.52,0.06),"br":(1.34,1.52,0.06)}
def search(yb,pip):
    res=[]
    for cx,cy,cz,tx,ty,tz,lens in itertools.product([0.2,0.3,0.4,0.5,0.6,0.7],[0.5,0.6,0.7,0.8,0.9,1.0,1.1],[0.5,0.6,0.7,0.8,0.9],[1.2,1.3,1.4,1.5,1.6,1.7],[1.2,1.3,1.4,1.5],[0.3,0.4,0.5],[22,24,26,28,30]):
        cam=(cx,cy,cz); tgt=(tx,ty,tz)
        if math.hypot(cx-REST[0],cy-REST[1])<1.0: continue
        P={}
        for c in (REST,PRESS):
            for k,p in maru_pts(c).items(): P["m"+k+str(c)]=proj(cam,tgt,lens,p)
        for k,p in phone.items(): P["p"+k]=proj(cam,tgt,lens,p)
        ok=True
        for k,(x,y) in P.items():
            ymax=0.86 if ("feet" in k or k in ("pbl","pbr")) else 0.77
            if not (0.03<x<0.97 and 0.03<y<ymax): ok=False
            if k.startswith("m") and x>0.54 and y<yb: ok=False
            if pip and x<0.48 and y<0.48 and "lens" in k: ok=False
        wph=P["ptr"][0]-P["ptl"][0]
        if wph<0.1: ok=False
        if ok:
            h=P["mfeet"+str(REST)][1]-P["mhat"+str(REST)][1]
            res.append((round(h+wph,3),cam,tgt,lens,round(h,2),round(wph,2)))
    res.sort(reverse=True); return res
for nm,yb,pip in (("A28c",0.13,0),("A28c2",0.13,1),("A28d",0.2,0),("A28e",0.26,0),("A28f",0.44,0),("A28g",0.44,0)):
    r=search(yb,pip); print(nm,len(r))
    for x in r[:3]: print("  ",x)
