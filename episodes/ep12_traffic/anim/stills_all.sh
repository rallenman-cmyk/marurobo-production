# 17本目：全部のカットの試しの絵（カットごとに 2 枚）を描く。16本目の決まり（全部描く前に、カットごとに 2 枚だけ試しに描く）
# bash stills_all.sh <blender> <出力フォルダ> <ジョブの表（カット名 秒,秒）>
B=$1; OUT=$2; JOBS=$3
cd "$(dirname "$0")"
one(){ mkdir -p "$OUT/$1"; TEX12=$TEX12 timeout 900 "$B" -b --factory-startup --python scenes.py -- "$1" "$OUT/$1" --samples 4 --res 480 270 --stills "$2" > "$OUT/$1/r.log" 2>&1 || echo "FAIL $1"; }
export -f one; export B OUT TEX12
cat "$JOBS" | xargs -P 4 -L 1 bash -c 'one "$@"' _
echo STILLS_DONE
