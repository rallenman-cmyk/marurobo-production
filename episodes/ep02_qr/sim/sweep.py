from qrsim import *
import json, sys
S='MARU ROBO'; TOT=26
res={}
for e,t in [('l',None),('h',None)]:
    q,m=matrix(S,e,version=1); cw=codeword_map(1,TOT); f=function_mask(1); n=21
    for color in ['white','black']:
        for k in [3,4,5,6,7,8]:
            rows=[]
            for r0 in range(0,n-k+1):
                for c0 in range(0,n-k+1):
                    mm=m.copy(); val=0 if color=='white' else 1
                    mm[r0:r0+k,c0:c0+k]=val
                    flip=(mm!=m)
                    bad=set(cw[flip & (cw>=0)].tolist())
                    touch=set(f[r0:r0+k,c0:c0+k].ravel().tolist())-{0}
                    d=decode(render(mm))
                    rows.append(dict(r=r0,c=c0,bad=len(bad),finder=int(1 in touch),fmt=int(4 in touch),
                        z=int(d['zxing']==S),o=int(d['opencv']==S),b=int(d['zbar']==S),
                        wrong=int(any(v and v!=S for v in d.values()))))
            res[f'{e}_{color}_{k}']=rows
json.dump(res,open('sweep.json','w'))
