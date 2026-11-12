# PC 用の一式（QR回）

PC（Blender 4.3.2）で本番の 3D を描くための、QR回の分。PC には `marurobo_tools.zip`（この中身＋1本目の共通部品）を渡す。
- `qr/`：QR回の舞台と動き。共通の部品は `plan_util.py`（白いフチとマスで立つ高さを変える置き直しなど）。3章は `c3_plan.py`・`qr_c3_world.py`。4章は `c4_plan.py` と、舞台ごとに `qr_c4_crates.py`（数字の空間）・`qr_c4_world.py`（大地）・`qr_c4_factory.py`（工場）。4章の T35・T28（スマホの肩越し）は冒頭の描画を使い回す。2章は `c2_plan.py`（時刻とまるロボの動き）・`qr_c2_world.py`（中の世界）・`qr_c2_table.py`（卓上）。`c1_timeline.py`（1章の時刻。v18 から台本 v2.0 の `c1_v20_times.json` を読む）・`c1_plan.py`（まるロボの動き）・`qr_c1_*.py`（場面）・`op_*`（冒頭）
- `run_pc_render.ps1`：PC で 1 行貼ると、100 コマずつ 3 本同時に描いてドライブへ送る
- `README_PC.md`：ユーザー向けの手順（いまやること）
- 共通の部品（`kit/`・`maru/` など）は `episodes/ep01_earphone/stage/marurobo_tools/` にある
- 試し描き（こちらの container）：`blender -b --factory-startup --python qr/qr_c1_world.py -- --out DIR --res 640 360 --samples 4 --standin 1 --still 400,2000`
