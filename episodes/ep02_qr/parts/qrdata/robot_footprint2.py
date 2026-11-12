import sys; sys.path.insert(0,'.')
exec(open('robot_footprint.py').read().split('res=[]')[0])
out=[]
for mod in np.arange(0.10,0.165,0.01):
    for cx in np.arange(15.0,20.01,0.25):
        bad,_=bad_boxes(covered(cx,cx,mod))
        if not (5<=len(bad)<=8): continue
        d1=decode(shot(cx,cx,mod))
        if not all(v==S for v in d1.values()): continue
        for stepm in (0.30,0.35,0.40,0.45):
            st=stepm/mod/1.414
            bad2,_=bad_boxes(covered(cx-st,cx-st,mod))
            if len(bad2)<9: continue
            d2=decode(shot(cx-st,cx-st,mod))
            if any(v==S for v in d2.values()): continue
            out.append((round(mod,2),cx,stepm,len(bad),len(bad2),bad,bad2))
for o in out: print(o[:5])
import json; json.dump([dict(mod=o[0],cx=o[1],step=o[2],stand_bad=o[5],step_bad=o[6]) for o in out],open('robot_footprint_ok.json','w'))
