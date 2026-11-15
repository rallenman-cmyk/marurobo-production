# 集めた検索結果とチャンネルの数字から、題材ごとの需要と「当たり動画」をまとめる
# python3 analyze.py <calib.json> <cand.json> <disc.json> <channels.json> <出力.md>
import json, re, sys, statistics

calib, cand, disc, chans, outp = sys.argv[1:6]
C = json.load(open(chans))
JA = re.compile(r"[ぁ-んァ-ン一-龥]")

# 題材ごとに、検索語と「関係ある動画」を見分ける言葉
TOPICS = {
    "calib": [
        ("3本目 会話と広告", ["スマホ 会話 盗聴 広告", "スマホ 聞いてる 広告 なぜ"], r"(盗聴|聞いて|聞かれ|会話).*(広告)|広告.*(盗聴|聞いて|聞かれ|会話)"),
        ("4本目 私はロボットではありません", ["私はロボットではありません 仕組み", "reCAPTCHA 仕組み"], r"ロボットではありません|ロボットじゃない|reCAPTCHA|CAPTCHA|キャプチャ"),
        ("5本目 ロボット掃除機", ["ロボット掃除機 仕組み", "ルンバ 仕組み 地図"], r"(ロボット掃除機|ルンバ).*(仕組み|しくみ|なぜ|地図|マップ)|(仕組み|しくみ|なぜ).*(ロボット掃除機|ルンバ)"),
        ("6本目 配膳ロボット", ["配膳ロボット 仕組み", "ネコ型 配膳ロボット"], r"配膳ロボ|ネコ型ロボ|猫型ロボ|BellaBot|ベラボット"),
        ("7本目 キーボード", ["キーボード 配列 なぜ", "QWERTY 配列 理由"], r"(QWERTY|ABC順|配列).*(なぜ|理由|歴史)|(なぜ|理由).*(QWERTY|ABC順)"),
    ],
    "cand": [
        ("BS 再起動で直る", ["再起動 なぜ 直る", "パソコン 再起動 理由"], r"再起動.*(なぜ|理由|直る)|(なぜ|理由).*再起動"),
        ("BT USB が差さらない", ["USB 向き なぜ 刺さらない", "USB 3回 裏返す"], r"USB.*(向き|刺さ|挿さ|裏|逆)"),
        ("BU 保存はフロッピー", ["保存 アイコン フロッピー なぜ", "パソコン アイコン 由来"], r"(フロッピー|アイコン).*(なぜ|由来|理由|保存)|保存.*(アイコン|マーク)"),
        ("BV Ctrl+C/V", ["Ctrl+V なぜ V", "コピー 貼り付け ショートカット 由来"], r"(Ctrl|コピー|ペースト|貼り付け).*(由来|なぜ|理由|V)"),
        ("BW シャッター音", ["スマホ シャッター音 日本 なぜ", "カメラ 音 消せない 理由 日本"], r"シャッター音|カメラ.*音.*(消せ|なぜ)"),
        ("BX ○×の決定ボタン", ["決定ボタン ○ × 逆 なぜ", "PS5 ×決定 理由"], r"(決定|○|×|まる|バツ).*(逆|なぜ|理由|ボタン)"),
        ("BY アプリの更新", ["アプリ アップデート 多い なぜ"], r"(アップデート|更新).*(なぜ|理由|多い)"),
        ("BZ 電源マーク", ["電源ボタン マーク 意味"], r"電源.*(マーク|記号)"),
        ("CA ファンがうるさい", ["パソコン ファン うるさい 理由"], r"ファン.*(うるさ|音)"),
        ("CB アットマーク", ["アットマーク 由来"], r"アットマーク|@.*由来"),
    ],
}


def secs(l):
    if not l:
        return 0
    p = [int(x) for x in l.split(":")]
    s = 0
    for x in p:
        s = s * 60 + x
    return s


def enrich(v):
    c = C.get(v.get("channel_id") or "", {})
    med = c.get("median")
    v["subs"] = c.get("subs")
    v["median"] = med
    v["ratio"] = round(v["views"] / med, 1) if (v.get("views") and med) else None
    return v


def topic_rows(path, topics):
    d = json.load(open(path))["queries"]
    rows = []
    for name, qs, pat in topics:
        seen = {}
        for q in qs:
            for v in d.get(q, []):
                if v["id"] in seen or not v.get("views") or not JA.search(v["title"]) or secs(v["length"]) < 120:
                    continue
                if re.search(pat, v["title"], re.I):
                    seen[v["id"]] = enrich(dict(v))
        vs = sorted(seen.values(), key=lambda x: -x["views"])
        rows.append((name, vs))
    return rows


def fmt(n):
    if n is None:
        return "—"
    return f"{n/10000:.1f}万" if n >= 10000 else f"{n:,}"


out = ["# YouTube（日本語）の需要調べ", "", f"取った日：{json.load(open(calib))['fetched_at'][:10]}（YouTube の検索結果とチャンネルの動画ページから。数字はその日のスナップショット）",
       "「ふだん」＝そのチャンネルの最近の動画（最大30本）の再生回数の中央値。「倍」＝その動画の再生 ÷ ふだん。", ""]
for key, title in (("calib", "採用した回（ものさし）"), ("cand", "10回目の候補")):
    out += [f"## {title}", "", "| 題材 | 関係ある動画の数 | 一番見られた動画 | 再生 | 公開 | チャンネル登録者 | ふだん | 倍 | 2番目の再生 |", "|---|---|---|---|---|---|---|---|---|"]
    for name, vs in topic_rows(calib if key == "calib" else cand, TOPICS[key]):
        if not vs:
            out.append(f"| {name} | 0 | — | — | — | — | — | — | — |")
            continue
        t = vs[0]
        second = fmt(vs[1]["views"]) if len(vs) > 1 else "—"
        out.append(f"| {name} | {len(vs)} | {t['title'][:40]}（{t['channel']}） | {fmt(t['views'])} | {t['published']} | {fmt(t['subs'])} | {fmt(t['median'])} | {t['ratio'] or '—'} | {second} |")
    out.append("")

# 掘り出し：なぜ・仕組み・理由の動画で、ふだんより大きく伸びた物
d = json.load(open(disc))["queries"]
pool = {}
for src in (calib, cand):
    for vs in json.load(open(src))["queries"].values():
        for v in vs:
            pool.setdefault(v["id"], v)
for vs in d.values():
    for v in vs:
        pool.setdefault(v["id"], v)
hits = []
for v in pool.values():
    if not v.get("views") or not JA.search(v["title"]) or secs(v["length"]) < 120:
        continue
    if not re.search(r"なぜ|仕組み|しくみ|理由|由来|正体|謎", v["title"]):
        continue
    enrich(v)
    if v["views"] >= 50000 and v["ratio"] and v["ratio"] >= 3:
        hits.append(v)
hits.sort(key=lambda x: -x["ratio"])
out += ["## 当たり動画（なぜ・仕組み・理由の題で、5万回以上・ふだんの3倍以上）", "", "| 倍 | 再生 | 公開 | 題 | チャンネル（登録者・ふだん） |", "|---|---|---|---|---|"]
for v in hits[:60]:
    out.append(f"| {v['ratio']} | {fmt(v['views'])} | {v['published']} | {v['title'][:60]} | {v['channel']}（{fmt(v['subs'])}・{fmt(v['median'])}） |")
open(outp, "w").write("\n".join(out) + "\n")
print("hits", len(hits))
