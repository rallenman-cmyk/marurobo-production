# 図の場面の 3D 台本の頭（どの場面でも同じ）。台本の 1 行目で exec する
#   blender -b --factory-startup --python <場面>.py -- <出力> [samples] [--res W H] [--step N] --tex <絵> [--track-only]
import os, sys, math
ARGS = sys.argv[sys.argv.index("--") + 1:]
_LOOK = os.path.dirname(os.path.abspath(__file__))
_ANIM_HERE = os.path.join(_LOOK, "..", "anim")
def opt(name, default):
    return [type(d)(ARGS[ARGS.index(name) + 1 + k]) for k, d in enumerate(default)] if name in ARGS else default
TEX, = opt("--tex", [os.path.join(_ANIM_HERE, "..", "storyboard", "tex")])
OUTDIR = ARGS[0]; N_SAMPLES = int(ARGS[1]) if len(ARGS) > 1 and ARGS[1].isdigit() else 32
RESX, RESY = opt("--res", [1920, 1080]); STEP, = opt("--step", [1]); TRACK_ONLY = "--track-only" in ARGS
exec(open(os.path.join(_ANIM_HERE, "common.py"), encoding="utf-8").read())
exec(open(os.path.join(_LOOK, "kit3d.py"), encoding="utf-8").read())
import bpy
sc = bpy.context.scene


def span(t0, t1):
    global T0, T1
    T0, T1 = t0, t1; CLOCK["T0"] = T0
    sc.frame_start, sc.frame_end = 0, round((T1 - T0) * FPS)


def finish(name):
    glare()
    render(name, T0, T1, OUTDIR, N_SAMPLES, (RESX, RESY), STEP)
    print(name.upper() + "DONE")


def next_sub(text):
    """text の字幕の、次の字幕の始まり（場面の終わりに使う）"""
    a = said(text)
    return min(e[0] for e in SUBS if e[0] > a + 0.01)
