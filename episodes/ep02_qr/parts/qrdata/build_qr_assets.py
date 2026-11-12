# QRコード回のデータ一式（3D・図・印刷・実験の元）を1つのJSONに書き出す
import sys, json, random
sys.path.insert(0,'/home/user/qr_plan/sim')
from qrsim import *
exec(open('robot_footprint.py').read().split('res=[]')[0])
n=21; TOT=26; NDATA=9
MASKS=[lambda r,c:(r+c)%2==0,lambda r,c:r%2==0,lambda r,c:c%3==0,lambda r,c:(r+c)%3==0,
 lambda r,c:(r//2+c//3)%2==0,lambda r,c:(r*c)%2+(r*c)%3==0,lambda r,c:((r*c)%2+(r*c)%3)%2==0,lambda r,c:((r+c)%2+(r*c)%3)%2==0]
fm=function_mask(1); cw=codeword_map(1,TOT)
LABEL={0:'data',1:'finder',2:'timing',3:'align',4:'format',5:'dark'}
order=[]; col=n-1; up=True
while col>0:
    if col==6: col-=1
    for r in (range(n-1,-1,-1) if up else range(n)):
        for c in (col,col-1):
            if fm[r,c]==0: order.append([r,c])
    up=not up; col-=2
def sym(s,lvl):
    q,m=matrix(s,lvl,version=1)
    un=m.copy()
    for r in range(n):
        for c in range(n):
            if fm[r,c]==0 and MASKS[q.mask](r,c): un[r,c]^=1
    byts=[int(''.join(str(int(un[r,c])) for r,c in order[i*8:i*8+8]),2) for i in range(TOT)]
    return q,m,un,byts
out={'about':'QRコード回のデータ一式。座標は[行,列]、左上が[0,0]、黒=1。箱＝コードワード（8マス）。番号は1から（読む順）。',
     'size':n,'quiet_zone':4,'function_labels':[[LABEL[int(fm[r,c])] for c in range(n)] for r in range(n)],
     'box_of':[[int(cw[r,c])+1 if cw[r,c]>=0 else 0 for c in range(n)] for r in range(n)],
     'read_order':order,'boxes':{str(i+1):order[i*8:i*8+8] for i in range(TOT)},'symbols':{},'experiments':{}}
for name,s,lvl in [('HELLO_H','HELLO','h'),('HELLO_L','HELLO','l'),('MATANE_H','MATANE','h')]:
    q,m,un,byts=sym(s,lvl); ndata={'h':9,'l':19}[lvl]
    out['symbols'][name]=dict(text=s,level=lvl.upper(),version=1,mask=q.mask,data_boxes=list(range(1,ndata+1)),
        spare_boxes=list(range(ndata+1,TOT+1)),fixable_boxes={'h':8,'l':3}[lvl],
        matrix=m.astype(int).tolist(),before_pattern=un.astype(int).tolist(),box_bytes=byts,decode=decode(render(m)))
S='HELLO'; q,m,un,byts=sym('HELLO','h')
# 中身の読み方（3章）：英数字モード 0010・文字数 9bit・2文字ごと11bit
bits=''.join(format(b,'08b') for b in byts[:NDATA])
AL='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'
segs=[('モード（英数字）',bits[0:4]),('文字数=5',bits[4:13])]
p=13
for pair in ['HE','LL']:
    segs.append((pair,bits[p:p+11])); p+=11
segs.append(('O',bits[p:p+6])); p+=6
segs.append(('終わりの印',bits[p:p+4])); p+=4
out['symbols']['HELLO_H']['reading']=dict(bits=bits,segments=[{'label':a,'bits':b} for a,b in segs],
  pad_note='残りは8の倍数にそろえる0と、すき間を埋める決まった数（11101100・00010001のくり返し）')
def exp(name,mm,note,extra=None):
    flip=(mm!=m); bad=sorted(set(int(x)+1 for x in cw[flip&(cw>=0)])); d=decode(render(mm))
    e=dict(note=note,changed=[[int(r),int(c),int(mm[r,c])] for r,c in zip(*np.where(flip))],bad_boxes=bad,n_bad=len(bad),
           sim={k:(v==S) for k,v in d.items()})
    if extra: e.update(extra)
    out['experiments'][name]=e
# まるロボの体（1マス0.13m、中心(16.5,16.5)マス、一歩0.40m斜め内側）
mod=0.13; cx=16.5; st=0.40/mod/1.414
for nm,c0 in [('robot_stand',cx),('robot_step',cx-st)]:
    cov=covered(c0,c0,mod); mm=m.copy(); mm[cov]=0
    d=decode(shot(c0,c0,mod))
    exp(nm,mm,'まるロボの体（上から見た楕円 1.02×0.92m）。白い体でマスが白く見える',
        dict(center_rc=[c0,c0],module_m=mod,ellipse_modules=[1.02/mod,0.92/mod],covered=[[int(r),int(c)] for r,c in zip(*np.where(cov))],
             sim_with_band={k:(v==S) for k,v in d.items()}))
mm=m.copy(); mm[13:,13:]=0; exp('square8',mm,'右下8×8マス（参考）')
mm=m.copy(); mm[12:,12:]=0; exp('square9',mm,'右下9×9マス（参考）')
mm=m.copy(); mm[2:5,2:5]=0; exp('finder_box3',mm,'左上の目印の真ん中に3×3マスの白い箱（S16）')
for k in (8,9):
    mm=m.copy(); mm[(cw>=0)&(cw<k)]=0; exp(f'content_erase_{k}',mm,f'中身の箱1〜{k}を白く塗りつぶす（S31）')
white=[(r,c) for r in range(n) for c in range(n) if cw[r,c]>=0 and m[r,c]==0]
for seed in range(100):
    random.seed(seed); w=white[:]; random.shuffle(w); pts=[]; used=set()
    for r,c in w:
        if cw[r,c] not in used: pts.append((r,c)); used.add(cw[r,c])
        if len(pts)==12: break
    mm=m.copy()
    for r,c in pts: mm[r,c]=1
    if not any(v==S for v in decode(render(mm)).values()): break
exp('ink12',mm,'白いマスにインクのしずく12か所、すべて別の箱（S32）',dict(drops=[[int(r),int(c)] for r,c in pts],seed=seed))
logo=m.copy(); logo[7:14,7:14]=0; exp('logo7',logo,'中央に7×7マスのロゴ（白地として計算。ロゴの絵柄しだいで変わる）（S33）')
lb=set(cw[(logo!=m)&(cw>=0)].tolist())
cand=[(r,c) for r in range(n) for c in range(n) if cw[r,c]>=0 and cw[r,c] not in lb and m[r,c]==0 and not(7<=r<14 and 7<=c<14)]
for r,c in sorted(cand,key=lambda x:(abs(x[0]-4)+abs(x[1]-16))):
    mm=logo.copy(); mm[r,c]=1
    if not any(v==S for v in decode(render(mm)).values()): break
exp('logo7_ink1',mm,'ロゴ＋しずく1つ（S33）',dict(drop=[r,c]))
qL,mL,_,_=sym('HELLO','l')
for lvl,mx in [('H',m),('L',mL)]:
    mm=mx.copy(); mm[16:,16:]=0
    bad=sorted(set(int(x)+1 for x in cw[(mm!=mx)&(cw>=0)])); d=decode(render(mm))
    out['experiments'][f'box5_{lvl}']=dict(note=f'右下に5×5マスの白い箱（レベル{lvl}、S34）',changed=[[int(r),int(c),0] for r,c in zip(*np.where(mm!=mx))],
        bad_boxes=bad,n_bad=len(bad),sim={k:(v==S) for k,v in d.items()})
json.dump(out,open('qr_assets.json','w'),ensure_ascii=False)
for k,e in out['experiments'].items(): print(k.ljust(16),'bad',str(e['n_bad']).rjust(2),e['sim'],e.get('sim_with_band',''))
print(segs)
