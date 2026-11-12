# まるロボの体（上から見た楕円 1.02m×0.92m、半径0.51/0.46）が QR の右下に乗ったとき、
# どのマスが隠れるかを、マスの大きさと立つ位置を変えて調べる（スマホは真上から見る近似）
import sys, json, itertools
sys.path.insert(0,'/home/user/qr_plan/sim')
from qrsim import *
from PIL import Image, ImageDraw
S='HELLO'; q,m=matrix(S,'h',version=1); cw=codeword_map(1,26); n=21; Q=4
def shot(cx,cy,mod,scale=12,band=True):
    """cx,cy：QRの左上を(0,0)としたマス単位の中心。mod：1マスの大きさ(m)"""
    img=Image.fromarray(render(m,scale,Q)).convert('L'); d=ImageDraw.Draw(img)
    rx=0.51/mod*scale; ry=0.46/mod*scale; X=(cx+Q)*scale; Y=(cy+Q)*scale
    d.ellipse([X-rx,Y-ry,X+rx,Y+ry],fill=235)
    if band: d.ellipse([X-rx,Y-ry,X+rx,Y+ry],outline=117,width=max(2,int(0.06*rx)))
    return np.array(img)
def covered(cx,cy,mod):
    rx=0.51/mod; ry=0.46/mod; cov=np.zeros((n,n),bool)
    for r in range(n):
        for c in range(n):
            # マスの中心が楕円の中なら隠れる
            if ((c+0.5-cx)/rx)**2+((r+0.5-cy)/ry)**2<=1: cov[r,c]=True
    return cov
def bad_boxes(cov):
    mm=m.copy(); mm[cov]=0   # 白い体＝白
    return sorted(set(int(x)+1 for x in cw[(mm!=m)&(cw>=0)])), mm
res=[]
for mod in [0.10,0.11,0.12,0.13,0.14]:
    for cx in np.arange(15.0,19.6,0.5):
        cy=cx
        bad,_=bad_boxes(covered(cx,cy,mod)); d1=decode(shot(cx,cy,mod)); ok1=all(v==S for v in d1.values())
        step=0.30/mod/1.414   # 一歩（0.30m）を斜め内側へ
        bad2,_=bad_boxes(covered(cx-step,cy-step,mod)); d2=decode(shot(cx-step,cy-step,mod)); ok2=any(v==S for v in d2.values())
        res.append(dict(mod=mod,cx=float(cx),nbad=len(bad),ok_stand=ok1,nbad_step=len(bad2),any_ok_step=ok2,
                        stand=d1,step=d2))
good=[r for r in res if r['ok_stand'] and not r['any_ok_step']]
for r in good: print({k:r[k] for k in ['mod','cx','nbad','nbad_step']}, r['stand'])
json.dump(res,open('robot_footprint_search.json','w'),ensure_ascii=False,default=str)
