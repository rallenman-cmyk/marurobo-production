# まるロボ：いま走っている描画が終わるのを待ってから、新しいキット（この中の marurobo_tools）に入れ替えて、続けて描く
#   使い方：新しい PowerShell の窓に次の1行を貼って Enter（いま描いている窓はそのまま。閉じない）
#     $f = Get-ChildItem C:\marurobo -Recurse -Filter run_after.ps1 | Select-Object -First 1; powershell -ExecutionPolicy Bypass -File $f.FullName
#   1. いまの描画（run_pc_render.ps1）が終わるまで待つ（5 分ごとに様子を出す）
#   2. 終わったら、いまのキットのフォルダに新しいキットを上書きする（描けた絵と「済み」の印はそのまま）
#   3. 新しいキットで描く（描けている所は飛ばして、足りない所だけ）。そろわなければ、もう 1 回だけ描き直す
#   4. 終わったあとも 4 時間は PC をスリープさせない（Google ドライブへのアップロードのため）
#   2026-11-14 v24b 用
$ErrorActionPreference = "Continue"
$here = $PSScriptRoot
$newKit = Join-Path $here "marurobo_tools"
$Host.UI.RawUI.WindowTitle = "まるロボ あとで続ける"
function Say([string]$m) { Write-Host ("{0}  {1}" -f (Get-Date -Format "MM/dd HH:mm"), $m) }
if (-not (Test-Path (Join-Path $newKit "run_pc_render.ps1"))) { Say "見つかりません：$newKit\run_pc_render.ps1（zip を展開し直してください）"; Read-Host "Enter で閉じます"; exit 1 }

# PC をスリープさせない（この窓が開いているあいだ）
Add-Type -Namespace MaruAfter -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][MaruAfter.Power]::SetThreadExecutionState([uint32]2147483649)

# いま走っている描画（この marurobo_next の外の run_pc_render.ps1）を探す
function Running {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ($_.Name -eq "powershell.exe" -or $_.Name -eq "pwsh.exe") -and $_.CommandLine -and
    $_.CommandLine -match "run_pc_render\.ps1" -and $_.CommandLine -notmatch "marurobo_next"
  })
}
# いまのキットのフォルダ：走っている描画の場所から。走っていなければ C:\marurobo の中を探す
$oldDir = $null
foreach ($p in (Running)) {
  if ($p.CommandLine -match '-File\s+"?([^"]*run_pc_render\.ps1)') { $oldDir = Split-Path -Parent $Matches[1]; break }
}
if (-not $oldDir) {
  $c = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "marurobo_next" } | Select-Object -First 1
  if ($c) { $oldDir = $c.DirectoryName }
}
if (-not $oldDir -or -not (Test-Path $oldDir)) { Say "いまのキット（marurobo_tools）が C:\marurobo の中に見つかりません"; Read-Host "Enter で閉じます"; exit 1 }
$root = Split-Path -Parent $oldDir
if ((Split-Path -Leaf $root) -eq "marurobo_tools") { $root = Split-Path -Parent $root }
$log = Join-Path $root "render_log.txt"
Say "いまのキット：$oldDir"

# 1. いまの描画が終わるのを待つ
$n = 0
while ((Running).Count -gt 0) {
  if ($n % 10 -eq 0) {
    $last = ""
    if (Test-Path $log) { $last = @(Get-Content $log -Encoding UTF8 -Tail 1) -join "" }
    Say "いまの描画が終わるのを待っています（窓は閉じないでください）。最後の記録：$last"
  }
  Start-Sleep -Seconds 30
  $n++
}
Say "いまの描画が終わりました。新しいキットに入れ替えます"
Start-Sleep -Seconds 20

# 2. 新しいキットを上書きする
robocopy $newKit $oldDir /E /R:3 /W:5 /NFL /NDL /NJH /NJS /NP | Out-Null
$bad = @("run_pc_render.ps1", "qr\qr_c4_factory.py", "qr\qr_op2_stage.py" | Where-Object { (Get-FileHash (Join-Path $newKit $_)).Hash -ne (Get-FileHash (Join-Path $oldDir $_)).Hash })
if ($bad.Count -gt 0) { Say "入れ替えに失敗しました（$oldDir が開かれていないか確かめてください）"; Read-Host "Enter で閉じます"; exit 1 }
Say "入れ替えました。新しいキットで描きます"

# 3. 新しいキットで描く。そろわなければ、もう 1 回だけ
for ($k = 1; $k -le 2; $k++) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $oldDir "run_pc_render.ps1")
  $last = ""
  if (Test-Path $log) { $last = @(Get-Content $log -Encoding UTF8 -Tail 1) -join "" }
  if ($last -notmatch "そろっていない") { break }
  if ($k -lt 2) { Say "そろっていない所があるので、もう 1 回だけ描きます" }
}

# 4. アップロードのため、4 時間は PC をスリープさせない
Say "描き終わりました。Google ドライブへのアップロードのため、4 時間は PC をスリープさせません（この窓は閉じなくて大丈夫です）"
Start-Sleep -Seconds 14400
[void][MaruAfter.Power]::SetThreadExecutionState([uint32]2147483648)
Say "おわり（スリープの止めを外しました）"
