import bpy
O = bpy.data.objects
def hier(o):
    out = [o]
    for c in o.children: out += hier(c)
    return out
for o in hier(O["Earbud exterior"]):
    if o.type != "MESH": continue
    me = o.data
    mats = [(m.name, [n.bl_idname for n in m.node_tree.nodes][:8] if m and m.use_nodes else None) for m in me.materials]
    print("EB3", o.name, "verts", len(me.vertices), "polys", len(me.polygons), "mods", [m.type for m in o.modifiers], "smooth", sum(p.use_smooth for p in me.polygons), "mats", mats)
    for m in me.materials:
        if m and m.use_nodes:
            b = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
            if b: print("EB3   ", m.name, "base", tuple(round(v, 3) for v in b.inputs["Base Color"].default_value), "rough", round(b.inputs["Roughness"].default_value, 2),
                        "metal", round(b.inputs["Metallic"].default_value, 2), "coat", round(b.inputs["Coat Weight"].default_value, 2), "sss", round(b.inputs["Subsurface Weight"].default_value, 2))
