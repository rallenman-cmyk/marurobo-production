import bpy, time
s=bpy.context.scene
s.render.engine='BLENDER_EEVEE_NEXT'; s.render.resolution_x=320; s.render.resolution_y=180
s.eevee.taa_render_samples=8
s.render.filepath='/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad/stage/eevee_test.png'
t=time.time(); bpy.ops.render.render(write_still=True); print("EEVEE_OK %.2fs"%(time.time()-t))
