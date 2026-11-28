import math,sys
def proj(cam,tgt,lens,p):
    f=[tgt[i]-cam[i] for i in range(3)]; n=math.sqrt(sum(x*x for x in f)); f=[x/n for x in f]
    up=(0,0,1); r=[f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]]; rn=math.sqrt(sum(x*x for x in r)); r=[x/rn for x in r]
    u=[r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], r[0]*f[1]-r[1]*f[0]]
    d=[p[i]-cam[i] for i in range(3)]; z=sum(d[i]*f[i] for i in range(3)); x=sum(d[i]*r[i] for i in range(3)); y=sum(d[i]*u[i] for i in range(3))
    sw=36.0; sh=sw*9/16
    return round(0.5+x*lens/z/sw,2), round(0.5-y*lens/z/sh,2)   # 左上 0,0
cases=eval(sys.argv[1])
for name,cam,tgt,lens,pts in cases:
    print(name,[ (k,proj(cam,tgt,lens,p)) for k,p in pts])
