# 動画レビューに上げる前の関所（2026-11-20、7本目 v7 のコメント 43 件の振り返り。決まりを書いても守れていなかったので、守らないと上げられない形にした）
#   python3 pre_upload_gate.py <回のフォルダ> <版の番号> <通し.mp4> <字幕.ass>
#   ① 字幕の数：1 枚 2 秒未満・1 秒 8 字こえ・1 行 25 字こえ・3 行以上（Main の字幕だけ）が 1 枚でもあれば不合格
#   ② 点検表 <回のフォルダ>/点検_v<番号>.md（ひな形：references/点検表_ひな形.md）：
#      全部の項目の「結果：」が書いてあり、「まだ・未・あとで・確かめていない・見ていない」がなく、「OK・問題なし・見た」だけで終わっていないこと
#      例外（2026-11-21 3本目 ユーザーの選択「ためだけ 2 秒未満を許す」）：<回のフォルダ>/字幕_ため.json（字幕の文字のリスト）にある「……」でためる短い 1 枚は、1 秒以上なら 2 秒未満でよい
#   ③ 字幕と声のずれ（2026-11-21 7本目 ユーザー「なんでテロップのタイミングまだ治ってないの」）：scripts/subs_sync_check.py が作る <字幕.ass>.sync.json が、
#      この字幕のもので、「声の途中で切り替わる」0 枚・「聞き取りが読みと合わない」0 枚（聞き取りを渡していないときも不合格）
#   合格なら <通し.mp4>.gate.json（動画の sha256・字幕の数・時刻）を作る。vr_version.py build は、この印がないと止まる
import os, re, sys, json, hashlib, statistics, datetime

MIN_DUR, MAX_CPS, MAX_LEN = 2.0, 8.0, 25
NG = ("まだ", "未", "あとで", "後で", "確かめていない", "見ていない", "していない")
EMPTY = re.compile(r"^(ok|ＯＫ|問題なし|見た|確認した|大丈夫|済み?)[。.]?$", re.I)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def subs(ass):
    L = []
    for l in open(ass, encoding="utf-8"):
        if not l.startswith("Dialogue"): continue
        p = l.split(",", 9)
        if p[3] != "Main": continue
        f = lambda x: sum(float(v) * m for v, m in zip(x.split(":"), (3600, 60, 1)))
        L.append((f(p[1]), f(p[2]), re.sub(r"\{.*?\}", "", p[9].strip())))   # 行の分け目（\N）は残す（1 行ごとに数える）
    return sorted(L)


def main():
    ep, num, mp4, ass = sys.argv[1], sys.argv[2].lstrip("v"), sys.argv[3], sys.argv[4]
    bad = []
    L = subs(ass)
    tp = os.path.join(ep, "字幕_ため.json")
    TAME = set(json.load(open(tp, encoding="utf-8"))) if os.path.exists(tp) else set()
    for a, b, t in L:
        # 2026-11-20 ユーザー（6本目）「2 行のまま・道具を決まりに合わせる」：決まりは「1 行 25 字まで」。2 行の字幕は 1 行ごとに数え、3 行以上は外
        rows = t.split("\\N"); t = "".join(rows)
        n = len(t.replace(" ", "")); d = b - a
        mn = 1.0 if t in TAME else MIN_DUR                                     # ための 1 枚は 1 秒以上でよい（ユーザーの選択）
        if d < mn - 0.01 or n / d > MAX_CPS or max(len(r.replace(" ", "")) for r in rows) > MAX_LEN or len(rows) > 2: bad.append("  字幕 %6.2f 秒  %.2f 秒  %.1f 字/秒  %d 字  %s" % (a, d, n / d, n, t))
    print("字幕 %d 枚（いちばん短い %.2f 秒・まん中 %.2f 秒）。決まりの外：%d 枚" % (len(L), min(b - a for a, b, _ in L), statistics.median(b - a for a, b, _ in L), len(bad)))
    for x in bad: print(x)
    sheet = os.path.join(ep, "点検_v%s.md" % num)
    miss = []
    if not os.path.exists(sheet):
        miss.append("点検表がない：%s（references/点検表_ひな形.md を写して書く）" % sheet)
    else:
        lines = open(sheet, encoding="utf-8").read().split("\n")
        for i, l in enumerate(lines):
            if not l.strip().startswith("- ["): continue
            item = l.strip()[5:].strip()
            res = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not res.startswith("結果："): miss.append("結果の行がない：" + item); continue
            r = res[3:].strip()
            if "道具が書く" in r: continue
            if not r: miss.append("結果が空：" + item)
            elif any(w in r.replace("未満", "") for w in NG) and not r.startswith("なし（"): miss.append("確かめていない言葉がある：" + item + " → " + r)
            elif EMPTY.match(r): miss.append("何をどれだけ見たかがない：" + item + " → " + r)
    # ③ 字幕と声のずれ
    sp = ass + ".sync.json"
    if not os.path.exists(sp):
        miss.append("字幕と声のずれを測っていない：python3 scripts/subs_sync_check.py <字幕.ass> <placement.json> <声のフォルダ> <字幕を聞き取った.json> を動かす")
    else:
        sy = json.load(open(sp, encoding="utf-8"))
        if sy.get("ass_sha256") != sha(ass): miss.append("字幕と声のずれの測りが、いまの字幕のものでない（字幕を作り直したら、測り直す）")
        if sy.get("outside", 1): miss.append("声の途中で切り替わる字幕が %d 枚ある" % sy.get("outside"))
        if sy.get("heard_bad") is None: miss.append("字幕 1 枚ずつの声の聞き取りをしていない（sub_hear.py などの結果を subs_sync_check.py に渡す）")
        elif sy["heard_bad"]: miss.append("聞き取りで読みと合わない字幕が %d 枚ある" % sy["heard_bad"])
        else: print("字幕と声：声の途中で切り替わる 0 枚・聞き取りで読みと合わない 0 枚（%d 枚を聞いた）" % sy.get("heard", 0))
    for x in miss: print("  " + x)
    if bad or miss:
        print("不合格：上の所を直してから、もう一度通す（動画レビューには上げられない）"); sys.exit(1)
    st = {"mp4": os.path.basename(mp4), "sha256": sha(mp4), "subs": len(L), "subs_bad": 0, "sheet": os.path.relpath(sheet),
          "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(st, open(mp4 + ".gate.json", "w"), ensure_ascii=False, indent=1)
    print("合格：%s を作った" % (mp4 + ".gate.json"))


if __name__ == "__main__":
    main()
