# 12本目：書き起こし（heard_kana.json）と、読ませた文（tts）をひらがなにそろえて比べ、ちがう所を出す
#   pykakasi で漢字をひらがなに（読みの候補が 1 つなので、ちがって出た所は耳で聞いて決める）。長音「ー」・小さな字・句読点は比べない
# MARU_WORK=<作業フォルダ> python3 kana_diff.py [しきい値=0.93]
import os, sys, json, re, difflib
import pykakasi
W = os.environ["MARU_WORK"]; H = json.load(open(W + "/stage/voice/achernar/heard_kana.json", encoding="utf-8"))
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.93
kk = pykakasi.kakasi()
def hira(s):
    s = "".join(x["hira"] for x in kk.convert(s))
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    s = re.sub(r"[、。？！「」…・ 　\s,.?!]", "", s)
    s = s.replace("ー", "").translate(str.maketrans("ぁぃぅぇぉっゃゅょ", "あいうえおつやゆよ"))
    s = re.sub(r"(.)う", lambda m: m.group(1) + ("う" if m.group(1) not in "おこそとのほもよろごぞどぼぽょ" else ""), s)   # 「どう」と「どー」をそろえる
    return s.replace("を", "お").replace("は", "わ")
bad = []
for h in H:
    a, b = hira(h["tts"]), hira(h["kana"])
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if r < TH:
        bad.append((round(r, 3), h["no"], h["id"]))
        print("%.3f %s %s\n   台本: %s\n   聞く: %s" % (r, h["no"], h["id"], a, b))
print("ちがう所", len(bad), "／", len(H))
