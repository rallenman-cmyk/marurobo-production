# まるロボ：PC の本番描画（第3章 → 第1・2章 → 第4章 → 第7章 → 第8章の塔 → 第6章）。何本か同時に描く（既定 3 本）
#   使い方：PowerShell に次の1行を貼って Enter
#     powershell -ExecutionPolicy Bypass -File C:\marurobo\marurobo_tools\run_pc_render.ps1
#   同時に描く本数：最後に -Workers 2 のように付ける（1 なら 1 本ずつ。既定 3、多くても 4）
#   一部だけ描く：最後に -Only ch07,ch08 のように付ける（ch03・ch0102・ch04・ch07・ch08・ch06・sum をカンマで区切る）
#   2026-11-09：既定は sum（まとめの電車の場面）・ch07r（第7章 まるロボの版）・ch08r（第8章の塔 まるロボの版）。ほかの章は済み
#   2026-11-09 夜：op（冒頭の電車：網棚の上のまるロボ。0:00〜0:33 の 1〜800 コマだけ描き直す）を足した。-Only op で、これだけ描ける
#   途中で止まったり、窓を閉じたりしても、同じ行をもう一度走らせれば、できている所は飛ばして続きから描く
#   同時に描くときは、描き手ごとに小さな窓（最小化）が開く。止めるときは、この窓と「まるロボ 描き手」の窓をぜんぶ閉じる
#   描いているあいだ、PC がスリープしないようにする（画面は消えてもよい。ノート PC は電源につなぎ、ふたは閉じない）
#   終わると、送るファイルだけを C:\marurobo\marurobo_render にまとめる。Google ドライブ（パソコン版）があれば、そこへもコピーする
param([string]$Only = "sum,ch07r,ch08r", [string]$Blender = "", [int]$Workers = 3, [int]$Worker = 0)
$ErrorActionPreference = "Continue"
$tools = $PSScriptRoot
$root = Split-Path -Parent $tools
# zip を「すべて展開」で C:\marurobo\marurobo_tools\marurobo_tools のように二重に展開したときも、C:\marurobo を使う
if ((Split-Path -Leaf $root) -eq "marurobo_tools") { $root = Split-Path -Parent $root }
$jobs = @($Only.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$log = Join-Path $root "render_log.txt"
$done = Join-Path $root "render_done"
New-Item -ItemType Directory -Force -Path $done | Out-Null
$Workers = [Math]::Max(1, [Math]::Min($Workers, 4))
$who = ""
if ($Worker -gt 0) { $who = "[描き手{0}] " -f $Worker; $Host.UI.RawUI.WindowTitle = "まるロボ 描き手 $Worker" }

function Note([string]$m) {
  $line = "{0}  {1}{2}" -f (Get-Date -Format "MM/dd HH:mm"), $who, $m
  Write-Host $line
  for ($t = 0; $t -lt 10; $t++) { try { Add-Content -Path $log -Value $line -Encoding UTF8 -ErrorAction Stop; break } catch { Start-Sleep -Milliseconds 300 } }
}
function Fmt([TimeSpan]$t) {
  if ($t.TotalHours -ge 1) { return ("{0}時間{1}分" -f [int][Math]::Floor($t.TotalHours), $t.Minutes) }
  return ("{0}分{1}秒" -f $t.Minutes, $t.Seconds)
}
function Inv([double]$x) { return $x.ToString([Globalization.CultureInfo]::InvariantCulture) }
# 同時に描くとき、同じ範囲を二人で描かないように、範囲ごとに札（.lock）を立てる（先に立てた人が描く）
function Claim([string]$tag) {
  try { $fs = [System.IO.File]::Open((Join-Path $done "$tag.lock"), [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write); $fs.Close(); return $true }
  catch { return $false }
}
function Release([string]$tag) { Remove-Item (Join-Path $done "$tag.lock") -Force -ErrorAction SilentlyContinue }
function Frames-OK([string]$fd, [int]$i, [int]$j) {
  for ($q = $i; $q -lt $j; $q++) { $p = Join-Path $fd ("t_{0:D4}.png" -f $q); if (-not (Test-Path $p) -or (Get-Item $p).Length -eq 0) { return $false } }
  return $true
}

# ---------------------------------------------------------------- Blender と素材の場所
# Blender 4.3：-Blender で指定 → ふつうの入れ場所 → C:\marurobo の中（zip 版を展開したもの）→ Blender Foundation の中
$blender = $Blender
if (-not $blender -or -not (Test-Path $blender)) { $blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" }
if (-not (Test-Path $blender)) {
  $c = @(Get-ChildItem $root -Directory -Filter "blender-4.3*" -ErrorAction SilentlyContinue | ForEach-Object { Get-ChildItem $_.FullName -Recurse -Depth 1 -Filter blender.exe -ErrorAction SilentlyContinue }) +
       @(Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "4\.3" }) | Select-Object -First 1
  if ($c) { $blender = $c.FullName }
}
if (-not (Test-Path $blender)) { Note "Blender 4.3 が見つかりません。https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.msi を入れてから、もう一度走らせてください"; exit 1 }
# bluetooth_handoff_restored を探す（C:\marurobo の中。一段深く展開していても見つける）
$hand = $null
if (Test-Path (Join-Path $root "bluetooth_handoff_restored\bt_production_v1\output\story.blend")) { $hand = Join-Path $root "bluetooth_handoff_restored" }
else {
  $c = Get-ChildItem $root -Directory -Recurse -Depth 2 -Filter "bluetooth_handoff_restored" -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName "bt_production_v1\output\story.blend") } | Select-Object -First 1
  if ($c) { $hand = $c.FullName }
}
if (-not $hand) { Note "見つかりません：bluetooth_handoff_restored（marurobo_assets.zip を $root に展開してください。$root の中に bluetooth_handoff_restored フォルダができれば OK）"; exit 1 }
$src = Join-Path $hand "bt_production_v1"
$op = Join-Path $hand "restore\v3\bt_opening\output"
if ((($jobs -contains "ch03") -or ($jobs -contains "ch0102") -or ($jobs -contains "sum") -or ($jobs -contains "op")) -and -not (Test-Path "$op\maru_opening.blend")) { Note "見つかりません：$op\maru_opening.blend"; exit 1 }

# ---------------------------------------------------------------- 100 コマずつ mp4 で描く（できている範囲と、ほかの描き手が描いている範囲は飛ばす）
function Render-Chunks([string]$name, [int]$n, [string]$outdir, [string]$prefix, [string[]]$pre, [int]$first = 1) {
  New-Item -ItemType Directory -Force -Path $outdir | Out-Null
  $chunks = @(); for ($s = $first; $s -le $n; $s += 100) { $chunks += ,@($s, [Math]::Min($s + 99, $n)) }
  $times = @()
  $blog = Join-Path $outdir ("blender_log{0}.txt" -f $Worker)
  for ($k = 0; $k -lt $chunks.Count; $k++) {
    $a = $chunks[$k][0]; $b = $chunks[$k][1]
    $tag = "{0}{1:D4}-{2:D4}" -f $prefix, $a, $b
    $mp4 = Join-Path $outdir "$tag.mp4"; $mark = Join-Path $done "$tag.ok"
    if ((Test-Path $mark) -and (Test-Path $mp4)) { continue }
    if (-not (Claim $tag)) { continue }
    if ((Test-Path $mark) -and (Test-Path $mp4)) { Release $tag; continue }
    if (Test-Path $mp4) { Remove-Item $mp4 -Force -ErrorAction SilentlyContinue }
    Note ("{0}：{1}〜{2} コマ目を描いています（全 {3} コマ）" -f $name, $a, $b, $n)
    $t0 = Get-Date
    $argv = $pre + @("--frames", "$($a):$($b)", "--video", "1")
    & $blender @argv *>> $blog
    $code = $LASTEXITCODE; $dt = (Get-Date) - $t0
    if ($code -eq 0 -and (Test-Path $mp4) -and ((Get-Item $mp4).Length -gt 10000)) {
      New-Item -ItemType File -Force -Path $mark | Out-Null
      $times += $dt.TotalSeconds
      $left = 0; for ($q = 0; $q -lt $chunks.Count; $q++) { $tq = "{0}{1:D4}-{2:D4}" -f $prefix, $chunks[$q][0], $chunks[$q][1]; if (-not (Test-Path (Join-Path $done "$tq.ok"))) { $left++ } }
      $avg = ($times | Measure-Object -Average).Average
      Note ("{0}：{1}〜{2} できました（{3}）。この章の残り {4} 本、およそ {5}" -f $name, $a, $b, (Fmt $dt), $left, (Fmt ([TimeSpan]::FromSeconds($avg * $left / $Workers))))
    } else {
      Note ("{0}：{1}〜{2} が止まりました（終了コード {3}）。{4} の最後の 20 行を送ってください。次の範囲へ進みます" -f $name, $a, $b, $code, $blog)
    }
    Release $tag
  }
}

# ---------------------------------------------------------------- 送るファイルを marurobo_render にまとめる（そろっていれば $true）
function Collect([string]$name, [string[]]$patterns, [int]$need) {
  $dst = Join-Path $root "marurobo_render\$name"
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  foreach ($p in $patterns) { Get-ChildItem $p -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item $_.FullName $dst -Force } }
  $files = @(Get-ChildItem $dst -File)
  $mb = [Math]::Round((($files | Measure-Object Length -Sum).Sum) / 1MB)
  $nmp4 = @($files | Where-Object { $_.Extension -eq ".mp4" }).Count
  if ($nmp4 -lt $need) { Note ("{0}：mp4 が {1} 本しかありません（{2} 本のはず）。同じ行をもう一度走らせてください" -f $name, $nmp4, $need); return $false }
  Note ("{0}：送るファイル {1} 個（{2} MB）を {3} にまとめました" -f $name, $files.Count, $mb, $dst); return $true
}

# ---------------------------------------------------------------- 描く仕事（描き手が順に回る）
function Run-Jobs {
  # 第3章：舞台（1283 コマ）と電車の場面（C1・C2 の 461 コマ、C12 の 101 コマ）
  if ($jobs -contains "ch03") {
    $out3 = Join-Path $root "render_ch03_1080"
    Render-Chunks "第3章 舞台" 1283 $out3 "ch03_stage_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch03_stage.py", "--", "--out", $out3, "--res", "1920", "1080", "--samples", "32")
    $fd = Join-Path $out3 "train\frames_train"
    $tlog = Join-Path $out3 ("train_blender_log{0}.txt" -f $Worker)
    foreach ($r in @(@(0, 461), @(1651, 1752))) {
      for ($i = $r[0]; $i -lt $r[1]; $i += 48) {
        $j = [Math]::Min($i + 48, $r[1])
        if (Frames-OK $fd $i $j) { continue }
        $tag = "ch03_train_{0:D4}" -f $i
        if (-not (Claim $tag)) { continue }
        if (Frames-OK $fd $i $j) { Release $tag; continue }
        Note ("第3章 電車：{0}〜{1} コマ目を描いています" -f $i, ($j - 1))
        $t0 = Get-Date
        $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", "$tools\ch03\ch03_train.py", "--", "--blend", "$op\maru_opening.blend", "--out", "$out3\train", "--res", "1920", "1080", "--samples", "32", "--anim", ("{0}:{1}" -f (Inv ($i / 24)), (Inv ($j / 24))))
        & $blender @argv *>> $tlog
        $code = $LASTEXITCODE
        if ($code -eq 0 -and (Frames-OK $fd $i $j)) { Note ("第3章 電車：{0}〜{1} できました（{2}）" -f $i, ($j - 1), (Fmt ((Get-Date) - $t0))) }
        else { Note ("第3章 電車：{0}〜{1} が止まりました（終了コード {2}）。{3} の最後の 20 行を送ってください" -f $i, ($j - 1), $code, $tlog) }
        Release $tag
      }
    }
    # 電車の絵を mp4 にまとめる：ほかの描き手がまだ電車を描いていないときだけ（最後に描き終えた人がまとめる）
    foreach ($sq in @(@(0, 460, "train_c1c2.mp4"), @(1651, 1751, "train_c12.mp4"))) {
      $o = Join-Path $out3 $sq[2]; $mark = Join-Path $done ("ch03_" + $sq[2] + ".ok")
      if ((Test-Path $mark) -and (Test-Path $o)) { continue }
      if (@(Get-ChildItem $done -Filter "ch03_train_*.lock" -ErrorAction SilentlyContinue).Count -gt 0) { continue }
      if (-not (Frames-OK $fd $sq[0] ($sq[1] + 1))) { continue }
      $tag = "ch03_" + $sq[2]
      if (-not (Claim $tag)) { continue }
      $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", "$tools\ch03\seq2mp4.py", "--", "--dir", $fd, "--prefix", "t_", "--start", "$($sq[0])", "--end", "$($sq[1])", "--out", $o)
      & $blender @argv *>> $tlog
      if ($LASTEXITCODE -eq 0 -and (Test-Path $o)) { New-Item -ItemType File -Force -Path $mark | Out-Null; Note ("第3章 電車：{0} にまとめました" -f $sq[2]) }
      else { Note ("第3章 電車：{0} にまとめられませんでした" -f $sq[2]) }
      Release $tag
    }
  }
  # 第1・2章（1944 コマ）
  if ($jobs -contains "ch0102") {
    $out12 = Join-Path $root "render_ch0102"
    Render-Chunks "第1・2章" 1944 $out12 "ch0102_" @("-b", "--factory-startup", "--python-exit-code", "1", "--python", "$tools\human\opening_phys.py", "--", "--seq", "ch0102_seq.py", "--blend", "$op\maru_opening.blend", "--crowd", "1", "--world_len", "1450", "--acts", "1", "--out", $out12, "--res", "1920", "1080", "--samples", "64")
  }
  # 第4章 v8 のペアリング（3D 2826 コマ）
  if ($jobs -contains "ch04") {
    $out4 = Join-Path $root "render_ch04"
    Render-Chunks "第4章" 2826 $out4 "ch04_pair_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch04_pairing6.py", "--", "--out", $out4, "--engine", "eevee", "--res", "1920", "1080", "--samples", "64")
  }
  # 第7章（イヤホンの中：貯蔵タワー 3458 コマ）・第8章の塔（510 コマ）・第6章（送り直し 1933 コマ）
  if ($jobs -contains "ch07") {
    $out7 = Join-Path $root "render_ch07_1080"
    Render-Chunks "第7章" 3458 $out7 "ch07_stage_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch07_stage.py", "--", "--out", $out7, "--res", "1920", "1080", "--samples", "32", "--part", "ch7")
  }
  if ($jobs -contains "ch08") {
    $out8 = Join-Path $root "render_ch08_tower_1080"
    Render-Chunks "第8章の塔" 510 $out8 "ch08_tower_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch07_stage.py", "--", "--out", $out8, "--res", "1920", "1080", "--samples", "32", "--part", "ch8")
  }
  # まとめの電車の場面（第1・2章の続き：1945〜2340 コマ＝396 コマ。止まった電車 → 時間が動き出す → 主人公が踊る）
  if ($jobs -contains "sum") {
    $outs = Join-Path $root "render_summary"
    Render-Chunks "まとめ" 2340 $outs "summary_" @("-b", "--factory-startup", "--python-exit-code", "1", "--python", "$tools\human\opening_phys.py", "--", "--seq", "summary_seq.py", "--blend", "$op\maru_opening.blend", "--crowd", "1", "--world_len", "1450", "--acts", "1", "--out", $outs, "--res", "1920", "1080", "--samples", "64") 1945
  }
  # 冒頭（2026-11-09 夜）：網棚の上のまるロボ。まるロボが映る 0:00〜0:33（1〜800 コマ）だけ描き直す。前の版と名前を分ける（ch0102r_）
  if ($jobs -contains "op") {
    $outo = Join-Path $root "render_ch0102r"
    Render-Chunks "冒頭（網棚のまるロボ）" 800 $outo "ch0102r_" @("-b", "--factory-startup", "--python-exit-code", "1", "--python", "$tools\human\opening_phys.py", "--", "--seq", "ch0102_seq.py", "--blend", "$op\maru_opening.blend", "--crowd", "1", "--world_len", "1450", "--acts", "1", "--out", $outo, "--res", "1920", "1080", "--samples", "64", "--vprefix", "ch0102r_")
  }
  # 第7章・第8章の塔：まるロボが中で見守る版（2026-11-09）。前の版と名前を分けて、全部描き直す
  if ($jobs -contains "ch07r") {
    $out7r = Join-Path $root "render_ch07r_1080"
    Render-Chunks "第7章（まるロボ）" 3458 $out7r "ch07r_stage_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch07_stage.py", "--", "--out", $out7r, "--res", "1920", "1080", "--samples", "32", "--part", "ch7", "--vprefix", "ch07r_stage_")
  }
  if ($jobs -contains "ch08r") {
    $out8r = Join-Path $root "render_ch08r_1080"
    Render-Chunks "第8章の塔（まるロボ）" 510 $out8r "ch08r_tower_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch07_stage.py", "--", "--out", $out8r, "--res", "1920", "1080", "--samples", "32", "--part", "ch8", "--vprefix", "ch08r_tower_")
  }
  if ($jobs -contains "ch06") {
    $out6 = Join-Path $root "render_ch06_1080"
    Render-Chunks "第6章" 1933 $out6 "ch06_stage_" @("-b", "$src\output\story.blend", "--python-exit-code", "1", "--python", "$tools\ch03\ch06_stage.py", "--", "--out", $out6, "--res", "1920", "1080", "--samples", "32")
  }
}

if ($Worker -gt 0) { Run-Jobs; exit 0 }

# ---------------------------------------------------------------- ここからは、まとめ役（描き手を起こして見守り、最後にまとめる）
Add-Type -Namespace Maru -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483649)          # スリープさせない（終わったら元に戻す）
Get-ChildItem $done -Filter "*.lock" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue   # 前に止めたときの札を片付ける
Note ("はじめます：{0}（同時に {1} 本。Blender：{2}）" -f ($jobs -join "・"), $Workers, $blender)
$tAll = Get-Date
if ($Workers -le 1) { Run-Jobs }
else {
  $n0 = @(Get-Content $log -Encoding UTF8).Count
  $procs = @()
  for ($k = 1; $k -le $Workers; $k++) {
    $al = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Only "{1}" -Blender "{2}" -Workers {3} -Worker {4}' -f $PSCommandPath, $Only, $blender, $Workers, $k
    $procs += Start-Process -FilePath "powershell.exe" -ArgumentList $al -WindowStyle Minimized -PassThru
    Start-Sleep -Seconds 20                                              # 場面を組む時間を少しずつずらす
  }
  Write-Host "描き手 $Workers 人が描いています（タスクバーの「まるロボ 描き手」の窓）。進み具合は、この窓にも出ます"
  while (@($procs | Where-Object { -not $_.HasExited }).Count -gt 0) {
    Start-Sleep -Seconds 15
    $all = @(Get-Content $log -Encoding UTF8)
    if ($all.Count -gt $n0) { $all[$n0..($all.Count - 1)] | ForEach-Object { Write-Host $_ }; $n0 = $all.Count }
  }
}
# 送るファイルをまとめる。Google ドライブ（パソコン版）があれば、そろった章をそこへもコピーする（アップロードは自動で進む）
$okc = @{}
if ($jobs -contains "ch03") { $okc["ch03"] = Collect "ch03" @("$root\render_ch03_1080\ch03_stage_*.mp4", "$root\render_ch03_1080\train_c1c2.mp4", "$root\render_ch03_1080\train_c12.mp4", "$root\render_ch03_1080\train\train_frames_log_*.json") 15 }
if ($jobs -contains "ch0102") { $okc["ch0102"] = Collect "ch0102" @("$root\render_ch0102\ch0102_*.mp4", "$root\render_ch0102\ch0102_log.json") 20 }
if ($jobs -contains "ch04") { $okc["ch04"] = Collect "ch04" @("$root\render_ch04\ch04_pair_*.mp4", "$root\render_ch04\pairing_log.json") 29 }
if ($jobs -contains "ch07") { $okc["ch07"] = Collect "ch07" @("$root\render_ch07_1080\ch07_stage_*.mp4", "$root\render_ch07_1080\ch07_log.json") 35 }
if ($jobs -contains "ch08") { $okc["ch08"] = Collect "ch08" @("$root\render_ch08_tower_1080\ch08_tower_*.mp4", "$root\render_ch08_tower_1080\ch08_tower_log.json") 6 }
if ($jobs -contains "ch07r") { $okc["ch07r"] = Collect "ch07r" @("$root\render_ch07r_1080\ch07r_stage_*.mp4", "$root\render_ch07r_1080\ch07_log.json") 35 }
if ($jobs -contains "ch08r") { $okc["ch08r"] = Collect "ch08r" @("$root\render_ch08r_1080\ch08r_tower_*.mp4", "$root\render_ch08r_1080\ch08_tower_log.json") 6 }
if ($jobs -contains "sum") { $okc["sum"] = Collect "sum" @("$root\render_summary\summary_*.mp4", "$root\render_summary\summary_log.json") 4 }
if ($jobs -contains "op") { $okc["op"] = Collect "op" @("$root\render_ch0102r\ch0102r_*.mp4", "$root\render_ch0102r\ch0102_log.json") 8 }
if ($jobs -contains "ch06") { $okc["ch06"] = Collect "ch06" @("$root\render_ch06_1080\ch06_stage_*.mp4", "$root\render_ch06_1080\ch06_log.json") 20 }
$g = @(Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Root }) + @($env:USERPROFILE) | ForEach-Object { foreach ($nm in "マイドライブ", "My Drive") { Join-Path $_ $nm } } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($g) {
  foreach ($ch in $okc.Keys) {
    if ($okc[$ch]) { $gd = Join-Path $g "marurobo_render"; New-Item -ItemType Directory -Force -Path $gd | Out-Null; Copy-Item (Join-Path $root "marurobo_render\$ch") $gd -Recurse -Force; Note ("{0}：Google ドライブ（{1}）にコピーしました" -f $ch, $gd) }
  }
}
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483648)
if (@($okc.Values | Where-Object { -not $_ }).Count -gt 0) {
  Note ("終わりました（{0}）。そろっていない章があります。同じ行をもう一度走らせると、足りない所だけ描きます" -f (Fmt ((Get-Date) - $tAll)))
} elseif ($g) {
  Note ("ぜんぶ終わりました（{0}）。Google ドライブへのアップロードは自動で進みます（PC は、アップロードが終わるまで入れたままに）" -f (Fmt ((Get-Date) - $tAll)))
} else {
  Note ("ぜんぶ終わりました（{0}）。{1} の中身（新しくできたフォルダ）を、Google ドライブの marurobo_render フォルダにアップロードしてください" -f (Fmt ((Get-Date) - $tAll)), (Join-Path $root "marurobo_render"))
}
