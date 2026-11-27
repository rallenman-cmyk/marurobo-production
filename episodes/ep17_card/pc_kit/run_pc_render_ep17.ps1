# まるロボ 17本目「使っていないカード」：PC の本番描画（3D の 202 カット・合わせて 29010 コマ。承認ずみの章：本編 0.00〜974.00 秒）
#   使い方：PowerShell に README_PC.md の 1 行を貼って Enter
#   同時に描く本数：最後に -Workers 2 のように付ける（既定 3、1〜4）
#   一部だけ描く：最後に -Only B12e,I35 のように付ける（カットの名前をカンマで区切る）
#   描く細かさ：-Samples 24（既定。光の跳ね返りを減らす --fast と合わせて、48 の約 3 倍速い）。大きくすると、きれいになるが時間がかかる
#   途中で止まったり窓を閉じたりしても、同じ行をもう一度走らせれば、できている所は飛ばして続きから描く
#   描いているあいだ、PC がスリープしないようにする（画面は消えてもよい。ノート PC は電源につなぎ、ふたは閉じない）
#   終わると、送るファイルだけを C:\marurobo\marurobo_render\ep17_v1 にまとめる。Google ドライブ（パソコン版）があれば、そこへもコピーする
#   （9本目の手順と同じ作り。17本目の 3D の中の絵（カード・数字のタイル・スマホの画面・札）は anim/tex17 の PNG を使う）
param([string]$Only = "", [string]$Blender = "", [int]$Workers = 3, [int]$Worker = 0, [int]$Samples = 24)
$ErrorActionPreference = "Continue"
$kit = Split-Path -Parent $PSScriptRoot                      # ...\marurobo_ep17
$anim = Join-Path $kit "episodes\ep17_card\anim"
$env:MARU_REQUIRE_REAL = "1"
$env:TEX17 = Join-Path $anim "tex17"   # カード・数字のタイル・スマホの画面・札の絵   # 本物のまるロボ（story.blend）がないときは止める（代わりの体で本番を描かない）
$root = "C:\marurobo"
if (-not (Test-Path $root)) { $root = Split-Path -Parent $kit }
$JOBS = @(
  @("A01", 72, "scenes.py"),
  @("A01b", 196, "scenes.py"),
  @("A01c", 147, "scenes.py"),
  @("A01d", 164, "scenes.py"),
  @("A02", 140, "scenes.py"),
  @("A02b", 96, "scenes.py"),
  @("A02c", 103, "scenes.py"),
  @("A02d", 149, "scenes.py"),
  @("A02e", 89, "scenes.py"),
  @("A02f", 88, "scenes.py"),
  @("A02g", 145, "scenes.py"),
  @("A02h", 151, "scenes.py"),
  @("A03", 119, "scenes.py"),
  @("A03a", 158, "scenes.py"),
  @("A03b", 138, "scenes.py"),
  @("A03b2", 102, "scenes.py"),
  @("A03c", 95, "scenes.py"),
  @("A04", 112, "scenes.py"),
  @("A04b", 187, "scenes.py"),
  @("A04c", 130, "scenes.py"),
  @("A04d", 154, "scenes.py"),
  @("P05", 325, "scenes.py"),
  @("A05", 171, "scenes.py"),
  @("A05b", 58, "scenes.py"),
  @("A05b2", 86, "scenes.py"),
  @("A05c", 93, "scenes.py"),
  @("A05d", 132, "scenes.py"),
  @("P06", 396, "scenes.py"),
  @("A06", 164, "scenes.py"),
  @("A06b", 158, "scenes.py"),
  @("A06c", 143, "scenes.py"),
  @("P07", 353, "scenes.py"),
  @("A07", 157, "scenes.py"),
  @("A07b", 120, "scenes.py"),
  @("A07c", 144, "scenes.py"),
  @("A08", 136, "scenes.py"),
  @("A08b", 138, "scenes.py"),
  @("A08c", 144, "scenes.py"),
  @("A08d", 96, "scenes.py"),
  @("A08e", 166, "scenes.py"),
  @("A09", 143, "scenes.py"),
  @("A09b", 107, "scenes.py"),
  @("A09c", 125, "scenes.py"),
  @("A10", 151, "scenes.py"),
  @("A10b", 78, "scenes.py"),
  @("A10b2", 134, "scenes.py"),
  @("A10b3", 124, "scenes.py"),
  @("A10c", 108, "scenes.py"),
  @("A10d", 148, "scenes.py"),
  @("A10e", 88, "scenes.py"),
  @("A11", 86, "scenes.py"),
  @("A11a", 164, "scenes.py"),
  @("A11a2", 122, "scenes.py"),
  @("A11b", 145, "scenes.py"),
  @("A11c", 175, "scenes.py"),
  @("A11d", 148, "scenes.py"),
  @("A12", 101, "scenes.py"),
  @("A12b", 138, "scenes.py"),
  @("A12c", 153, "scenes.py"),
  @("A12c2", 157, "scenes.py"),
  @("A12d", 111, "scenes.py"),
  @("A12e", 130, "scenes.py"),
  @("C13", 144, "scenes.py"),
  @("C13b", 147, "scenes.py"),
  @("C13c", 157, "scenes.py"),
  @("C13d", 161, "scenes.py"),
  @("C13e", 108, "scenes.py"),
  @("C13f", 139, "scenes.py"),
  @("C13g", 100, "scenes.py"),
  @("C13h", 162, "scenes.py"),
  @("C13i", 77, "scenes.py"),
  @("C13j", 189, "scenes.py"),
  @("I14", 107, "scenes.py"),
  @("I14c", 93, "scenes.py"),
  @("I14b", 155, "scenes.py"),
  @("C14", 199, "scenes.py"),
  @("C14b", 110, "scenes.py"),
  @("C14b2", 135, "scenes.py"),
  @("C14c", 183, "scenes.py"),
  @("C14d", 130, "scenes.py"),
  @("C14e", 165, "scenes.py"),
  @("B15", 146, "scenes.py"),
  @("B15b", 111, "scenes.py"),
  @("B15c", 228, "scenes.py"),
  @("B15d", 125, "scenes.py"),
  @("B15e", 161, "scenes.py"),
  @("B15f", 104, "scenes.py"),
  @("B15g", 196, "scenes.py"),
  @("B15h", 125, "scenes.py"),
  @("B15h2", 157, "scenes.py"),
  @("B15i", 154, "scenes.py"),
  @("B15j", 135, "scenes.py"),
  @("C16", 127, "scenes.py"),
  @("C16b", 91, "scenes.py"),
  @("C16c", 119, "scenes.py"),
  @("C16c2", 93, "scenes.py"),
  @("C16d", 140, "scenes.py"),
  @("C16e", 140, "scenes.py"),
  @("C16f", 211, "scenes.py"),
  @("C16g", 60, "scenes.py"),
  @("C16h", 119, "scenes.py"),
  @("C16i", 117, "scenes.py"),
  @("C16j", 161, "scenes.py"),
  @("C16k", 123, "scenes.py"),
  @("C16l", 158, "scenes.py"),
  @("C17", 84, "scenes.py"),
  @("C17b", 132, "scenes.py"),
  @("C17c", 138, "scenes.py"),
  @("C17d", 109, "scenes.py"),
  @("C17e", 126, "scenes.py"),
  @("C17f", 94, "scenes.py"),
  @("C17h", 101, "scenes.py"),
  @("C17g", 89, "scenes.py"),
  @("C18", 110, "scenes.py"),
  @("C18b", 92, "scenes.py"),
  @("C18c", 49, "scenes.py"),
  @("A18", 149, "scenes.py"),
  @("A18b", 157, "scenes.py"),
  @("A18c", 242, "scenes.py"),
  @("A18d", 107, "scenes.py"),
  @("P18", 341, "scenes.py"),
  @("A18e", 234, "scenes.py"),
  @("A18f", 157, "scenes.py"),
  @("A19", 192, "scenes.py"),
  @("P19", 173, "scenes.py"),
  @("A19b", 194, "scenes.py"),
  @("A19c", 146, "scenes.py"),
  @("A19d", 177, "scenes.py"),
  @("A20", 235, "scenes.py"),
  @("A20b", 160, "scenes.py"),
  @("D21", 126, "scenes.py"),
  @("D21b", 165, "scenes.py"),
  @("D21c", 150, "scenes.py"),
  @("P21", 73, "scenes.py"),
  @("D21d", 103, "scenes.py"),
  @("D21e", 127, "scenes.py"),
  @("D21f", 150, "scenes.py"),
  @("D21g", 155, "scenes.py"),
  @("D21h", 164, "scenes.py"),
  @("D21i", 178, "scenes.py"),
  @("A22", 143, "scenes.py"),
  @("A22b", 137, "scenes.py"),
  @("A22c", 756, "scenes.py"),
  @("A22d", 165, "scenes.py"),
  @("C23", 170, "scenes.py"),
  @("C23b", 109, "scenes.py"),
  @("C23c", 114, "scenes.py"),
  @("C23d", 164, "scenes.py"),
  @("C23e", 110, "scenes.py"),
  @("C24", 114, "scenes.py"),
  @("C24b", 162, "scenes.py"),
  @("C24c", 98, "scenes.py"),
  @("C24d", 134, "scenes.py"),
  @("C24e", 162, "scenes.py"),
  @("C24f", 216, "scenes.py"),
  @("C25", 165, "scenes.py"),
  @("C25b", 143, "scenes.py"),
  @("C25c", 178, "scenes.py"),
  @("C26", 96, "scenes.py"),
  @("C26b", 83, "scenes.py"),
  @("C26c", 76, "scenes.py"),
  @("C26d", 88, "scenes.py"),
  @("C26e", 173, "scenes.py"),
  @("C26f", 87, "scenes.py"),
  @("C26g", 59, "scenes.py"),
  @("C26h", 190, "scenes.py"),
  @("C26i", 94, "scenes.py"),
  @("C26j", 105, "scenes.py"),
  @("C26k", 42, "scenes.py"),
  @("C26l", 135, "scenes.py"),
  @("C26m", 185, "scenes.py"),
  @("C26n", 200, "scenes.py"),
  @("C26o", 95, "scenes.py"),
  @("C26p", 135, "scenes.py"),
  @("C26q", 180, "scenes.py"),
  @("C26r", 145, "scenes.py"),
  @("C27", 149, "scenes.py"),
  @("C27a", 146, "scenes.py"),
  @("C27b", 116, "scenes.py"),
  @("A28", 131, "scenes.py"),
  @("A28b", 135, "scenes.py"),
  @("A28c", 165, "scenes.py"),
  @("A28c2", 186, "scenes.py"),
  @("A28d", 227, "scenes.py"),
  @("A28e", 175, "scenes.py"),
  @("A28f", 160, "scenes.py"),
  @("A28g", 124, "scenes.py"),
  @("A28h", 152, "scenes.py"),
  @("A29", 138, "scenes.py"),
  @("A29b", 121, "scenes.py"),
  @("A29c", 186, "scenes.py"),
  @("A29d", 137, "scenes.py"),
  @("A29e", 159, "scenes.py"),
  @("A29f", 108, "scenes.py"),
  @("A30", 169, "scenes.py"),
  @("A30b", 80, "scenes.py"),
  @("A30c", 104, "scenes.py"),
  @("A30d", 96, "scenes.py"),
  @("A30d2", 113, "scenes.py"),
  @("A30e", 153, "scenes.py"),
  @("A31", 160, "scenes.py"),
  @("A31b", 120, "scenes.py")
)
if ($Only) { $want = @($Only.Split(",") | ForEach-Object { $_.Trim() }); $sel = New-Object System.Collections.ArrayList; foreach ($j in $JOBS) { if ($want -contains $j[0]) { [void]$sel.Add($j) } }; $JOBS = $sel.ToArray() }
$out = Join-Path $root "render_ep17_v1"
$log = Join-Path $root "render_log_ep17.txt"
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
if ($gdrive) { $gep = Join-Path $gdrive "marurobo_render\ep17_v1"; New-Item -ItemType Directory -Force -Path $gep -ErrorAction SilentlyContinue | Out-Null }

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
if (-not (Test-Path (Join-Path $anim "scenes.py"))) { Note "見つかりません：$anim\scenes.py（marurobo_ep17.zip を C:\marurobo に展開し直してください）"; exit 1 }

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
    $argv = @("-b", "--factory-startup", "--python-exit-code", "1", "--python", (Join-Path $anim $py), "--", $key, $out, "--samples", "$Samples", "--res", "1920", "1080", "--frames", "$a", "$b", "--gpu", "--video", "--fast")
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
  if (-not $waited) { Note ("ほかの回の描画（Blender {0} 本）が動いています。終わるのを待ってから、17本目を描き始めます（このままで大丈夫です）" -f $busy.Count); $waited = $true }
  Start-Sleep -Seconds 300
}
if ($waited) { Note "ほかの回の描画が終わったので、17本目を描き始めます" }
if ($gep) { Get-ChildItem $out -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".mp4" -or $_.Name -like "*_log.json" } | ForEach-Object { if (-not (Test-Path (Join-Path $gep $_.Name))) { Copy-Item $_.FullName $gep -Force -ErrorAction SilentlyContinue } } }
$total = (AllChunks).Count
Note ("はじめます：{0} カット・{1} 本（100 コマずつ）。残り {2} 本。同時に {3} 本。Blender：{4}" -f $JOBS.Count, $total, (Left), $Workers, $blender)
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
$dst = Join-Path $root "marurobo_render\ep17_v1"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem $out -File | Where-Object { $_.Extension -eq ".mp4" -or $_.Name -like "*_log.json" } | ForEach-Object { Copy-Item $_.FullName $dst -Force }
$left = Left
$mb = [Math]::Round(((Get-ChildItem $dst -File | Measure-Object Length -Sum).Sum) / 1MB)
Note ("送るファイルを {0} にまとめました（{1} MB）" -f $dst, $mb)
$g = @(Get-PSDrive -PSProvider FileSystem | ForEach-Object { $_.Root }) + @($env:USERPROFILE) | ForEach-Object { foreach ($nm in "マイドライブ", "My Drive") { Join-Path $_ $nm } } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($g) { $gd = Join-Path $g "marurobo_render"; New-Item -ItemType Directory -Force -Path $gd | Out-Null; Copy-Item $dst $gd -Recurse -Force; Note ("Google ドライブ（{0}\ep17_v1）にコピーしました" -f $gd) }
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483648)
if ($left -gt 0) { Note ("終わりました（{0}）。まだ {1} 本そろっていません。同じ行をもう一度走らせると、足りない所だけ描きます" -f (Fmt ((Get-Date) - $tAll)), $left) }
elseif ($g) { Note ("ぜんぶ終わりました（{0}）。Google ドライブへのアップロードは自動で進みます（終わるまで PC は入れたままに）。チャットで知らせてください" -f (Fmt ((Get-Date) - $tAll))) }
else { Note ("ぜんぶ終わりました（{0}）。{1} のフォルダを、Google ドライブの marurobo_render にアップロードして、チャットで知らせてください" -f (Fmt ((Get-Date) - $tAll)), $dst) }
