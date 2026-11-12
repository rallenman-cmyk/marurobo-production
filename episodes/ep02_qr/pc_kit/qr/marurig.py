# まるロボ（Blender の部品）に、marumotion の毎コマの姿勢を当てる
#   rig = MaruRig(bpy.data.objects["Maru"])     # 部品を名前で探し、足首の回転軸（靴と靴底の親）を足す
#   bk = Baker(); for i, fr in enumerate(frames): rig.apply(fr, i + 1, bk); bk.write()
# 予定の座標＝ルートの親の座標（親がなければ世界）。story.blend の「Maru」と maru_opening.blend の「MARU / pause」の両方で使える
import math, re
import numpy as np
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
import marumotion as mm


def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out


class Baker:
    """毎コマの値をため、最後にまとめてFカーブにする（速い）"""
    def __init__(self): self.ch = {}

    def put(self, idb, path, index, frame, value):
        self.ch.setdefault((idb.name, idb.__class__.__name__, path, index), [idb, []])[1].append((frame, float(value)))

    def write(self, interp="LINEAR"):
        for (nm, kind, path, index), (idb, kv) in self.ch.items():
            ad = idb.animation_data or idb.animation_data_create()
            if ad.action is None: ad.action = bpy.data.actions.new(nm + " action")
            fc = ad.action.fcurves.find(path, index=index) or ad.action.fcurves.new(path, index=index)
            kv.sort(); fc.keyframe_points.add(len(kv))
            fc.keyframe_points.foreach_set("co", np.array(kv, np.float32).ravel())
            fc.keyframe_points.foreach_set("interpolation", np.full(len(kv), 1 if interp == "LINEAR" else 0, np.int32))
            fc.update()


class MaruRig:
    def __init__(self, root, cradle_lift=mm.CRADLE_LIFT):
        self.root = root; H = hier(root)
        for o in H:                                              # 前の動きを消す（形と置き場所は残す）
            if o.animation_data:
                mb = o.matrix_basis.copy(); o.animation_data_clear(); o.matrix_basis = mb
        find = lambda pred: next((o for o in H if pred(o)), None)
        self.torso = find(lambda o: o.name.endswith("• torso"))
        self.legs = sorted([o for o in H if re.search(r"• leg(\.\d+)?$", o.name)], key=lambda o: o.location.x)   # 左（x−）、右
        self.antenna = find(lambda o: "• antenna" in o.name)
        self.cradle = find(lambda o: "cradle" in o.name and "•" in o.name)
        self.iris = find(lambda o: o.name.startswith("Inner lens ring"))
        self.light = find(lambda o: o.name.startswith("Antenna light"))
        self.cargo = find(lambda o: o.name.startswith("Maru cargo") and o.type == "EMPTY")
        assert self.torso and len(self.legs) == 2, "まるロボの部品が見つからない"
        bpy.context.view_layer.update()
        # 足首の回転軸：脚の子、足首の位置。靴と靴底をその子にする（足が地面で平らに置けるように）
        self.pivots = []
        for leg in self.legs:
            piv = bpy.data.objects.new(leg.name + " ankle", None); piv.empty_display_size = 0.05
            for c in leg.users_collection: c.objects.link(piv)
            piv.parent = leg; piv.matrix_parent_inverse = Matrix.Identity(4); piv.location = (0, 0, -mm.ANKLE)
            bpy.context.view_layer.update()
            for ch in list(leg.children):
                if ch.name.startswith(("Soft boot", "Boot sole")):
                    mw = ch.matrix_world.copy(); ch.parent = piv; ch.matrix_parent_inverse = Matrix.Identity(4)
                    bpy.context.view_layer.update(); ch.matrix_basis = piv.matrix_world.inverted() @ mw
            self.pivots.append(piv)
        bpy.context.view_layer.update()
        self.ctrl = [o for o in [root, self.torso, *self.legs, *self.pivots, self.antenna, self.cradle, self.iris, self.cargo] if o]
        for o in self.ctrl: o.rotation_mode = "QUATERNION"
        self.rest = {o.name: o.matrix_basis.copy() for o in self.ctrl}
        self.PI = {o.name: o.matrix_parent_inverse.copy() for o in self.ctrl}
        self.rest_local = {o.name: self.PI[o.name] @ self.rest[o.name] for o in self.ctrl}      # 親から見た休みの形
        # 荷台の板は荷物のトレーにする（荷物と一緒に受け渡す）。頭には小さな受け皿を付け、回転軸を頭のてっぺんへ移す
        if self.cradle:
            L = self.rest_local[self.cradle.name].copy(); L.translation = Vector(tuple(float(v) for v in mm.CRADLE)); self.rest_local[self.cradle.name] = L
        if self.cargo:
            L = self.rest_local[self.cargo.name].copy(); L.translation = Vector((0.0, 0.0, float(mm.CARGO_Z))); self.rest_local[self.cargo.name] = L
        self.saddle = None
        if self.cradle and self.cargo:
            bpy.context.view_layer.update()
            cargo_set0 = set(hier(self.cargo))
            plate = [o for o in hier(self.cradle) if o.type == "MESH" and o not in cargo_set0]
            body = [c for c in self.cargo.children]
            for c in body:                                       # 箱と札を 3cm 上へ（トレーの分）
                c.location.z += (mm.CARGO_HALF[1] - 0.34)
            mat_t = plate[0].active_material if plate else None
            for o in plate:                                      # 板 → トレー（箱の下、厚さ6cm）。底を荷物の底（受け皿の上面）の 1mm 上にそろえる
                o.parent = self.cargo; o.matrix_parent_inverse = Matrix.Identity(4)
                zs = [v[2] for v in o.bound_box]; h0 = max(zs) - min(zs)
                if o.name.startswith("Cradle"):
                    sz = o.scale.z * (mm.TRAY_H / (h0 * o.scale.z) if h0 > 1e-6 else 1.0)
                    o.scale = (o.scale.x, o.scale.y, sz); o.location = (o.location.x, o.location.y, -mm.CARGO_HALF[1] + 0.001 - min(zs) * sz)
                else:                                            # 前の荷台の真鍮の縁：トレーでは箱の下に隠れるので、描かない
                    o.hide_render = True; o.hide_viewport = True; o["keep_hidden"] = True
            import bmesh as _bm
            me = bpy.data.meshes.new(root.name + " saddle"); bmx = _bm.new()
            _bm.ops.create_cone(bmx, cap_ends=True, segments=40, radius1=mm.SADDLE_R, radius2=mm.SADDLE_R, depth=0.02); bmx.to_mesh(me); bmx.free()
            for p_ in me.polygons: p_.use_smooth = True
            sd = bpy.data.objects.new(root.name + " saddle", me)
            for c in self.cradle.users_collection: c.objects.link(sd)
            sd.parent = self.cradle; sd.matrix_parent_inverse = Matrix.Identity(4); sd.location = (0.0, 0.0, mm.CRADLE_TOP - 0.01)
            if mat_t: me.materials.append(mat_t)
            self.saddle = sd
        self.leg_hip = [self.rest_local[l.name].translation.copy() for l in self.legs]
        self.prev_q = {}
        # アンテナの光：このロボ専用の材質にして、明るさを動かす
        self.light_in = None; self.light_base = 1.6
        if self.light and self.light.data.materials:
            m = self.light.data.materials[0].copy(); m.name = root.name + " antenna light"; self.light.data.materials[0] = m
            for n in m.node_tree.nodes:
                if n.bl_idname == "ShaderNodeBsdfPrincipled":
                    self.light_in = (m.node_tree, 'nodes["%s"].inputs["Emission Strength"].default_value' % n.name)
                    self.light_base = n.inputs["Emission Strength"].default_value
        self.cargo_meshes = [o for o in hier(self.cargo) if o.type == "MESH" and not o.get("keep_hidden")] if self.cargo else []
        cargo_set = set(self.cargo_meshes)
        self.cradle_meshes = [o for o in hier(self.cradle) if o.type == "MESH" and o not in cargo_set] if self.cradle else []

    # ---------------------------------------------------------- 世界の座標（ほかの物をまるロボに合わせて動かすため）
    def world_mats(self, fr):
        """1コマの姿勢 → 世界の行列 {root, torso, cradle, cargo}（apply と同じ計算。cargo は荷物＝トレーの中心）。
        背中の受け皿に載せた物（バケツなど）は cargo の行列 @ (0, 0, TRAY_TOP) に置けばよい"""
        x, y, z = fr["root"]; psi = fr["psi"]
        M_root = Matrix.Translation((x, y, z)) @ Matrix.Rotation(psi, 4, "Z")
        Rl = Euler((-math.radians(fr["pitch"]), -math.radians(fr["roll"]), math.radians(fr["twist"])), "YXZ").to_matrix()
        Pv = Vector((0, 0, mm.HIP_Z)); T = Vector((0, 0, mm.TORSO_Z))
        M_t = M_root @ Matrix.Translation(Pv + Rl @ (T - Pv)) @ Rl.to_4x4()
        out = dict(root=M_root, torso=M_t)
        if self.cradle:
            out_c = fr.get("cradle_out", 1.0)
            L_c = Matrix.Translation((0, 0, -(1.0 - out_c) * mm.SADDLE_DROP)) @ self.rest_local[self.cradle.name] @ Matrix.Rotation(-math.radians(fr["cradle"]), 4, "X")
            out["cradle"] = M_t @ L_c
            if self.cargo:
                c = fr["cargo"]
                out["cargo"] = (M_t @ L_c @ Matrix.Translation((0, c[1], 0)) @ self.rest_local[self.cargo.name]) if c[0] == "on" else Matrix([list(r) for r in c[1]])
        return out

    TRAY_TOP = -mm.CARGO_HALF[1] + 0.001 + mm.TRAY_H                # 荷物の中心 → トレーの上面

    # ---------------------------------------------------------- 書き込み
    def _put(self, bk, o, L, f, scale=False):
        """L＝親から見た形（4×4）。matrix_basis = 親の逆行列⁻¹ @ L"""
        B = self.PI[o.name].inverted() @ L
        loc, q, sc = B.decompose()
        p = self.prev_q.get(o.name)
        if p is not None and p.dot(q) < 0: q = -q
        self.prev_q[o.name] = q
        for i in range(3): bk.put(o, "location", i, f, loc[i])
        for i in range(4): bk.put(o, "rotation_quaternion", i, f, q[i])
        if scale:
            for i in range(3): bk.put(o, "scale", i, f, sc[i])

    def apply(self, fr, f, bk):
        x, y, z = fr["root"]; psi = fr["psi"]
        M_root = Matrix.Translation((x, y, z)) @ Matrix.Rotation(psi, 4, "Z")
        self._put(bk, self.root, M_root, f)
        # 胴：脚の付け根の高さを中心に前後・左右に傾き、上でひねる（Rz・Rx・Ry の順）
        Rl = Euler((-math.radians(fr["pitch"]), -math.radians(fr["roll"]), math.radians(fr["twist"])), "YXZ").to_matrix()
        Pv = Vector((0, 0, mm.HIP_Z)); T = Vector((0, 0, mm.TORSO_Z))
        L_t = Matrix.Translation(Pv + Rl @ (T - Pv)) @ Rl.to_4x4()
        self._put(bk, self.torso, L_t, f)
        M_t = M_root @ L_t
        # 脚：付け根から足首へ向け、長さは伸び縮み（脚の上の端は胴の中に隠れる）。足首の軸で靴を地面の向きへ
        Mi = M_root.inverted()
        for j, (leg, piv) in enumerate(zip(self.legs, self.pivots)):
            ft = fr["feet"][j]
            A = Mi @ Vector(ft["ankle"]); Hh = self.leg_hip[j]
            d = A - Hh; n = max(d.length, 1e-6); dh = d / n
            q = Vector((0, 0, -1)).rotation_difference(dh)
            L_leg = Matrix.Translation(Hh + dh * (n - mm.ANKLE)) @ q.to_matrix().to_4x4()
            self._put(bk, leg, L_leg, f)
            R_leg_w = (M_root @ L_leg).to_3x3()
            R_f = (Matrix.Rotation(ft["psi"], 3, "Z") @ Matrix.Rotation(math.radians(ft["pitch"]), 3, "X"))
            L_p = (R_leg_w.inverted() @ R_f).to_4x4(); L_p.translation = Vector((0, 0, -mm.ANKLE))
            self._put(bk, piv, L_p, f)
        # アンテナ：休みの形に、根元のばねの振れを足す（胴の座標で、前へ ay・右へ ax）
        if self.antenna:
            ay, ax = fr["ant"]; R0 = self.rest_local[self.antenna.name]
            D = Matrix.Rotation(-ay, 4, "X") @ Matrix.Rotation(ax, 4, "Y")
            L_a = Matrix.Translation(R0.translation) @ D @ R0.to_3x3().to_4x4()
            ext = fr.get("ant_ext", 1.0)                           # 荷台を出す間は、軸の向きに体の中へしまう
            if ext < 0.999: L_a = L_a @ Matrix.Translation(Vector(mm.ANT_TIP).normalized() * (-mm.ANT_RETRACT * (1.0 - ext)))
            self._put(bk, self.antenna, L_a, f)
        # 目：内側の輪の大きさ（まばたき・見開き）、視線、ズーム（前へ）。輪はレンズの丸い面に沿って転がるように動く
        #   （ずらすだけだと片側がレンズの面の奥に沈み、ガラスの屈折でゆがんで見える）
        if self.iris:
            ir = fr["iris"]; s = ir["scale"]; R0 = self.rest_local[self.iris.name]
            Ln = mm.LENS; rr = min(Ln["ring_r"] * s, Ln["r"] * 0.999)
            yy = Ln["y"] + Ln["depth"] * math.sqrt(max(0.0, 1 - (rr / Ln["r"]) ** 2)) + 0.013 * s + ir["zoom"]
            loc0, rot0, sc0 = R0.decompose()
            C = Vector((0.0, yy, Ln["z"])); P = C - Vector((0.0, 0.5, 0.0))           # 面の曲がりの中心（半径 0.5m）
            Rg = Matrix.Rotation(-ir["dx"] / 0.5, 4, "Z") @ Matrix.Rotation(ir["dz"] / 0.5, 4, "X")
            L_i = Matrix.Translation(P) @ Rg @ Matrix.Translation(C - P) @ rot0.to_matrix().to_4x4() @ Matrix.Diagonal((*(sc0 * s), 1.0))
            self._put(bk, self.iris, L_i, f, scale=True)
        # 荷台の傾き（＋＝前が下がる）
        L_c = None
        if self.cradle:
            R0 = self.rest_local[self.cradle.name]
            out = fr.get("cradle_out", 1.0)
            L_c = Matrix.Translation((0, 0, -(1.0 - out) * mm.SADDLE_DROP)) @ R0 @ Matrix.Rotation(-math.radians(fr["cradle"]), 4, "X")
            self._put(bk, self.cradle, L_c, f)                    # 受け皿は使わないとき 2.5cm 下がる（頭のてっぺんにそろう）
        # 荷物：運ぶ間はベルトのばねで前後に、降ろしたら世界の位置（荷台から見た形に直す）
        if self.cargo and L_c is not None:
            c = fr["cargo"]; R0 = self.rest_local[self.cargo.name]
            if c[0] == "on":
                L_g = Matrix.Translation((0, c[1], 0)) @ R0
            else:
                Mw = Matrix([list(r) for r in c[1]]); L_g = (M_t @ L_c).inverted() @ Mw
            self._put(bk, self.cargo, L_g, f)
            vis = fr.get("cargo_vis", fr["carry"])
            for o in self.cargo_meshes:
                bk.put(o, "hide_render", 0, f, 0.0 if vis else 1.0); bk.put(o, "hide_viewport", 0, f, 0.0 if vis else 1.0)
        # アンテナの光
        if self.light_in:
            bk.put(self.light_in[0], self.light_in[1], 0, f, self.light_base * fr["light"])
