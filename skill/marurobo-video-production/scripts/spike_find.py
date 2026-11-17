# 1コマだけ別の絵が映る所（前後のコマが似ていて、その1コマだけ大きく違う）を探す
import subprocess,numpy as np,sys
for p in sys.argv[1:]:
    r=subprocess.run(['ffmpeg','-v','error','-i',p,'-vf','scale=96:54,format=gray','-f','rawvideo','-'],capture_output=True)
    x=np.frombuffer(r.stdout,np.uint8).reshape(-1,54,96).astype(np.float32)
    d=np.abs(np.diff(x,axis=0)).mean(axis=(1,2))
    out=[]
    for i in range(1,len(x)-1):
        if d[i-1]>12 and d[i]>12:
            same=np.abs(x[i-1]-x[i+1]).mean()
            if same<0.6*min(d[i-1],d[i]): out.append((round(i/24,2),round(float(d[i-1]),1),round(float(same),1)))
    print(p.split('/')[-1], len(x), out)
