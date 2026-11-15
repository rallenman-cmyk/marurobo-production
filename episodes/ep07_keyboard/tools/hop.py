# 跳ねる距離の計算（キー中心どうしの距離、キー1個分=1。段のずれ 0・1/4・3/4）
import math
def lay(rows, offs=(0,0.25,0.75)):
    p={}
    for r,(row,o) in enumerate(zip(rows,offs)):
        for i,c in enumerate(row): p[c]=(i+o, r)
    return p
Q=lay(["QWERTYUIOP","ASDFGHJKL","ZXCVBNM"])
A=lay(["ABCDEFGHIJ","KLMNOPQRS","TUVWXYZ"])
D=lay(["'.,PYFGCRL".replace("'","1").replace(".","2").replace(",","3"),"AOEUIDHTNS","4QJKXBMWVZ"])  # dvorak letters only
def dist(L,w):
    w=[c for c in w.upper() if c in L]
    return sum(math.dist(L[a],L[b]) for a,b in zip(w,w[1:]))
if __name__=="__main__":
  for w in ["MARUROBO","ARIGATOU","KONNICHIWA","KEYBOARD","SUSHI","OHAYOU","TYPEWRITER"]:
      print(f"{w:12s} QWERTY {dist(Q,w):5.1f}  ABC {dist(A,w):5.1f}  Dvorak {dist(D,w):5.1f}")
