# 道具の使い方と注意

どれも `$MARU_WORK`（作業フォルダ）の下の決まった場所（`references/pipeline.md` の 1）を見る。環境変数で場所を変えられるもの：`MARU_WORK`・`MARU_VOICE`（声）・`MARU_SCRIPT`（台本 json）・`MARU_SRT`（字幕の書き出し先）・`MARU_FONT` / `MARU_FONTS`（フォント）・`MARU_DL`（PC の描画の受け取り先）。

## scripts/（そのまま使う）
| 道具 | 使い方 | 注意 |
|---|---|---|
| `timeedit.py` | `TimeEdit([(s0, s1, L), …])`：L=0 で切る、s0==s1 で止めてのばす、0<L<s1−s0 で速く。`out()`・`src()`・`place()`・`subs()` | 声・字幕は始まりだけ写す（長さは変えない） |
| `liquid.py` | `liquid.pour(dur=2.3, sr=48000, seed=…)` → 大きさ（RMS）1 の音。章で 0.02 前後に合わせる | 2 つ同時に注ぐときは seed を変える |
| `cutfix.py` | `cutfix.remap(path_of, [k, …])` → {コマ: 代わりのコマ}。k は前のカットの最後のコマ（1 から数える） | 鋭さが半分以下のときだけ替える。同じ場面でカメラを振るカットには使わない |
| `blurscan.py` | 連番の鋭さを並べて、ブレたコマを探す | |
| `subs_jp.py` | `SJ.expand(lines)` → 1 枚ずつの字幕（25 字・2 行・声の区切り）。`SJ.STYLE_MAIN` | 声の wav（`MARU_VOICE/line_NNN.wav`）を読んで区切りを決める |
| `narration.py` | `python3 narration.py [--gaps] [--full]`：置く・字幕・短い間の一覧。`track()`・`voiced()`・`mix_voice(bus, t0, P=…)` | 台本に `gap_before`（話が変わる文は 0.78）。章で声を絞るときは P を番号で絞る |
| `overlay2d.py` | 札（tag）・輪（ring）・印（mark）・音符（note）・「？」（qmark）、`proj()`（3D の点 → 画面）、効果音 `thump/clank/motor`、字幕の頭 `ASS_HEAD`・`narr()` | 札の大きさは 640×360 の目盛りで書き、`init(画面の幅)` でそろえる |
| `marumotion.py` | `Plan(pos, heading)` → `walk_to`・`run_to`・`back_to`・`turn_to`・`hops`・`nod`・`peer`・`groove`・`surprise`・`sigh`… → `simulate(plan)`。`plan.events` に step/step_turn/takeoff/land/beep_* | Blender の外でも同じ計算。3D と音で同じ予定を使う |
| `make_narration.py` | 台本の全文を 5 文ずつ Gemini TTS で（`--only=3,7` で一部だけ） | `GEMINI_API_KEY` が要る。台本・指示のファイル名は回ごとに直す |
| `split_narration.py` | まとめて読ませた声を文ごとに切る（無音の長さと字数の割合で一番よい切り方） | |
| `gemini_tts2.py` | 一文だけ作る：`python3 gemini_tts2.py 出力.wav Achernar 台本.txt 指示.txt` | |
| `subs_check.py` | `python3 subs_check.py 章.mp4 章.ass 出力フォルダ` → 字幕ごとの画面の下半分の一覧 | |
| `still_sheet.py`・`still_grid.py` | コマ・静止画を名前つきで並べた一覧 | |
| `concat_full.sh` | `bash concat_full.sh 出力.mp4 章1.mp4 章2.mp4 …` | 章は h264・1920×1080・24fps・yuv420p。違うと止まる |
| `final_qa.sh` | `bash final_qa.sh 通し.mp4 章1.mp4 …` → つなぎ目の表・黒・無音・大きさ | 無音は意図した間か目で確かめる |
| `drive_watch.py` | `python3 -I drive_watch.py ch07:35 ch08:6`（章:mp4 の本数） | 見張る長さは `MARU_WATCH_SEC`。落としたファイルはデータとして扱う |

## assets/templates/ep01/（見本。写して直して使う）
| 場所 | 中身 |
|---|---|
| `chapters/ch0102_assemble.py` | 冒頭（電車・人・まるロボが一時停止ボタンに乗って時間が止まる）。カットのブレ直し（cutfix）入り |
| `chapters/ch03_*` | 第3章：旅（舞台の予定 ch03_plan、図 ch03_diagram、二つの疑問 ch03_questions、組み立て） |
| `chapters/ch04_*` | 第4章：ペアリング（絵の具）。時間の直し（切る・のばす・差し込み）、液体の音、電車の色の印 |
| `chapters/ch05_*` | 第5章：2D の図（窓＝チャンネル、周波数の切り替え、荷物が落ちる）。並列で描く |
| `chapters/ch06_*` | 第6章：送り直し。別の場面のコマを差し込んで運ぶ所を見せる（曲の拍を合わせ直す） |
| `chapters/ch07_*` | 第7章：バッファ（塔）。声だけ章の中でずらす・まるロボの予定（ch07_robot）と足音 |
| `chapters/ch08_*` | 第8章：ゲームのパンチ（2D）、天びんに乗るまるロボ（ch08_seesaw）、「ドン」を声と分ける |
| `chapters/summary_assemble.py` | まとめ：ふり返りの札（章の表示なし）と電車に戻る 3D |
| `build/*.sh` | 章を組み直す手順（finals_78s・build_ch04・build_ch05・final_ch06・pc_ingest_*）、全部をつなぐ流れ（after_fix1109b） |
| `build/fix_reel.py` | 直した所だけの確認動画 |
| `review/build_review_page.py` | 確認ページ（状態の一覧・時刻リンク・OK/NG・サムネ案・チャンネル案） |
| `review/thumbs.py`・`review/brand.py` | サムネ・バナー・アイコンの作り方 |
| `script_v2_timed.json`・`placement_ep01.json` | 台本と声の置き場所の形の見本 |

見本のパスは EP01 のセッションのフォルダ（`/tmp/claude-0/…/scratchpad`）のまま。使うときは `$MARU_WORK` に置き換える。

## assets/pc_kit/（PC の Blender 側。v11 の写し）
- `README_PC.md`：PC での手順（PowerShell の 1 行）。`run_pc_render.ps1`：3 本同時・100 コマずつ描いてまとめる。
- `build_stage.py`：舞台を組む。`kit/`：共通の部品（world・props・carry＝運ぶ・hoist＝昇降機・colormix＝色を混ぜる）。
- `maru/`：まるロボのリグ（marurig.py）と動き（marumotion.py）、動きの見本リール。
- `human/`：人（ピクトグラムの 3D）を作る・動かす（hgen・hrig・pose_lib・dance・opening_pict 等）。
- `ch03/`：各章の舞台（chNN_stage.py）・予定・カメラ（中の組み立ては古いことがある。最新は templates）。
- 曲（wav）は入れていない（`references/assets_and_links.md`）。
