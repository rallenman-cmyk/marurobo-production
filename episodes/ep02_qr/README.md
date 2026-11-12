# 2本目：QRコードは欠けてもなぜ読める？

台本は v2.0 で確定しています（`台本_v2_0_確定.md`）。1本目の決まりに、この回の直しを足して作りました。

## 状況（2026-11-12）
- 確認用の通しは v8 まで作成。動画レビューツール（下）で見てもらっている。
- 本番の組み立て（1920×1080）の試しまでできている。3D はまだ絵コンテの静止画で、本番はユーザーの PC で描く。
- 3D の描き直し用の時刻表：`3D描き直し用_時刻表.md`（.csv も同じ中身）。PC に送るのは、頼まれてから。
- YouTube 一式：`youtube/QR回_YouTube一式.md`（概要欄・もくじの時刻・固定コメント）、`youtube/qr_ep02_ja.srt`（字幕）。`youtube/make_youtube_kit.py` を走らせ直すと、時刻がそろう。

## フォルダ
| 場所 | 中身 |
|---|---|
| `台本_*.md` | 台本の版（v0.1〜v2.0）。直した理由は、台本レビューツールの各行のメモにある |
| `review_tool/` | 台本レビューツールに登録したデータを作るスクリプト（版ごと） |
| `parts/v2/` | 組み立ての本体。`anim2.py`（声の ID から絵の時刻を決める）・`chapters.py`（章ごとの絵と札）・`fig_anim.py`（動く 2D の図）・`final_build.py`（本番 1080p）・`make_3d_sheet.py`（3D の時刻表） |
| `parts/review/` | 通しを組む `through_review.py`、点検 `autocheck/auto_check.py` |
| `parts/ch1`〜`ch4`・`c5`・`opening` | 3D の絵コンテ（Blender）のスクリプト |
| `parts/sfx_qr/` | 効果音の部品 |
| `parts/voice_v2/` | 声の読み（`yomi.py`）と仕上げ（`master_voice.py`） |
| `review_tool_marurobo.html` | 動画レビューツールのページ（スマホの書く欄・よくある指摘ボタン入り） |

## ページ（claude.ai）
- 動画レビューツール：https://claude.ai/artifact/S3dTcoRuFr2n7Eg99RiJWi（作品 MARU-EP02）
- 台本レビューツール：https://claude.ai/artifact/3kj4tZtaZWwbvig7GmEs4c（作品 MARU-QR）

## 大きなファイル（ここには入れていない）
声（`parts/voice_v2/master/*.wav`）・通しの動画・本番の試し・絵コンテの画像は、作業した container にある。残すものは Google ドライブ `marurobo_render/ep02_qr/` に置く。

## この回で増えた決まり（主なもの）
- 3D の中に字を書かない。数字・式・名前は 2D の札で、字幕と同じかそれより大きく。字のある場面は幅 390px で全部読めるか確かめる。
- 字幕の切り替えは、声の切れ目の組み合わせ全体で選ぶ（`subs_jp.events`）。台本の指示「（間）」は字幕に出さない。
- 見てもらう前に `auto_check.py` で全部点検（効果音と声・長い間・短い字幕・字幕と図の重なり・図の字の大きさ）。
- 地のある図にフェードで描くときは、色を混ぜる設定にする（`fig_anim.D`）。
