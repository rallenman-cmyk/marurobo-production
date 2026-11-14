# 5本目：部屋の間取り（3D の部屋・スマホの地図・光の物差しの点を、全部ここから作る。形が必ずそろう）
# bpy を使わない（Blender でも、ふつうの python でも読める）
# 単位はメートル。x＝右、y＝奥、z＝上。部屋は x -3〜3、y -2.5〜2.5、天井 2.4
import math

ROOM = (-3.0, -2.5, 3.0, 2.5)
CEIL = 2.4
LIDAR_Z = 0.095            # 光の物差しの高さ（この高さで切った形が地図になる）
DOOR = (-2.4, -1.4)        # 左の壁の出入り口（y の範囲）。外は廊下で、x=-3.7 で下へ降りる段差
HALL_X = -4.6              # 廊下の左の端
STEP_X = -3.75             # 段差の線（これより左は 0.18 m 低い）
STEP_H = 0.18

# 家具：名前 → (x0, y0, x1, y1, 光の物差しから見えるか, 足だけか)
# 足だけ＝ソファ・机は足の下に光が通る（「ここは、ソファの足」）
FURN = {
    "sofa":  (-2.85, 1.55, -0.95, 2.4, True, True),
    "desk":  (1.15, 1.75, 2.85, 2.4, True, True),
    "bed":   (1.25, -2.4, 2.9, -0.35, True, False),
    "shelf": (-2.95, -0.9, -2.62, 0.45, True, False),
    "dock":  (0.05, 2.32, 0.55, 2.5, True, False),     # 充電の台
}
LEG = 0.045               # 足の太さ（四角の一辺）
RUG = (-1.6, -0.9, 0.3, 0.55)                          # じゅうたん（4 章で車輪がすべる）


def legs(name):
    x0, y0, x1, y1 = FURN[name][:4]
    d = 0.06
    return [(x0 + d, y0 + d), (x1 - d, y0 + d), (x0 + d, y1 - d), (x1 - d, y1 - d)]


def segments(with_front=True):
    """光の物差しの高さで見える線分（壁・家具の足・家具のふち）"""
    x0, y0, x1, y1 = ROOM
    S = []
    S.append(((x0, y1), (x1, y1)))                      # 奥の壁
    S.append(((x1, y0), (x1, y1)))                      # 右の壁
    if with_front:
        S.append(((x0, y0), (x1, y0)))                  # 手前の壁（3D では描かないが、地図には出る）
    S.append(((x0, y1), (x0, DOOR[1])))                 # 左の壁（出入り口の上）
    S.append(((x0, DOOR[0]), (x0, y0)))                 # 左の壁（出入り口の下）
    # 廊下（出入り口の外）
    S.append(((x0, DOOR[1]), (HALL_X, DOOR[1])))
    S.append(((x0, DOOR[0]), (HALL_X, DOOR[0])))
    for k, (a, b, c, d, vis, leg) in FURN.items():
        if not vis: continue
        if leg:
            for (lx, ly) in legs(k):
                h = LEG / 2
                S += [((lx - h, ly - h), (lx + h, ly - h)), ((lx + h, ly - h), (lx + h, ly + h)), ((lx + h, ly + h), (lx - h, ly + h)), ((lx - h, ly + h), (lx - h, ly - h))]
        else:
            S += [((a, b), (c, b)), ((c, b), (c, d)), ((c, d), (a, d)), ((a, d), (a, b))]
    return S


def ray(px, py, ang, S, maxd=8.0):
    """(px,py) から ang の向きへ光を出し、いちばん近い当たりの距離と点"""
    dx, dy = math.cos(ang), math.sin(ang)
    best = maxd
    for (ax, ay), (bx, by) in S:
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9: continue
        t = ((ax - px) * ey - (ay - py) * ex) / den
        u = ((ax - px) * dy - (ay - py) * dx) / den
        if t > 1e-4 and -1e-6 <= u <= 1 + 1e-6 and t < best:
            best = t
    if best >= maxd: return None
    return best, (px + dx * best, py + dy * best)


# 光の物差しの先輩が、地図を描くときに走る道（台から出て、右 → 手前 → 左 → 奥とひと回りして台へ戻る）（時刻は 0〜1 の割合。場面の時刻に合わせて伸ばす）
LIDAR_PATH = [(0.3, 1.95), (0.3, 0.75), (1.9, 0.75), (2.45, 1.35), (2.5, 0.05), (0.8, -0.15), (0.8, -1.95), (-1.0, -2.1), (-2.2, -1.9), (-2.25, -0.9), (-2.2, 0.95), (-1.3, 1.25), (-0.4, 0.4), (0.3, 0.75), (0.3, 1.95)]


def path_at(P, u):
    """道 P の上で、長さの割合 u（0〜1）の点と向き（ラジアン）"""
    L = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]
    tot = sum(L); d = max(0.0, min(1.0, u)) * tot
    for i, l in enumerate(L):
        if d <= l or i == len(L) - 1:
            k = d / l if l else 0
            x = P[i][0] + (P[i + 1][0] - P[i][0]) * k; y = P[i][1] + (P[i + 1][1] - P[i][1]) * k
            return (x, y), math.atan2(P[i + 1][1] - P[i][1], P[i + 1][0] - P[i][0])
        d -= l
    return P[-1], 0.0


def scan_points(P, t0, t1, rot_per_s=2.0, rays=120, S=None, u0=0.0, u1=1.0):
    """道 P を t0〜t1 秒で走りながら光を回したとき、当たった点（x, y, 生まれた時刻）の一覧
       実物はもっと速く回る（1 秒に何回も）。絵では点がふえる様子が見えるよう、ゆっくり回して見せる"""
    S = S or segments()
    out = []
    n_rot = max(1, int((t1 - t0) * rot_per_s))
    for r in range(n_rot):
        for k in range(rays):
            a = (k / rays) * 2 * math.pi
            t = t0 + (r + k / rays) / rot_per_s
            if t > t1: break
            u = u0 + (u1 - u0) * (t - t0) / (t1 - t0)
            (px, py), _ = path_at(P, u)
            h = ray(px, py, a + r * 0.37, S)
            if h: out.append((round(h[1][0], 3), round(h[1][1], 3), round(t, 3)))
    return out


def map_points(step_deg=1.0):
    """出来上がった地図（スマホの地図・冒頭・オチ）。道のいくつかの場所から見える点を全部集める"""
    S = segments()
    pts = set()
    for u in [i / 60 for i in range(61)]:
        (px, py), _ = path_at(LIDAR_PATH, u)
        for k in range(int(360 / step_deg)):
            h = ray(px, py, math.radians(k * step_deg), S)
            if h: pts.add((round(h[1][0] / 0.03) * 0.03, round(h[1][1] / 0.03) * 0.03))
    return sorted(pts)


# 4 章：じゅうたんを横切ってから、部屋をひと回りして台の前の壁へ戻る道（ずれと、ぴたっと直る所）
RUG_PATH = [(0.3, 1.95), (0.3, 0.75), (-0.2, 0.2), (-1.9, -0.5), (-2.2, 0.95), (-1.3, 1.2), (-0.4, 1.25), (0.3, 1.95)]
RUG_U = (0.18, 0.42)       # この道の、じゅうたんの上にいる割合（ここで車輪がすべり、点がずれ始める）


# ---------------- 走り方（3D の動きと、光の点の計算に同じものを使う）
def face_deg(dx, dy):
    """進む向き (dx, dy) → 体の向き（度）。前＝-y を 0 度とする（まるロボと同じ決め方）"""
    return math.degrees(math.atan2(dx, -dy))


class Drive:
    """道 pts を、t0 から速さ v（m/秒）で走る。角では止まって、その場で向きを変える（1 秒に turn 度）
       pose(t) → (x, y, 向き[度])。drift：(t → (dx, dy, dθ度)) を渡すと『自分で思っている場所』も出せる"""
    def __init__(self, pts, t0, v=0.28, turn=150.0, face0=None, wait=0.0):
        self.keys = []                     # (t, x, y, 向き)
        t = t0; ang = face0
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            a = face_deg(x1 - x0, y1 - y0)
            if ang is None: ang = a
            d = (a - ang + 180) % 360 - 180
            if i == 0 and not self.keys: self.keys.append((t, x0, y0, ang))
            if abs(d) > 0.5:
                t += abs(d) / turn; ang = ang + d; self.keys.append((t, x0, y0, ang))
            t += math.dist((x0, y0), (x1, y1)) / v
            self.keys.append((t, x1, y1, ang))
            if wait: t += wait; self.keys.append((t, x1, y1, ang))
        self.t0, self.t1 = t0, t

    def pose(self, t):
        K = self.keys
        if t <= K[0][0]: return K[0][1:]
        for i in range(len(K) - 1):
            a, b = K[i], K[i + 1]
            if t <= b[0]:
                k = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 1.0
                return (a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k)
        return K[-1][1:]


def scan_drive(dr, t0, t1, rot_per_s=1.0, rays=180, S=None, drift=None, jitter=0.0, seed=1):
    """走りながら光を回したとき当たった点 (x, y, 生まれた秒)。drift があれば、思っている場所で置く（ずれた地図）"""
    import random as _r
    _r.seed(seed)
    S = S or segments()
    out = []
    n = int((t1 - t0) * rot_per_s * rays)
    for i in range(n):
        t = t0 + i / (rot_per_s * rays)
        x, y, th = dr.pose(t)
        a = 2 * math.pi * (i % rays) / rays + i * 0.0007
        h = ray(x, y, a, S)
        if not h: continue
        hx, hy = h[1]
        if jitter: hx += _r.gauss(0, jitter); hy += _r.gauss(0, jitter)
        if drift:
            ddx, ddy, dth = drift(t)
            c, s = math.cos(math.radians(dth)), math.sin(math.radians(dth))
            rx, ry = hx - x, hy - y
            hx, hy = x + ddx + rx * c - ry * s, y + ddy + rx * s + ry * c
        out.append((round(hx, 3), round(hy, 3), round(t, 3)))
    return out


def clearance(x, y, S):
    """(x, y) から、いちばん近い線分までの距離"""
    best = 9.0
    for (ax, ay), (bx, by) in S:
        ex, ey = bx - ax, by - ay; L = ex * ex + ey * ey or 1e-12
        t = max(0.0, min(1.0, ((x - ax) * ex + (y - ay) * ey) / L))
        best = min(best, math.hypot(x - ax - ex * t, y - ay - ey * t))
    return best


def bounce_path(start, face, n_bounce, seed, step=0.02, r=0.13, extra=()):
    """目の光を消したまるロボ・昔の先輩：まっすぐ進んで、ぶつかったら向きを変える。
       体の半径 r だけ壁から離れた所で止まる（斜めにぶつかっても壁にめりこまない）。出入り口は閉めておく"""
    import random as _r
    _r.seed(seed)
    S = segments() + [((ROOM[0], DOOR[0]), (ROOM[0], DOOR[1]))] + list(extra)
    x, y = start; a = math.radians(face + 90)
    pts = [(x, y)]; hits = []
    while len(hits) < n_bounce:
        moved = 0.0
        while clearance(x + math.cos(a) * step, y + math.sin(a) * step, S) > r and moved < 8.0:
            x += math.cos(a) * step; y += math.sin(a) * step; moved += step
        if moved > 0.05: pts.append((round(x, 3), round(y, 3)))
        hits.append((x, y))
        for _ in range(80):
            na = a + math.pi + math.radians(_r.uniform(-70, 70))
            ok = all(clearance(x + math.cos(na) * k * 0.1, y + math.sin(na) * k * 0.1, S) > r for k in range(1, 6))
            if ok: a = na; break
    return pts, hits
