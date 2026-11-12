import bpy, sys
from mathutils import Vector
s = bpy.context.scene
print("PROBE file", bpy.data.filepath, "frames", s.frame_start, s.frame_end, "cam", s.camera.name if s.camera else None)
dg = bpy.context.evaluated_depsgraph_get()
def hier(o):
    r = [o]
    for c in o.children: r += hier(c)
    return r
def bbox(objs):
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3); n = 0
    for o in objs:
        if o.type not in {"MESH", "CURVE", "FONT", "SURFACE", "META"}: continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p)); n += 1
    return (lo, hi) if n else None
for o in bpy.data.objects:
    if o.parent is None:
        H = hier(o); bb = bbox(H); vis = [x for x in H if not x.hide_render]
        anim = sum(1 for x in H if x.animation_data and x.animation_data.action)
        if bb: print("PROBE root %-30s %-6s n=%3d vis=%3d anim=%2d  lo=(%.2f,%.2f,%.2f) hi=(%.2f,%.2f,%.2f)" % (o.name[:30], o.type, len(H), len(vis), anim, *bb[0], *bb[1]))
        else: print("PROBE root %-30s %-6s n=%3d loc=(%.2f,%.2f,%.2f)" % (o.name[:30], o.type, len(H), *o.matrix_world.translation))
for o in bpy.data.objects:
    if o.type == "LIGHT": print("PROBE light", o.name, o.data.type, round(o.data.energy, 2), tuple(round(c, 2) for c in o.data.color), tuple(round(v, 2) for v in o.matrix_world.translation), "hide", o.hide_render)
    if o.type == "CAMERA": print("PROBE camera", o.name, round(o.data.lens, 1), tuple(round(v, 2) for v in o.matrix_world.translation), "anim", bool(o.animation_data and o.animation_data.action))
for m in s.timeline_markers: print("PROBE marker", m.frame, m.name, m.camera.name if m.camera else None)
w = s.world
if w and w.node_tree:
    for n in w.node_tree.nodes: print("PROBE world node", n.bl_idname, n.name)
print("PROBE view", s.view_settings.view_transform, s.view_settings.look, s.view_settings.exposure)
