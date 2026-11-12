# 1本目：電車でイヤホン（Bluetooth の音楽が途切れる・遅れるしくみ）

## 状況（2026-11-12）
- 通し 18:10（1920×1080・-14 LUFS）で完成。ユーザーの OK は 2026-11-09。
- この回で作った決まりは、スキルにまとめてある（`skill/marurobo-video-production/SKILL.md`。直しの記録は `references/feedback_log.md`）。
- YouTube の文（概要欄・章・タグ・タイトル案・サムネのテスト案）は `youtube/`。チャンネル名は「まるロボのなるほどデジタル」。
- 動画レビューツール（まるロボ動画レビュー）には、この回は登録していない（ユーザーの判断）。

## フォルダ
| 場所 | 中身 |
|---|---|
| `台本_v2_確定.md` | 最終の台本（189 文・章の見出しつき）。声のファイルと同じ番号 |
| `stage/script/` | 台本の元データ（`script_v2_round1.md`・`script_v2.md`・`script_v2.json`・時刻つきの `script_v2_timed.json`・直しの `script_fixes.json`）、字幕（`bluetooth_voice_rev3.srt` が声に合わせた最終）、それらを作るスクリプト |
| `stage/voice/achernar/` | 声の文字の資料：文ごとの声の長さ（`lines.json`）・置き場所（`placement.json`）・読み（`readings.json`）・5 文ずつのまとめ（`batch_XX.json`）。声の wav は入れていない |
| `stage/voice_test/` | 声の指示（`style_gentle.txt`） |
| `stage/human/` | 冒頭（0:00〜1:21：電車・人・まるロボ）の組み立て `ch0102_assemble.py`、人（ピクトグラムの 3D）を作る・動かすスクリプト（`hgen`・`hrig`・`pose_lib`・`dance`・`opening_pict` など）、人の見た目を決めるまでの試し |
| `stage/ch03/` | 第3章〜まとめの組み立て（`chNN_assemble.py`・`summary_assemble.py`）、図（`chNN_diagram.py`）、3D の舞台と予定（`chNN_stage.py`・`chNN_plan.py`・`ch07_robot.py`）。第4章は `ch04_assemble6.py`・`ch04_pairing6.py` が最新 |
| `stage/kit/`・`stage/maru/` | 3D の共通部品（世界・小物・運ぶ・昇降機・色を混ぜる）と、まるロボのリグと動き（`marurig.py`・`marumotion.py`） |
| `stage/marurobo_tools/` | PC（Blender）で本番を描く一式（v11）。スキルの説明にある `assets/pc_kit` と同じもの（このリポジトリのスキルには入っていない） |
| `stage/final/` | 概要欄・チャンネル説明の元の文 |
| `tools/` | この回だけの道具：章を組み直す手順（`*.sh`）、確認ページ（`build_review_page.py`）、直した所だけの確認動画（`fix_reel.py`）、サムネ（`thumbs.py`）・バナーとアイコン（`brand.py`）、絵コンテ、点検 |
| `tools/shared_ep01_versions/` | 共通の道具のうち、この回で使った版。QR 回で直した最新版（`skill/marurobo-video-production/scripts/`）と中身がちがうものだけ（下の表）。新しい回では最新版を使う |
| `dl_pc/` | PC で描いた 3D の記録（`*_log.json`：カメラ・点の位置・出来事）。札の位置や効果音の時刻を出すのに使う |
| `review_page/` | 確認ページの HTML（画像・動画は入れていない） |
| `cloud_render/` | 初めのころ、クラウドで 3D を描いていた手順 |
| `youtube/` | `EP01_YouTube一式.md`（タイトル案・サムネのテスト案・概要欄・章・タグ）、`チャンネル説明.txt`、`チャンネルのガイドライン.md` |

### 共通の道具とのちがい（`tools/shared_ep01_versions/`）
`concat_full.sh`・`drive_watch.py`・`final_qa.sh`・`make_narration.py`・`narration.py`・`split_narration.py`・`still_grid.py`・`subs_check.py`・`subs_jp.py`・`subs_sample.py`・`transcribe.py` は、この回の版と共通の最新版で中身がちがう（この回の版はパスが作業場所に固定されている・QR 回の直しが入っていない）。
`stage/ch03/overlay2d.py` も、共通の `overlay2d.py` とはちがう（この回の版）。
`blurscan.py`・`cutfix.py`・`gemini_tts.py`・`gemini_tts2.py`・`liquid.py`・`still_sheet.py`・`timeedit.py`・`vr_version.py` は共通の版と同じなので、ここには入れていない。

## ページ（claude.ai）
- 制作バイブル（Claude Docs）：https://claude.ai/artifact/H9g24qNzjBPUeafePMgxoz
- 確認ページ（章の状態・OK/NG・直した所の確認動画・サムネ案・チャンネル案）：https://claude.ai/artifact/DFSHG8vdWK4rRq9zHuYYYi
- まるロボ動画レビュー：https://claude.ai/artifact/S3dTcoRuFr2n7Eg99RiJWi（この回は未登録）

## 作業場所に戻して使うとき
- `stage/`・`tools/`・`dl_pc/` を、作業フォルダ（`$MARU_WORK`）の下に同じ形で置く。`tools/shared_ep01_versions/` の中身も `tools/` に入れると、この回と同じ動きになる。
- スクリプトの中のパスは、1本目のセッションの作業場所（`/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad`）のまま。`$MARU_WORK` に置き換える。
- 古い版の写し（`*_before_*`・`*_backup*`・新しい版がある `*_vN`）は入れていない。

## まだ入っていないもの（大きなファイル）
- 通し `bluetooth_full_1080.mp4`（18:10・315MB）と章ごとの本番 mp4：ユーザーにはチャットで送付済み。リポジトリには入れない。
- 声（`stage/voice/achernar/line_NNN.wav`、189 本）：1本目のセッションの作業場所にだけある。作り直すときは `台本_v2_確定.md` と `readings.json` から Gemini TTS（声 Achernar・指示 `style_gentle.txt`）で。QR 回と同じく FLAC にして `media/` に入れることもできる。
- BGM：Codex 版の曲（`song_mono.wav`）の 40.04 秒からの 3.08 秒（8 拍）をくり返して使った。元の曲はユーザーの PC の引き継ぎ素材（`C:\marurobo\bluetooth_handoff_restored\`）にある。
- PC で描いた 3D（mp4）：ユーザーの PC `C:\marurobo\marurobo_render\<章>\` と Google ドライブ `marurobo_render`。
- フォント（Noto Sans CJK JP の `japanese.ttc`）：ユーザーの PC の引き継ぎ素材にある。
- 画像（絵コンテ・サムネ・バナー・アイコン・確認ページの画像）：作業場所にだけある。サムネ・バナー・アイコンは `tools/thumbs.py`・`tools/brand.py` で作り直せる（本編のコマが要る）。
