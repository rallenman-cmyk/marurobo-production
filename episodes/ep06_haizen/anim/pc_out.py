# PC の本番描画の設定（scenes.py が描く前に exec する。sc・_argv は呼ぶ側のもの）。3本目の anim/pc_out.py と同じ
#   --gpu   ：グラフィックボードで描く（OPTIX → CUDA → HIP → ONEAPI の順に探す。なければ CPU のまま）
#   --video ：コマを PNG ではなく mp4（H.264・高画質）で書く。名前は <クリップ>_<始め4桁>-<終わり4桁>.mp4（Blender が付ける）
import bpy as _bpy
if "--gpu" in _argv:
    _pr = _bpy.context.preferences.addons["cycles"].preferences
    _got = None
    for _t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            _pr.compute_device_type = _t; _pr.get_devices()
            _ds = [d for d in _pr.devices if d.type == _t]
            if _ds:
                for d in _pr.devices: d.use = (d.type == _t)
                _got = _t; break
        except Exception:
            pass
    if _got:
        sc.cycles.device = "GPU"
        if _got == "OPTIX": sc.cycles.denoiser = "OPTIX"
    print("DEVICE", _got or "CPU")
if "--video" in _argv:
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.ffmpeg.audio_codec = "NONE"
