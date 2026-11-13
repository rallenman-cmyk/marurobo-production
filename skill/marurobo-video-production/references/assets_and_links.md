# 大きなファイルの置き場所とリンク

このスキルには、プログラムと小さな素材だけを入れている。大きなファイルは次の場所にある。

## リンク
- 制作バイブル（Claude Docs）：https://claude.ai/artifact/H9g24qNzjBPUeafePMgxoz — 決めたことの元帳。【指示】【コンテキスト】【絵コンテ】の節。
- 3本目（会話と広告の回）の確認ページ（Artifact）：https://claude.ai/artifact/JCZiLxFCQ9QDY8fRuvJMz4 — db の reviews（場面ごとの OK/NG・メモ）・bgm（曲の選択）。
- 動画レビューツール：https://claude.ai/artifact/S3dTcoRuFr2n7Eg99RiJWi — 作品 MARU-EP02（QR回）・MARU-EP03（会話と広告の回。v1＝通し 15:29）。区切って上げる手順は scripts/vr_version.py。
- EP01 の確認ページ（Artifact）：https://claude.ai/artifact/DFSHG8vdWK4rRq9zHuYYYi — 章の状態・OK/NG（db: reviews）・直した所の確認動画・サムネ案・チャンネル案。

## ユーザーの PC（Windows）
- `C:\marurobo\bluetooth_handoff_restored\` — Codex 版から引き継いだ素材（ユーザーがくれた分割 ZIP 15 個を展開したもの）。
  - `bt_production_v1\output\story.blend`、`restore\v3\bt_opening\output\maru_opening.blend`（まるロボのもとのモデル）
  - `bt_production_v1\assets\japanese.ttc`（Noto Sans CJK JP。FONT_LICENSE.txt つき）
- `C:\marurobo\marurobo_tools\` — PC 用の一式（このスキルの `assets/pc_kit` と同じもの）。新しい版は zip にしてユーザーに渡し、同じ場所へ展開してもらう。
- `C:\marurobo\marurobo_render\<章>\` — 描いた mp4 と記録。Google ドライブへコピーされる。
- Blender 4.3.2（`C:\Program Files\Blender Foundation\Blender 4.3\`）。

## Google ドライブ
- `marurobo_render`（リンク共有・見るだけ、フォルダ ID `1thcAROo3WmIhr6hKVZxydPrw-X9ACjrk`）— PC の描画の受け渡し。中に章ごとのフォルダ。`drive_watch.py` が見る。
- こちら（クラウド）からドライブへ大きなファイルを上げる道具はない（コネクタは本文を直接送る形なので数 MB は無理）。PC かユーザーの手で上げてもらう。

## クラウドのセッションで要るもの
- フォント `japanese.ttc`：上の PC か引き継ぎ ZIP から。無いときはユーザーに、引き継ぎ ZIP の 1 つ目か PC のファイルを上げてもらう。
- BGM の作り方（2026-11-12）：Gemini の作曲モデル Lyria（`models/lyria-3.5`・`lyria-3-clip-preview`、generateContent に英語の指示、mp3 が返る。GEMINI_API_KEY で使える）。vidIQ は使わない（ユーザー）。
- BGM：EP01 は Codex 版の曲（`stage/human/audio/song_mono.wav`、39MB）。40.04 秒からの 3.08 秒（8 拍）を継ぎ目なくくり返す。ユーザーは「BGM は変えたい」と言っている（未決定）。新しい曲にするときは継ぎ目のないループを作り直す。
- 声：`GEMINI_API_KEY`（環境の秘密の設定。値をファイルや画面に出さない）。
- まるロボのモデル：PC の `maru_opening.blend`。クラウドで確認用に描くときは、ユーザーにそのファイルを上げてもらう（または PC の Remote Control）。

## EP01 でできたもの（参考）
- 通し：`bluetooth_full_1080.mp4`（18分10秒・1920×1080・-14 LUFS）— チャットで送付済み。
- YouTube の章：0:00 電車の中の二つの疑問／1:21 音楽を届ける、小さな旅／2:55 届くことと、再生することは違う／7:06 途切れる理由と、周波数を変える工夫／10:45 送り直す（再送）／12:09 先に受け取って待たせる（バッファ）／15:01 ためれば解決？（遅れとの両立）／16:59 まとめ
- サムネ案 6・チャンネル案 3 組（`references/branding.md`）— zip でチャットに送付済み。
- 3本目の PC 用一式：`episodes/ep03_ad/pc_kit/`（`make_kit.sh` → `marurobo_ep03.zip`。PC では `C:\marurobo\marurobo_ep03`、出力は `C:\marurobo\render_ep03` → `marurobo_render\ep03`）。場面の道具に `--gpu --video` を付けると、グラフィックボードで描いて mp4 で書く（`anim/pc_out.py`）。
