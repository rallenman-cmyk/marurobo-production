exec(open('robot_footprint.py').read().split('res=[]')[0])
cands=[(0.12,17.0,0.40),(0.12,17.0,0.45),(0.13,16.25,0.35),(0.13,16.5,0.40),(0.12,17.25,0.45),(0.13,16.75,0.45)]
for mod,cx,stepm in cands:
    st=stepm/mod/1.414; okS=0; failT=0; N=0
    for dx in (-0.25,0,0.25):
        for dy in (-0.25,0,0.25):
            N+=1
            okS+= all(v==S for v in decode(shot(cx+dx,cx+dy,mod)).values())
            failT+= not any(v==S for v in decode(shot(cx-st+dx,cx-st+dy,mod)).values())
    print(mod,cx,stepm,'stand readable',okS,'/',N,' step fails',failT,'/',N)
