# 19本目（16本目から）：下書き（480×270・4 サンプル・3 コマおき）を全カット描く。4 本ずつ並列
# bash render_all.sh <blender> <出力フォルダ> [カット名…]
B=$1; OUT=$2; shift 2
cd "$(dirname "$0")"
LIST=${@:-$(TEX19=$TEX19 "$B" -b --factory-startup --python scenes19.py -- --list 2>/dev/null | python3 -c "import json,sys,re
m=re.search(r'\{.*\}',sys.stdin.read()); d=json.loads(m.group(0)); print(' '.join(sorted(d,key=lambda k:-(d[k][1]-d[k][0]))))")}
one(){
  if [ -f "$OUT/$1/_done" ]; then echo "skip $1"; return; fi
  mkdir -p "$OUT/$1"
  if TEX19=$TEX19 timeout 2400 "$B" -b --factory-startup --python scenes19.py -- "$1" "$OUT/$1" --samples 4 --res 480 270 --step 3 > "$OUT/$1/r.log" 2>&1; then
    touch "$OUT/$1/_done"; echo "done $1 $(ls $OUT/$1/*.png 2>/dev/null | wc -l)"
  else
    echo "FAIL $1"; grep -A4 "Error\|Traceback" "$OUT/$1/r.log" | tail -5
  fi
}
export -f one; export B OUT TEX19
printf "%s\n" $LIST | xargs -P 4 -I{} bash -c 'one "$@"' _ {}
echo ALL_RENDERED
