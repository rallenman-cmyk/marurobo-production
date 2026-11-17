# 4本目の PC 手順（run_pc_render_ep04.ps1）を、5本目の手順から作る：python3 make_ps1.py
#   カットとコマ数は、クラウドの描画の記録（*_log.json の frames）と同じ。カットを足したら JOBS を直して作り直す
import os, sys
VER = sys.argv[1] if len(sys.argv) > 1 else "v13"     # 版（出力とドライブのフォルダ名 ep04_<版>）。直しの描き直しは新しい版にする（できた印が前の版と混ざらない）
H = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(H, '../../ep05_vacuum/pc_kit/run_pc_render_ep05.ps1'), encoding='utf-8-sig').read()
C, S, L = "anim\\clip_anim.py", "anim\\scenes.py", "look\\%s_3d.py"
jobs = [("c_s01", 285, C), ("c_s02a", 320, C), ("c_s03", 408, C), ("s04", 650, S), ("c_s05b", 175, C), ("c_s05x", 227, C),
        ("s06", 277, L % "s06"), ("c_s06b", 271, C), ("s07", 1071, L % "s07"), ("c_s08e", 169, C), ("c_s08f", 318, C),
        ("s08x", 294, L % "s08x"), ("s09", 577, L % "s09"), ("s10", 891, L % "s10"), ("c_s11", 158, C), ("c_s11b", 112, C),
        ("c_s11c", 200, C), ("c_s11d", 148, C), ("c_s12a", 498, C), ("c_s13a", 275, C), ("c_s13b", 224, C), ("c_s13d", 433, C),
        ("c_s14", 287, C), ("c_s15a", 289, C), ("s15", 396, L % "s15"), ("c_s15e", 197, C), ("c_s16", 728, C), ("c_s17a", 293, C),
        ("c_s17b", 198, C), ("c_s18a", 736, C), ("s19", 1468, L % "s19"), ("s20", 1023, L % "s20"), ("c_s20e", 268, C),
        ("c_s21", 155, C), ("c_s21b", 165, C), ("c_s22", 121, C), ("c_s22b", 139, C), ("c_s22c", 132, C), ("s22", 437, L % "s22"),
        ("c_s23a", 343, C)]
tot = sum(j[1] for j in jobs)
s = src
a = s.index("$JOBS = @("); b = s.index("\n)\n", s.index('  @("S27c"')) + 3
s = s[:a] + "$JOBS = @(\n" + ",\n".join('  @("%s", %d, "%s")' % j for j in jobs) + "\n)\n" + s[b:]
s = s[s.index("param("):]
head = f"""# まるロボ 4本目「私はロボットではありません」：PC の本番描画（3D の {len(jobs)} カット・合わせて {tot} コマ）
#   使い方：PowerShell に README_PC.md の 1 行を貼って Enter
#   同時に描く本数：最後に -Workers 2 のように付ける（既定 3、1〜4）
#   一部だけ描く：最後に -Only c_s01,s04 のように付ける（カットの名前をカンマで区切る）
#   描く細かさ：-Samples 24（既定。光の跳ね返りを減らす --fast と合わせて、48 の約 3 倍速い）
#   途中で止まったり窓を閉じたりしても、同じ行をもう一度走らせれば、できている所は飛ばして続きから描く
#   描いているあいだ、PC がスリープしないようにする（画面は消えてもよい。ノート PC は電源につなぎ、ふたは閉じない）
#   終わると、送るファイルだけを C:\\marurobo\\marurobo_render\\ep04_{VER} にまとめる。Google ドライブ（パソコン版）があれば、そこへもコピーする
#   5本目の手順と同じ作り。描き方は 3 種類：部屋の場面＝anim\\clip_anim.py、0:44 のマウス＝anim\\scenes.py、図の場面＝look\\<名前>_3d.py
"""
s = head + s
R = [('$anim = Join-Path $kit "episodes\\ep05_vacuum\\anim"', '$ep = Join-Path $kit "episodes\\ep04_robot"'),
     ("...\\marurobo_ep05", "...\\marurobo_ep04"), ("render_ep05_v3", "render_ep04_" + VER), ("ep05_v3", "ep04_" + VER),
     ("render_log_ep05.txt", "render_log_ep04.txt"), ("5本目を描き始めます", "4本目を描き始めます"), ("marurobo_ep05.zip", "marurobo_ep04.zip"),
     ('$tex = Join-Path $kit "tex"', '$tex = Join-Path $kit "tex"\n$scr = Join-Path $kit "scr"')]
for o, n in R:
    assert o in s, o; s = s.replace(o, n)
o = 'if (-not (Test-Path (Join-Path $anim "scenes.py"))) { Note "見つかりません：$anim\\scenes.py（marurobo_ep04.zip を C:\\marurobo に展開し直してください）"; exit 1 }'
assert o in s; s = s.replace(o, 'if (-not (Test-Path (Join-Path $ep "anim\\clip_anim.py"))) { Note "見つかりません：$ep\\anim\\clip_anim.py（marurobo_ep04.zip を C:\\marurobo に展開し直してください）"; exit 1 }')
old = '    $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $anim $py), "--", $key, $out, "--samples", "$Samples", "--res", "1920", "1080", "--frames", "$a", "$b", "--gpu", "--video", "--fast", "--tex", $tex)'
new = '''    $common = @("--res", "1920", "1080", "--frames", "$a", "$b", "--gpu", "--video", "--fast", "--tex", $tex)
    if ($py -like "anim\\clip_anim.py") { $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $ep $py), "--", $key, (Join-Path $ep "anim\\clips.json"), $out, "$Samples") + $common + @("--scr", $scr) }
    elseif ($py -like "anim\\scenes.py") { $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $ep $py), "--", $key, $out, "$Samples") + $common + @("--scr", $scr) }
    else { $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $ep $py), "--", $out, "$Samples") + $common }'''
assert old in s; s = s.replace(old, new, 1)
# 本物のまるロボで描く（2026-11-17）：story.blend が見つからなければ、代わりの体で描かずに止める
o = '    $common = @('
assert o in s; s = s.replace(o, '    $env:MARU_REQUIRE_REAL = "1"\n' + o, 1)
# 本物のまるロボのファイル（story.blend）を 1 回だけ探し、描き手に渡す（Blender の中で毎回探すと遅いため）
o = "# ---------------------------------------------------------------- 100 コマずつ mp4 で描く"
assert o in s
s = s.replace(o, '''# ---------------------------------------------------------------- 本物のまるロボ（story.blend）を探す
if (-not $env:MARU_BLEND -or -not (Test-Path $env:MARU_BLEND)) {
  $sb = Get-ChildItem $root -Recurse -Filter story.blend -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "bt_production_v1.output" } | Select-Object -First 1
  if (-not $sb) { $sb = Get-ChildItem $root -Recurse -Filter story.blend -ErrorAction SilentlyContinue | Select-Object -First 1 }
  if ($sb) { $env:MARU_BLEND = $sb.FullName } else { Note "本物のまるロボ（story.blend）が C:\\marurobo の下に見つかりません"; exit 1 }
}
if ($Worker -eq 0) { Note ("本物のまるロボ：{0}" -f $env:MARU_BLEND) }

''' + o, 1)
bad = [l for l in s.splitlines() if "ep05" in l or "5本目を" in l]
assert not bad, bad
open(os.path.join(H, 'run_pc_render_ep04.ps1'), 'w', encoding='utf-8-sig').write(s)
print(len(jobs), "カット", tot, "コマ")
