# QRコード回：舞台B「スマホが見ている像の中」＝巨大なQRの大地（Blender 4.3）
#   使い方（PC）：blender -b -P qr_world.py -- --preview out.png  （試し描き）
#   ほかの場面の台本からは import qr_world as QW; W = QW.build(); QW.paint(W, ...) で使う
#   1マス＝MOD m（既定 1.5m）。まるロボ（高さ約1.2m）が1マスに立てる大きさ。
#   マスの色は「物の色（object color）」をキーにできるので、色分け・抜け殻・半透明の復元をコマ単位で切り替えられる。
import sys, os, json, math
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W

MOD = 1.5          # 1マスの大きさ（m）
TILE_H = 0.22      # マスの厚み
GAP = 0.035        # マスとマスの溝
QUIET = 4          # 余白のマス数
COL = {            # 色の決まり（台本の冒頭の決まりと同じ）
    "white": "#E9EEF2", "black": "#15191F",
    "finder": "#D9475A", "timing": "#3E9E62", "format": "#8C55B8",
    "data": "#3F86DD", "spare": "#F0953A", "broken": "#8A9097", "restored": "#7FE3F0",
}
ROLE_OF_LABEL = {"finder": "finder", "timing": "timing", "format": "format", "dark": "format", "align": "finder"}


def load_assets(path=None):
    return json.load(open(path or os.path.join(HERE, "qr_assets.json"), encoding="utf-8"))


def tile_material():
    """1つの材質を全部のマスで使う。色と透け具合は物の色（RGBA）から"""
    m = bpy.data.materials.new("QR tile"); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(oi.outputs["Color"], bs.inputs["Base Color"]); nt.links.new(oi.outputs["Alpha"], bs.inputs["Alpha"])
    bs.inputs["Roughness"].default_value = 0.42; bs.inputs["Coat Weight"].default_value = 0.0
    # 復元された箱だけ少し光る：アルファが 0.5 未満のときに発光を足す
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.5; nt.links.new(oi.outputs["Alpha"], lt.inputs[0])
    nt.links.new(oi.outputs["Color"], bs.inputs["Emission Color"]); nt.links.new(lt.outputs[0], bs.inputs["Emission Strength"])
    try: m.surface_render_method = "DITHERED"     # 不透明のマスはそのまま。抜け殻・復元だけアルファで透ける
    except Exception: pass
    m.diffuse_color = (0.8, 0.8, 0.8, 1)
    return m


def mixc(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def color_for(value, state):
    """value：黒=1/白=0。state：none/finder/timing/format/data/spare/broken/restored"""
    base = W.srgb(COL["black"] if value else COL["white"])
    if state in (None, "none"): return (*base, 1.0)
    if state == "broken": return (*mixc(W.srgb(COL["broken"]), base, 0.25), 0.55)
    if state == "restored": return (*mixc(W.srgb(COL["restored"]), base, 0.30), 0.35)
    tint = W.srgb(COL[state])
    return (*(mixc(base, tint, 0.38) if value else mixc(base, tint, 0.32)), 1.0)    # 白黒ははっきり残し、役割の色をうすく乗せる


def build(symbol="HELLO_H", mod=MOD, assets=None, coll_name="QR world"):
    A = assets or load_assets(); S = A["symbols"][symbol]; n = A["size"]; mtx = S["matrix"]
    coll = bpy.data.collections.new(coll_name); bpy.context.scene.collection.children.link(coll)
    tm = tile_material()
    origin = Vector((-(n * mod) / 2, (n * mod) / 2, 0))        # QRの左上の角。x＝列（右へ）、y＝行（手前へ −）
    def xy(r, c): return origin + Vector(((c + 0.5) * mod, -(r + 0.5) * mod, 0))
    # 余白（白い岸）と、その外の暗い床
    qz = W.box("Quiet zone", ((n + 2 * QUIET) * mod, (n + 2 * QUIET) * mod, TILE_H), W.mat("Quiet", W.srgb(COL["white"]), rough=0.5), bevel=0.06, coll=coll)
    qz.location = (0, 0, -TILE_H / 2 - 0.01)
    void = W.box("Void floor", (800, 800, 1.0), W.mat("Void", W.srgb("#0E1522"), rough=0.8), coll=coll); void.location = (0, 0, -TILE_H - 0.6)
    # 箱（8マス）ごとの親。持ち上げる・落とすは親を動かす
    box_par = {}
    for b, cells in A["boxes"].items():
        cen = sum((xy(r, c) for r, c in cells), Vector()) / len(cells)
        e = W.empty(f"Box {int(b):02d}", coll, size=0.4); e.location = cen; e["box"] = int(b)
        e["role"] = "data" if int(b) in S["data_boxes"] else "spare"; box_par[int(b)] = e
    tiles = {}
    for r in range(n):
        for c in range(n):
            v = mtx[r][c]; t = W.box(f"Tile {r:02d}-{c:02d}", (mod - GAP, mod - GAP, TILE_H), tm, bevel=0.03, seg=2, coll=coll)
            t["r"], t["c"], t["v"] = r, c, v
            t["label"] = A["function_labels"][r][c]; t["box"] = A["box_of"][r][c]
            p = xy(r, c); p.z = TILE_H / 2 + (0.04 if v else 0.0)        # 黒いマスを少しだけ高く（形で白黒が分かる）
            if t["box"]:
                par = box_par[t["box"]]; t.parent = par; t.location = p - par.location
            else:
                t.location = p
            t.color = color_for(v, None); tiles[(r, c)] = t
    return dict(assets=A, symbol=S, coll=coll, tiles=tiles, boxes=box_par, xy=xy, mod=mod, origin=origin)


def paint(Wd, cells, state, frame=None):
    """cells のマスを state の色に（frame を渡すとその時刻にキー）"""
    for rc in cells:
        t = Wd["tiles"][tuple(rc)]; t.color = color_for(t["v"], state)
        if frame is not None: t.keyframe_insert("color", frame=frame)


def cells_of(Wd, what):
    """what：'finder' 'timing' 'format' 'data' 'spare' または箱の番号の list"""
    A = Wd["assets"]; S = Wd["symbol"]; n = A["size"]; out = []
    for r in range(n):
        for c in range(n):
            lab = A["function_labels"][r][c]; b = A["box_of"][r][c]
            if isinstance(what, (list, tuple, set)):
                if b in what: out.append((r, c))
            elif what in ("finder", "timing", "format"):
                if ROLE_OF_LABEL.get(lab) == what: out.append((r, c))
            elif what == "data" and b and b in S["data_boxes"]: out.append((r, c))
            elif what == "spare" and b and b in S["spare_boxes"]: out.append((r, c))
    return out


def lift_box(Wd, b, h, frame=None):
    e = Wd["boxes"][b]; e.location.z = h
    if frame is not None: e.keyframe_insert("location", index=2, frame=frame)


def lights_c(scene, coll, center=Vector((0, 0, 0)), size=40.0):
    """作り物の世界（C案）：暗い空。上からの大きな面光源（5600K）と、斜め後ろからの月明かり（8000K）"""
    wd = bpy.data.worlds.new("QR void"); scene.world = wd; wd.use_nodes = True
    bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*W.srgb("#0B1220"), 1); bg.inputs[1].default_value = 1.0
    la = bpy.data.lights.new("Key area", "AREA"); la.shape = "DISK"; la.size = size * 1.2; la.energy = 52000; la.color = W.kelvin(5600)
    key = W.link(bpy.data.objects.new("Key area", la), coll); key.location = center + Vector((-6, 8, 34)); key.rotation_euler = (math.radians(12), math.radians(-8), 0)
    lm = bpy.data.lights.new("Moon", "SUN"); lm.energy = 1.2; lm.color = W.kelvin(8000); lm.angle = math.radians(3)
    moon = W.link(bpy.data.objects.new("Moon", lm), coll); moon.rotation_euler = (math.radians(58), 0, math.radians(200))
    return key, moon


def camera(scene, coll, loc, look, lens=24):
    cd = bpy.data.cameras.new("Cam"); cd.lens = lens; cd.clip_end = 600
    cam = W.link(bpy.data.objects.new("Cam", cd), coll); cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.camera = cam; return cam


def preview(out, view="hero", state="roles", engine="eevee", res=(960, 540)):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene; Wd = build()
    if state in ("roles", "lift"):
        paint(Wd, cells_of(Wd, "finder"), "finder"); paint(Wd, cells_of(Wd, "timing"), "timing"); paint(Wd, cells_of(Wd, "format"), "format")
        paint(Wd, cells_of(Wd, "data"), "data"); paint(Wd, cells_of(Wd, "spare"), "spare")
    if state == "lift":
        for b in range(1, 10): lift_box(Wd, b, 0.9 + 0.1 * b)
    if state == "restore":
        st = Wd["assets"]["experiments"]["robot_stand"]
        broken = st["bad_boxes"]; paint(Wd, cells_of(Wd, "spare"), "spare")
        paint(Wd, cells_of(Wd, broken[:len(broken)//2]), "restored"); paint(Wd, cells_of(Wd, broken[len(broken)//2:]), "broken")
    lights_c(sc, Wd["coll"])
    half = 21 * MOD / 2
    if view == "top": camera(sc, Wd["coll"], (0, 0, 62), (0, 0, 0), lens=35)
    elif view == "hero": camera(sc, Wd["coll"], (half * 0.95, -half * 1.15, 5.5), (-half * 0.25, half * 0.2, 0), lens=20)
    else: camera(sc, Wd["coll"], (half + 6, -half - 6, 2.2), (half - 6, -half + 6, 0.6), lens=18)
    W.render_setup(sc, engine=engine, res=res, samples=16)
    if engine == "cycles":
        sc.render.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.device = "CPU"; sc.cycles.use_denoising = True
        sc.view_settings.view_transform = "AgX"
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--preview" in argv:
        out = argv[argv.index("--preview") + 1]
        view = argv[argv.index("--view") + 1] if "--view" in argv else "hero"
        state = argv[argv.index("--state") + 1] if "--state" in argv else "roles"
        engine = argv[argv.index("--engine") + 1] if "--engine" in argv else "eevee"
        preview(out, view, state, engine)
