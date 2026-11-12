import bpy
s = bpy.context.scene
print("PROBE scene", s.name, s.frame_start, s.frame_end, s.render.fps)
for sc in bpy.data.scenes: print("PROBE scenes:", sc.name, sc.frame_start, sc.frame_end)
se = s.sequence_editor
if se:
    for st in sorted(se.sequences_all, key=lambda x: x.frame_final_start):
        a, b = st.frame_final_start / s.render.fps, st.frame_final_end / s.render.fps
        if b < 78 or a > 165: continue
        extra = ""
        if st.type == "SCENE": extra = "scene=%s off=%d cam=%s" % (st.scene.name if st.scene else None, st.animation_offset_start, st.scene_camera.name if st.scene_camera else None)
        elif hasattr(st, "filepath"): extra = st.filepath
        elif hasattr(st, "directory"): extra = st.directory + (st.elements[0].filename if st.elements else "")
        print("PROBE strip %-28s ch%d %-6s %6.2f-%6.2f %s" % (st.name[:28], st.channel, st.type, a, b, extra[:120]))
