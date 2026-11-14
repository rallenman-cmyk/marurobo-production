# まるロボ 3本目「さっき話した物が、なぜ広告に出る？」：PC の本番描画（3D の 21 場面・合わせて 19,564 コマ）
#   使い方：PowerShell に README_PC.md の 1 行を貼って Enter
#   同時に描く本数：最後に -Workers 2 のように付ける（既定 3、1〜4）
#   一部だけ描く：最後に -Only gate,phone のように付ける（場面の名前をカンマで区切る）
#   描く細かさ：-Samples 48（既定）。大きくすると、きれいになるが時間がかかる
#   途中で止まったり窓を閉じたりしても、同じ行をもう一度走らせれば、できている所は飛ばして続きから描く
#   描いているあいだ、PC がスリープしないようにする（画面は消えてもよい。ノート PC は電源につなぎ、ふたは閉じない）
#   終わると、送るファイルだけを C:\marurobo\marurobo_render\ep03_v6 にまとめる。Google ドライブ（パソコン版）があれば、そこへもコピーする
param([string]$Only = "", [string]$Blender = "", [int]$Workers = 3, [int]$Worker = 0, [int]$Samples = 48)
$ErrorActionPreference = "Continue"
$kit = Split-Path -Parent $PSScriptRoot                      # ...\marurobo_ep03
$anim = Join-Path $kit "episodes\ep03_ad\anim"
$root = "C:\marurobo"
if (-not (Test-Path $root)) { $root = Split-Path -Parent $kit }
$JOBS = @(
  @("s00", 173, "scenes_all.py"),
  @("s01", 354, "scenes_all.py"),
  @("s02", 609, "scenes_all.py"),
  @("s04", 476, "scenes_all.py"),
  @("s05", 918, "scenes_all.py"),
  @("s06a", 557, "scenes_all.py"),
  @("s06b", 255, "scenes_all.py"),
  @("gate", 3541, "s07s08_gate.py"),
  @("phone", 307, "s07s08_gate.py"),
  @("s10", 1644, "scenes_all.py"),
  @("s11", 336, "scenes_all.py"),
  @("s12", 1467, "scenes_all.py"),
  @("s13", 963, "scenes_all.py"),
  @("s14", 1442, "scenes_all.py"),
  @("s15", 1254, "scenes_all.py"),
  @("s16", 1148, "scenes_all.py"),
  @("s17", 478, "scenes_all.py"),
  @("s18", 925, "scenes_all.py"),
  @("s19", 1298, "scenes_all.py"),
  @("s21", 776, "scenes_all.py"),
  @("s22", 643, "scenes_all.py")
)
if ($Only) { $want = @($Only.Split(",") | ForEach-Object { $_.Trim() }); $sel = New-Object System.Collections.ArrayList; foreach ($j in $JOBS) { if ($want -contains $j[0]) { [void]$sel.Add($j) } }; $JOBS = $sel.ToArray() }
$out = Join-Path $root "render_ep03_v6"                  # v6（2026-11-14 確定版）。前に止めた描画（render_ep03）は古いので使わない
$log = Join-Path $root "render_log_ep03.txt"
$done = Join-Path $out "_done"
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
function Claim([string]$tag) {
  try { $fs = [System.IO.File]::Open((Join-Path $done "$tag.lock"), [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write); $fs.Close(); return $true }
  catch { return $false }
}
function Release([string]$tag) { Remove-Item (Join-Path $done "$tag.lock") -Force -ErrorAction SilentlyContinue }
function AllChunks() { $c = @(); foreach ($j in $JOBS) { for ($a = 0; $a -lt $j[1]; $a += 100) { $c += ,@($j[0], $a, [Math]::Min($a + 99, $j[1] - 1), $j[2]) } }; return ,$c }
function Left() { $n = 0; foreach ($c in (AllChunks)) { $tag = "{0}_{1:D4}-{2:D4}" -f $c[0], $c[1], $c[2]; if (-not (Test-Path (Join-Path $done "$tag.ok"))) { $n++ } }; return $n }

# Google ドライブ（パソコン版）の場所。1 本できるたびに、そこへすぐコピーする（こちらで進み具合を見られるように）
$gdrive = @(Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Root }) + @($env:USERPROFILE) | ForEach-Object { foreach ($nm in "マイドライブ", "My Drive") { Join-Path $_ $nm } } | Where-Object { Test-Path $_ } | Select-Object -First 1
$gep = $null
if ($gdrive) { $gep = Join-Path $gdrive "marurobo_render\ep03_v6"; New-Item -ItemType Directory -Force -Path $gep -ErrorAction SilentlyContinue | Out-Null }

# ---------------------------------------------------------------- Blender 4.3 を探す
$blender = $Blender
if (-not $blender -or -not (Test-Path $blender)) { $blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" }
if (-not (Test-Path $blender)) {
  $c = @(Get-ChildItem $root -Directory -Filter "blender-4.3*" -ErrorAction SilentlyContinue | ForEach-Object { Get-ChildItem $_.FullName -Recurse -Depth 1 -Filter blender.exe -ErrorAction SilentlyContinue }) +
       @(Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "4\.3" }) | Select-Object -First 1
  if ($c) { $blender = $c.FullName }
}
if (-not (Test-Path $blender) -and $Worker -eq 0) {
  # Blender 4.3 が無ければ、持ち運び版（入れなくても動く zip）を C:\marurobo に落として広げる
  Note "Blender 4.3 が見つかりません。持ち運び版を落とします（約 300MB。初回だけ・数分）"
  $zip = Join-Path $root "blender-4.3.2-windows-x64.zip"
  try {
    if (-not (Test-Path $zip)) { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile("https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.zip", $zip) }
    Note "広げています…"
    Expand-Archive -Path $zip -DestinationPath $root -Force
    $c = Get-ChildItem $root -Directory -Filter "blender-4.3*" -ErrorAction SilentlyContinue | ForEach-Object { Get-ChildItem $_.FullName -Recurse -Depth 1 -Filter blender.exe -ErrorAction SilentlyContinue } | Select-Object -First 1
    if ($c) { $blender = $c.FullName; Note ("Blender を用意しました：{0}" -f $blender) }
  } catch { Note ("Blender を落とせませんでした（{0}）。手で入れてください：https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.msi" -f $_.Exception.Message) }
}
if (-not (Test-Path $blender)) { Note "Blender 4.3 が見つかりません。https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.msi を入れてから、もう一度走らせてください"; exit 1 }
if (-not (Test-Path (Join-Path $anim "scenes_all.py"))) { Note "見つかりません：$anim\scenes_all.py（marurobo_ep03.zip を C:\marurobo に展開し直してください）"; exit 1 }

# ---------------------------------------------------------------- 100 コマずつ mp4 で描く（できている範囲と、ほかの描き手が描いている範囲は飛ばす）
function Run-Jobs {
  $times = @()
  foreach ($c in (AllChunks)) {
    $key = $c[0]; $a = $c[1]; $b = $c[2]; $py = $c[3]
    $tag = "{0}_{1:D4}-{2:D4}" -f $key, $a, $b
    $mp4 = Join-Path $out "$tag.mp4"; $mark = Join-Path $done "$tag.ok"
    if ((Test-Path $mark) -and (Test-Path $mp4)) { continue }
    if (-not (Claim $tag)) { continue }
    if ((Test-Path $mark) -and (Test-Path $mp4)) { Release $tag; continue }
    if (Test-Path $mp4) { Remove-Item $mp4 -Force -ErrorAction SilentlyContinue }
    Note ("{0}：{1}〜{2} コマ目を描いています" -f $key, $a, $b)
    $t0 = Get-Date
    $blog = Join-Path $out ("blender_log{0}.txt" -f $Worker)
    $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $anim $py), "--", $key, $out, "$Samples", "--res", "1920", "1080", "--frames", "$a", "$b", "--gpu", "--video")
    & $blender @argv *>> $blog
    $code = $LASTEXITCODE; $dt = (Get-Date) - $t0
    if ($code -eq 0 -and (Test-Path $mp4) -and ((Get-Item $mp4).Length -gt 10000)) {
      New-Item -ItemType File -Force -Path $mark | Out-Null
      if ($gep) { Copy-Item $mp4 $gep -Force -ErrorAction SilentlyContinue; Copy-Item (Join-Path $out "$($key)_log.json") $gep -Force -ErrorAction SilentlyContinue }
      $times += $dt.TotalSeconds; $avg = ($times | Measure-Object -Average).Average; $n = Left
      Note ("{0}：{1}〜{2} できました（{3}）。残り {4} 本、およそ {5}" -f $key, $a, $b, (Fmt $dt), $n, (Fmt ([TimeSpan]::FromSeconds($avg * $n / $Workers))))
    } else {
      Note ("{0}：{1}〜{2} が止まりました（終了コード {3}）。{4} の最後の 20 行を送ってください。次へ進みます" -f $key, $a, $b, $code, $blog)
    }
    Release $tag
  }
}

if ($Worker -gt 0) { Run-Jobs; exit 0 }

# ---------------------------------------------------------------- まとめ役（描き手を起こして見守り、最後にまとめる）
Add-Type -Namespace Maru -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483649)
Get-ChildItem $done -Filter "*.lock" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
# ほかの回（QR回など）の描画が動いているあいだは待つ（同じグラフィックボードを取り合うと、どちらも遅くなる）
$waited = $false
while ($true) {
  $busy = @(Get-CimInstance Win32_Process -Filter "Name='blender.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match '\s-b\s' })
  if ($busy.Count -eq 0) { break }
  if (-not $waited) { Note ("ほかの回の描画（Blender {0} 本）が動いています。終わるのを待ってから、3本目を描き始めます（このままで大丈夫です）" -f $busy.Count); $waited = $true }
  Start-Sleep -Seconds 300
}
if ($waited) { Note "ほかの回の描画が終わったので、3本目を描き始めます" }
if ($gep) { Get-ChildItem $out -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".mp4" -or $_.Name -like "*_log.json" } | ForEach-Object { if (-not (Test-Path (Join-Path $gep $_.Name))) { Copy-Item $_.FullName $gep -Force -ErrorAction SilentlyContinue } } }
$total = (AllChunks).Count
Note ("はじめます：{0} 場面・{1} 本（100 コマずつ）。残り {2} 本。同時に {3} 本。Blender：{4}" -f $JOBS.Count, $total, (Left), $Workers, $blender)
$tAll = Get-Date
if ($Workers -le 1) { Run-Jobs }
else {
  $n0 = @(Get-Content $log -Encoding UTF8 -ErrorAction SilentlyContinue).Count
  $procs = @()
  for ($k = 1; $k -le $Workers; $k++) {
    $al = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Only "{1}" -Blender "{2}" -Workers {3} -Worker {4} -Samples {5}' -f $PSCommandPath, $Only, $blender, $Workers, $k, $Samples
    $procs += Start-Process -FilePath "powershell.exe" -ArgumentList $al -WindowStyle Minimized -PassThru
    Start-Sleep -Seconds 20
  }
  Write-Host "描き手 $Workers 人が描いています（タスクバーの「まるロボ 描き手」の窓）。進み具合は、この窓にも出ます"
  while (@($procs | Where-Object { -not $_.HasExited }).Count -gt 0) {
    Start-Sleep -Seconds 15
    $all = @(Get-Content $log -Encoding UTF8 -ErrorAction SilentlyContinue)   # 描き手が書いている最中は読めないことがある（次の回に読む）
    if ($all.Count -gt $n0 -and $all.Count -gt 0) { $all[$n0..($all.Count - 1)] | ForEach-Object { Write-Host $_ }; $n0 = $all.Count }
  }
}
# 送るファイルをまとめる（mp4 と、場面ごとの記録 *_log.json）
$dst = Join-Path $root "marurobo_render\ep03_v6"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem $out -File | Where-Object { $_.Extension -eq ".mp4" -or $_.Name -like "*_log.json" } | ForEach-Object { Copy-Item $_.FullName $dst -Force }
$left = Left
$mb = [Math]::Round(((Get-ChildItem $dst -File | Measure-Object Length -Sum).Sum) / 1MB)
Note ("送るファイルを {0} にまとめました（{1} MB）" -f $dst, $mb)
$g = @(Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Root }) + @($env:USERPROFILE) | ForEach-Object { foreach ($nm in "マイドライブ", "My Drive") { Join-Path $_ $nm } } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($g) { $gd = Join-Path $g "marurobo_render"; New-Item -ItemType Directory -Force -Path $gd | Out-Null; Copy-Item $dst $gd -Recurse -Force; Note ("Google ドライブ（{0}\ep03_v6）にコピーしました" -f $gd) }
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483648)
if ($left -gt 0) { Note ("終わりました（{0}）。まだ {1} 本そろっていません。同じ行をもう一度走らせると、足りない所だけ描きます" -f (Fmt ((Get-Date) - $tAll)), $left) }
elseif ($g) { Note ("ぜんぶ終わりました（{0}）。Google ドライブへのアップロードは自動で進みます（終わるまで PC は入れたままに）。チャットで知らせてください" -f (Fmt ((Get-Date) - $tAll))) }
else { Note ("ぜんぶ終わりました（{0}）。{1} のフォルダを、Google ドライブの marurobo_render にアップロードして、チャットで知らせてください" -f (Fmt ((Get-Date) - $tAll)), $dst) }
