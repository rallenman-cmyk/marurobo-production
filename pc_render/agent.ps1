# まるロボ PC の描画係（置きっぱなしで動く。1 件ずつ順に描く）
#   はじめ方：pc_render/はじめに.md の 1 行を PowerShell に貼る（最初の 1 回だけ）。あとは PC を入れると自動で立ち上がる
#   やること：GitHub から依頼票（pc_render/queue/*.json）を取る → 短い直しを先に、1 件ずつ、その回の手順（run_pc_render_*.ps1）で描く
#             → 終わった印を GitHub の枝 pc-render-status に置く。動画は、各回の手順が Google ドライブ（marurobo_render）へコピーする
#   止め方：この窓を閉じる（描いている途中なら、描き手の窓も閉じる）。もう一度はじめると、できている所は飛ばして続きから
#   記録：C:\marurobo\pc_agent_log.txt
param([int]$Every = 120)
$VER = "8"
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
function Heartbeat([string]$state, $job, $waiting, [string]$progress = "") {
  if (-not (Status-Ready)) { return }
  $jid = ""
  if ($job) { $jid = $job.id }
  Write-Json (Join-Path $stat "agent.json") ([ordered]@{ at = (Get-Date).ToString("s"); ver = $VER; state = $state; job = $jid; waiting = @($waiting); progress = $progress })
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
function Other-Blender {
  return @(Get-CimInstance Win32_Process -Filter "Name='blender.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match '\s-b\s' }).Count
}
# その一式（フォルダ）から動いている手順と Blender を、ぜんぶ止める（できている所は残る。次に走らせると続きから）
function Kill-Kit([string]$kitdir) {
  if (-not $kitdir -or $kitdir.Length -lt 12) { return }
  for ($k = 0; $k -lt 3; $k++) {
    $ps = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine.ToLower().Contains($kitdir.ToLower()) })
    if ($ps.Count -eq 0) { break }
    foreach ($p in $ps) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 4
  }
}
# 同時に何本描くのが一番速いかを、最初の全部描きのときに 1 回だけ測る（測るのに描いた分は、そのまま本番に使う）
#   長いカット（1000 コマ以上・まだ手つかず）を 1 つ選び、1 本 → 2 本 → 3 本 → 4 本同時で、100 コマずつ描く速さを比べる
function Measure-Workers($job, $ps1) {
  $wf = Join-Path $root "pc_workers.json"
  if (Test-Path $wf) { return }
  $txt = Get-Content $ps1.FullName -Raw -Encoding UTF8
  $mo = [regex]::Match($txt, '\$out = Join-Path \$root "([A-Za-z0-9_.-]+)"')
  $cuts = [regex]::Matches($txt, '@\("([A-Za-z0-9_]+)",\s*(\d+),')
  if (-not $mo.Success -or $cuts.Count -eq 0) { return }
  $done = Join-Path $root ($mo.Groups[1].Value + "\_done")
  $cut = ""; $best = 0
  foreach ($c in $cuts) {
    $nm = $c.Groups[1].Value; $fr = [int]$c.Groups[2].Value
    if ($fr -lt 1000 -or $fr -le $best) { continue }
    if (@(Get-ChildItem $done -Filter ($nm + "_*.ok") -ErrorAction SilentlyContinue).Count -gt 0) { continue }
    $cut = $nm; $best = $fr
  }
  if (-not $cut) { Note "同時本数は、まだ測れません（長い手つかずのカットが無い）。既定の本数で描きます"; return }
  $kitdir = Split-Path -Parent (Split-Path -Parent $ps1.FullName)
  Note ("同時に何本が一番速いかを測ります（カット {0} で 1〜4 本。描いた分はそのまま使います）" -f $cut)
  $rate = [ordered]@{}; $limit = 5400
  foreach ($w in 1, 2, 3, 4) {
    $before = @(Get-ChildItem $done -Filter ($cut + "_*.ok") -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    $al = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Only {1} -Workers {2}' -f $ps1.FullName, $cut, $w
    if ($job.samples) { $al += " -Samples {0}" -f [int]$job.samples }
    $t0 = Get-Date
    $pr = Start-Process -FilePath "powershell.exe" -ArgumentList $al -WindowStyle Minimized -PassThru
    $new = @()
    while (((Get-Date) - $t0).TotalSeconds -lt $limit) {
      Start-Sleep -Seconds 5
      $new = @(Get-ChildItem $done -Filter ($cut + "_*.ok") -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Name } | Sort-Object LastWriteTime)
      if ($new.Count -ge $w) { break }
      if ($pr.HasExited) { break }
    }
    Start-Sleep -Seconds 15          # できた mp4 をドライブへコピーし終えるのを待ってから止める
    Kill-Kit $kitdir
    Start-Sleep -Seconds 8
    if ($new.Count -ge $w) {
      # k 番目の描き手は 20 秒ずつ遅れて始まる。1 本あたりの時間の平均から、1 分あたりに描ける本数を出す
      $sum = 0.0
      for ($k = 0; $k -lt $w; $k++) { $sum += [Math]::Max(30.0, ($new[$k].LastWriteTime - $t0).TotalSeconds - 20.0 * $k) }
      $mean = $sum / $w
      $rate["$w"] = [Math]::Round($w * 60.0 / $mean, 3)
      Note ("  {0} 本同時：1 本（100 コマ）に平均 {1} 秒 → 1 分に {2} 本" -f $w, [int]$mean, $rate["$w"])
      if ($w -eq 1) { $limit = [Math]::Max(1200, [int]($mean * 4)) }
    } else {
      $rate["$w"] = 0
      Note ("  {0} 本同時：描ききれませんでした（遅すぎるか、グラフィックボードのメモリ不足）" -f $w)
    }
  }
  $bw = 0; $br = 0.0
  foreach ($w in 1, 2, 3, 4) { if ([double]$rate["$w"] -gt $br * 1.03) { $bw = $w; $br = [double]$rate["$w"] } }
  if ($bw -eq 0) { Note "同時本数を測れませんでした。既定の本数で描きます"; return }
  Write-Json $wf ([ordered]@{ workers = $bw; rate = $rate; cut = $cut; job = $job.id; at = (Get-Date).ToString("s") })
  Copy-Item $wf (Join-Path $stat "pc_workers.json") -Force -ErrorAction SilentlyContinue
  Note ("同時本数は {0} 本に決めました（これからの描画に使います）" -f $bw)
  Status-Push ("同時本数：{0}" -f $bw)
}
function Best-Workers {
  try { $j = Get-Content (Join-Path $root "pc_workers.json") -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json; return [int]$j.workers } catch { return 0 }
}
function Get-Kit($job) {
  # 一式（zip）は、GitHub の枝 pc-kit/<名前> に 1 つだけ入っている。取ってきて C:\marurobo に広げる
  New-Item -ItemType Directory -Force -Path $kits | Out-Null
  $o = G -C $repo fetch -q origin $job.kit_branch
  if ($LASTEXITCODE -ne 0) { return ("一式の枝 {0} を取れません：{1}" -f $job.kit_branch, ($o -join " ")) }
  $zip = Join-Path $kits $job.zip
  if (Test-Path $zip) { Remove-Item $zip -Force }
  # 枝の中身（zip 1 つ）を、包みの zip として書き出してから開く（画面への出力を経由しないので、中身が壊れない）
  $wrap = Join-Path $kits "_wrap.zip"
  if (Test-Path $wrap) { Remove-Item $wrap -Force }
  $o = G -C $repo archive --format=zip -o $wrap FETCH_HEAD
  if (-not (Test-Path $wrap)) { return ("一式を枝から取り出せません：{0}" -f ($o -join " ")) }
  try { Expand-Archive -Path $wrap -DestinationPath $kits -Force -ErrorAction Stop } catch { return ("一式の包みを開けません：{0}" -f $_.Exception.Message) }
  Remove-Item $wrap -Force -ErrorAction SilentlyContinue
  if (-not (Test-Path $zip) -or (Get-Item $zip).Length -lt 1000) { return ("一式 {0} が枝に見つかりません" -f $job.zip) }
  try { Expand-Archive -Path $zip -DestinationPath $root -Force -ErrorAction Stop } catch { return ("一式を広げられません：{0}" -f $_.Exception.Message) }
  return ""
}
# 依頼に fresh があるとき：同じ出力フォルダに残っている前の絵を捨ててから描く（残っていると「できている」と見なされて描き直されない）
#   --only があればそのカットの分だけ、無ければ出力フォルダごと
function Clear-Old($job, $ps1) {
  $txt = Get-Content $ps1.FullName -Raw -Encoding UTF8
  $mo = [regex]::Match($txt, '\$out = Join-Path \$root "(render_[A-Za-z0-9_.-]+)"')
  if (-not $mo.Success) { Note "描き直しの指定がありますが、出力フォルダの名前が手順から読めないので、捨てずに進みます"; return }
  $od = Join-Path $root $mo.Groups[1].Value
  if (-not (Test-Path $od)) { return }
  if ($job.only) {
    $n = 0
    foreach ($c in ("$($job.only)".Split(","))) {
      $c = $c.Trim()
      if (-not $c) { continue }
      $fs = @(Get-ChildItem $od -File -Filter ($c + "_*") -ErrorAction SilentlyContinue | Where-Object { $_.Name -match ("^" + [regex]::Escape($c) + "_(\d{4}-\d{4}\.mp4|log\.json)$") })
      $fs += @(Get-ChildItem (Join-Path $od "_done") -File -Filter ($c + "_*") -ErrorAction SilentlyContinue | Where-Object { $_.Name -match ("^" + [regex]::Escape($c) + "_\d{4}-\d{4}\.(ok|lock)$") })
      foreach ($f in $fs) { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue; $n++ }
    }
    Note ("描き直し：前の絵を {0} 個捨てました（{1}）" -f $n, $job.only)
  } else {
    Remove-Item $od -Recurse -Force -ErrorAction SilentlyContinue
    Note ("描き直し：前の出力フォルダ {0} を捨てました" -f $od)
  }
}
# 係のセッションからの合図：pc_render/control.json の restart_token が、前に見た値と変わっていたら $true（見た値は PC に覚える）
function Restart-Asked {
  try {
    $cf = Join-Path $repo "pc_render\control.json"
    if (-not (Test-Path $cf)) { return $false }
    $tok = "$((Get-Content $cf -Raw -Encoding UTF8 | ConvertFrom-Json).restart_token)"
    if (-not $tok) { return $false }
    $sf = Join-Path $root "pc_control_seen.txt"
    $seen = ""
    if (Test-Path $sf) { $seen = (Get-Content $sf -Raw -ErrorAction SilentlyContinue).Trim() }
    if ($tok -eq $seen) { return $false }
    Set-Content -Path $sf -Value $tok -Encoding ASCII
    return $true
  } catch { return $false }
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
  $preempt = $false
  $cancel = $false
  if ($err) { Note $err; [void]$tail.Add($err) }
  else {
    $kitdir = Split-Path -Parent (Split-Path -Parent $ps1.FullName)
    $freshMark = Join-Path $kits ("fresh_{0}.done" -f $job.id)
    if ($job.fresh -and -not (Test-Path $freshMark)) {
      try { Clear-Old $job $ps1; New-Item -ItemType File -Force -Path $freshMark | Out-Null } catch { Note ("前の絵を捨てる途中で止まりました：{0}" -f $_.Exception.Message) }
    }
    if ($job.kind -ne "fix" -and -not $job.workers) {
      try { Measure-Workers $job $ps1 } catch { Note ("同時本数を測る途中で止まりました（{0}）。既定の本数で描きます" -f $_.Exception.Message); Kill-Kit $kitdir }
    }
    $lastCheck = Get-Date
    $lastProg = Get-Date
    $prog = ""
    for ($try = 1; $try -le 2 -and $state -ne "done" -and -not $preempt -and -not $cancel; $try++) {
      $a = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ps1.FullName)
      if ($job.only) { $a += @("-Only", "$($job.only)") }
      $w = 0
      if ($job.workers) { $w = [int]$job.workers } else { $w = Best-Workers }
      if ($w -gt 0) { $a += @("-Workers", "$w") }
      if ($job.samples) { $a += @("-Samples", "$([int]$job.samples)") }
      Note ("描きます：{0}（{1} 回目）" -f $job.id, $try)
      & powershell.exe @a 2>&1 | ForEach-Object {
        $line = "$_"
        Write-Host $line
        [void]$tail.Add($line)
        if ($tail.Count -gt 40) { $tail.RemoveAt(0) }
        if ($line -match "ぜんぶ終わりました") { $state = "done" }
        # 進み具合（「残り N 本、およそ …」の行）を、30 分ごとに印の枝へ（係のセッションが、次に見に来る時間を決めるのに使う）
        if ($line -match "残り") { $prog = $line }
        if ($prog -and ((Get-Date) - $lastProg).TotalMinutes -ge 30) {
          $lastProg = Get-Date
          try { Heartbeat "描いています" $job @() $prog } catch { }
        }
        # 全部描きの途中に短い直しが来たら、いったん止めて直しを先に描く（できている所は残り、あとで続きから）
        #   割り込むのは小さな直し（3000 コマまで・およそ 2 時間半）だけ。大きな直しは、いまの 1 件が終わってから先頭で描く
        if (-not $preempt -and -not $cancel -and ((Get-Date) - $lastCheck).TotalSeconds -ge 180) {
          $lastCheck = Get-Date
          try {
            if (Pull-Repo) {
              if (-not (Test-Path (Join-Path $repo ("pc_render\queue\{0}.json" -f $job.id)))) {
                # 依頼票が消された＝取り消し。描いている途中でも止める
                $cancel = $true
                Note ("依頼 {0} が取り消されたので、止めます" -f $job.id)
                Kill-Kit $kitdir
              } elseif (Restart-Asked) {
                # 係からの合図：いったん止める（できている所は残る）。回る所に戻ると、新しい描画係に入れ替わって続きから描く
                $preempt = $true
                Note ("係からの合図で、{0} をいったん止めます（新しい描画係で続きから描きます）" -f $job.id)
                Kill-Kit $kitdir
              } elseif ($job.kind -ne "fix") {
                $q2 = Read-Queue
                $small = $false
                if ($q2.Count -gt 0 -and $q2[0].kind -eq "fix") { $small = (-not $q2[0].frames) -or ([int]$q2[0].frames -le 3000) }
                if ($small) {
                  $preempt = $true
                  Note ("短い直し（{0}）が来たので、{1} をいったん止めて、直しを先に描きます" -f $q2[0].id, $job.id)
                  Kill-Kit $kitdir
                }
              }
            }
          } catch { }
        }
      }
    }
  }
  if ($cancel) {
    Write-Json (Join-Path $stat ("done\{0}.json" -f $job.id)) ([ordered]@{ id = $job.id; state = "canceled"; finished = (Get-Date).ToString("s"); minutes = [int]((Get-Date) - $t0).TotalMinutes; tail = @() })
    Status-Push ("{0}：canceled" -f $job.id)
    return
  }
  if ($preempt) { Start-Sleep -Seconds 5; return }
  $min = [int]((Get-Date) - $t0).TotalMinutes
  Write-Json (Join-Path $stat ("done\{0}.json" -f $job.id)) ([ordered]@{ id = $job.id; state = $state; finished = (Get-Date).ToString("s"); minutes = $min; tail = @($tail | Select-Object -Last 12) })
  if ($state -eq "done") { Note ("終わりました：{0}（{1} 分）" -f $job.id, $min) }
  else { Note ("そろいませんでした：{0}（{1} 分）。印に記録して、次へ進みます" -f $job.id, $min) }
  Status-Push ("{0}：{1}" -f $job.id, $state)
}

# ---------------------------------------------------------------- 回し続ける
Note "描画係をはじめます（この窓は置いたままにしてください。最小化して大丈夫です）"
$me = (Get-FileHash $PSCommandPath -Algorithm SHA256).Hash
[void](Restart-Asked)
$lastBeat = Get-Date "2000-01-01"
$badHash = ""
$waitSaid = $false
while ($true) {
  if ((Status-Ready) -and (Pull-Repo)) {
    $newHash = (Get-FileHash (Join-Path $repo "pc_render\agent.ps1") -Algorithm SHA256).Hash
    if ($newHash -ne $me -and $newHash -ne $badHash) {
      # 入れ替える前に、新しい描画係の書き方を点検する。誤りがあれば入れ替えず、今のまま動き続ける
      $perr = $null; $ptok = $null
      [void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo "pc_render\agent.ps1"), [ref]$ptok, [ref]$perr)
      if ($perr -and $perr.Count -gt 0) {
        $badHash = $newHash
        Note ("新しい描画係に書き方の誤りがあるので、入れ替えません（今のまま動きます）：{0}" -f $perr[0].ToString())
        Write-Json (Join-Path $stat "agent_error.json") ([ordered]@{ at = (Get-Date).ToString("s"); error = @($perr | Select-Object -First 5 | ForEach-Object { "{0}（{1} 行目）" -f $_.Message, $_.Extent.StartLineNumber }) })
        Status-Push "描画係：新しい版に誤り"
      } else {
        Note "描画係が新しくなったので、入れ替えて立ち上げ直します"
        $mutex.ReleaseMutex(); $mutex.Dispose()
        Start-Process -FilePath "powershell.exe" -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $repo "pc_render\agent.ps1"))
        exit 0
      }
    }
    [void](G -C $stat pull -q --rebase origin $sbranch)
    $q = Read-Queue
    if ($q.Count -gt 0) {
      $job = $q[0]
      $rest = @($q | Select-Object -Skip 1 | ForEach-Object { $_.id })
      $ob = Other-Blender
      if ($ob -gt 0) {
        if (-not $waitSaid) { Note ("手で始めた描画（Blender {0} 本）が動いています。終わるのを待ちます（止めません）" -f $ob); Heartbeat "手で始めた描画が終わるのを待っています" $null @($q | ForEach-Object { $_.id }); $waitSaid = $true }
        Start-Sleep -Seconds $Every
        continue
      }
      $waitSaid = $false
      Heartbeat "描いています" $job $rest
      Run-Job $job
      $lastBeat = Get-Date "2000-01-01"
      continue
    }
  }
  if (((Get-Date) - $lastBeat).TotalMinutes -ge 60) { Heartbeat "待っています" $null @(); $lastBeat = Get-Date }
  Start-Sleep -Seconds $Every
}
