# Stage "earbud reception" built from the user's sketch.
# Usage: blender -b hero.blend --python build_stage.py -- <mode:layout|render> <outdir> <variants:A,B,C> <json-params>
import bpy, bmesh, sys, math, json, os, random, time
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if len(argv) > 0 else "layout"
OUT = argv[1] if len(argv) > 1 else "/tmp"
VARIANTS = argv[2].split(",") if len(argv) > 2 else ["A", "B", "C"]
P = json.loads(argv[3]) if len(argv) > 3 else {}

def p(key, default):
    return P.get(key, default)

scene = bpy.context.scene
scene.frame_set(1)
O = bpy.data.objects

def hier(o):
    out = [o]
    for c in o.children:
        out += hier(c)
    return out

# --- freeze everything at frame 1 (the robot stands still with its parcel) ---
for ob in list(O):
    if ob.animation_data:
        loc, rot, scl, hr = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy(), ob.hide_render
        ob.animation_data_clear()
        ob.location, ob.rotation_euler, ob.scale, ob.hide_render = loc, rot, scl, hr
for coll in (bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds, bpy.data.meshes):
    for idb in coll:
        if getattr(idb, "animation_data", None):
            idb.animation_data_clear()
        nt = getattr(idb, "node_tree", None)
        if nt and nt.animation_data:
            nt.animation_data_clear()

maru, earbud, floor = O["Maru"], O["Earbud exterior"], O["Shared slate floor"]
keep = set(hier(maru)) | set(hier(earbud)) | {floor}
floor.scale = (6, 6, 1)
for ob in list(O):
    if ob.type == "LIGHT":
        O.remove(ob, do_unlink=True)
        continue
    if ob not in keep and ob.type != "CAMERA":
        ob.hide_render = True
        ob.hide_viewport = True

# --- layout numbers (stage metres) ---
STEM = Vector((0.0, 11.12, 0.0)); STEM_R = 1.38
R = Vector(p("robot", [-3.6, 5.0]) + [0.0])
dir_to_robot = (R - STEM).normalized()
W = STEM + dir_to_robot * (STEM_R + 0.12); W.z = p("win_z", 1.95)
earbud.location, earbud.rotation_euler, earbud.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
d = W - R
maru.location = (R.x, R.y, 0.06)
maru.rotation_euler = (0, 0, math.radians(p('robot_yaw_deg', math.degrees(math.atan2(-d.x, d.y)))))

def mat_emit(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0])
    return m

def box(name, dims, loc, rot_z, mat, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2]))
    bm.to_mesh(me); bm.free()
    ob = O.new(name, me); scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (0, 0, rot_z)
    if bevel > 0:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = 4; b.limit_method = "ANGLE"
    me.materials.append(mat)
    return ob

def torus(name, major, minor, loc, rot, mat, seg=48, rseg=12):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg; r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        for j in range(rseg):
            bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % rseg], rings[i][(j + 1) % rseg]))
    bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    ob = O.new(name, me); scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; me.materials.append(mat)
    return ob

# --- reception window on the stem, facing the robot ("音を受けとる") ---
yaw_w = math.atan2(dir_to_robot.x, -dir_to_robot.y)   # local -Y faces the robot
frame_mat = bpy.data.materials.get("Petrol aluminium")
glow = mat_emit("Reception glow", (0.25, 0.95, 0.88), 3.0)
mark = mat_emit("Own mark glow", (0.25, 0.95, 0.88), 4.0)
box("Reception frame", (1.9, 0.5, 2.3), W, yaw_w, frame_mat, bevel=0.12)
fwd = Vector((math.sin(yaw_w), -math.cos(yaw_w), 0))      # world direction of local -Y
box("Reception opening", (1.45, 0.06, 1.85), W + fwd * 0.24, yaw_w, glow, bevel=0.03)
torus("Own mark ring", 0.32, 0.055, W + fwd * 0.2 + Vector((0, 0, 1.7)), (math.pi / 2, 0, yaw_w), mark)

# --- the neighbour's earbud (right foreground, cut by the frame) ---
mapping = {}
for ob in hier(earbud):
    new = ob.copy(); scene.collection.objects.link(new); mapping[ob] = new
for ob, new in mapping.items():
    if ob.parent in mapping:
        new.parent = mapping[ob.parent]; new.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
warm = bpy.data.materials.get("Neighbor ceramic")
for new in mapping.values():
    if new.type == "MESH":
        for slot in new.material_slots:
            if slot.material and slot.material.name.startswith("Porcelain") and warm:
                slot.link = "OBJECT"; slot.material = warm
nb = mapping[earbud]; s = p("nb_scale", 0.22); yaw_n = math.radians(p("nb_yaw", 200))
N = Vector(p("nb_stem", [3.4, 0.6]) + [0.0])
rot = Matrix.Rotation(yaw_n, 4, "Z")
nb.scale = (s, s, s); nb.rotation_euler = (0, 0, yaw_n)
nb.location = N - (rot @ (STEM * s)).to_3d()

# --- floating motes between the robot and the earbud (the small marks in the sketch) ---
mote_mat = mat_emit("Mote glow", (0.75, 1.0, 1.0), 2.0)
me = bpy.data.meshes.new("Motes"); bm = bmesh.new(); rnd = random.Random(7)
for i in range(55):
    c = Vector((rnd.uniform(-8, 3), rnd.uniform(-2, 10), rnd.uniform(0.4, 6.5)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rnd.uniform(0.012, 0.03), matrix=Matrix.Translation(c))
bm.to_mesh(me); bm.free(); motes = O.new("Motes", me); scene.collection.objects.link(motes); me.materials.append(mote_mat)

# --- camera ---
cam_data = bpy.data.cameras.new("Sketch camera"); cam = O.new("Sketch camera", cam_data); scene.collection.objects.link(cam)
cam.location = Vector(p("cam", [-6.5, -3.5, 1.1])); tgt = Vector(p("tgt", [0.0, 9.5, 5.5]))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
cam_data.lens = p("lens", 24); cam_data.sensor_width = 36; cam_data.clip_end = 400
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = p("res", [960, 540]); scene.render.resolution_percentage = 100

def proj(label, v):
    c = world_to_camera_view(scene, cam, Vector(v))
    print(f"LAYOUT {label:18s} x={c.x:.2f} y={c.y:.2f} depth={c.z:.1f}")

bpy.context.view_layer.update()
proj("robot body", (R.x, R.y, 0.8)); proj("robot parcel top", (R.x, R.y, 1.9))
proj("window", W); proj("window top mark", W + Vector((0, 0, 1.7)))
proj("earbud head", (-2.0, 11.0, 13.0)); proj("earbud top", (-1.8, 11.0, 18.0)); proj("stem base", STEM)
proj("nb head", nb.matrix_world @ Vector((-2.0, 11.0, 13.0))); proj("nb base", N)
if MODE == "layout":
    sys.exit(0)

# --- lighting variants ---
def kelvin(k):
    t = k / 100.0
    if t <= 66:
        r = 255; g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592); g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [max(0.0, min(255.0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

fwd_cam = (tgt - cam.location); fh = Vector((fwd_cam.x, fwd_cam.y, 0)).normalized()
back = -fh; right = Vector((fh.y, -fh.x, 0))
def from_dir(rel_az, el):
    a, e = math.radians(rel_az), math.radians(el)
    h = back * math.cos(a) + right * math.sin(a)
    return Vector((h.x * math.cos(e), h.y * math.cos(e), math.sin(e))).normalized()

made = []
def sun(name, rel_az, el, k, strength, angle_deg, shadow=True):
    ld = bpy.data.lights.new(name, "SUN"); ld.energy = strength; ld.color = kelvin(k)
    ld.angle = math.radians(angle_deg); ld.use_shadow = shadow
    ob = O.new(name, ld); scene.collection.objects.link(ob)
    ob.rotation_euler = from_dir(rel_az, el).to_track_quat("Z", "Y").to_euler(); made.append(ob)

def area(name, loc, aim, k_or_rgb, power, size_x, size_y):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size_x, size_y
    ld.color = kelvin(k_or_rgb) if isinstance(k_or_rgb, (int, float)) else k_or_rgb
    ob = O.new(name, ld); scene.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(loc) - Vector(aim)).to_track_quat("Z", "Y").to_euler(); made.append(ob)

def spot(name, loc, aim, k, power, size_deg, blend):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = power; ld.color = kelvin(k)
    ld.spot_size = math.radians(size_deg); ld.spot_blend = blend; ld.shadow_soft_size = 0.3
    ob = O.new(name, ld); scene.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(loc) - Vector(aim)).to_track_quat("Z", "Y").to_euler(); made.append(ob)

def world(rgb, strength, density):
    w = bpy.data.worlds.new("Variant world"); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs[0].default_value = (*rgb, 1); bg.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(bg.outputs[0], out.inputs["Surface"])
    scene.world = w
    # haze as a local box: a world volume would block sun lights entirely in EEVEE
    hz = O.get("Haze volume")
    if hz is None:
        me = bpy.data.meshes.new("Haze volume"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
        hz = O.new("Haze volume", me); scene.collection.objects.link(hz)
        hz.location = (0, 12, 10); hz.scale = (90, 90, 30)
        hm = bpy.data.materials.new("Haze"); hm.use_nodes = True; hnt = hm.node_tree; hnt.nodes.clear()
        vs = hnt.nodes.new("ShaderNodeVolumeScatter"); ho = hnt.nodes.new("ShaderNodeOutputMaterial")
        hnt.links.new(vs.outputs[0], ho.inputs["Volume"]); me.materials.append(hm)
    vs = hz.data.materials[0].node_tree.nodes["Volume Scatter"]
    vs.inputs["Density"].default_value = density; vs.inputs["Anisotropy"].default_value = P.get("aniso", 0.4)
    hz.hide_render = density <= 0

ee = scene.eevee
scene.render.engine = "BLENDER_EEVEE_NEXT"
ee.taa_render_samples = p("samples", 32)
ee.use_shadows = True; ee.use_raytracing = False
for k, v in (("volumetric_start", 0.1), ("volumetric_end", 150.0), ("volumetric_samples", 64), ("use_volumetric_shadows", True)):
    if hasattr(ee, k):
        setattr(ee, k, v)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"

robot_top = Vector((R.x, R.y, 6.5))
for v in VARIANTS:
    for ob in made:
        O.remove(ob, do_unlink=True)
    made.clear()
    if v == "A":   # clear daylight: readable first
        sun("Key A", -45, 50, 5600, 4.0, 3.0); sun("Fill A", 70, 25, 6500, 1.6, 10.0, shadow=False)
        world((0.55, 0.63, 0.72), 0.45, 0.0012); motes.hide_render = True; glow.node_tree.nodes["Emission"].inputs[1].default_value = 3.0
        mote_mat.node_tree.nodes["Emission"].inputs[1].default_value = 1.0; scene.view_settings.exposure = 0.0
    elif v == "B": # evening backlight: impact and scale
        sun("Key B", 155, 13, 3000, 5.0, 0.53); sun("Fill B", -15, 20, 7500, 0.7, 10.0, shadow=False)
        world((0.10, 0.13, 0.22), 0.55, 0.006); motes.hide_render = False; glow.node_tree.nodes["Emission"].inputs[1].default_value = 4.0
        mote_mat.node_tree.nodes["Emission"].inputs[1].default_value = 3.0; scene.view_settings.exposure = 0.3
    elif v == "C": # night, only the reception window glows: focus
        sun("Moon rim C", 170, 30, 8000, 0.5, 1.0)
        area("Window light C", W + fwd * 0.6, (R.x, R.y, 1.0), (0.25, 0.95, 0.88), 900.0, 1.4, 1.8)
        spot("Robot spot C", robot_top, (R.x, R.y, 0.6), 3500, 1400.0, 34, 0.45)
        world((0.008, 0.012, 0.03), 0.6, 0.010); motes.hide_render = False; glow.node_tree.nodes["Emission"].inputs[1].default_value = 14.0
        mote_mat.node_tree.nodes["Emission"].inputs[1].default_value = 4.0; scene.view_settings.exposure = 0.5
    scene.render.filepath = os.path.join(OUT, f"stage_{v}.png")
    t = time.time(); bpy.ops.render.render(write_still=True)
    print(f"RENDERED {v} {time.time() - t:.1f}s -> {scene.render.filepath}")
