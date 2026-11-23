# まるロボ 9本目「エスカレーターの段は、どこへ消える？」　PC の本番描画

3D の 125 カット（合わせて 26,363 コマ・約 16 分半）を、1920×1080 で描きます。字幕・札・音は、こちら（クラウド）で重ねるので、描かなくて大丈夫です。

## やること（2つだけ）
1. 届いた `marurobo_ep09.zip` を右クリック →「すべて展開」→ 展開先を `C:\marurobo` にする。`C:\marurobo\marurobo_ep09` ができれば OK。
2. PowerShell を開いて、次の 1 行を貼って Enter。あとは放っておくだけ（Blender 4.3 が入っていなければ、自動で持ち運び版を落として使います）：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep09.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "marurobo_ep09.zip を C:\marurobo に展開し直してください" }
```

3. 100 コマずつ mp4 で、3 本同時に描きます（グラフィックボードを使います）。最初の何本かが終わると、残りの時間の見込みが出ます。
   - 描き手ごとに小さな窓（「まるロボ 描き手 1〜3」、最小化）が開きます。進み具合は最初の窓と `C:\marurobo\render_log_ep09.txt` に出ます。
   - 止めるときは、最初の窓と描き手の窓をぜんぶ閉じる。同じ 1 行をもう一度走らせれば、できている所は飛ばして続きから描きます。
   - ほかの回の描画が動いていたら、それが終わるのを待ってから描き始めます。
4. 終わると `C:\marurobo\marurobo_render\ep09_v3` にまとまり、Google ドライブ（パソコン版）があれば `marurobo_render\ep09_v3` へ自動でコピーされます。終わったらチャットで知らせてください。
5. 止まった所があれば、`render_log_ep09.txt` と、そこに書いてある `blender_log*.txt` の最後の 20 行をチャットに貼ってください。

## 最初に 1 カットだけ試すとき（おすすめ）
段が歯車のまわりをくるっとさかさまになる場面（B12b）だけ描いて、きれいさと時間を確かめる：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render_ep09.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName -Only B12b } else { "見つかりません" }
```

`C:\marurobo\render_ep09_v3\B12b_0000-0099.mp4` を開いて見る。よければ、上の「やること」の 2 の 1 行で残りを描く（B12b は飛ばされます）。

## 付けられるもの（1 行の最後に足す）
- ` -Workers 2`：同時に描く本数（1〜4。既定 3）。パソコンが重いときは減らす。
- ` -Only B12b,I35`：一部のカットだけ描く。カットの名前は `episodes/ep09_escalator/anim/clips.json` の A01〜A40b。
- ` -Samples 48`：描く細かさ（既定 24。光の跳ね返りを減らす速い設定と合わせて描く）。大きいほどざらつきが減るが、時間がかかる。

## 中身
- `pc_kit/run_pc_render_ep09.ps1`：描く順番と、100 コマずつの mp4 にする手順（7本目と同じ作り）。
- `episodes/ep09_escalator/anim/`：場面を組む道具（`scenes.py`・`kit9.py`・`esc_geom.py`＝エスカレーターの形と動き・`maru9.py`＝まるロボの動き）。`episodes/ep06_haizen/anim/` の `kit.py`・`core.py`・`plan.py`・`pc_out.py`（グラフィックボードと mp4 の設定）も使う。
- `episodes/ep03_ad/storyboard/scenes.py`：まるロボ・材質・光の部品（3本目と同じ）。
- `episodes/ep09_escalator/voice/`：声の時刻（動きを声に合わせるため）。
