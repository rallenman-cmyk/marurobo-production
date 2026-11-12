# 連番の絵（PNG）を、Blender だけで mp4（H.264・ほぼ劣化なし）にまとめる（PC に ffmpeg がなくても動く）
# 使い方: blender -b --factory-startup --python seq2mp4.py -- --dir 連番のフォルダ --prefix t_ --start 0 --end 460 --out 出力.mp4 [--fps 24]
import bpy, sys, os, argparse
ap = argparse.ArgumentParser()
ap.add_argument("--dir"); ap.add_argument("--prefix", default="t_"); ap.add_argument("--start", type=int); ap.add_argument("--end", type=int)
ap.add_argument("--out"); ap.add_argument("--fps", type=int, default=24); ap.add_argument("--digits", type=int, default=4)
A = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
files = ["%s%0*d.png" % (A.prefix, A.digits, i) for i in range(A.start, A.end + 1)]
missing = [f for f in files if not os.path.exists(os.path.join(A.dir, f))]
if missing: print("足りない絵:", len(missing), missing[:5]); sys.exit(1)
sc = bpy.context.scene; se = sc.sequence_editor_create()
st = se.sequences.new_image("seq", os.path.join(A.dir, files[0]), channel=1, frame_start=1)
for f in files[1:]: st.elements.append(f)
img = bpy.data.images.load(os.path.join(A.dir, files[0])); w, h = img.size
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
sc.render.fps = A.fps; sc.frame_start, sc.frame_end = 1, len(files)
sc.render.image_settings.file_format = "FFMPEG"; ff = sc.render.ffmpeg
ff.format = "MPEG4"; ff.codec = "H264"; ff.constant_rate_factor = "PERC_LOSSLESS"; ff.ffmpeg_preset = "GOOD"; ff.audio_codec = "NONE"
sc.render.use_sequencer = True; sc.render.filepath = A.out
bpy.ops.render.render(animation=True)
print("WROTE", A.out, len(files), "frames", w, "x", h)
