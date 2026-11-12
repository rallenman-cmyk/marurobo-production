from qrsim import *
from PIL import Image, ImageDraw, ImageFont
import random
F=lambda s: ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', s)
S='MARU ROBO'; n=21; Q=4
qh,mh=matrix(S,'h',version=1); ql,ml=matrix(S,'l',version=1)
cw=codeword_map(1,26); fm=function_mask(1)
OUT='/home/user/qr_plan/'

def draw_qr(m, sc=16, overlay=None, quiet=Q):
    W=(n+2*quiet)*sc; im=Image.new('RGB',(W,W),'white'); d=ImageDraw.Draw(im,'RGBA')
    for r in range(n):
        for c in range(n):
            if m[r,c]: d.rectangle([(c+quiet)*sc,(r+quiet)*sc,(c+quiet+1)*sc-1,(r+quiet+1)*sc-1],fill='black')
    if overlay: overlay(d,sc,quiet)
    return im

# --- Fig1: anatomy
def anatomy(m, ndata, title):
    sc=34; quiet=1; W=(n+2*quiet)*sc
    im=Image.new('RGB',(W,W+60),'white'); d=ImageDraw.Draw(im)
    blues=[(70,130,220),(120,170,240)]; oranges=[(240,150,60),(250,190,110)]
    for r in range(n):
        for c in range(n):
            x,y=(c+quiet)*sc,(r+quiet)*sc+60
            f=fm[r,c]; k=cw[r,c]
            if f==1: col=(200,60,80) if m[r,c] else (250,215,220)
            elif f==2: col=(60,150,90) if m[r,c] else (200,235,210)
            elif f==4: col=(140,80,180) if m[r,c] else (225,205,240)
            elif f==5: col=(140,80,180)
            else:
                base=(blues if k<ndata else oranges)[k%2]
                col=tuple(int(v*0.55) for v in base) if m[r,c] else base
            d.rectangle([x,y,x+sc-1,y+sc-1],fill=col,outline=(255,255,255))
    # codeword labels at centroid
    for k in range(26):
        ys,xs=np.where(cw==k); r,c=ys.mean(),xs.mean()
        x,y=(c+quiet+0.5)*sc,(r+quiet+0.5)*sc+60
        d.text((x,y),str(k+1),font=F(20),fill='white',anchor='mm',stroke_width=2,stroke_fill='black')
    d.text((10,12),title,font=F(26),fill='black')
    return im
a=anatomy(mh,9,'V1-H「MARU ROBO」の中身　青=内容 9個／橙=復元用 17個')
b=anatomy(ml,19,'V1-L「MARU ROBO」の中身　青=内容 19個／橙=復元用 7個')
leg=Image.new('RGB',(a.width*2+20,120),'white'); d=ImageDraw.Draw(leg)
items=[((200,60,80),'目印（ファインダパターン＋区切り）'),((60,150,90),'タイミングパターン（マスの間隔）'),((140,80,180),'形式情報（訂正レベル・マスク番号）×2か所'),((70,130,220),'内容のまとまり（8マス=1コードワード）'),((240,150,60),'復元用のまとまり（リード・ソロモン）')]
for i,(col,t) in enumerate(items):
    x=20+(i%3)*(leg.width//3); y=15+(i//3)*50
    d.rectangle([x,y,x+30,y+30],fill=col); d.text((x+40,y+3),t,font=F(22),fill='black')
fig=Image.new('RGB',(a.width*2+20,a.height+leg.height),'white'); fig.paste(a,(0,0)); fig.paste(b,(a.width+20,0)); fig.paste(leg,(0,a.height))
fig.save(OUT+'fig1_anatomy_H_vs_L.png')

# --- Fig2: experiments on V1-H
def box(r0,c0,k,col):
    def ov(d,sc,q):
        d.rectangle([(c0+q)*sc,(r0+q)*sc,(c0+q+k)*sc-1,(r0+q+k)*sc-1],fill=col)
    return ov
def bad_of(mm,m): return len(set(cw[(mm!=m)&(cw>=0)].tolist()))
def res(mm): 
    dd=decode(render(mm)); return all(v==S for v in dd.values()), dd
panels=[]
def add(m,mm,overlay,label):
    ok,dd=res(mm); b=bad_of(mm,m)
    im=draw_qr(m,overlay=overlay); 
    im2=Image.new('RGB',(im.width,im.height+110),'white'); im2.paste(im,(0,110)); d=ImageDraw.Draw(im2)
    d.text((10,8),label,font=F(24),fill='black')
    verdict='読める' if ok else ('読めない' if not any(dd.values()) else 'アプリで差')
    d.text((10,45),f'壊れたまとまり {b}個 → {verdict}',font=F(26),fill=(20,140,60) if ok else (200,40,40))
    d.text((10,80),' / '.join(f"{k}:{'○' if v==S else '×'}" for k,v in dd.items()),font=F(18),fill='gray')
    panels.append(im2)
m=mh
mm=m.copy(); mm[13:,13:]=0; add(m,mm,box(13,13,8,(255,215,0,200)),'① 右下 8×8マス（15%）')
mm=m.copy(); mm[12:,12:]=0; add(m,mm,box(12,12,9,(255,215,0,200)),'② 右下 9×9マス（18%）')
mm=m.copy(); mm[7:14,7:14]=0; add(m,mm,box(7,7,7,(255,215,0,200)),'③ 中央ロゴ 7×7マス')
mm=m.copy(); mm[2:5,2:5]=0; add(m,mm,box(2,2,3,(255,215,0,200)),'④ 目印の中心 3×3マスだけ')
# scattered 12 flips: find failing seed for display
data=[(r,c) for r in range(n) for c in range(n) if cw[r,c]>=0]
for seed in range(100):
    random.seed(seed); pts=random.sample(data,12); mm=m.copy()
    for r,c in pts: mm[r,c]^=1
    if bad_of(mm,m)==12 and not res(mm)[0]: break
def dots(pts):
    def ov(d,sc,q):
        for r,c in pts: d.ellipse([(c+q)*sc-4,(r+q)*sc-4,(c+q+1)*sc+3,(r+q+1)*sc+3],outline=(230,0,120),width=4)
    return ov
pm=mm.copy(); add(m,pm,dots(pts),'⑤ 点の汚れ 12マス（3%）')
W=sum(p.width for p in panels)+20*4; fig=Image.new('RGB',(W,panels[0].height),'white'); x=0
for p in panels: fig.paste(p,(x,0)); x+=p.width+20
fig.save(OUT+'fig2_experiments_V1H.png')
print('saved')
