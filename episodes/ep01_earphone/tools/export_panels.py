# 絵コンテを 1 コマずつの画像（960×540 JPEG）と一覧（JSON）にする：スマホで縦に流して見るページ用
import json, os, sys
from PIL import Image
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; ST = SC + "/stage"
OUT = SC + "/review_page/img"; os.makedirs(OUT, exist_ok=True)
TL = {e["no"]: e for e in json.load(open(ST + "/script/script_v2_timed.json", encoding="utf-8"))}
def line_at(t):
    best = None
    for n, e in sorted(TL.items()):
        if e["start"] - 0.05 <= t <= e["end"] + 0.3: best = e
    return best
man = {}
# ---- 第5章：図を今の作り方で描き直す
sys.path.insert(0, ST + "/ch03"); sys.argv = ["x"]; os.chdir(ST + "/ch03")
import ch05_diagram as c5
NOTE5 = [(430.0, "頭：第3章の終わりと同じ「二つの疑問」"), (436.0, "① に「解けた ✓」、② を強く"), (446.0, "図へ（自分の組・隣の組）"), (450.5, "真ん中に窓の列（チャンネル）"),
         (453.8, "二組とも同じ窓を照らす"), (457.6, "自分の組だけなら、届いて読める"), (468.4, "同じタイミングで、二組の荷物が同じ窓で重なる"), (476.5, "二つの荷物は窓でぶつかって落ちる。受け取る側に届かない（×）"),
         (481.0, "ほかの電波が邪魔をする"), (486.0, "つないだ相手は分かっている ✓"), (488.8, "でも、データは届かない ×（落ちた荷物）"), (494.6, "隣の曲になるのではなく、自分の曲が途切れる"),
         (508.5, "自分の組だけに"), (512.5, "窓を三つに"), (521.8, "いまは、両方ともここ"), (527.0, "スマホだけ次の窓へ"), (532.0, "窓2の先に受け取る光がない → 荷物は落ちる ×"),
         (535.0, "イヤホンは元の窓のまま"), (544.6, "二台でそろえて変える → 届く"), (546.3, "次は、ここ"), (550.5, "順番とタイミングを合わせる（二台の下に同じ順番）"),
         (555.0, "つないだときに、そろえた"), (566.8, "窓の正体は周波数（窓の中に波）"), (570.0, "1秒間に振動する回数"), (576.0, "実際は数十の窓"),
         (582.0, "二台で足並みをそろえて次々に（実際はもっと速い）"), (589.6, "隣の組が戻る"), (594.0, "隣も、その組の順番で切り替える"), (599.95, "同じ窓で重なった"),
         (600.6, "「あ、ここでは重なりました」：ぶつかった荷物は落ちる"), (603.5, "それでも次へ切り替わる"), (617.3, "うまく通信できない窓（ざらざら）に当たると、壊れて落ちる"), (621.0, "その窓を使う候補から外す"),
         (623.5, "外した窓の地図を二台で共有"), (633.0, "外した窓を避けて、そろえて切り替える"), (642.4, "それでも、たまに重なって自分の荷物が落ちる"), (648.0, "落ちた荷物に「？」：なかったことになる？ → 第6章（まるロボの配達）へ")]
man["ch05"] = []
for j, (t, note) in enumerate(NOTE5):
    fn = "c5_%02d.jpg" % (j + 1); c5.frame(t).resize((960, 540), Image.LANCZOS).save(os.path.join(OUT, fn), quality=82)
    e = line_at(t); man["ch05"].append(dict(img=fn, t=t, note=note, line=e["text"] if e else ""))
# ---- 第6章・第7章：絵コンテの作り方（tools/ch06_storyboard.py・ch07_storyboard.py）の panel() を使う
for key, path in (("ch06", SC + "/tools/ch06_storyboard.py"), ("ch07", SC + "/tools/ch07_storyboard.py")):
    src = open(path, encoding="utf-8").read(); src = src[:src.index("f1 = ImageFont.truetype")]
    g = {"__name__": "panels"}; exec(compile(src, path, "exec"), g)
    man[key] = []
    for j, (n, ln) in enumerate(g["PANELS"]):
        fn = "%s_%02d.jpg" % (key[2:].replace("0", "c", 1) if False else key, j + 1)
        g["panel"](n).resize((960, 540), Image.LANCZOS).save(os.path.join(OUT, fn), quality=82)
        man[key].append(dict(img=fn, t=TL[ln]["start"], note=g["NOTE"][n], line=TL[ln]["text"]))
json.dump(man, open(SC + "/review_page/panels.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in man.items()})
