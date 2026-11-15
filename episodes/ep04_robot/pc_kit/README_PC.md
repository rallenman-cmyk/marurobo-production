# まるロボ 4本目「私はロボットではありません」　PC の本番描画

3D の 40 カット（合わせて 15,356 コマ・約 10 分40秒）を、1920×1080 で描きます。字幕・札・音・2D の場面は、こちら（クラウド）で重ねるので、描かなくて大丈夫です。

## やること（2つだけ）
1. 届いた `marurobo_ep04.zip` を右クリック →「すべて展開」→ 展開先を `C:\marurobo` にする。`C:\marurobo\marurobo_ep04` ができれば OK。
2. PowerShell を開いて、次の 1 行を貼って Enter。あとは放っておくだけ（Blender 4.3 が入っていなければ、自動で持ち運び版を落として使います）：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep04.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "marurobo_ep04.zip を C:\marurobo に展開し直してください" }
```

3. 100 コマずつ mp4 で、3 本同時に描きます（グラフィックボードを使います）。最初の何本かが終わると、残りの時間の見込みが出ます。
   - 描き手ごとに小さな窓（「まるロボ 描き手 1〜3」、最小化）が開きます。進み具合は最初の窓と `C:\marurobo\render_log_ep04.txt` に出ます。
   - 止めるときは、最初の窓と描き手の窓をぜんぶ閉じる。同じ 1 行をもう一度走らせれば、できている所は飛ばして続きから描きます。
   - ほかの回の描画が動いていたら、それが終わるのを待ってから描き始めます。
4. 終わると `C:\marurobo\marurobo_render\ep04_v13` にまとまり、Google ドライブ（パソコン版）があれば `marurobo_render\ep04_v13` へ自動でコピーされます。終わったらチャットで知らせてください。
5. 止まった所があれば、`render_log_ep04.txt` と、そこに書いてある `blender_log*.txt` の最後の 20 行をチャットに貼ってください。

## 最初に 1 カットだけ試すとき（おすすめ）
まるロボがマウスを押す場面（s04・約 27 秒）だけ描いて、きれいさと時間を確かめる：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep04.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName -Only s04 } else { "見つかりません" }
```

`C:\marurobo\render_ep04_v13\s04_0000-0099.mp4` を開いて見る。よければ、上の「やること」の 2 の 1 行で残りを描く（s04 は飛ばされます）。

## 付けられるもの（1 行の最後に足す）
- ` -Workers 2`：同時に描く本数（1〜4。既定 3）。パソコンが重いときは減らす。
- ` -Only s04,c_s01`：一部のカットだけ描く。部屋の場面は c_s01〜c_s23a、図の場面は s06 s07 s08x s09 s10 s15 s19 s20 s22。
- ` -Samples 48`：描く細かさ（既定 24。光の跳ね返りを減らす速い設定と合わせて描く）。大きいほどざらつきが減るが、時間がかかる。

## 中身
- `pc_kit/run_pc_render_ep04.ps1`：描く順番と、100 コマずつの mp4 にする手順（5本目と同じ作り）。
- `episodes/ep04_robot/anim/`：部屋の場面（`clip_anim.py`・`clips.json`）と 0:44 のマウスの場面（`scenes.py`）。`common.py` に、グラフィックボードと mp4 の設定。
- `episodes/ep04_robot/look/`：図の場面（`<名前>_3d.py`・`kit3d.py`）。
- `episodes/ep04_robot/storyboard/`：部屋の舞台（`board.py`・`rich.py`）。`episodes/ep03_ad/storyboard/`：まるロボ・門番・材質・光の部品（3本目と同じ）。
- `episodes/ep04_robot/voice/`・`animatic/`：声と字幕の時刻（動きを声に合わせるため）。
- `tex/`：絵（字なし）。`scr/`：パソコンの画面のコマ。
