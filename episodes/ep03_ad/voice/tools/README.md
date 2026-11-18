# 声の高さをそろえる（3本目 v10）
- `line_pitch.py <声.wav> ../word_times.json`：文ごとの高さ。中央値より 20Hz 以上高い文に「← 高い」。
- `even_pitch.py <入.wav> ../word_times.json <出.wav> [上限 Hz=12] [文ID=上限]`：高い文を中央値＋上限まで下げる（長さは変えない）。2 回通すと残りも下がる。
- `check_shifted.py <元.wav> <直した.wav> ../word_times.json 文ID…`：書き起こしと音のゆがみを AI に聞く。
- v10 の作り方：even_pitch を 2 回（07-05b=18）→ 07-05b は下げると「音の泡も」が聞き取れなくなったので、声を作り直して（4 本作り、224Hz・4.52 秒の 3 本目）同じ長さに縮め、同じ大きさで差し替え（作業フォルダ animatic_tmp/retake_07-05b.wav）。できあがりは animatic_tmp/voice_v10.wav。組み立て（assemble.py）は、あればこれを使う。
