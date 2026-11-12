# 声と BGM の元（作り直しに手間がかかるので、ここに残す）

- `voice_master_flac/`：仕上げた声（`parts/voice_v2/master/*.wav` を FLAC にしたもの・音は同じ）。ファイル名は台本の ID。`v2_voice_map.json` は ID → 文・長さ。
  wav に戻す：`ffmpeg -i 10-01.flac 10-01.wav`（48kHz）
- `bgm_flac/`：BGM（マリンバ）。`A_loop_points.txt` は継ぎ目なくくり返す位置。
- 絵コンテの画像・通しの動画は入れていない（スクリプトから作り直せる。本番の 3D は PC で描く）。
