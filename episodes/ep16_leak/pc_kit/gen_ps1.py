# 16本目：PC の本番描画の手順（run_pc_render_ep16.ps1）を、9本目の手順と clips.json から作る
#   使い方：python3 gen_ps1.py <この章の終わりの秒（その前に始まるカットだけ描く）> <版の名前 例 ep16_v1>
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); EP = os.path.dirname(HERE)
t_end, ver = float(sys.argv[1]), sys.argv[2]
C = json.load(open(os.path.join(EP, "anim", "clips.json"), encoding="utf-8"))
cuts = sorted([(v[0], k, round((v[1] - v[0]) * 24)) for k, v in C.items() if v[2] < t_end])
src = open(os.path.join(EP, "..", "ep09_escalator", "pc_kit", "run_pc_render_ep09.ps1"), encoding="utf-8-sig").read()
a = src.index("$JOBS = @("); b = src.index("\n)\n", a) + 3
jobs = "$JOBS = @(\n" + ",\n".join('  @("%s", %d, "scenes.py")' % (k, n) for _, k, n in cuts) + "\n)\n"
src = src[:a] + jobs + src[b:]
head = ("# まるロボ 16本目「情報流出」：PC の本番描画（3D の %d カット・合わせて %d コマ。承認ずみの章：本編 %.2f 秒まで）\n" % (len(cuts), sum(n for *_, n in cuts), t_end))
src = head + src[src.index("\n") + 1:]
src = src.replace("ep09_escalator", "ep16_leak").replace("marurobo_ep09", "marurobo_ep16").replace("render_log_ep09", "render_log_ep16")
src = src.replace("render_ep09_v3", "render_" + ver).replace("ep09_v3", ver).replace("9本目", "16本目")
src = src.replace("（7本目の手順と同じ作り。出力・記録のフォルダは 16本目だけのもの。16本目は 3D の中に字がないのでフォントは要らない）",
                  "（9本目の手順と同じ作り。16本目の 3D の中の絵（名札・印・値札）は anim/tex16 の PNG を使う）")
src = src.replace('$env:MARU_REQUIRE_REAL = "1"', '$env:MARU_REQUIRE_REAL = "1"\n$env:TEX16 = Join-Path $anim "tex16"   # 名札・お城の印・値札の絵', 1)
assert "ep09" not in src, [m.start() for m in re.finditer("ep09", src)]
open(os.path.join(HERE, "run_pc_render_ep16.ps1"), "w", encoding="utf-8-sig").write(src)
print(len(cuts), "カット", sum(n for *_, n in cuts), "コマ", cuts[0][1], "〜", cuts[-1][1])
