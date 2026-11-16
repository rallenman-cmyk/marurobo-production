# 7本目：確認用に全部のクリップを描く（480×270・8 サンプル・3 コマおき）。長いクリップから、4 本ずつ並べて（1 本 1 スレッド）
# bash render_all.sh <blender> <出力フォルダ> [クリップ名…]   止まった所から続けるときは、終わったクリップ（_done の印）をとばす
B=$1; OUT=$2; shift 2
cd "$(dirname "$0")"
LIST=${@:-$(python3 -c "import json;c=json.load(open('clips.json'));print(' '.join(sorted(c,key=lambda k:-(c[k][1]-c[k][0]))))")}
# キーの字のフォント：KEY_FONT=<Noto Sans JP Bold の ttf> を付けて動かす（無いと Blender の英字フォント）
one(){ [ -f "$OUT/$1/_done" ] && { echo "skip $1"; return; }
  mkdir -p "$OUT/$1"; timeout 14400 "$B" -b --factory-startup -t 1 --python scenes.py -- "$1" "$OUT/$1" --samples 8 --res 480 270 --step 3 > "$OUT/$1/render.log" 2>&1 \
   && touch "$OUT/$1/_done" && echo "done $1 $(ls $OUT/$1/*.png | wc -l)" || { echo "FAIL $1"; grep -A5 Traceback "$OUT/$1/render.log" | tail -4; }; }
export -f one; export B OUT
printf "%s\n" $LIST | xargs -P 4 -I{} bash -c 'one {}'
echo ALL_RENDERED
