import numpy as np, sys
W=sys.argv[1]; t0=float(sys.argv[2])
m=np.load(W+"_music.npy"); v=np.load(W+"_voice.npy"); SR=48000
def db(x): return 20*np.log10(np.sqrt((x**2).mean())+1e-9)
h=int(0.1*SR); n=len(m)//h
me=np.array([db(m[i*h:(i+1)*h]) for i in range(n)]); ve=np.array([db(v[i*h:(i+1)*h]) for i in range(n)])
on=ve>-50
print("声 %.1f dB／曲：声のある所 %.1f・ない所 %.1f dB → 声との差 %.1f dB"%(np.median(ve[on]),np.median(me[on]),np.median(me[~on]),np.median(ve[on])-np.median(me[on])))
print("曲の 0.1 秒の大きさ（10〜90%%）: %.1f〜%.1f dB"%tuple(np.percentile(me,[10,90])))
low=me<np.median(me)-12
r=[];i=0
while i<n:
    if low[i]:
        j=i
        while j<n and low[j]: j+=1
        if j-i>=3: r.append((round(t0+i/10,1),round((j-i)/10,1)))
        i=j
    else: i+=1
print("曲が 12 dB 以上へこむ 0.3 秒以上の所:", r)
