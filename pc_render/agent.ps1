# まるロボ PC の描画係（置きっぱなしで動く。1 件ずつ順に描く）
#   はじめ方：pc_render/はじめに.md の 1 行を PowerShell に貼る（最初の 1 回だけ）。あとは PC を入れると自動で立ち上がる
#   やること：GitHub から依頼票（pc_render/queue/*.json）を取る → 短い直しを先に、1 件ずつ、その回の手順（run_pc_render_*.ps1）で描く
#             → 終わった印を GitHub の枝 pc-render-status に置く。動画は、各回の手順が Google ドライブ（marurobo_render）へコピーする
#   止め方：この窓を閉じる（描いている途中なら、描き手の窓も閉じる）。もう一度はじめると、できている所は飛ばして続きから
#   記録：C:\marurobo\pc_agent_log.txt
param([int]$Every = 120)
$ErrorActionPreference = "Continue"
$root = "C:\marurobo"
$repo = Join-Path $root "repo"
$stat = Join-Path $root "status_repo"
$kits = Join-Path $root "kit_zip"
$log = Join-Path $root "pc_agent_log.txt"
$branch = "claude/focused-cannon-l5328u"
$sbranch = "pc-render-status"
$url = "https://github.com/rallenman-cmyk/marurobo-production.git"
$Host.UI.RawUI.WindowTitle = "まるロボ 描画係"

function Note([string]$m) {
  $line = "{0}  {1}" -f (Get-Date -Format "MM/dd HH:mm"), $m
  Write-Host $line
  try { Add-Content -Path $log -Value $line -Encoding UTF8 -ErrorAction Stop } catch { }
}

# ---------------------------------------------------------------- 二重に立ち上げない
$created = $false
$mutex = New-Object System.Threading.Mutex($true, "Global\marurobo_pc_agent", [ref]$created)
if (-not $created) { Write-Host "描画係は、もう動いています（タスクバーの「まるロボ 描画係」の窓）。この窓は閉じて大丈夫です"; Start-Sleep -Seconds 8; exit 0 }

# ---------------------------------------------------------------- Git を探す
$git = "C:\Program Files\Git\cmd\git.exe"
if (-not (Test-Path $git)) { $g = Get-Command git.exe -ErrorAction SilentlyContinue; if ($g) { $git = $g.Source } }
if (-not (Test-Path $git)) { Note "Git が見つかりません。pc_render/はじめに.md の 1 行を、もう一度 PowerShell に貼ってください"; Start-Sleep -Seconds 30; exit 1 }
function G { & $git @args 2>&1 | ForEach-Object { "$_" } }

# ---------------------------------------------------------------- PC を入れたら自動で立ち上がるようにする（スタートアップに置く）
try {
  $lnk = Join-Path ([Environment]::GetFolderPath("Startup")) "marurobo_pc_agent.lnk"
  if (-not (Test-Path $lnk)) {
    $ws = New-Object -ComObject WScript.Shell
    $s = $ws.CreateShortcut($lnk)
    $s.TargetPath = "powershell.exe"
    $s.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $repo "pc_render\agent.ps1")
    $s.WindowStyle = 7
    $s.Save()
    Note "PC を入れたとき、描画係が自動で立ち上がるようにしました"
  }
} catch { Note ("自動の立ち上げは設定できませんでした（{0}）。PC を入れ直したら、はじめに.md の 1 行をもう一度貼ってください" -f $_.Exception.Message) }

# ---------------------------------------------------------------- 眠らせない
Add-Type -Namespace Maru -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Maru.Power]::SetThreadExecutionState([uint32]2147483649)

# ---------------------------------------------------------------- 終わった印を置く枝（pc-render-status）の用意
function Status-Ready {
  if (Test-Path (Join-Path $stat ".git")) { return $true }
  $o = G clone --single-branch -b $sbranch $url $stat
  if (Test-Path (Join-Path $stat ".git")) { return $true }
  Note ("終わった印の枝を取れませんでした：{0}" -f ($o -join " "))
  return $false
}
function Status-Push([string]$msg) {
  if (-not (Status-Ready)) { return }
  for ($t = 0; $t -lt 3; $t++) {
    [void](G -C $stat add -A)
    [void](G -C $stat -c user.name=marurobo-pc -c user.email=pc@marurobo.invalid commit -q -m $msg)
    $o = G -C $stat push -q origin $sbranch
    if ($LASTEXITCODE -eq 0) { return }
    [void](G -C $stat pull -q --rebase origin $sbranch)
    Start-Sleep -Seconds (5 * ($t + 1))
  }
  Note "終わった印を送れませんでした（次の機会にまとめて送ります）"
}
function Write-Json([string]$path, $obj) {
  $dir = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $txt = $obj | ConvertTo-Json -Depth 6
  [System.IO.File]::WriteAllText($path, $txt, (New-Object System.Text.UTF8Encoding($false)))
}
function Heartbeat([string]$state, $job, $waiting) {
  if (-not (Status-Ready)) { return }
  $jid = ""
  if ($job) { $jid = $job.id }
  Write-Json (Join-Path $stat "agent.json") ([ordered]@{ at = (Get-Date).ToString("s"); state = $state; job = $jid; waiting = @($waiting) })
  Status-Push ("描画係：{0} {1}" -f $state, $jid)
}

# ---------------------------------------------------------------- 依頼票を読む（短い直しを先に。同じ重さなら order、その次に受付の順）
function Pull-Repo {
  $o = G -C $repo fetch -q origin $branch
  if ($LASTEXITCODE -ne 0) { Note ("GitHub から取れませんでした（ネットを確かめてください。あとでまた試します）：{0}" -f ($o -join " ")); return $false }
  [void](G -C $repo reset -q --hard "origin/$branch")
  return $true
}
function Read-Queue {
  $list = @()
  $qd = Join-Path $repo "pc_render\queue"
  if (-not (Test-Path $qd)) { return ,$list }
  foreach ($f in (Get-ChildItem $qd -Filter "*.json" -File)) {
    try {
      $j = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
      if (-not $j.id -or -not $j.ps1 -or -not $j.zip -or -not $j.kit_branch) { continue }
      if ($j.id -notmatch '^[A-Za-z0-9_.-]+$' -or $j.ps1 -notmatch '^[A-Za-z0-9_.-]+\.ps1$' -or $j.zip -notmatch '^[A-Za-z0-9_.-]+\.zip$' -or $j.kit_branch -notmatch '^pc-kit/[A-Za-z0-9_.-]+$') { continue }
      if ($j.only -and $j.only -notmatch '^[A-Za-z0-9_,.-]+$') { continue }
      if (Test-Path (Join-Path $stat ("done\{0}.json" -f $j.id))) { continue }
      $list += $j
    } catch { Note ("読めない依頼票：{0}" -f $f.Name) }
  }
  $sorted = @($list | Sort-Object @{ Expression = { if ($_.kind -eq "fix") { 0 } else { 1 } } }, @{ Expression = { if ($_.order) { [int]$_.order } else { 999 } } }, @{ Expression = { "$($_.created)" } }, @{ Expression = { "$($_.id)" } })
  return ,$sorted
}

# ---------------------------------------------------------------- 1 件を描く
function Wait-OtherBlender {
  $said = $false
  while ($true) {
    $busy = @(Get-CimInstance Win32_Process -Filter "Name='blender.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match '\s-b\s' })
    if ($busy.Count -eq 0) { break }
    if (-not $said) { Note ("手で始めた描画（Blender {0} 本）が動いています。終わるのを待ちます（止めません）" -f $busy.Count); $said = $true }
    Start-Sleep -Seconds 120
  }
}
function Get-Kit($job) {
  # 一式（zip）は、GitHub の枝 pc-kit/<名前> に 1 つだけ入っている。取ってきて C:\marurobo に広げる
  New-Item -ItemType Directory -Force -Path $kits | Out-Null
  $o = G -C $repo fetch -q origin $job.kit_branch
  if ($LASTEXITCODE -ne 0) { return ("一式の枝 {0} を取れません：{1}" -f $job.kit_branch, ($o -join " ")) }
  $zip = Join-Path $kits $job.zip
  if (Test-Path $zip) { Remove-Item $zip -Force }
  cmd /c ('""{0}" -C "{1}" cat-file blob FETCH_HEAD:{2} > "{3}""' -f $git, $repo, $job.zip, $zip)
  if (-not (Test-Path $zip) -or (Get-Item $zip).Length -lt 1000) { return ("一式 {0} が枝に見つかりません" -f $job.zip) }
  try { Expand-Archive -Path $zip -DestinationPath $root -Force -ErrorAction Stop } catch { return ("一式を広げられません：{0}" -f $_.Exception.Message) }
  return ""
}
function Run-Job($job) {
  $t0 = Get-Date
  $tail = New-Object System.Collections.ArrayList
  $state = "failed"
  $err = Get-Kit $job
  if (-not $err) {
    $ps1 = Get-ChildItem $root -Recurse -Depth 3 -Filter $job.ps1 -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "$repo\*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $ps1) { $err = ("手順 {0} が一式の中に見つかりません" -f $job.ps1) }
  }
  if ($err) { Note $err; [void]$tail.Add($err) }
  else {
    for ($try = 1; $try -le 2 -and $state -ne "done"; $try++) {
      $a = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ps1.FullName)
      if ($job.only) { $a += @("-Only", "$($job.only)") }
      if ($job.workers) { $a += @("-Workers", "$([int]$job.workers)") }
      if ($job.samples) { $a += @("-Samples", "$([int]$job.samples)") }
      Note ("描きます：{0}（{1} 回目）" -f $job.id, $try)
      & powershell.exe @a 2>&1 | ForEach-Object {
        $line = "$_"
        Write-Host $line
        [void]$tail.Add($line)
        if ($tail.Count -gt 40) { $tail.RemoveAt(0) }
        if ($line -match "ぜんぶ終わりました") { $state = "done" }
      }
    }
  }
  $min = [int]((Get-Date) - $t0).TotalMinutes
  Write-Json (Join-Path $stat ("done\{0}.json" -f $job.id)) ([ordered]@{ id = $job.id; state = $state; finished = (Get-Date).ToString("s"); minutes = $min; tail = @($tail | Select-Object -Last 12) })
  if ($state -eq "done") { Note ("終わりました：{0}（{1} 分）" -f $job.id, $min) }
  else { Note ("そろいませんでした：{0}（{1} 分）。印に記録して、次へ進みます" -f $job.id, $min) }
  Status-Push ("{0}：{1}" -f $job.id, $state)
}

# ---------------------------------------------------------------- 回し続ける
Note "描画係をはじめます（この窓は置いたままにしてください。最小化して大丈夫です）"
$me = (Get-FileHash $PSCommandPath -Algorithm SHA256).Hash
$lastBeat = Get-Date "2000-01-01"
while ($true) {
  if ((Status-Ready) -and (Pull-Repo)) {
    if ((Get-FileHash (Join-Path $repo "pc_render\agent.ps1") -Algorithm SHA256).Hash -ne $me) {
      Note "描画係が新しくなったので、入れ替えて立ち上げ直します"
      $mutex.ReleaseMutex(); $mutex.Dispose()
      Start-Process -FilePath "powershell.exe" -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $repo "pc_render\agent.ps1"))
      exit 0
    }
    [void](G -C $stat pull -q --rebase origin $sbranch)
    $q = Read-Queue
    if ($q.Count -gt 0) {
      $job = $q[0]
      $rest = @($q | Select-Object -Skip 1 | ForEach-Object { $_.id })
      Wait-OtherBlender
      Heartbeat "描いています" $job $rest
      Run-Job $job
      $lastBeat = Get-Date "2000-01-01"
      continue
    }
  }
  if (((Get-Date) - $lastBeat).TotalMinutes -ge 60) { Heartbeat "待っています" $null @(); $lastBeat = Get-Date }
  Start-Sleep -Seconds $Every
}
