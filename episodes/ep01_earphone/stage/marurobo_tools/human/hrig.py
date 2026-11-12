# 骨格を動かす：順運動学（親から順に）、2関節の逆運動学（腕・脚）、視線、キーフレームの書き込み
import math
import numpy as np
from mathutils import Matrix, Quaternion, Vector


def qaxis(axis, deg):
    return Quaternion(Vector(axis).normalized(), math.radians(deg))


def m3(M): return np.array([[M[i][j] for j in range(3)] for i in range(3)])


def to_mat4(R, t):
    M = Matrix.Identity(4)
    for i in range(3):
        for j in range(3): M[i][j] = float(R[i, j])
        M[i][3] = float(t[i])
    return M


def norm(v):
    v = np.asarray(v, float); n = np.linalg.norm(v); return v / n if n > 1e-12 else v


class Rig:
    def __init__(self, arm_ob):
        self.ob = arm_ob; bones = arm_ob.data.bones
        self.names = [b.name for b in bones]
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in bones}
        depth = {}
        def dep(n): return 0 if self.parent[n] is None else 1 + dep(self.parent[n])
        self.order = sorted(self.names, key=dep)
        self.rest = {b.name: b.matrix_local.copy() for b in bones}
        self.rel = {n: (self.rest[self.parent[n]].inverted() @ self.rest[n]) if self.parent[n] else self.rest[n].copy() for n in self.names}
        self.length = {b.name: b.length for b in bones}
        self.reset()

    def reset(self):
        self.q = {n: Quaternion() for n in self.names}; self.loc = {n: Vector((0, 0, 0)) for n in self.names}

    # ---- 局所の回転（骨の向きを基準：X＝曲げ、Z＝横、Y＝ねじり）
    def rot(self, n, x=0.0, y=0.0, z=0.0, add=False):
        q = qaxis((0, 0, 1), z) @ qaxis((1, 0, 0), x) @ qaxis((0, 1, 0), y)
        self.q[n] = (self.q[n] @ q) if add else q

    def fk(self):
        M = {}
        for n in self.order:
            B = Matrix.Translation(self.loc[n]) @ self.q[n].to_matrix().to_4x4()
            p = self.parent[n]
            M[n] = (M[p] @ self.rel[n] @ B) if p else (self.rel[n] @ B)
        self.M = M
        return M

    def head_pos(self, n): return np.array(self.M[n].translation)
    def tail_pos(self, n): return np.array((self.M[n] @ Vector((0, self.length[n], 0, 1)))[:3]) if False else np.array(self.M[n] @ Vector((0, self.length[n], 0)))

    def set_world_rot(self, n, Rdes):
        """骨 n の姿勢（骨格空間の3x3）を指定 → 局所回転を逆算"""
        p = self.parent[n]
        Pm = (self.M[p] @ self.rel[n]) if p else self.rel[n]
        Rl = m3(Pm).T @ Rdes
        self.q[n] = to_mat4(Rl, (0, 0, 0)).to_quaternion()
        self.fk_one(n)

    def fk_one(self, n):
        p = self.parent[n]; B = Matrix.Translation(self.loc[n]) @ self.q[n].to_matrix().to_4x4()
        self.M[n] = (self.M[p] @ self.rel[n] @ B) if p else (self.rel[n] @ B)
        # 子も更新
        for c in self.order:
            if self.parent[c] == n: self.fk_one(c)

    def ik2(self, upper, lower, target, pole, end=None, end_R=None):
        """2関節の逆運動学。target＝lower の先端（手首・足首）の位置、pole＝ひじ／ひざを向ける方向"""
        S = self.head_pos(upper); L1 = self.length[upper]; L2 = self.length[lower]
        d = np.asarray(target, float) - S; D = np.linalg.norm(d)
        D = min(max(D, abs(L1 - L2) + 1e-4), L1 + L2 - 1e-4); u = d / max(np.linalg.norm(d), 1e-9)
        a = (L1 * L1 - L2 * L2 + D * D) / (2 * D); hh = math.sqrt(max(L1 * L1 - a * a, 0.0))
        pp = np.asarray(pole, float); pp = norm(pp - (pp @ u) * u)
        E = S + u * a + pp * hh; T = S + u * D
        Y1, Y2 = norm(E - S), norm(T - E)
        # 休みの姿勢での「曲げの面」に対する骨のロールを保つ
        R1r, R2r = m3(self.rest[upper]), m3(self.rest[lower])
        n_r = np.cross(R1r[:, 1], R2r[:, 1]); n_r = norm(n_r) if np.linalg.norm(n_r) > 1e-6 else R1r[:, 0]
        n = np.cross(Y1, Y2); n = norm(n) if np.linalg.norm(n) > 1e-6 else norm(np.cross(Y1, pp))
        for bn, Y, Rr in ((upper, Y1, R1r), (lower, Y2, R2r)):
            Yr = Rr[:, 1]; Xr = Rr[:, 0]
            b1 = n_r; b2 = np.cross(Yr, n_r)
            th = math.atan2(Xr @ b2, Xr @ b1)
            X = math.cos(th) * n + math.sin(th) * np.cross(Y, n); X = norm(X - (X @ Y) * Y)
            Z = np.cross(X, Y)
            self.set_world_rot(bn, np.stack([X, Y, Z], 1))
        if end is not None and end_R is not None:
            self.set_world_rot(end, end_R)
        return E

    def posed_point(self, bone, p_rest):
        """休み姿勢で骨 bone に固定された点が、今どこにあるか（骨格空間）"""
        v = self.M[bone] @ self.rest[bone].inverted() @ Vector(tuple(float(x) for x in p_rest))
        return np.array(v)

    def look(self, eye, target, max_yaw=38.0, max_pitch=28.0):
        """目の骨を target（骨格空間）へ向ける（頭に対する角度で制限）"""
        Mh = self.M[self.parent[eye]] @ self.rel[eye]
        R = m3(Mh); p = np.array(Mh.translation)
        d = R.T @ norm(np.asarray(target) - p)   # 目の休み姿勢の座標で：+Y＝前、+Z＝上、+X＝右(人物の)
        yaw = math.degrees(math.atan2(-d[0], d[1])); pitch = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
        yaw = max(-max_yaw, min(max_yaw, yaw)); pitch = max(-max_pitch, min(max_pitch, pitch))
        g = getattr(self, "eye_gain", 1.0)
        self.rot(eye, x=pitch * g, z=yaw * g); self.fk_one(eye)
        return yaw, pitch


class Baker:
    """毎コマの値をため、最後にまとめてFカーブにする（速い）"""
    def __init__(self): self.ch = {}

    def put(self, idb, path, index, frame, value, group=None):
        self.ch.setdefault((idb.name, idb.__class__.__name__, path, index, group), [idb, []])[1].append((frame, float(value)))

    def pose(self, rig, frame, bones=None):
        for n in (bones or rig.names):
            pb_path = f'pose.bones["{n}"]'
            q = rig.q[n]
            for i in range(4): self.put(rig.ob, pb_path + ".rotation_quaternion", i, frame, q[i], n)
            if n in ("hips", "brow.L", "brow.R"):
                for i in range(3): self.put(rig.ob, pb_path + ".location", i, frame, rig.loc[n][i], n)

    def write(self, interp="LINEAR"):
        for (nm, kind, path, index, group), (idb, kv) in self.ch.items():
            ad = idb.animation_data or idb.animation_data_create()
            if ad.action is None:
                import bpy
                ad.action = bpy.data.actions.new(nm + " action")
            act = ad.action
            fc = act.fcurves.find(path, index=index) or act.fcurves.new(path, index=index, action_group=group or "")
            kv.sort()
            fc.keyframe_points.add(len(kv))
            co = np.array(kv, np.float32).ravel()
            fc.keyframe_points.foreach_set("co", co)
            fc.keyframe_points.foreach_set("interpolation", np.full(len(kv), 1 if interp == "LINEAR" else 2, np.int32))
            fc.update()
