# 保存した場面を開き、光の強さ・露出・人ごとの色（物体の属性）だけ変えて描く（色合わせ用に速く）
# 使い方: blender -b BLEND --python relight.py -- OUT.png W H SAMPLES CONFIG.json
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
out, W, H, S, cfg = a[0], int(a[1]), int(a[2]), int(a[3]), json.load(open(a[4]))
def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type == "LIGHT" and ob.name in cfg.get("lights", {}): ob.data.energy = cfg["lights"][ob.name]
if "world" in cfg: sc.world.node_tree.nodes["Background"].inputs[1].default_value = cfg["world"]
for who, cols in cfg.get("colors", {}).items():
    for ob in sc.objects:
        if ob.name.startswith(who + " "):
            for k, v in cols.items():
                if k in ob.keys(): ob[k] = srgb(v)
for mname, vals in cfg.get("materials", {}).items():
    m = bpy.data.materials.get(mname)
    if m is None: continue
    for nd in m.node_tree.nodes:
        if nd.type == "BSDF_PRINCIPLED":
            for k, v in vals.items(): nd.inputs[k].default_value = v
for arm_name, bones in cfg.get("bone_loc", {}).items():     # 骨の位置を少しずらす（眉を上げるなど）
    arm = sc.objects.get(arm_name)
    if arm is None: continue
    for bn, loc in bones.items(): arm.pose.bones[bn].location = loc
sc.view_settings.exposure = cfg.get("exposure", 0.0); sc.render.resolution_x, sc.render.resolution_y = W, H; sc.eevee.taa_render_samples = S
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
if cfg.get("save"): bpy.ops.wm.save_as_mainfile(filepath=cfg["save"])
print("DONE", out)
