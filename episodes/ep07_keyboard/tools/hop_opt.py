# まるロボ専用の並び（跳ねる距離が最短）を焼きなましで探す。文は仮。台本で決めて計算し直す
import math,random,itertools
from hop import lay,Q,A,dist
text="""watashi wa marurobo desu kyou wa ii tenki desu ne konnichiwa arigatou gozaimasu ohayou gozaimasu
kiibo-do wa naze abc jun ni narande inai no deshou ka minna ga oboete shimatta kara kawaranai no desu
nihon de wa ooku no hito ga ro-maji de nyuuryoku shite imasu sushi wo tabetai desu kaeri ni kaimono wo shimasu
ashita mo yoroshiku onegai shimasu kono douga wo mite kurete arigatou sayounara mata ne"""
letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def tot(L): return sum(dist(L,w) for w in text.split())
print("QWERTY",round(tot(Q)),"ABC",round(tot(A)))
random.seed(1)
cur=list(letters); random.shuffle(cur)
def mk(s): return lay(["".join(s[:10]),"".join(s[10:19]),"".join(s[19:])])
best=cur[:];bv=tot(mk(cur));cv=bv;T=5.0
for it in range(60000):
    i,j=random.sample(range(26),2); cur[i],cur[j]=cur[j],cur[i]
    v=tot(mk(cur))
    if v<cv or random.random()<math.exp((cv-v)/T): cv=v
    else: cur[i],cur[j]=cur[j],cur[i]
    if cv<bv: bv=cv;best=cur[:]
    T*=0.9999
print("best",round(bv),"".join(best[:10]),"".join(best[10:19]),"".join(best[19:]))
