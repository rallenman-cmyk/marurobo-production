# 12本目：全部のカットで、カメラが物の中に入っていないかを数える（camcheck.py を 4 本ずつ並べて）
# bash camcheck_all.sh <blender> <出力フォルダ>
B=$1; OUT=$2; mkdir -p $OUT
cd "$(dirname "$0")"
python3 -c "import json;print(' '.join(json.load(open('clips.json'))))" | tr ' ' '\n' | xargs -P 4 -I{} bash -c "TEX12=\$TEX12 timeout 900 '$B' -b --factory-startup --python camcheck.py -- {} > '$OUT/{}.log' 2>&1; grep -h 'CAMCHECK' '$OUT/{}.log' || echo 'CAMCHECK {} 失敗'"
echo CAM_ALL_DONE
