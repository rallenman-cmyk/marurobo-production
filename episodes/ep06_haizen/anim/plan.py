# 6本目（配膳ロボット）：ファミレスの間取り（3D の店・上から見た地図・光の物差しの点を、全部ここから作る。形が必ずそろう）
# bpy を使わない（Blender でも、ふつうの python でも読める）
# 単位はメートル。x＝右、y＝奥、z＝上。店は x -3.6〜3.6、y -3.2〜3.4、天井 2.7
# 5本目（掃除機）の plan.py の考え方（光を当てて、当たった所を点にする）を使い、ファミレスの形にした
import math

ROOM = (-3.6, -3.2, 3.6, 3.4)
CEIL = 2.7
LIDAR_Z = 0.30             # 回る光の物差しの高さ（この高さを、水平にぐるりと見る）
AISLE = 0.0                # 通路のまん中（x）
KITCHEN = (-0.75, 0.75)    # 奥の壁の、台所の出口（x の範囲）
WAIT = (0.0, 2.75)         # 先輩が料理を待つ所（台所の出口の前）

# テーブル（4 人がけ・正方形 0.9 m）。番号 → (x, y)。通路の左右に 3 つずつ
TABLE = {10: (1.45, 1.35), 11: (1.45, -0.25), 12: (1.45, -1.85),
         20: (-1.45, 1.35), 21: (-1.45, -0.25), 22: (-1.45, -1.85)}
TSIZE = 0.9
TLEG = 0.06
# いす：テーブルの通路がわ（in）と壁がわ（out）に 1 つずつ。通路がわのいすの前の端は x=±0.55
CHAIR_D = 0.45


def chair_pos(n, side, pull=0.0):
    """テーブル n の、通路がわ（side='in'）か壁がわ（'out'）のいすの真ん中（pull＝通路へ引き出す長さ）"""
    x, y = TABLE[n]; sg = 1 if x > 0 else -1
    if side == 'in':
        return (x - sg * (TSIZE / 2 + CHAIR_D / 2 - 0.08 + pull), y)
    return (x + sg * (TSIZE / 2 + CHAIR_D / 2 - 0.08), y)


def seat_point(n):
    """席の点：先輩がここで止まれば、その席に料理が届く（通路の中、テーブルの横）"""
    x, y = TABLE[n]; sg = 1 if x > 0 else -1
    return (sg * 0.32, y)


def table_legs(n):
    x, y = TABLE[n]; d = TSIZE / 2 - 0.07
    return [(x - d, y - d), (x + d, y - d), (x - d, y + d), (x + d, y + d)]


def chair_legs(c):
    x, y = c; d = 0.17
    return [(x - d, y - d), (x + d, y - d), (x - d, y + d), (x + d, y + d)]


def _box(cx, cy, h):
    return [((cx - h, cy - h), (cx + h, cy - h)), ((cx + h, cy - h), (cx + h, cy + h)), ((cx + h, cy + h), (cx - h, cy + h)), ((cx - h, cy + h), (cx - h, cy - h))]


def segments(pull=None):
    """光の物差しの高さで見える線分（壁・テーブルの脚・いすの脚）。pull：{テーブル番号: 引き出す長さ}"""
    x0, y0, x1, y1 = ROOM
    S = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x0, y0), (x0, y1)),
         ((x0, y1), (KITCHEN[0], y1)), ((KITCHEN[1], y1), (x1, y1))]
    # 台所の出口の奥（台所の台）
    S.append(((KITCHEN[0], y1 + 0.9), (KITCHEN[1], y1 + 0.9)))
    for n in TABLE:
        for (lx, ly) in table_legs(n): S += _box(lx, ly, TLEG / 2)
        for side in ('in', 'out'):
            c = chair_pos(n, side, (pull or {}).get(n, 0.0) if side == 'in' else 0.0)
            for (lx, ly) in chair_legs(c): S += _box(lx, ly, 0.02)
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


def ray_circles(px, py, ang, C, maxd=8.0):
    """円（人の足・まるロボ）への当たり。C：[(cx, cy, r)]"""
    dx, dy = math.cos(ang), math.sin(ang); best = None
    for cx, cy, r in C:
        fx, fy = px - cx, py - cy
        b = fx * dx + fy * dy; c = fx * fx + fy * fy - r * r; disc = b * b - c
        if disc < 0: continue
        t = -b - math.sqrt(disc)
        if 1e-3 < t < maxd and (best is None or t < best): best = t
    if best is None: return None
    return best, (px + dx * best, py + dy * best)


def face_deg(dx, dy):
    """進む向き (dx, dy) → 体の向き（度）。前＝-y を 0 度とする（まるロボと同じ決め方）"""
    return math.degrees(math.atan2(dx, -dy))


class Drive:
    """道 pts を、t0 から速さ v（m/秒）で走る。角では少し遅くなって曲がる（なめらかに。22 章）
       pose(t) → (x, y, 向き[度])"""
    def __init__(self, pts, t0, v=0.55, turn=90.0, face0=None, wait=0.0):
        self.keys = []
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
                k = k * k * (3 - 2 * k)          # 走り出し・止まりはなめらかに（スープをこぼさない）
                return (a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k)
        return K[-1][1:]


def scan(pose_at, t0, t1, rot_per_s=1.0, rays=160, S=None, people=None, maxd=7.0, pull=None):
    """t0〜t1 秒、光を回したとき当たった点。止まった物 → (x, y, 秒)、動く物（人の足） → (x, y, 秒)
       pose_at(t) → (x, y)。people(t) → [(cx, cy, r)]（その時刻の人の足の円）"""
    S = S or segments(pull)
    still, moving = [], []
    n = int((t1 - t0) * rot_per_s * rays)
    for i in range(n):
        t = t0 + i / (rot_per_s * rays)
        x, y = pose_at(t)
        a = 2 * math.pi * (i % rays) / rays + i * 0.0009
        h = ray(x, y, a, S, maxd)
        hc = ray_circles(x, y, a, people(t), maxd) if people else None
        if hc and (not h or hc[0] < h[0]):
            moving.append((round(hc[1][0], 3), round(hc[1][1], 3), round(t, 3)))
        elif h:
            still.append((round(h[1][0], 3), round(h[1][1], 3), round(t, 3)))
    return still, moving


# 天井の目印（シール）：1.2 m ごと。上を向いたカメラで見る（11 章）
CEIL_MARKS = [(x * 1.2, y * 1.2 - 0.2) for x in range(-2, 3) for y in range(-2, 3)]

# 12 番の席までの道（台所の出口 → 通路 → 12 番の席の点）
ROUTE12 = [WAIT, (0.0, 1.6), (0.0, -1.2), seat_point(12)]
