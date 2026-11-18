# 文ごとの絵コンテ表（3本目 v10。CLAUDE.md「描く前に、文ごとに見せる物・動き・音を決めた表を作り、それに合わせて作る」）
#   作り方：
#     PLAN_DUMP=<dir> blender -b --factory-startup --python scenes_all.py -- <場面> <dir> 4 --blend   （全部の場面と s07s08_gate.py の gate）
#     BOARD_DUMP=<dir>/board.json python3 assemble.py <fonts> x.mp4 <絵のフォルダ…>
#     python3 make_board_table.py <dir> ../絵コンテ表_v10.md
#   列：文・秒・言うこと｜カット（カメラの場所 → 見る所・レンズ）｜まるロボの動き｜札・差し込み・小窓｜音
import glob, json, os, sys
D, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
WT = json.load(open(os.path.join(HERE, "..", "voice", "word_times.json"), encoding="utf-8"))
plans = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(D, "*_plan.json")))]
plans = [p for p in plans if p["key"] not in ("s05i", "s22i", "walktest")]
B = json.load(open(os.path.join(D, "board.json")))
JP = dict(go="歩く", face="向く", look="見上げ・見下ろし", hop="跳ねる", hops="跳ねる", roll="首をかしげる", pitch="前後に傾く", light="光る", blink="まばたき",
          surprise="驚く", nod="うなずく", shake="首を振る", think="考える", peer="のぞき込む", sigh="ほっとする", look_around="見回す", confused="首をかしげる（？）",
          present="見せる", greet="あいさつ", awe="見とれる", groove="ノる", rest="休む", wake="起きる", stagger="よろける", bonk="ぶつかる", move="走る・下がる", jump="跳び乗る")
SND = dict(pop="泡がはじける", bubble_in="泡が出る", land="着地", jump="跳ぶ", pipo="ピポ", whoosh="ヒュッ", clatter="ガチャン", hat="帽子", towel="タオル", dive="吸い込まれる",
           spot="照明が点く", spot_off="照明が消える", win="当たり", rise="上がる", lamp="ランプ", pop_ui="広告が出る", beep_surprise="ピロッ（驚く）", beep_yes="ピッピッ（うなずく）",
           beep_no="ブブッ（首を振る）", beep_think="ポッ…（考える）", ding="ピン（ひらめく）", sigh="ほっ", beep_question="ピポ？（かしげる）", beep_wow="ほぉ〜（見とれる）", zoom="ズーム",
           beep_happy="ピロリ（喜ぶ）", beep_hello="ピポッ（あいさつ）", step="足音")
def plan_at(t):
    c = [p for p in plans if p["t0"] - 0.01 <= t < p["t1"]]
    return c[0] if c else None
def cut_at(p, t):
    for a, b, l0, g0, lens in p["shots"]:
        if a - 0.01 <= t < b: return (a, b, l0, g0, lens)
    return None
keys = sorted(WT, key=lambda k: WT[k]["start"])
rows = ["# 3本目 v10 絵コンテ表（文ごと）", "", "道具で書き出した表（`anim/make_board_table.py`）。描く前にこれで、文ごとに「見せる物・動き・音」を決め、描いたあとに絵と見比べる。", "",
        "| 文 | 秒 | 言うこと | カット（カメラ → 見る所・レンズ） | まるロボの動き | 札・差し込み・小窓 | 音 |", "|---|---|---|---|---|---|---|"]
for k in keys:
    v = WT[k]; a, b = v["start"], v["end"]; p = plan_at(a + 0.05)
    cut = "—"; mv = []; snd = []
    if p:
        cs = [c for c in p["shots"] if c[0] < b and c[1] > a]
        cut = "<br>".join("%s：(%.1f, %.1f, %.1f) → (%.1f, %.1f, %.1f)・%dmm" % ((p["key"],) + tuple(c[2]) + tuple(c[3]) + (c[4],)) for c in cs[:3]) or p["key"]
        for m in p["maru"]:
            for t, kd, ar in m:
                if a - 0.6 <= t < b + 0.3:
                    extra = "" if not ar else "（" + "・".join("%s=%s" % (x, y) for x, y in ar.items()) + "）"
                    mv.append("%.1f %s%s" % (t, JP.get(kd, kd), extra))
        for t, kd in p["events"]:
            if a - 0.3 <= t < b + 0.3 and kd != "step": snd.append("%.1f %s" % (t, SND.get(kd, kd)))
    ins = ["%.1f〜%.1f 差し込み：%s" % (x[0], x[1], (x[3] if isinstance(x[3], str) else ("%s の %s 秒" % tuple(x[3]) if isinstance(x[3], list) else "%.1f 秒の絵" % x[3]))) for x in B["ins"] if x[0] < b and x[1] > a]
    ov = ["%.1f 札：%s" % (o[0], "・".join(o[3]) if o[3] else o[2]) for o in B["ov"] if a - 0.3 <= o[0] < b + 0.3]
    pip = ["%.1f 小窓：%s" % (q[0], q[3]) for q in B["pips"] if a - 0.3 <= q[0] < b + 0.3]
    rows.append("| %s | %.1f | %s | %s | %s | %s | %s |" % (k, a, v["text"].replace("|", "｜"), cut, "<br>".join(mv) or "—", "<br>".join(ins + ov + pip) or "—", "<br>".join(snd) or "—"))
open(OUT, "w", encoding="utf-8").write("\n".join(rows) + "\n")
print(len(keys), "文")
