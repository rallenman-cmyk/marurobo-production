# 第3章：絵はそのまま（OUT/full の連番）、字幕・音・動画だけ作り直す。python3 ch03_audio_only.py OUT_DIR
import sys, os
ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage", "ch03", "ch03_assemble.py")
lines = open(ASM, encoding="utf-8").read().split("\n")
i_pic = next(i for i, l in enumerate(lines) if l.startswith("# ---------------------------------------------------------------- 絵をつなぐ"))
i_sub = next(i for i, l in enumerate(lines) if l.startswith("# ---------------------------------------------------------------- 字幕"))
i_ts = next(i for i, l in enumerate(lines) if l.startswith("def ts("))                       # 字幕で使う時刻の書き方（絵の所の終わりにある）
code = "\n".join(lines[:i_pic]) + "\nSEQ = os.path.join(OUT, 'full')\n" + "\n".join(lines[i_ts:])
sys.argv = [ASM] + sys.argv[1:]
exec(compile(code, ASM, "exec"), {"__file__": ASM, "__name__": "__main__"})
