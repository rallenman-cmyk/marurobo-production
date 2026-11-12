import bpy
O=bpy.data.objects
def hier(o):
    r=[o]
    for c in o.children: r+=hier(c)
    return r
h=O["PASSENGER 00"]; names=[(o.name,o.type,[m.name for m in o.data.materials] if o.type in {"MESH","CURVE"} and o.data else None) for o in hier(h)]
print("PROBE", names[24:])
