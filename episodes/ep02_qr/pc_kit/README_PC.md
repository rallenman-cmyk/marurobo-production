# まるロボ PC用の道具一式（本番描画の手順）

中身：⓪いまやること（QR回の1〜5章・台本 v2.0）　①バッファの章の30秒サンプル　②冒頭22秒（電車）　③まるロボの動きの見本リール　④第3章　⑤第1・2章　⑥共通の部品（kit）　⑦台本の直し（script）　⑧第4章のペアリング v8　⑨第5章（2D）　⑩第6〜8章（確認中）。どれも同じフォルダの置き方で動く。

# ⓪ いまやること（2026-11-12・v23）：1章 → 5章と冒頭を、確定した台本 v2.0 の時刻で描く

（v23：v21 に 5章と冒頭の描き直しを足した。何も付けずに 1 行を貼ると、1章 → 5章 → 冒頭の順に描きます。v21・v22 で描いている途中なら、窓をぜんぶ閉じて止め、v23 に入れ替えて同じ 1 行で。描けた所は飛ばして続きから描きます）

1. 新しい `marurobo_tools.zip`（ドライブの `marurobo_tools_v23.zip`）を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で、いつもの 1 行を貼って Enter（下の v19 の手順と同じ）。
3. 1章（70 本）→ 2章（71 本）→ 3章（28 本）→ 4章（95 本）→ 5章（22 本）→ 冒頭の描き直し（21 本）。終わると `marurobo_render` の `qrc1`〜`qrc5`・`qrop4` にまとまり、ドライブへコピーされます。
4. 5章の中身：26 個の箱が並んだ中の世界で、場面ごとに「壊れた箱」が灰色になる。一歩踏み込む（10 個）／インクのしずくが 12 か所に落ちる（12 個）／真ん中に乗る（6 個）／
   真ん中にロゴ（透けて 8 個）／ロゴ＋しずく 1 つ（9 個目）。数は 2D の札で出すので、3D の中に字はありません。
5. 冒頭（qrop4）：前に描いた冒頭は台本 v1.2 の時刻で、v2.0 の声と最大 7 秒ずれるので、v2.0 の時刻で描き直します。動きは同じ。スマホの画面の「HELLO」の字は 3D から外し、組み立てで札にします。
6. 結び（まとめ）は、冒頭・1章・3章・4章・5章で描いた絵の使い回しなので、PC で新しく描くものはありません。

# （前の版）⓪ いまやること（2026-11-12・v21）：1章 → 2章 → 3章 → 4章を、確定した台本 v2.0 の時刻で描く

（v21：v20 に 4章を足した。何も付けずに 1 行を貼ると、1章 → 4章の順に描きます。前の版で描き始めていたら、窓をぜんぶ閉じて止め、v21 に入れ替えて同じ 1 行で。描けた所は飛ばして続きから描きます）

1. 新しい `marurobo_tools.zip`（ドライブの `marurobo_tools_v21.zip`）を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で、いつもの 1 行を貼って Enter（下の v19 の手順と同じ）。
3. 1章（70 本）→ 2章（71 本）→ 3章（28 本）→ 4章（95 本：工場 8・数字の空間 63・中の世界 24）。終わると `marurobo_render` の `qrc1`〜`qrc4` にまとまり、ドライブへコピーされます。
4. 4章の中身：工場の作業台で伝票に油が落ちる／青い箱「2・5・3」→ 布で隠す → 汚れで 7 に見える → 台が光って 5 に戻る／0〜255 の輪・たくさんの予備から線／
   予備が光る・箱の 0 と 1・白いマスに汚れ・体で隠れた所に赤い輪・壊れた 6 個に予備から光の線が集まって直る。3D の中の字は、青い箱の数字だけ（箱の顔として大きく）。

# （前の版）⓪ いまやること（2026-11-12・v20）：1章 → 2章 → 3章を、確定した台本 v2.0 の時刻で描く

（v20：v19 に 3章を足した。何も付けずに 1 行を貼ると、1章 → 2章 → 3章の順に描きます。前の版で描き始めていたら、窓をぜんぶ閉じて止め、v20 に入れ替えて同じ 1 行で。描けた所は飛ばして続きから描きます）

1. 新しい `marurobo_tools.zip`（ドライブの `marurobo_tools_v20.zip`）を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で、いつもの 1 行を貼って Enter（下の v19 の手順と同じ）。
3. 1章（70 本）→ 2章（71 本）→ 3章（28 本）。終わると `marurobo_render` の `qrc1`・`qrc2`・`qrc3` にまとまり、ドライブへコピーされます。
4. 3章の中身：右下の角からジグザグの道 → 通った 8 マスが箱に → 早回しで 9 個を右の白いフチに並べる → ふたが開いて 0 と 1 の板が 8 枚浮かぶ → 読む（空に 2D の図）→ 予備の 17 個が光る。3D の中に字はありません。

# （前の版）⓪ いまやること（2026-11-12・v19）：1章 → 2章を、確定した台本 v2.0 の時刻で描く

（v19：v18 に 2章を足した。何も付けずに 1 行を貼ると、1章を描き終えたら続けて 2章を描きます。v18 で 1章を描き始めていたら、窓をぜんぶ閉じて止め、v19 に入れ替えて同じ 1 行で。描けた所は飛ばして続きから描きます）

1. 新しい `marurobo_tools.zip`（ドライブの `marurobo_tools_v19.zip`）を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で次の 1 行を貼って Enter：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. 1章（70 本）→ 2章（中の世界 55 本・卓上 16 本＝71 本）を、3 本同時に 100 コマずつ描きます。2章は 3D の場面だけを描きます（2D の図の場面は、こちらの組み立てで重ねるので描きません）。
4. 終わると `C:\marurobo\marurobo_render\qrc1`・`qrc2` にまとまり、ドライブへコピーされます。止まったら `render_log.txt` と、`render_qrc1` か `render_qrc2` の `blender_log*.txt` の最後の 20 行を送ってください。
5. 2章の中身：目の光でなぞるとマスが浮いて黒白の帯になる／大地ごと回って、元の向きに戻りながら L 字／黒白交互の列を跳ぶ／柄を外す／紫の読み方の帯 2 本／白いフチ／小さな箱で目印を隠すと、スマホは枠を出したまま読めない。3D の中に字はありません。

# （済み）⓪ いまやること（2026-11-12・v18）：1章を、確定した台本 v2.0 の時刻で描く

（v18：台本 v2.0 で 1章に文が増え、動きの間も合わせ直したので、1章を新しい名前で全部描きます。冒頭（qrop）は描き直し不要）

1. 新しい `marurobo_tools.zip` を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で次の 1 行を貼って Enter（何も付けなければ 1章だけ描きます）：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. 卓上（qrc1t2_・3 本）→ 中の世界（qrc1w5_・64 本）→ スマホで探す（qrc1s2_・3 本）＝ 70 本を、3 本同時に 100 コマずつ描きます。あとは放っておいて大丈夫です（PC はスリープしないように。画面は消えてよい）。
4. 終わると `C:\marurobo\marurobo_render\qrc1` にまとまり、Google ドライブの `marurobo_render` へコピーされます（こちらで受け取ります）。止まったら `render_log.txt` と `render_qrc1\blender_log*.txt` の最後の 20 行を送ってください。
5. v18 で変わったこと：3D の中の字（「21」「HELLO」「予備の数字」）はなし（組み立てで 2D の大きな札を重ねる）。まるロボは、v2.0 で足した文の間に「考える」「うなずく」などの待機の動きをします。

# ⓪ （済み）（2026-11-10 夜・v17）：冒頭が終わったら、1章を描く（台本 v1.4）

（v17：v16 から、1章の中の世界の名前を `qrc1w4_`（248〜5324 コマ）に変えた。手順は下の v16 と同じ。v16 で 1章を描き始めていたら、止めて v17 に入れ替えてから同じ 1 行で）


（この一式は v16。v15 から：動画レビューのコメントで 1章の中の世界の動きが変わった（最後の 2 個の箱をまるロボがたたむ・目の光で箱を開ける・数字の札など）。1章の中の世界は新しい名前 `qrc1w3_`（248〜5271 コマ）で描き、「スマホで探す」場面（`qrc1s_`・222 コマ）を足した。冒頭（`qrop`）と 1章の卓上（`qrc1t_`）は v15 と同じ）

1. 冒頭（`-Only qrop`）を v15 で描いている途中なら、そのまま終わるまで待つ（v16 にしても冒頭は同じなので、止めて入れ替えても大丈夫。描けた所は飛ばします）。
2. 新しい `marurobo_tools.zip` を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_*`・`render_done` はそのまま）。
3. PowerShell で次の 1 行を貼って Enter（1章だけ描く）：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName -Only qrc1 } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

4. 卓上 3 本・中の世界 51 本・スマホで探す 3 本＝57 本。終わると `marurobo_render\qrc1` にまとまり、ドライブへコピーされます。

# （v15）2026-11-10 夜：QRコード回の冒頭＋1章を描く（台本 v1.2）

（この一式は v15。v14 から：台本 v1.2 で冒頭に 1 文、1章に 1 文足したので時刻が変わった。
- 冒頭：1〜700 コマは前と同じ絵なので、描けている `qrop2_0001〜0700` はそのまま使う。701 コマから先は `qrop3_` として描き直す（v13・v14 で描いた `qrop2_0701` 以降は使わない）。
- 1章：卓上（`qrc1t_`）は前と同じ。中の世界は `qrc1w2_`（248〜4520 コマ・43 本）として描く（v14 で描いた `qrc1w_` は使わない）。
- 描いている途中なら、窓をぜんぶ閉じて止めてから v15 に入れ替えて、いつもの 1 行で続きから描けます）

（以下は v14 のときの説明。コマ数だけ上のとおりに変わった。v14。v13 から：1章（`qrc1`）を足した。冒頭（`qrop`）をまだ描いていなければ、続けて 1章も描きます。冒頭が済んでいれば、冒頭は飛ばして 1章だけ描きます。v13 を描いている途中なら、窓をぜんぶ閉じて止めてから入れ替えてください。描けた所は `render_done` の印で飛ばすので、やり直しにはなりません）

1. 新しい `marurobo_tools.zip` を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`render_qrop`・`render_done`・`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で、いつもの 1 行を貼って Enter：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. 1章は 2 つに分けて描きます（3 本同時・100 コマずつ）。
   - 卓上（1〜247 コマ・3 本）：まるロボが画面に飛び込むまで。冒頭と同じく、まず「スマホのカメラの絵」（今回は画面いっぱいまで寄るので 1080×2240）を描いてから本番を描きます。
   - 中の世界（248〜4520 コマ・43 本。v15 では qrc1w2_）：21×21 の大地、箱をたたむ・運ぶ・のぞく・開ける、影、青と橙、元に戻す。1 本ごとに場面を組むのに 1〜2 分かかります。
4. 終わると `C:\marurobo\marurobo_render\qrc1`（mp4 46 本＋記録 2 つ）にまとまり、Google ドライブの `marurobo_render` へコピーされます（こちらで受け取って、声・字幕・効果音・URL の図をつけます）。止まったら `render_log.txt` と `render_qrc1\blender_log*.txt` の最後の 20 行を送ってください。
5. 1章だけ描くとき：最後に ` -Only qrc1`。

| ファイル（qr フォルダ） | 役割 |
|---|---|
| qr_c1_table.py | 1章の卓上：冒頭と同じ机・紙・スマホ。画面に飛び込む・波紋・カメラが画面の中へ |
| qr_c1_world.py | 1章の中の世界：大地（qr_world.py）・縦横の線・目の光・箱の板とふた・光・HELLO・影・カメラ 21 カット |
| c1_timeline.py | 1章の時刻の決まり（声の置き場所から） |
| c1_plan.py | 1章のまるロボの予定（卓上と中の世界）。動きの山が声に合うように前もって長さを測って並べる |
| qr_world.py・qr_assets.json | 巨大な QR の大地と、マス・箱・読む順のデータ |

# （v13）2026-11-10：QRコードの冒頭（0:00〜1:14.8）を描く

（この一式は v13。v12 から：冒頭のナレーションを見せ方に合わせて直したので、時刻が変わった。v12 で描いた分（qrop_）は使わず、qrop2_ として全部描き直します。v12 を描いている途中なら、窓をぜんぶ閉じて止めてから v13 に入れ替えてください）

1. 新しい `marurobo_tools.zip` を `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`bluetooth_handoff_restored` はそのまま。まるロボは story.blend の「Maru」、字は assets の japanese.ttc を使います）。
2. PowerShell で、いつもの 1 行を貼って Enter：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. 1795 コマを 100 コマずつ 18 本、3 本同時に描きます。1 本ごとに、まず「スマホのカメラから見た絵」（540×1120）を描き、それをスマホの画面に貼ってから本番（1920×1080）を描きます。
4. 終わると `C:\marurobo\marurobo_render\qrop` にまとまり、Google ドライブの `marurobo_render` へコピーされます（こちらで受け取ります）。止まったら `render_log.txt` と `render_qrop\blender_log*.txt` の最後の 20 行を送ってください。

| ファイル（qr フォルダ） | 役割 |
|---|---|
| qr_op_stage.py | 舞台（机・QR の紙・スマホと台・見ている範囲の線）、カメラ 10 カット、スマホの画面の表示、2 段の描画 |
| op_timeline.py | 時刻の決まり（声・スマホの結果・線・まるロボの位置） |
| op_plan.py | まるロボの動きの予定（marumotion）。足音の時刻もここから |
| qr_paper.png | QR「HELLO」（V1-H）の紙 |

# （済み）2026-11-09 夜：まとめの電車の場面・第7章（まるロボの版）・第8章の塔（まるロボの版）を描く

（この一式は v11。v10 から：冒頭の電車の描き直し（op）を足した。手順 1〜3 は v10 と同じ。v10 で描き始めていたら、そのまま続けて大丈夫です）

1. 新しい `marurobo_tools.zip` を、前と同じく `C:\marurobo` に展開する（前の `marurobo_tools` フォルダは先に消す。`bluetooth_handoff_restored` はそのまま）。
2. PowerShell で、いつもの 1 行を貼って Enter（何も付けなければ、この 3 つを描きます）：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. まとめ（4 本）→ 第7章（35 本）→ 第8章の塔（6 本）を、3 本同時に、100 コマずつ描きます。終わると `C:\marurobo\marurobo_render` の `sum`・`ch07r`・`ch08r` にまとまり、Google ドライブの `marurobo_render` へ自動でコピーされます（こちらで受け取ります）。
4. （冒頭のまるロボに OK を出したあと）続けてこの 1 行も貼って Enter。冒頭の 0:00〜0:33（800 コマ・8 本）だけ描き直します（15〜30 分）。`op` にまとまり、ドライブへコピーされます：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName -Only op } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

# （済み）2026-11-08 夜：第3章・第1〜2章・第4章 v8 の本番を、PC でまとめて描く

1. 置き方：`marurobo_assets.zip`（描くのに使う素材：story.blend・maru_opening.blend・フォント）と `marurobo_tools.zip`（この一式）を、どちらも右クリック →「すべて展開」→ 展開先を `C:\marurobo` にして展開する。`C:\marurobo` の中に `bluetooth_handoff_restored` と `marurobo_tools` ができれば OK（前の `marurobo_tools` があれば、先に消す）。Blender 4.3 は `C:\Program Files\Blender Foundation\Blender 4.3\` に（https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.msi）。
2. PowerShell を開いて、次の 1 行を貼って Enter：

```powershell
$f = Get-ChildItem C:\marurobo -Recurse -Filter run_pc_render.ps1 | Select-Object -First 1; if ($f) { powershell -ExecutionPolicy Bypass -File $f.FullName } else { "見つかりません：marurobo_tools.zip を展開し直してください" }
```

3. 第3章（舞台 13 本・電車 2 本）→ 第1・2章（20 本）→ 第4章（29 本）→ 第7章（35 本）→ 第8章の塔（6 本）→ 第6章（20 本）を、**3 本同時に**、100 コマずつ mp4 で描く（RAM 64GB・RTX 3050 8GB で、GPU にまだ余裕があるため）。できている章は飛ばす（2026-11-09：第3・1〜2・4章は済み）。
   - 描き手ごとに小さな窓（「まるロボ 描き手 1〜3」、最小化）が開く。進み具合は最初の窓と `C:\marurobo\render_log.txt` に出る。
   - 止めるときは、最初の窓と描き手の窓をぜんぶ閉じる。同じ行をもう一度走らせれば、できている所は飛ばして続きから描く。
   - 本数を変えるときは最後に ` -Workers 2`（1〜4）。一部だけ描くときは ` -Only ch04`（`ch03`・`ch0102`・`ch04` をカンマで区切る）。
   - 描いているあいだ PC はスリープしない（画面は消えてよい）。
4. 終わると、送るファイルだけが `C:\marurobo\marurobo_render`（`ch03`・`ch0102`・`ch04`）にまとまる。Google ドライブの `marurobo_render` フォルダ（こちらで作って、リンク共有・見るだけにしてある）に、この 3 つのフォルダをアップロードして、チャットで知らせる。Google ドライブ（パソコン版）が入っていれば、そろった章は自動でそこへコピーされる。
5. 止まった所があれば、`render_log.txt` と、そこに書いてある `blender_log*.txt` の最後の 20 行をチャットに貼る。

# ① 30秒サンプルをPCで本番描画する手順

## 必要なもの
- Blender 4.3.2（`C:\Program Files\Blender Foundation\Blender 4.3\` に入っている前提）
- Codexの15個のZIPを展開したフォルダ（`bluetooth_handoff_restored`）
- このフォルダ（`marurobo_tools`）

## フォルダの置き方（例）
```
C:\marurobo\
  bluetooth_handoff_restored\   ← Codexの15個のZIPを展開したもの
  marurobo_tools\               ← marurobo_tools.zip を展開したもの
```

## 手順
1. PowerShellを開く（スタートメニューで「PowerShell」と入力）
2. 下のコマンドを貼り付けて実行する。1行目のフォルダの場所だけ、自分の置き場所に合わせる
3. 終わるまで待つ（RTX 3050で30〜60分ほどの見込み。初回は実際の時間を記録する）
4. できた `C:\marurobo\render_buffer_1080\buffer_sample_0001-0720.mp4` をチャットに送る（音と字幕はこちらで付ける）

```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1"
& $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\buffer_sample.py" -- --mode anim --out "$root\render_buffer_1080" --res 1920 1080 --samples 64 --final --video --font "$src\assets\japanese.ttc"
```

## 中身
| ファイル | 役割 |
|---|---|
| buffer_sample.py | 舞台モデル2（貯蔵タワー）を組み、30秒の動き（物理の計算）を付けて描画する |
| build_stage.py | 舞台モデル1（巨大イヤホンの受付口）を組み、静止画を描く |
| make_audio.py | 動きの記録から効果音を合成し、曲と混ぜる |
| make_graphs.py | 動きの見える化グラフを描く |
| subs.ass | 30秒サンプルの字幕（仮） |

---

# ② 冒頭22秒（物理版：走る電車・流れる景色・本物の光）をPCで本番描画する手順

人はピクトグラムの3D（A案）。主人公は白い体＋紺白しまの上着＋黄色いキャップ＋点の目、乗客はグレーで顔なし、イヤホンは白。
電車は時速60kmで走り、窓の外の景色・柱の影・つり革（振り子）・乗客の揺れ・ほこりは物理で計算する。光は太陽・空・天井の照明だけ。
まるロボと一時停止ボタンは `maru_opening.blend` から持ってくる。動きはコードで計算するので、PCでも同じ動きになる。

## 手順
1. PowerShellを開く
2. 下のコマンドを貼り付けて実行する（1行目の場所だけ自分の置き場所に合わせる）
3. できた `C:\marurobo\render_opening_phys_1080\opening_phys_0001-0528.mp4` をチャットに送る（音と字幕はこちらで付ける）

```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\restore\v3\bt_opening\output"
& $blender -b --factory-startup --python "$root\marurobo_tools\human\opening_phys.py" -- --blend "$src\maru_opening.blend" --out "$root\render_opening_phys_1080" --res 1920 1080 --samples 32 --frames 1:528 --video 1
```

確認用の静止画（11枚）だけなら、3行目までは同じで、4行目をこれにする（`check_*.png` ができる）：

```powershell
& $blender -b --factory-startup --python "$root\marurobo_tools\human\opening_phys.py" -- --blend "$src\maru_opening.blend" --out "$root\render_opening_check" --res 960 540 --samples 16 --dry 1
```

---

# ③ まるロボの動きの見本リール（約75秒）をPCで本番描画する手順

まるロボの動きの部品集（`maru` フォルダ）で計算した動きを、何もないスタジオで全部見せる。待機・見回す・歩く・止まる・向きを変える・うなずく・首を振る・驚く・跳ねる・考える・のぞき込む・急ぎ足で止まる・ほっとする・台に跳び乗る／降りる・荷物を運んで後ろの台へ降ろす。追加で、走る・首をかしげる・紹介する・あいさつ・休む→起きる。

```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1\output"
& $blender -b "$src\story.blend" --python "$root\marurobo_tools\maru\maru_reel.py" -- --out "$root\render_maru_reel_1080" --res 1920 1080 --samples 32 --frames 1:1807 --video 1
```

できた `C:\marurobo\render_maru_reel_1080\maru_reel_0001-1807.mp4` をチャットに送る（字幕と電子音はこちらで付ける）。

追加の動き（走る・首をかしげる・紹介する・あいさつ・休む→起きる、約25秒）は、4行目をこれにする：

```powershell
& $blender -b "$src\story.blend" --python "$root\marurobo_tools\maru\maru_reel.py" -- --plan extra --out "$root\render_maru_extra_1080" --res 1920 1080 --samples 32 --frames 1:612 --video 1
```
静止画だけなら、4行目をこれにする（秒で指定。`still_*.png` ができる）：

```powershell
& $blender -b "$src\story.blend" --python "$root\marurobo_tools\maru\maru_reel.py" -- --out "$root\render_maru_reel_stills" --res 1920 1080 --samples 32 --still 2,11,22,48.6,68
```

## 中身（maru フォルダ）
| ファイル | 役割 |
|---|---|
| marumotion.py | 動きの部品集。予定（Plan）に動きを積み、simulate() で毎コマの姿勢にする（足の置き場所・アンテナと荷物のばね・荷物の滑り方まで物理で計算）。荷台は運ぶ間だけ出し、その間アンテナは体にしまう。積む（load_back：押し出し板で荷台へ、押される分だけ踏ん張る）・降ろす（unload_back：後ろの台へ。台は動力つきローラーにもできる） |
| marurig.py | まるロボ（Blenderの部品）に姿勢を当てる。足首の回転軸を足し、荷台を3cm上げる |
| maru_reel_plan.py | 見本リールの動きの順番と字幕 |
| maru_reel.py | スタジオ・跳び乗る台・荷物の台・カメラを作り、描画する |
| maru_reel_assemble.py | 字幕と電子音（出来事の記録から合成）を付けて mp4 にする（こちらで使う） |
| maru_check.py | 物理の点検：足の滑り・脚の伸び縮み・アンテナの振れなどを数値とグラフで出す（Blenderなしで動く） |

新しい場面で使うときの書き方（Blenderの中）：

```python
import marumotion as mm, marurig as mr
p = mm.Plan(pos=(0, 0), heading=180)          # 向き：0で+Y、左回りが＋（度）
p.idle(3); p.look(30); p.walk_to((2.6, 0)); p.turn_to(180); p.nod(); p.surprise(); p.hops()
p.run_to((6, 0)); p.confused(); p.present(45); p.greet(); p.rest(2); p.wake()      # 走る・首をかしげる・紹介する・あいさつ・休む・起きる
p.load_back(); p.walk_to((0, 5)); p.unload_back(dock=dict(near=0.47, depth=1.5, height=1.03, mu=0.35, v=0.5))   # 積む→運ぶ→後ろの台へ降ろす
p.awe(); p.groove(4.0, bpm=96)                                                       # 見上げる・曲に合わせて揺れる
frames = mm.simulate(p, fps=24)
rig = mr.MaruRig(bpy.data.objects["Maru"]); bk = mr.Baker()
for i, fr in enumerate(frames): rig.apply(fr, i + 1, bk)
bk.write()
```

## 中身（human フォルダ）
| ファイル | 役割 |
|---|---|
| opening_phys.py | 冒頭の場面を組む（物理版：晴れた朝の電車・乗客10人と主人公・まるロボと一時停止ボタン・本物の光だけ） |
| opening_phys_seq.py | 冒頭22秒の動き（3ショット）：つり革の振り子・乗客の揺れ・流れる景色・ほこり・時間が止まると全部止まる |
| train_env_exec.py / train_world.py | 電車の車内（座席・窓・ドア・網棚・つり革・天井の照明）と、窓の外の動く世界（地面・架線柱・建物・遠くの街・空）・太陽 |
| opening_pict.py / opening_pict_seq.py | 前の版（光を暗くしてスポットを当てる版。比べる用） |
| iconfig.py | 人の見た目（ピクトグラムの3D。主人公の服装、点の目、イヤホン） |
| hero_anim.py | 主人公の時間割（聴く→音が途切れる→目→頭→体→手でイヤホンに触れる） |
| people.py | 乗客の座り方（片手・両手でスマホ） |
| motion.py | 動きの部品（躍度最小・まばたき・呼吸・ばね・電車の揺れ） |
| hrig.py / hgen.py / sdf.py / hbuild.py / hchar.py ほか | 骨格・逆運動学・形の計算・材質 |
| screens / refscene | スマホの画面と、窓の外の街の画像 |

## かかった時間を記録する
本番の描画が終わったら、PowerShellに出た時間（または始めと終わりの時刻）をチャットに書く。投稿ペースを決めるのに使う。

## うまくいかないとき
- 「blender.exe が見つからない」と出る：Blenderの入っている場所を確認して、2行目を直す
- 「maru_opening.blend が見つからない」と出る：`$src` の場所を確認する
- 途中で止めたい：PowerShellの画面で Ctrl + C
- 表示された文字（エラー）をそのままチャットに貼ってもらえれば、こちらで直す

---

# ④ 第3章「音楽を届ける、小さな旅」（2026-11-07 OK。本番を PC で 1 回だけ描く）

`ch03` フォルダ：舞台（巨大スマホの積み込み口→巨大イヤホンの受付口）と、電車の場面（時間が止まった瞬間）を組んで描く。

## 本番の手順（3D の絵だけを PC で描く。図・字幕・声・音は、こちらで 1080p に合わせて付ける）

PC で描くのは2つ：**A. 舞台（1283 コマ・約 53 秒）** と **B. 電車の場面（C1・C2 の 461 コマと C12 の 101 コマ）**。
どちらも、**短い範囲ごとに Blender を起動し直して描く**。こちらの機械では、Blender は 1 コマ描くごとに使うメモリが少しずつ増え（640×360 で 1 コマ約 55MB）、長く描き続けると止められた。PC でも同じことが起きる場合に備えて、舞台は 100 コマ、電車は 48 コマ（2 秒）ずつに分ける。途中で止まっても、その範囲だけ描き直せばよい。

```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1"
$op = "$root\bluetooth_handoff_restored\restore\v3\bt_opening\output"
$out = "$root\render_ch03_1080"

# A. 舞台：100 コマずつ mp4（ch03_stage_0001-0100.mp4 … ch03_stage_1201-1283.mp4 の 13 本）
for ($s = 1; $s -le 1283; $s += 100) {
  $e = [Math]::Min($s + 99, 1283)
  & $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\ch03_stage.py" -- --out $out --res 1920 1080 --samples 32 --frames "${s}:${e}" --video 1
}

# B. 電車の場面：48 コマずつ連番の絵を描いて（frames_train）、最後に mp4 にまとめる
foreach ($r in @(@(0, 461), @(1651, 1752))) {
  for ($i = $r[0]; $i -lt $r[1]; $i += 48) {
    $a = $i / 24; $b = [Math]::Min($i + 48, $r[1]) / 24
    & $blender -b --factory-startup --python "$root\marurobo_tools\ch03\ch03_train.py" -- --blend "$op\maru_opening.blend" --out "$out\train" --res 1920 1080 --samples 32 --anim "${a}:${b}"
  }
}
& $blender -b --factory-startup --python "$root\marurobo_tools\ch03\seq2mp4.py" -- --dir "$out\train\frames_train" --prefix t_ --start 0 --end 460 --out "$out\train_c1c2.mp4"
& $blender -b --factory-startup --python "$root\marurobo_tools\ch03\seq2mp4.py" -- --dir "$out\train\frames_train" --prefix t_ --start 1651 --end 1751 --out "$out\train_c12.mp4"
```

送ってほしいもの（Google ドライブに `marurobo_render\ch03` のフォルダを作って入れ、チャットで知らせる）：
- `render_ch03_1080` の中の mp4 ぜんぶ（舞台 13 本・電車 2 本）
- `render_ch03_1080\train` の中の `train_frames_log_*.json` ぜんぶ（電車のカメラの記録。電波の波面をカメラに合わせて重ねるのに使う）

うまくいかないとき：エラーの最後の 20 行くらいをチャットに貼る。描けた範囲の mp4 はそのまま残しておく（描き直すのは止まった範囲だけ）。電車の場面は、同じ行をもう一度走らせれば、描けたコマは飛ばして続きから描く。
初めて描くときは、A の最初の範囲（1:100）にかかった時間を記録して知らせる（残りの見込みを出す）。描いているあいだにタスクマネージャーでメモリと GPU のメモリを見て、範囲の途中でどんどん増えていくようなら、その様子も知らせる（範囲をもっと短くする）。
電車の場面は、車内の人と窓の外の長い町並みを組むので、1 本で約 4.5GB のメモリを使う（こちらの機械で測った値）。同時に 2 本走らせない。

| ファイル | 役割 |
|---|---|
| ch03_plan.py | 舞台の配置と、まるロボの予定（あいさつ→見上げる→積む→歩く→受付口を見つける→後ろの台へ降ろす→曲に合わせて揺れる） |
| ch03_stage.py | 舞台を組んで描く（`--engine workbench` で動きの確認用の簡易描画、`--still 秒,秒` で静止画） |
| ch03_train.py | 冒頭の電車を止まった最後のコマで組み、スマホの画面・耳のイヤホン・引きの絵を描く |
| ch03_waves.py | 止まった電波の波面（12.3cmおきの同心円のゆがみ）を絵の上に重ねる |
| ch03_screen.py | スマホの曲の画面（細かく描き直したもの）。曲のデータのまとまり01〜05の帯と、いま送る03が光る画面（screens フォルダ） |
| ch03_diagram.py | 最後の図（送る→受け取る→音にする） |
| ch03_assemble.py | 章ぜんぶ（80秒）を、字幕・効果音・曲をつけてつなぐ（こちらで使う） |
| frame_check.py | カメラの候補を数値で確かめる（Blenderなしで動く） |
| ch03_questions.py | 章の終わりの「二つの疑問」の画（台本 v2 の 34。第5章の頭でも使う） |
| earbud_v2.py | 巨大イヤホン v2（なめらかな一体の形・つやのある白い樹脂・シリコンの耳の先・金属のふた）。ch03_stage.py が使う（`--eb2 0` で Codex版に戻る）。形は初回に cache フォルダへ保存（数秒） |
| seq2mp4.py | 連番の絵（PNG）を Blender だけで mp4 にまとめる（PC に ffmpeg がなくてよい）。電車の場面で使う |

---

# ⑤ 第1・2章（本編 0:00〜1:21。2026-11-08 OK。本番を PC で 1 回だけ描く）

`human` フォルダ：冒頭の電車（opening_phys.py）に、第1・2章の15カット（ch0102_seq.py）を入れて描く。

| ファイル | 役割 |
|---|---|
| ch0102_seq.py | カット・カメラ・まるロボ（一時停止ボタンに跳び乗る）・時間が止まる・踊りの場面 |
| dance.py | K7〜K9 の踊り：曲の拍（1拍0.3848秒）に合わせた振り。K7 は全員（想像）、K8〜K9 は主人公だけ（現実） |
| people.py | 乗客の姿勢と、小さな自然な動き（`--acts 1`：顔を上げる・スクロール・座り直す・持ち直す・イヤホンを押す） |
| hero_anim.py | 主人公（うなずき・音が途切れたときの反応・イヤホンに触れる） |
| pose_lib.py | スマホを持つ手（丸い手はスマホの裏に触れる位置） |
| ch0102_assemble.py | 字幕・効果音・曲をつけてつなぐ（こちらで使う） |

本番の手順：④と同じく、100 コマずつ Blender を起動し直して mp4 で描く（描くほどメモリが増えるため）。1 本で約 4.5GB のメモリを使うので、同時に 2 本走らせない。
```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
# 第1〜2章：100 コマずつ mp4（ch0102_0001-0100.mp4 … ch0102_1901-1944.mp4 の 20 本）
for ($s = 1; $s -le 1944; $s += 100) {
  $e = [Math]::Min($s + 99, 1944)
  & $blender -b --factory-startup --python "$root\marurobo_tools\human\opening_phys.py" -- --seq ch0102_seq.py --crowd 1 --world_len 1450 --acts 1 --out "$root\render_ch0102" --frames "${s}:${e}" --res 1920 1080 --samples 64 --video 1
}
```
送ってほしいもの：`render_ch0102` の中の mp4 ぜんぶ（20 本）と `ch0102_log.json`（まるロボの足音・跳ぶ音の時刻）を、Google ドライブの `marurobo_render\ch0102` へ。
2026-11-08 の直し：第2章の終わり（1:14.7〜1:21）で、まるロボがスマホの見やすい所へ横に 4 歩（足音）。「まずは、中をのぞいてみます。」は 1:14.85 へ（声の置き場所はこちらで付ける）。

---

# ⑥ 共通の部品（kit フォルダ。ほかの場面でも使い回す）

| ファイル | 中身 |
|---|---|
| kit/colormix.py | 絵の具の混ぜ方（顔料の量で重みを付けた反射率の幾何平均）。混ぜる順番によらず同じ量なら同じ色＝鍵共有のたとえの要 |
| kit/carry.py | 運ぶ物の物理：吊った物の振り子（支点の加速）、器の中の液体の揺れ（第1モード。円柱の器の固有振動数の式つき） |
| kit/hoist.py | 天井クレーンの動きの予定（台車の位置・フックの高さを躍度最小で。つかむ・はなす。硬い棒なら振れない） |
| kit/props.py | 小物：バケツ（すける胴・取っ手・液面）、ひみつの色の小びん（回る腕・傾けるフォーク・流れ）、タンク、台、片持ちクレーン、鍵（歯の並びで形が変わる）、鍵穴の板（差すと光る輪）、錠の箱（台の上に置き、鍵を真上から差す。鍵は立って正面から形と色が見える。上の輪と前の灯が光る）、鍵の型（寝かせた鍵の形のくぼみに色が満ちる）、地面の灯 |
| kit/world.py | 石の床（1m の目地）、物理の空と太陽、遠くのかすみ、EEVEE／簡易描画の設定 |
| maru/marurig.py | MaruRig.world_mats(1コマの姿勢) → 背中の受け皿・トレーの世界の位置（ほかの物を載せて運ぶとき） |

使っている場面：第4章のペアリング（ch03/ch04_pairing.py。3D は本編 4:07.6〜4:24.4 の 404 コマ。その前の 4:04.6〜 は 2D のよく見るペアリング画面で、ch03/ch04_diagram.py が描く）。描くコマンドの形：
```powershell
& $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\ch04_pairing.py" -- --out "$root\render_ch04_pairing" --engine eevee --res 1920 1080 --samples 64 --frames 1:404
python "$root\marurobo_tools\ch03\ch04_diagram.py" "$root\ch04_out" --pair="$root\render_ch04_pairing"
```
2D の二台は、3D の最初のコマの巨大スマホ・巨大イヤホンと同じ所・大きさへ寄ってから 3D に変わる（pairing_log.json の match）。だから 3D を描いて pairing_log.json ができてから、図を描く。

| ファイル | 足したこと |
|---|---|
| maru/marumotion.py | turn_to(…, step=, gap=)：向きを変える1歩の時間と歩の間（ふだんは 0.30・0.05。急ぐときは 0.22・0.03） |
| maru/marumotion.py | back_to(目標, step=, sw=, gap=, look=)：前を向いたまま横へ小走り（第4章 v6 でコップを運ぶ。2.2m で約4.5秒） |
| kit/props.py | cup（透明なコップ。液面と絵の具の体）、tilt_holder（柱の上の U 字の腕で、びん・缶を傾けて注ぐ。口の位置つき） |

# ⑦ 台本の直し（script フォルダ）

| ファイル | 中身 |
|---|---|
| script/script_fixes.json | 元の台本（Codex の bluetooth_full_native.srt）から直した所。区間（秒）と、入れ替える文・時刻・理由 |
| script/make_srt_rev.py | 直しを当てて、直した字幕を作る：`python make_srt_rev.py 元.srt script_fixes.json bluetooth_full_native_rev1.srt` |
| script/bluetooth_full_native_rev1.srt | 直した字幕（声を作るとき・字幕を焼くときはこちらを使う） |

2026-11-06 の直し：ペアリング（4:04.6〜4:24.4）を、絵（よく見るペアリング画面 → 絵の具のたとえ）に合わせて5文に言い直した。

台本 v2（2026-11-06 確定。全体の見直しと、ペアリングを「いまの様子 → やってみる → 動きに合わせて説明」の形に書き直した）：

| ファイル | 中身 |
|---|---|
| script/make_script_v2.py | 元の文の番号ごとの直し（変える・足す・消す）と理由 → script_v2.md / script_v2.json |
| script/script_v2.md | 台本 v2 の全文（189文。直した所に理由） |
| script/make_srt_v2.py | 台本 v2 に時刻をつける：変えていない文は元の長さと間、変えた・足した文は 1秒 5.3字 → bluetooth_full_native_rev2.srt と script_v2_timed.json |
| script/bluetooth_full_native_rev2.srt | 台本 v2 の字幕（全体 18:14.7。声を作るとき・字幕を焼くときはこちら） |
| script/timewarp.py | 元の時刻 → 新しい時刻の対応（作ってある図を、新しい台本の時刻で流す。足した文の間は止めて待つ） |
| script/bluetooth_voice_rev3.srt | 声（Gemini の Achernar）を置いた時刻の字幕（2026-11-07）。声が長い文は、前の間を少し使う・少し速める・次へずらす、で合わせた。字幕を焼くとき・声を足すときはこちら |

章の時刻（台本 v2）：第1・2章 0:00〜1:21／第3章 1:21〜2:56／第4章 2:56〜7:07（ペアリング 4:34.5〜6:48）／第5章 7:07〜10:55／第6章 10:55〜12:11／第7章 12:11〜15:07／第8章 15:07〜17:05／まとめ 17:05〜18:15

---

# ⑧ 第4章のペアリング v8（スマホの台を大きくした版。2026-11-08）

3D は本編 4:44.7〜6:42.4（2826 コマ、24fps）。その前後と途中の「十人十色（車内）」は 2D（こちらで付ける）。境目で 3D と 2D を重ねるので、3D は 2826 コマぜんぶ描く。
v8：スマホの台を 2.40×1.12×0.10m に大きくした（`--phone` の既定値。ケースの幅 1.20m に対して、本物のスマホとケースの大きさの比に近い）。

| ファイル | 役割 |
|---|---|
| ch03/ch04_pairing6.py | 3D：スマホの形の台（画面つき）とイヤホンケースの形の台、白とひみつの色のびん、透明なコップ、まるロボがコップを背中の板で運んで交換、隣のイヤホン（見えた色の写しが光る）、同じ紫の鍵 |
| ch03/ch04_diagram.py | 2D の図（`--v6=3Dのフォルダ` で台本 v2 の時刻） |
| ch03/ch04_assemble6.py | 字幕・効果音・ラベルをつけてつなぐ（こちらで使う） |

描き方：⓪ の `run_pc_render.ps1` が描く（`-Only ch04` で第4章だけ）。手で描くときは、④と同じく 100 コマずつ Blender を起動し直して mp4 で描く（`ch04_pair_0001-0100.mp4` … `ch04_pair_2801-2826.mp4` の 29 本）：
```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1"
for ($s = 1; $s -le 2826; $s += 100) {
  $e = [Math]::Min($s + 99, 2826)
  & $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\ch04_pairing6.py" -- --out "$root\render_ch04" --engine eevee --res 1920 1080 --samples 64 --frames "${s}:${e}" --video 1
}
```
送ってほしいもの：`render_ch04` の中の mp4 ぜんぶ（29 本）と `pairing_log.json` を、Google ドライブの `marurobo_render\ch04` へ。
ガラス（コップ・びん）は「重ねて混ぜる」半透明（BLENDED、同じ物の中は一番手前の面だけ）。ディザの半透明は少ないサンプルで砂のようにザラつき、動画でちらつくので使わない。

---|---|
| ch03/ch04_pairing6.py | 3D：スマホの形の台（画面つき）とイヤホンケースの形の台、白とひみつの色のびん、透明なコップ、まるロボがコップを背中の板で運んで交換、隣のイヤホン（見えた色の写しが光る）、同じ紫の鍵 |
| ch03/ch04_diagram.py | 2D の図（`--v6=3Dのフォルダ` で台本 v2 の時刻） |
| ch03/ch04_assemble6.py | 字幕・効果音・ラベルをつけてつなぐ（こちらで使う） |

描くコマンド（381〜546 コマは使わない：その間は 2D の「人それぞれの色」の絵になる。だから二回に分ける）：
```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1"
& $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\ch04_pairing6.py" -- --out "$root\render_ch04_pairing6" --engine eevee --res 1920 1080 --samples 64 --frames 1:380
& $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\ch04_pairing6.py" -- --out "$root\render_ch04_pairing6" --engine eevee --res 1920 1080 --samples 64 --frames 547:2826
```
ガラス（コップ・びん）は「重ねて混ぜる」半透明（BLENDED、同じ物の中は一番手前の面だけ）。ディザの半透明は少ないサンプルで砂のようにザラつき、動画でちらつくので使わない。

---

# ⑨ 第5章（たたき台：絵コンテと動きの確認用。2D の図だけなので PC で描く必要はない）

| ファイル | 役割 |
|---|---|
| ch03/ch05_diagram.py | 第5章の図：窓＝電波のチャンネル。前半（電波の重なり）・中盤（そろえて切り替える、周波数、数十の窓）・後半（隣の組、使わない窓） |
| ch03/ch05_assemble.py | 図に字幕と効果音をつけて、確認用の動画にする（こちらで使う） |

第3章は台本 v2 の時刻に直した（ch03_plan.py の DV2：「目指すのは」から後は +3.8 秒、ch03_assemble.py：章の終わりは 175.786 秒、C14「二つの疑問」）。描くコマンドは ④ と同じで、コマ数は 1283。

---

# ⑩ 第6章「送り直し（再送）」・第7章「イヤホンの中：バッファ」・第8章の塔（2026-11-08 作り中。確認の動画を見てから本番）

`ch03` フォルダ：第6章は第3章の舞台をそのまま使う（06 を二回運ぶ）。第7章と第8章の前半は、イヤホンの中の部屋（貯蔵タワー・再生装置・昇降機）。
どれも ④ と同じく、**100 コマずつ Blender を起動し直して mp4 で描く**（`--video 1`。範囲ごとに `ch06_stage_0001-0100.mp4` のような名前になる）。

- 曲：荷物の札の棒とスピーカーの動きは、`marurobo_tools\human\audio\song_mono.wav`（曲の最初の 86 秒だけ）から作る。一式に入っているので、置き方はそのままで OK（④ 第3章の荷物の札も同じ）。
- 札「バッファ」の字：`bluetooth_handoff_restored\bt_production_v1\assets\japanese.ttc` を自動で使う（こちらと同じフォント）。描き始めの記録に `JFONT <bpy_struct, VectorFont("japanese.ttc")>` のように出ていれば OK。

| 描くもの | スクリプト | コマ数 | 追加の引数 |
|---|---|---|---|
| 第6章（本編 10:54.7〜12:15.2） | ch06_stage.py | 1933 | なし |
| 第7章（本編 12:15.2〜14:39.2） | ch07_stage.py | 3458 | `--part ch7` |
| 第8章の塔（本編 15:06.2〜15:27.4） | ch07_stage.py | 510 | `--part ch8` |

```powershell
$root = "C:\marurobo"
$blender = "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
$src = "$root\bluetooth_handoff_restored\bt_production_v1"
$jobs = @(
  @{ script = "ch06_stage.py"; n = 1933; extra = @();                 out = "$root\render_ch06_1080" },
  @{ script = "ch07_stage.py"; n = 3458; extra = @("--part", "ch7"); out = "$root\render_ch07_1080" },
  @{ script = "ch07_stage.py"; n = 510;  extra = @("--part", "ch8"); out = "$root\render_ch08_tower_1080" }
)
foreach ($j in $jobs) {
  $x = $j.extra
  for ($s = 1; $s -le $j.n; $s += 100) {
    $e = [Math]::Min($s + 99, $j.n)
    & $blender -b "$src\output\story.blend" --python "$root\marurobo_tools\ch03\$($j.script)" -- --out $j.out --res 1920 1080 --samples 32 --frames "${s}:${e}" --video 1 @x
  }
}
```

送ってほしいもの：`render_ch06_1080`・`render_ch07_1080`・`render_ch08_tower_1080` の中の mp4 ぜんぶと、それぞれの記録（`ch06_log.json`・`ch07_log.json`・`ch08_tower_log.json`）を、Google ドライブの `marurobo_render\ch06`・`ch07`・`ch08` へ。

| ファイル | 役割 |
|---|---|
| ch06_plan.py | 第6章の予定：06 を積む → 受付ボックスで光がなぞる → 灯が赤 → 返事を待つ輪 → スマホへ戻る → もう一度 → 灯が緑 → 返事の光 → 曲に合わせて揺れる |
| ch06_stage.py | 第6章の舞台（調べる門・受付の灯と灯の光・返事ランプと待ち時間の輪・返事の光・スマホに残しておく 06・耳の先へ飛び込む最後のカット） |
| ch07_plan.py | 第7章と第8章の塔の予定：荷物一つ＝31秒で沈む、積み重なり、昇降機で届く時刻、後半は 871.8 秒で音が止まる、第8章は塔がいっぱいになってから鳴らす |
| ch07_stage.py | イヤホンの中の部屋（塔・ブレーキ・上の扉・目盛りの灯・札「バッファ」・再生装置とスピーカー・昇降機） |
| ch06_assemble.py・ch07_assemble.py・ch08_assemble.py | 字幕・札・効果音・曲・声をつけてつなぐ（こちらで使う） |
| ch08_game.py | 第8章の図（時間の帯・てんびん・ゲームのパンチ・流れ・棒）。2D なので PC で描く必要はない |
| overlay2d.py | 札・印・字幕・効果音の共通の道具（こちらで使う） |
