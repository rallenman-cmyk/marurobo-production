# 乗客全員の形を先に計算してキャッシュに入れる
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hchar, people
t0 = time.time()
for n, cfg in people.PEOPLE.items():
    hchar.geometry(cfg); print("CACHED", n, round(time.time() - t0, 1), flush=True)
