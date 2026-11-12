import bpy
from mathutils import Vector
O = bpy.data.objects
def hier(o):
    r = [o]
    for c in o.children: r += hier(c)
    return r
for o in O:
    n = o.name
    if any(k in n for k in ("Inside", "Received", "Parcel", "parcel", "Package", "Delivery", "cargo", "Smartphone", "Sender", "Receipt")) and (o.parent is None or o.parent.name in ("Earbud cutaway", "Received delivery", "Smartphone exterior", "Receipt display", "Sender windows")):
        H = hier(o)
        print("PROBE %-34s %-6s parent=%-22s kids=%d loc=(%.2f,%.2f,%.2f) mats=%s" % (n[:34], o.type, (o.parent.name if o.parent else "-")[:22], len(H) - 1,
              *o.matrix_world.translation, sorted({s.material.name for x in H if x.type == "MESH" for s in x.material_slots if s.material})[:6]))
for n in ("Smartphone exterior",):
    for c in hier(O[n]):
        if c.type == "MESH":
            print("PROBE phone part %-30s dims=(%.2f,%.2f,%.2f) loc=(%.2f,%.2f,%.2f) mats=%s" % (c.name[:30], *c.dimensions, *c.matrix_world.translation, [s.material.name for s in c.material_slots if s.material][:3]))
for n in ("Earbud exterior",):
    for c in hier(O[n]):
        print("PROBE earbud part %-30s %-5s dims=(%.2f,%.2f,%.2f) loc=(%.2f,%.2f,%.2f) mats=%s" % (c.name[:30], c.type, *c.dimensions, *c.matrix_world.translation, [s.material.name for s in c.material_slots if s.material][:3]))
