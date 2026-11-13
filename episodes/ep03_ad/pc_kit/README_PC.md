# まるロボ 3本目「さっき話した物が、なぜ広告に出る？」　PC の本番描画（2026-11-13）

3D の 21 場面（合わせて 19,564 コマ・約 13 分半）を、1920×1080 で描きます。2D の場面（S03・S09・S20）は、こちら（クラウド）で作るので描かなくて大丈夫です。

## やること
1. 届いた `marurobo_ep03.zip` を右クリック →「すべて展開」→ 展開先を `C:\marurobo` にする。`C:\marurobo\marurobo_ep03` ができれば OK（前の回のフォルダはそのままで大丈夫）。
2. PowerShell を開いて、次の 1 行を貼って Enter：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep03.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_ep03.zip を C:\marurobo に展開し直してください" }
```

3. 100 コマずつ mp4 で、3 本同時に描きます（グラフィックボードを使います）。最初の何本かが終わると、残りの時間の見込みが出ます。
   - 描き手ごとに小さな窓（「まるロボ 描き手 1〜3」、最小化）が開きます。進み具合は最初の窓と `C:\marurobo\render_log_ep03.txt` に出ます。
   - 止めるときは、最初の窓と描き手の窓をぜんぶ閉じる。同じ 1 行をもう一度走らせれば、できている所は飛ばして続きから描きます。
   - 描いているあいだ PC はスリープしません（画面は消えてよい。ノート PC は電源につないで、ふたは閉じない）。
4. 終わると `C:\marurobo\marurobo_render\ep03` にまとまり、Google ドライブ（パソコン版）があれば `marurobo_render\ep03` へ自動でコピーされます。終わったらチャットで知らせてください。
5. 止まった所があれば、`render_log_ep03.txt` と、そこに書いてある `blender_log*.txt` の最後の 20 行をチャットに貼ってください。

## 最初に 1 場面だけ試すとき（おすすめ）
最初の場面（7 秒・2 本）だけ描いて、きれいさと時間を確かめる：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep03.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName -Only s00 } else { "見つかりません" }
```

`C:\marurobo\render_ep03\s00_0000-0099.mp4` を開いて見る。よければ、上の「やること」の 2 の 1 行で残りを描く（s00 は飛ばされます）。

## 付けられるもの（1 行の最後に足す）
- ` -Workers 2`：同時に描く本数（1〜4。既定 3）。パソコンが重いときは減らす。
- ` -Only gate,phone`：一部の場面だけ描く。場面の名前：s00 s01 s02 s04 s05 s06a s06b gate phone s10 s11 s12 s13 s14 s15 s16 s17 s18 s19 s21 s22
- ` -Samples 64`：描く細かさ（既定 48）。大きいほどざらつきが減るが、時間がかかる。

## 中身
- `pc_kit/run_pc_render_ep03.ps1`：描く順番と、100 コマずつの mp4 にする手順。
- `episodes/ep03_ad/anim/`：場面を組む道具（`scenes_all.py`・`s07s08_gate.py`・`common.py`・`pc_out.py`＝グラフィックボードと mp4 の設定）。
- `episodes/ep03_ad/storyboard/`：部品（人・番犬・門・スマホなど）と、スマホの画面の絵。
- `episodes/ep03_ad/voice/`：声の時刻（動きを声に合わせるため）。
- `episodes/ep01_earphone/stage/human/`：人の形を作る道具（1本目と同じ）。
