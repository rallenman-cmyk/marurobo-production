import bpy
s=bpy.context.scene; s.frame_set(1)
O=bpy.data.objects
for n in ["Inside 04","Inside 05","Inside 06"]:
    r=O[n]
    if r.animation_data: r.animation_data_clear()
    r.parent=None; r.location=(0,0,0); r.rotation_euler=(0,0,0); r.scale=(1,1,1)
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
for n in ["Inside 04"]:
    for c in O[n].children:
        e=c.evaluated_get(dg); me=e.to_mesh(); pts=[c.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear()
        mn=[round(min(p[i] for p in pts),3) for i in range(3)]; mx=[round(max(p[i] for p in pts),3) for i in range(3)]
        print("PROBE",c.name,"min",mn,"max",mx,"mats",[m.name for m in c.data.materials], "anim", bool(c.animation_data))
