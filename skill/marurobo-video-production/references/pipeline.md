# 作り方の流れと数値（EP01 でうまくいった形）

## 目次
1. 作業フォルダの形
2. 全体の流れ
3. 時刻の三つの物差し
4. 声（作る・切る・置く・字幕）
5. 章の組み立て（3D の章・2D の章）
6. 時間の直し（TimeEdit）
7. 音の大きさ
8. PC での本番描画と受け取り
9. 通し・点検・測り方

## 1. 作業フォルダの形（`$MARU_WORK` の下）
```
tools/                 道具（このスキルの scripts/ を写す）
stage/script/          台本（script_vN_timed.json：文ごとの no・start・end・text）・声に合わせた字幕（.srt）
stage/voice/achernar/  声（batch_XX.wav → line_NNN.wav）・lines.json・placement.json・tts_text.json
stage/voice_test/      声の指示（style_gentle.txt）
stage/av/fonts/        japanese.ttc（Noto Sans CJK JP）
stage/ch03/            章ごとの組み立て・図・3D の予定（chNN_assemble.py・chNN_diagram.py・chNN_plan.py・chNN_stage.py）と出力
stage/human/           冒頭（人の場面）の組み立てと素材（audio/song_mono.wav＝BGM）
stage/final/           章ごとの本番（chNN_final_1080.mp4）と通し
dl_pc/<章>/            PC で描いた 3D（<名前>_<始>-<終>.mp4、100 コマずつ）と記録（*_log.json）
review_page/           確認ページ（index.html・media/・img/）
```
EP01 は 3D の章のフォルダ名が歴史的に `stage/ch03/` にまとまっている。新しい回では `stage/epNN/` のように回ごとに分けてよい。

## 2. 全体の流れ
1. 台本（バイブルの決まりで）→ ユーザーの確認 → 時刻つきの台本（文ごとの仮の時刻）。
2. 声：`make_narration.py`（5 文ずつ Gemini TTS）→ `split_narration.py`（文ごとに切る・lines.json）→ `narration.py`（置く・placement.json・字幕 .srt。`--gaps` で短い間の一覧）。
3. 絵コンテ（静止画の一覧）→ ユーザーの確認。
4. 3D の章：舞台と予定（chNN_stage.py・chNN_plan.py・まるロボは chNN_robot.py）を PC で描く → `drive_watch.py` で受け取る → `chNN_assemble.py` で札・印・字幕・効果音・曲・声を重ねて本番 mp4。
5. 2D の章（図）：`chNN_diagram.py` でコマを描く（`MARU_RES=1080`）→ `chNN_assemble.py`。
6. 確認用（1280×720・15MB 以下）を確認ページへ → OK/NG と直し → 直す。
7. 通し：`concat_full.sh` → `final_qa.sh` → 目で見る → 送る（ファイルはチャットで）。YouTube の章の時刻を作る。

## 3. 時刻の三つの物差し
- **本編の秒**：台本・声の置き場所・3D の予定が使う時刻（声の placement.json の start）。
- **章の中の秒**：章の mp4 の頭からの秒。3D のコマ i は章の i/24 秒。
- **通しの秒**：章を順につないだ時刻。章の長さはコマ数 ÷ 24（音の長さではない）。
- 章の中で時間を直したら（切る・のばす）、本編の秒 → 章の中の秒は `TE.out()`、逆は `TE.src()`。
- ユーザーの「5:04」は通しの秒。章の始まりを引いて章の中の秒にし、`TE.src()` で本編の秒へ戻してから、声・3D の予定と照らす。

## 4. 声
- Gemini 3.8 Flash TTS（`generativelanguage.googleapis.com`、ヘッダー `x-goog-api-key: $GEMINI_API_KEY`）、声 `Achernar`、指示 `style_gentle.txt`。24kHz で返る → 48kHz に直して使う。1 日の回数に上限がある（429 は待ってやり直し、1 日の上限なら止まる）。
- 読み間違いは `tts_text.json`（文の番号 → 読ませる文）で直してから作り直す。
- 置き方（`narration.place()`）：台本の仮の時刻に始める。前の声がはみ出すときは遅らせ、次の文にかかるときは前を最大 0.6 秒早める → それでも無理なら 1.08 倍まで詰める。文ごとの大きさは −20 dBFS にそろえる。
- **話が変わる文には台本に `gap_before: 0.78` を書く**（前の声の終わりから 0.78 秒あける）。置いたら `python3 narration.py --gaps` で 0.5 秒未満の間を一覧にし、話が変わる所が残っていないか見る。
- 字幕：`narration.srt()` が声に合わせた .srt（声の終わり +0.35 秒、次の字幕の 0.05 秒前まで）を書く → 各章で `subs_jp.expand()` が 25 字・2 行・声の区切りで何枚かに分ける。ASS は PlayRes 1280×720、スタイルは `subs_jp.STYLE_MAIN`。

## 5. 章の組み立て
- 3D の章（例 `templates/ep01/chapters/ch07_assemble.py`）：PC の記録（`*_log.json`：fps・frames・t0・cam・shots・points・events・parcel など）から、札・印の画面の位置を計算して重ねる（`overlay2d.proj`）。効果音は記録の出来事（昇降機・扉・着く・まるロボの step/land）から置く。曲は拍の頭でくり返す。声は `narration.mix_voice(bus, t0, P=…)`。
- 本番は `MARU_STREAM=1`：コマを PNG に書かず、ffmpeg に直接流す（1080p の PNG はディスクに入らない）。`MARU_FINAL=1` で確認用の札（場面名・注記）を消す。`MARU_CRF=16`。
- 2D の章（例 `ch05_diagram.py`）：時刻は台本の文の時刻から決める（`at(n, "言葉")` で文の中の言葉の時刻）。並列で描く `ch05_frames_par.py`。
- まるロボの足音：3D を描いたのと同じ予定（`chNN_robot.plan_*()`）を作り直し、`pl.events` の step/step_turn/takeoff/land に音を置く。予定が同じか、記録の `robot`（根元の位置）と比べて確かめる（EP01 では差 0.0005m）。
- 差し込み（EP01 第6章）：別の場面のコマを使って場面を足すときは、コマの番号の写し（出すコマ → 元のコマ）を作り、声・字幕・効果音は `TimeEdit` の「止めてのばす」で後ろへずらす。曲は 3.08 秒の倍数にするか、差し込みの終わりで合わせ直す。

## 6. 時間の直し（`timeedit.py`）
```python
import timeedit
TE = timeedit.TimeEdit([(208.30, 208.30 + 83/24, 0.0),   # 切る（止まった絵・くり返す模様）
                        (374.95, 374.95, 0.55),          # その時刻で止めて 0.55 秒のばす（声の前に間を足す）
                        (556.90, 563.80, 5.90)])         # 6.9 秒を 5.9 秒に（動いている所を少し速く）
frame = render(TE.src(t_out))          # 出す時刻 t_out のコマは、元の時刻 TE.src(t_out) で描く
P2 = TE.place(placement)               # 声：始まりを写す（長さはそのまま）
subs = TE.subs(srt_lines)              # 字幕：始まりを写す（次の字幕の 0.05 秒前まで）
t_sfx = TE.out(t_event)                # 効果音：出来事の時刻を写す（切った所の音は出さない）
n_out = round((TE.out(T_end) - T_start) * 24)
```
- 切る前に、切る区間の最初と最後のコマが同じ（差 0）か確かめる。

## 7. 音の大きさ
- 効果音は章の中で一番大きい音が 0.45〜0.55 になるようにそろえ、曲を足し、`mix_voice(bus_peak=0.5, duck_db=6)` で全体の山を 0.5 にそろえて声を足す（声のある所は曲・効果音を 6 dB 下げる。上がり 0.12 秒・下がり 0.35 秒）。
- そろえる処理のあとで上げた分だけ残る。特定の音を上げるときは、そろえたあとに足す（EP01 の「ドン」）。
- 章の書き出し：loudnorm（I=-16）で AAC 160k。通し：一度測って −14 LUFS まで同じだけ足し、alimiter で −1.5 dBFS。

## 8. PC での本番描画と受け取り
- PC：Windows・RTX 3050・Blender 4.3.2。`C:\marurobo\` に `bluetooth_handoff_restored`（素材）と `marurobo_tools`（この一式。`assets/pc_kit` の写し）。
- 手順は PowerShell に貼る 1 行（`run_pc_render.ps1`）。3 本同時、100 コマずつの mp4（`<名前>_0001-0100.mp4`）。終わると `C:\marurobo\marurobo_render\<章>` にまとまり、Google ドライブの `marurobo_render` へコピー。
- こちらは `python3 -I tools/drive_watch.py ch07:35 ch08:6`（章:本数）で見張り、そろったら `dl_pc/<章>/` に落として 1920×1080・コマ数を確かめる。
- EEVEE。モーションブラーはシャッター 0.5（カメラが飛ぶカットはブレる → cutfix）。

## 9. 通し・点検・測り方
- `bash tools/concat_full.sh stage/final/full_1080.mp4 章1.mp4 章2.mp4 …` → `bash tools/final_qa.sh stage/final/full_1080.mp4 章1.mp4 …` → `work_full/qa_joins.jpg` を目で見る。
- 声の前の間の測り方：16kHz モノラルにして 10ms ごとの大きさ（dB）を出し、−42 dB 未満が 0.25 秒以上続く所を並べる（直す前と後を並べて数字で報告）。
- 文字・字幕は `subs_check.py 章.mp4 章.ass 出力フォルダ`（字幕 1 枚ごとの画面の下半分の一覧）。
- 直した所だけの確認動画：通しから区間を切り出し、左上に「前の時刻 → 今の時刻・直したこと」を出してつなぐ（見本 `templates/ep01/build/fix_reel.py`、14MB に収める 2 パス）。
