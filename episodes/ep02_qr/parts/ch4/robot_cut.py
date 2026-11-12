# まるロボ（仮）の切り抜き：透明の背景。2D の図の場面に置く用。 blender -b --factory-startup -P robot_cut.py -- OUT.png HEADING PITCH
import sys, os, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kit import world as W
import op_stage_standin as SI
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; hd = float(a[1]); pitch = float(a[2])
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene; wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes['Background'].inputs[0].default_value = (*W.srgb('#E4EAF0'), 1); wd.node_tree.nodes['Background'].inputs[1].default_value = 0.6
root, torso, legs = SI.build_robot(); psi = math.radians(hd); rx, ry = math.cos(psi), math.sin(psi)
SI.pose(root, torso, legs, dict(root=[0, 0, 0.03], psi=psi, pitch=pitch, twist=0.0, feet=[dict(ankle=[s * 0.255 * rx, s * 0.255 * ry, 0.21], psi=psi) for s in (-1, 1)]))
la = bpy.data.lights.new('k', 'AREA'); la.size = 4; la.energy = 600; k = W.link(bpy.data.objects.new('k', la)); k.location = (-2, -4, 5); k.rotation_euler = (Vector((0, 0, 0.8)) - k.location).to_track_quat('-Z', 'Y').to_euler()
cd = bpy.data.cameras.new('C'); cd.lens = 50; c = W.link(bpy.data.objects.new('C', cd)); c.location = (0, -6.0, 1.4); c.rotation_euler = (Vector((0, 0, 0.85)) - c.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = c
W.render_setup(sc, engine='eevee', res=(600, 600), samples=24, exposure=-0.4); sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
