# 会話と広告の回：全部の場面（3D の試し描き・2D の場面）をつなぎ、札・効果音・声・字幕を重ねた通しを作る
# MARU_WORK=<作業フォルダ> python3 assemble.py <フォントのフォルダ> <出力.mp4> <コマのフォルダ>...（場面の log.json とコマがある所）
#   場面の順：PARTS。足りない場面は、絵コンテの絵（storyboard/board/bXX_nosub.png）で埋める
#   札：OVERLAYS（台詞の番号で出す時刻を決める）。字は 44 以上、字幕の帯（下から 196px）にかけない
#   効果音：各場面の log.json の events・steps から合成（sfx.py）。声のある所は 6 dB 下げる
#   BGM：bgm/bgm_bus.py（曲B を基本に、場面に合わせて曲C・D）。声のある所は 6 dB 下げる
#   REMUX=<前に作った通し.mp4> を付けると、絵は作り直さずに、その絵に新しい音（声・効果音・BGM）だけを付け直す
#   出力と一緒に <出力>_check.txt（点検の結果）を書く
import os, sys, json, glob, subprocess, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, "..")
W_ = os.environ["MARU_WORK"]
FONTS, OUT, DIRS = sys.argv[1], sys.argv[2], sys.argv[3:]
FONT = os.path.join(FONTS, "NotoSansJP_700Bold.ttf")
TAGF, BIGF = ImageFont.truetype(FONT, 46), ImageFont.truetype(FONT, 72)
NAVY = (20, 36, 72)
P = json.load(open(os.path.join(EP, "voice", "placement.json"), encoding="utf-8"))
SID = {e["no"]: e for e in json.load(open(os.path.join(EP, "voice", "script_v1_0.json"), encoding="utf-8"))}
T = {SID[p["no"]]["id"]: (p["start"], p["end"]) for p in P}
def s(i, k=0): return T[i][k]
sys.path.insert(0, HERE); import wordtime as _wt
def W(i, frag, o=0.0): return _wt.W(i, frag, o)    # 答えの札は、その言葉を言う瞬間に（QR回 v10 の指摘の横展開）
END = P[-1]["end"] + 2.0
PARTS = ["s00", "s01", "s02", "s03", "s04", "s05", "s06a", "s06b", "gate", "phone", "s09", "s10", "s11", "s12",
         "s13", "s14", "s15", "s16", "s17", "s18", "s19", "s20", "s21", "s22"]
BOARD = dict(s00=0, s01=1, s02=2, s03=3, s04=4, s05=5, s06a=6, s06b=6, gate=7, phone=8, s09=9, s10=10, s11=11, s12=12,
             s13=13, s14=14, s15=15, s16=16, s17=17, s18=18, s19=19, s20=20, s21=21, s22=22)
tmp = W_ + "/assemble_tmp"; os.makedirs(tmp, exist_ok=True)
SUB_TOP = 720 - 40 - 72 * 2 - 12   # 字幕の帯の上の端（2 行のとき）


# ---------------- 札（透明の 1280×720 の絵を作り、出す時刻のあいだだけ重ねる）
def tag_png(name, items):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im); boxes = []
    for it in items:
        kind = it[0]
        if kind == "tag":
            _, text, cx, cy, tail, big, col = (list(it) + [None, False, None])[:7]   # col：ふちの色（容疑者の色：赤・橙・紫）
            font = BIGF if big else TAGF
            bb = d.textbbox((0, 0), text, font=font); w, th = bb[2] - bb[0], bb[3] - bb[1]; h = th + 30
            cx = min(max(cx, w / 2 + 30), 1250 - w / 2)
            x0, y0, x1, y1 = cx - w / 2 - 22, cy - h / 2, cx + w / 2 + 22, cy + h / 2
            if tail:
                by = y1 - 2 if tail[1] > cy else y0 + 2
                d.polygon([(cx - 16, by), (cx + 16, by), tail], fill="white", outline=NAVY)
            d.rounded_rectangle([x0, y0, x1, y1], 18, fill="white", outline=col or NAVY, width=8 if col else 4)
            d.text((x0 + 22 - bb[0], cy - th / 2 - bb[1]), text, font=font, fill=NAVY)
            boxes.append((text, x0, y0, x1, y1, font.size))
        elif kind == "ring":
            _, cx, cy, rx, ry = it
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(255, 138, 42), width=8)
        elif kind == "img":
            _, path, x, y, w = it
            sub = Image.open(path).convert("RGBA"); sub = sub.resize((w, int(sub.height * w / sub.width))); im.alpha_composite(sub, (x, y))
        elif kind == "wifi":
            _, cx, cy, ends = it
            for r in (90, 62, 34): d.arc([cx - r, cy - r, cx + r, cy + r], 225, 315, fill="white", width=12)
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill="white")
            for x, y in ends:
                for k in range(0, 100, 10):
                    a = (cx + (x - cx) * k / 100, cy + (y - cy) * k / 100); b = (cx + (x - cx) * (k + 5) / 100, cy + (y - cy) * (k + 5) / 100)
                    d.line([a, b], fill="white", width=6)
        elif kind == "dark":   # 「6時間前」の前に画面を暗く
            d.rectangle([0, 0, 1280, 720], fill=(0, 0, 0, 150))
    p = os.path.join(tmp, "ov_%s.png" % name); im.save(p)
    return p, boxes


def picbubble(name, cx, cy, r, drawer):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white", outline=NAVY, width=4)
    # v8 見直し：左下の小さな丸（考えごとの印）は消す。他の回で「丸が何か分からない」（決まり）
    drawer(d, cx, cy, r)
    p = os.path.join(tmp, "ov_%s.png" % name); im.save(p); return p, []


def leaf(d, cx, cy, r):
    pts = [(cx + r * (0.75 if i % 2 == 0 else 0.35) * math.cos(math.radians(90 + i * 36)), cy - r * (0.75 if i % 2 == 0 else 0.35) * math.sin(math.radians(90 + i * 36))) for i in range(10)]
    d.polygon(pts, fill=(217, 71, 43)); d.line([(cx, cy), (cx, cy + r * 0.7)], fill=(120, 40, 20), width=6)


def tent(d, cx, cy, r):
    d.polygon([(cx - r * 0.6, cy + r * 0.45), (cx, cy - r * 0.55), (cx + r * 0.6, cy + r * 0.45)], fill=(233, 105, 44))
    d.polygon([(cx - r * 0.15, cy + r * 0.45), (cx, cy + r * 0.05), (cx + r * 0.15, cy + r * 0.45)], fill=(122, 46, 18))


SB = os.path.join(EP, "storyboard")
def _xframe(part, sec):
    """差し込み専用の場面（s05i・s22i。時刻は場面の外）の sec 秒にいちばん近い絵"""
    d = next((d_ for d_ in DIRS if os.path.exists(os.path.join(d_, part + "_log.json"))), None)
    if d is None: raise SystemExit("差し込み専用の場面 %s の絵がない（PC で描く一覧に入れる）" % part)
    lg = json.load(open(os.path.join(d, part + "_log.json")))
    fs = sorted(glob.glob(os.path.join(d, part + "_[0-9]*.png")) + glob.glob(os.path.join(d, part + "_[0-9]*.jpg")))
    return min(fs, key=lambda x: abs(lg["t0"] + int(os.path.basename(x)[len(part) + 1:-4]) / 24 - sec))


def night_inset():
    """22-03：夜中、まるロボがスマホでキャンプの動画を見ている（小窓）。v10「右上のまるロボの切り抜きも 3D に」(15:19)：3D の場面 s22i の絵を白いふちで囲む"""
    sub = Image.open(_xframe("s22i", 3.0)).convert("RGB").resize((408, 230), Image.LANCZOS)
    im = Image.new("RGBA", (420, 242), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 419, 241], 16, fill=(255, 255, 255, 255)); im.paste(sub, (6, 6))
    p = os.path.join(tmp, "inset22.png"); im.save(p); return p


def night_inset_2d():
    """（v9 まで）2D の小さな絵"""
    im = Image.new("RGBA", (420, 260), (12, 20, 38, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 419, 259], 18, outline=(255, 255, 255), width=5)
    d.rounded_rectangle([230, 60, 330, 230], 14, fill=(34, 38, 43)); im.paste(Image.open(os.path.join(SB, "tent.png")).convert("RGBA").resize((84, 112)), (238, 80))
    d.ellipse([70, 90, 200, 220], fill=(244, 246, 247)); d.ellipse([150, 125, 205, 180], fill=(33, 193, 179)); d.ellipse([168, 142, 188, 162], fill=(11, 39, 48))
    d.polygon([(205, 150), (238, 110), (238, 190)], fill=(207, 239, 255, 120))
    p = os.path.join(tmp, "inset22.png"); im.save(p); return p


SUS = ((229, 72, 77), (242, 153, 58), (140, 100, 200))   # 容疑者の色（台本：赤＝①マイク・橙＝②・紫＝③）。札のふちも同じ色に
OVERLAYS = []   # (始まり, 終わり, png, 札の箱)
def ov(a, b, name, items): p, bx = tag_png(name, items); OVERLAYS.append((a, b, p, bx))
def ovp(a, b, pb): OVERLAYS.append((a, b, pb[0], pb[1]))

ov(6.2, 7.19, "s00_6h", [("dark",), ("tag", "6時間前", 640, 300, None, True)])
# v4：冒頭の絵を引いた（テント 3 枚が見える）ので、名札・吹き出しの場所を合わせた
ov(s("01-01"), s("01-03", 1), "s01_names", [("tag", "ハルさん", 290, 470, None, False, (62, 124, 177)), ("tag", "ソラさん", 1010, 470, None, False, (229, 140, 90))])   # v4「どっちがハルでどっちがソラか」：服の色のふちの名札
# v5「吹き出しの位置高すぎる」(0:11)・v7「しっぽ長いの安っぽい」(0:16)：話す人の頭のすぐ上に置き、しっぽは短く（約 30px）
ov(s("01-01") + 0.8, s("01-02") + 0.55, "s01_a", [("tag", "今度、キャンプ行きたいね", 470, 285, (488, 345))])
ov(s("01-02") + 0.6, s("01-03") + 0.2, "s01_b", [("tag", "いいね！", 800, 285, (800, 345))])
ovp(s("01-03"), s("01-03", 1) + 0.3, picbubble("s01_tent", 760, 330, 70, tent))
ov(s("04-04"), s("04-04", 1) + 0.3, "s04_title", [("tag", "さっき話した物が、なぜ広告に出る？", 640, 110, None, False)])
# v10「①②③の札の間がばらばら」(1:48)：札の幅を測り、左右の余白と札どうしのすき間を同じにする
def _even_x(texts, font=None, y_margin=30):
    font = font or TAGF; _d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    ws = [(_d.textbbox((0, 0), t, font=font)[2] - _d.textbbox((0, 0), t, font=font)[0]) + 44 for t in texts]   # 枠の幅（字＋左右 22）
    gap = (1280 - sum(ws)) / (len(ws) + 1); xs = []; x = gap
    for w in ws: xs.append(x + w / 2); x += w + gap
    return xs
_SX = _even_x(["①マイク", "②出ていく手がかり", "③わたしたちの記憶"])
ov(W("05-02", "マイク"), s("05-06", 1), "s05_1", [("tag", "①マイク", _SX[0], 70, None, False, SUS[0])])
ov(W("05-03", "出ていく"), s("05-06", 1), "s05_2", [("tag", "②出ていく手がかり", _SX[1], 70, None, False, SUS[1])])
ov(W("05-04b", "わたしたち"), s("05-06", 1), "s05_3", [("tag", "③わたしたちの記憶", _SX[2], 70, None, False, SUS[2])])   # ①②③とも y=70
# v10：穴の輪は 3D から計算した場所（s06a_log.json の pos2d）。カメラを変えたので手で決めた値は使わない
_p06 = next((json.load(open(os.path.join(d_, "s06a_log.json"))).get("pos2d") for d_ in DIRS if os.path.exists(os.path.join(d_, "s06a_log.json"))), None)
if not _p06: raise SystemExit("s06a_log.json に pos2d（穴の画面の場所）がない。s06a を描き直す")
HOLE = tuple(_p06[0])
ov(W("06-02", "この小さな穴"), s("06-02", 1), "s06_ring", [("ring", HOLE[0], HOLE[1], 150, 52)])
ov(W("07-02", "見張り番"), s("07-02b", 1), "s07_guard", [("tag", "見張り番", 1100, 120)])
ov(W("07-04", "あの合言葉"), s("07-04", 1) + 0.3, "s07_word", [("tag", "Hey Siri", 640, 110, None, True), ("tag", "OK Google", 640, 230)])
ov(s("08-08") - 1.3, s("08-08") + 2.5, "s08_similar", [("tag", "Hey, Siri-al（ヘイ、シリアル）", 640, 110)])
ov(s("08-11") - 1.3, s("08-11") + 2.5, "s08_real", [("tag", "Hey Siri", 640, 110, None, True)])
_dot = None
for _d in DIRS:
    _p = os.path.join(_d, "phone_log.json")
    if os.path.exists(_p): _dot = json.load(open(_p)).get("dot2d") or None; break
if _dot: ov(W("08-14", "同じ色の点"), s("08-15", 1), "s08_dot", [("ring", _dot[0], _dot[1], 70, 70)])   # 3D で計算した点の位置
ov(W("10-05", "いた場所"), s("10-05", 1), "s10_drop", [("tag", "いた場所", 640, 110)])
ov(W("10-06", "見たページ"), s("10-06", 1), "s10_square", [("tag", "見たページ", 640, 110)])
ov(W("10-07", "一緒にいた人"), s("10-07", 1), "s10_two", [("tag", "一緒にいた人", 640, 110)])
# v4「ここで出てくる札テロップ意味わかんない」(8:25)：3 つの札は、差し込みの「ハルさんの手がかり」の絵に置きかえた（INS）
ov(s("13-03"), s("13-04", 1), "s13_phone", [("tag", "ソラさんのスマホ", 1060, 90)])
ov(W("13-03", "テントの写真"), s("13-04", 1), "s13_photo", [("img", os.path.join(SB, "phone_ad.png"), 1010, 170, 160)])   # 写真（答え）は言う瞬間に
# v4「表現もっと分かりやすく」(9:26)：Wi-Fi の線は、差し込みの「電車の無料 Wi-Fi」「一緒にいた人」の絵に置きかえた（INS）
# v4「紅葉も分かりやすいように」(9:51)：吹き出しの葉は、差し込みの「窓の外の紅葉」の絵に置きかえた（INS）
ov(s("15-03") + 2.0, s("15-04", 1), "s15_q", [("tag", "？枚", 980, 110, None, True)])   # v10：まるロボに寄ったカットになったので、顔にかからない右上へ
# v8 見直し：輪の位置は 3D の広告の場所から計算した値（s15_log.json の pos2d）。手で決めた値は電車を作り直すとずれ、画面の端で切れた
# v10「テントの場所が冒頭と違う」(11:06)：答え合わせは冒頭の電車の止め絵（s01 の T_OPEN）に輪を付けて数える。輪の場所は s01_log.json の pos2d（3D から計算）
T_OPEN = 8.2                                                             # scenes_all.py の T_OPEN と同じ
_p15 = next((json.load(open(os.path.join(d_, "s01_log.json"))).get("pos2d") for d_ in DIRS if os.path.exists(os.path.join(d_, "s01_log.json"))), None)
if not _p15: raise SystemExit("s01_log.json に pos2d（テントの広告の画面の場所）がない。s01 を描き直す")
for k, (x, y) in enumerate(_p15):
    ov(W("15-05", "%d枚" % (k + 1)), s("15-05", 1) + 0.3, "s15_%d" % k, [("ring", x, y, 95, 105), ("tag", str(k + 1), x, y - 150, None, True)])
ov(W("16-06", "外れ"), s("16-06", 1), "s16b", [("tag", "外れ", 905, 90)])          # 差し込みの「数える」の絵の右の箱の上
ov(W("16-06", "当たり"), s("16-06", 1), "s16a", [("tag", "当たり", 305, 90)])        # 左の箱の上
ov(W("18-03", "メールアドレス"), s("18-03", 1) + 0.5, "s18", [("tag", "メールアドレスの名簿", 1000, 210)])   # v10：後ろからのカット。頭（x 520〜700）にかからない右上、名簿のななめ上
ov(s("21-02"), s("21-02", 1), "s21", [("tag", "ピポ、ピポ", 980, 170)])
ov(W("22-03", "キャンプの動画"), s("22-03", 1), "s22_inset", [("img", night_inset(), 820, 60, 420)])

# 前の場面のことを言う所は、その場面の切り抜きを左上に小さく（QR回 v10 の指摘の横展開）。(出す始まり, 終わり, 元の時刻, 名前)
# v10：15-01b の「あの鏡」の小窓はやめた（同じ時に、鏡の前のまるロボの差し込み s05i が出ていて、鏡が二重になる）
PIPS = [(W("07-01", "柱の穴"), s("07-01", 1) + 0.3, W("06-02", "この小さな穴") + 2.6, "さきほどの穴"),   # v10：まるロボが穴の前に着いて、のぞき込んでいる所（歩いている所を使わない）
        (W("12-03", "あの枠"), s("12-04") + 0.3, 29.0, "ハルさんの画面"),
        (W("10-02", "さきほどと同じ"), s("10-02", 1), 158.0, "さきほどのスマホの中")]


# 場面の始まり（差し込みの表でも使うので先に）
SCST = {}
for p in P:
    SCST.setdefault(SID[p["no"]]["scene"], max(0.0, p["start"] - 0.4))
SCST["S00"] = 0.0
_sk = list(SCST)
SCEND = {k: (SCST[_sk[i + 1]] if i + 1 < len(_sk) else END) for i, k in enumerate(_sk)}


# 言っている内容の場面を差し込む（v4「まるロボをただ映すのではなく、その内容のシーンを差し込んで」7:41 ほか）。
#   (始まり, 終わり, 種類, 中身)：clip＝別の時刻の 3D をそのまま流す（中身＝元の時刻）／still＝その時刻の絵を止めて／img＝差し込みの 2D（inserts_2d.py の名前）
#   前後 0.25 秒で溶かす。字幕は上に重なる
def _w(i, f, o=0.0): return W(i, f, o)
INS = [
    (s("02-03"), _w("02-03", "もちろん"), "clip", 10.0),                            # 0:30「昼間の電車の中だけ」→ 電車の二人（v8 見直し：冒頭でスマホの寄りが 17 秒続いていた）
    (_w("05-03", "どこへ"), _w("05-03", "何を見たか"), "clip", 9.0),                 # 1:30「どこへ行ったか」→ 電車の二人
    (_w("05-03", "何を見たか"), _w("05-03", "スマホから"), "clip", 23.0),            #       「何を見たか」→ ニュースを見るハルさん
    (s("05-04b"), _w("05-04b", "3人目は"), "img", "mirror_us"),                      # 1:39「鏡分かりにくい」→ 鏡に映る私たち
    (s("09-01b"), _w("09-01b", "電話の声"), "img", "home_talk"),                     # 5:23「家の会話のシーン」
    (_w("09-01b", "電話の声"), _w("09-01b", "考えただけで") + 0.6, "img", "phone_call"),   #       「電話のシーン」
    (s("09-06") - 0.1, s("09-06b") - 0.05, "xclip", ("s05i", 0.2)),       # 6:04 まとめの前置き → マイクのアップ（まとめの中身はまだ出さない）
    (s("09-07"), s("09-07", 1) + 0.3, "clip", 27.6),                                  # 6:34「スマホに出てきたときのシーン」
    (s("10-01"), s("10-01b", 1) + 0.2, "xclip", ("s05i", 9.2)),         # 6:45 2 人目の容疑者の台
    (_w("10-05", "ハルさんのスマホ"), s("10-05", 1) + 0.2, "clip", 9.0),            # 7:06「いつ、どこにあったか」→ 電車
    (_w("10-06", "ハルさんが"), s("10-06", 1) + 0.2, "clip", 23.0),                   # 7:21「どんなページを見たか」→ ニュース
    (_w("10-07", "ハルさんと"), s("10-07", 1) + 0.2, "clip", 14.0),                   # 7:30「一緒にいた人」→ 電車の二人
    (s("10-08"), s("10-08", 1) + 0.2, "img", "wifi_place"),                           # 7:30「同じ家やお店」
    (s("10-09"), s("10-09", 1) + 0.2, "img", "to_company"),                           # 7:41「アプリやサイトを通じて、広告の会社に」
    (s("10-10"), s("10-10", 1) + 0.4, "img", "permission"),                           #       「許可したもの」
    (_w("11-02b", "大きな会場"), SCST["S12"] + 0.05, "still", SCST["S12"] + 0.1),    # 8:00「大きな会場」で会場に切り替え
    (s("12-05"), s("12-05", 1) + 0.2, "img", "clues"),                                # 8:25 手がかりの札 → 絵で
    (s("12-05b"), _w("12-05b", "手がかりを見ると"), "clip", 23.0),                   # 8:31「ニュースを読んでいる場面」
    (_w("13-05", "同じ電車"), s("13-05", 1) + 0.2, "img", "wifi_train"),             # 9:26 Wi-Fi
    (s("13-05b"), s("13-05b", 1) + 0.2, "img", "together"),
    (_w("14-01b", "紅葉"), s("14-01c", 1) + 0.2, "img", "autumn"),                   # 9:51 紅葉（v5：1.2 秒だけだと 3D の窓→絵の窓→3D の窓とちらつくので、次の文の終わりまで）
    (s("14-05"), s("14-05b") - 0.05, "xclip", ("s05i", 9.2)),           # 10:21 2 人目の容疑者のまとめ → 容疑者の台
    (s("14-05b"), s("14-05c") - 0.05, "clip", 505.0),                                 # 10:30「競りで使われていました」→ 競り
    (s("14-05c"), _w("14-05c", "季節"), "clip", 563.0),                               #       「一緒にいた人」→ 二人
    (_w("14-05c", "季節"), s("14-05d") - 0.05, "img", "autumn"),                     #       「季節」→ 紅葉
    (_w("14-05d", "2人目の容疑者"), s("14-05d", 1) + 0.3, "xclip", ("s05i", 9.2)),   # 10:39 容疑者のシーン
    (s("15-01"), s("15-01", 1) + 0.2, "xclip", ("s05i", 18.2)),
    (W("15-05", "1枚") - 0.35, s("15-05", 1) + 0.3, "still", T_OPEN),              # 11:06「1枚、2枚、3枚」→ 冒頭の電車の止め絵に輪で数える                                  # 10:43 3 人目の容疑者 → 鏡の台
    (_w("15-01b", "私たち自身"), s("15-01b", 1) + 0.2, "img", "mirror_us"),
    (s("16-01"), s("16-02") - 0.05, "img", "ads_many"),                               # 11:35〜12:00 記憶の場面を絵で
    (s("16-02"), s("16-03") - 0.05, "img", "ads_forget"),
    (s("16-03"), s("16-04") - 0.05, "img", "ad_notice"),
    (s("16-04"), s("16-05") - 0.05, "img", "memory_strong"),
    (s("16-05"), s("16-06") - 0.05, "img", "miss_forgot"),
    (s("16-06"), s("16-06", 1) + 0.3, "img", "tally"),
    (s("16-08"), s("16-08", 1) + 0.3, "xclip", ("s05i", 18.2)),                                  # 12:15 3 人目の容疑者のシーン
    (s("18-00"), s("18-01", 1) + 0.2, "img", "government"),                           # 12:43 役所が調べる
    (s("19-08"), s("19-08b") - 0.05, "clip", 232.0),                                  # 14:02 スマホの耳は聞いていない → 門と見張り番
    (s("19-08b"), _w("19-08b", "好きそうな"), "clip", 410.0),                         #       出ていく手がかり → 箱
    (_w("19-08b", "好きそうな"), s("19-08c") - 0.05, "clip", 512.0),                 #       予想 → 競り
    (s("19-08c"), s("19-08c", 1) + 0.3, "img", "tally"),                              #       当たったときだけ覚えている
]


# ---------------- 絵の並び（場面ごとのコマ。間引いたコマは長さで埋める）
logs, rows = {}, []
for k in PARTS:
    lg = None
    for d in DIRS:
        p = os.path.join(d, k + "_log.json")
        if os.path.exists(p) and (glob.glob(os.path.join(d, k + "_[0-9]*.png")) or glob.glob(os.path.join(d, k + "_[0-9]*.jpg"))):   # 本番の絵は jpg（pc_frames.py）
            lg = json.load(open(p)); lg["dir"] = d; break
    logs[k] = lg
t_prev = 0.0
missing = []
for k in PARTS:
    lg = logs[k]
    if lg is None:
        missing.append(k); continue
    fs = sorted(glob.glob(os.path.join(lg["dir"], k + "_[0-9]*.png")) + glob.glob(os.path.join(lg["dir"], k + "_[0-9]*.jpg")))
    nums = [int(os.path.basename(x)[len(k) + 1:-4]) for x in fs]
    lim = min(lg["t1"], SCEND["S%02d" % BOARD[k]] if k != "gate" else SCEND["S08"])   # 場面の終わり（次の場面の始まり）で切る
    for i, (pth, n) in enumerate(zip(fs, nums)):
        a = lg["t0"] + n / 24
        b = min(lim, lg["t0"] + (nums[i + 1] / 24 if i + 1 < len(nums) else lg["frames"] / 24))
        if a < lim - 1e-6: rows.append((a, b, pth))
rows.sort()
# 足りない場面・すき間は絵コンテの絵で埋める
fill, cur = [], 0.0
SC = {}
for p in P:
    sc_ = SID[p["no"]]["scene"]
    SC.setdefault(sc_, p["start"] - 0.4)
for a, b, pth in rows + [(END, END, None)]:
    while a - cur > 0.05:                                    # すき間を場面の境目ごとに分けて、その場面の絵コンテで埋める
        sc_ = max([k for k, v in SCST.items() if v <= cur + 0.01] or ["S00"], key=lambda k: SCST[k])
        e = min(a, SCEND[sc_])
        fill.append((cur, e, os.path.join(SB, "board", "b%02d_nosub.png" % int(sc_[1:]))))
        cur = e
    cur = max(cur, b)
allrows = sorted(rows + fill)
def _frame_at(t):
    # その時刻に出ている絵。ちょうど境目などで見つからないときは、その時刻より前の最後の絵（v4「6:38 一瞬何かのシーン写って消えてる」：
    #   前は見つからないと最後の場面の絵を返し、それがつなぎに重なっていた）
    best = None
    for a, b, pth in allrows:
        if a <= t < b: return pth
        if a <= t: best = pth
    return best or allrows[0][2]
for k, (a, b, tsrc, label) in enumerate(PIPS):
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sub = Image.open(_frame_at(tsrc)).convert("RGB").resize((400, 225), Image.LANCZOS)
    if label == "さきほどの穴":                                              # 切り抜きにも、さきほどの穴の輪（06-02 と同じ所）を描く
        ImageDraw.Draw(sub).ellipse([(HOLE[0] - 150) * 400 / 1280, (HOLE[1] - 52) * 225 / 720, (HOLE[0] + 150) * 400 / 1280, (HOLE[1] + 52) * 225 / 720], outline=(255, 138, 42), width=4)
    d.rounded_rectangle([24, 24, 24 + 412, 24 + 237], 14, fill="white", outline=NAVY, width=4); im.paste(sub, (30, 30))
    bb = d.textbbox((0, 0), label, font=TAGF); w = bb[2] - bb[0]; th = bb[3] - bb[1]
    d.rounded_rectangle([30, 272, 30 + w + 40, 272 + th + 26], 14, fill=NAVY); d.text((50 - bb[0], 285 - bb[1]), label, font=TAGF, fill="white")
    pp = os.path.join(tmp, "pip_%d.png" % k); im.save(pp)
    OVERLAYS.append((a, b, pp, [(label, 24, 24, 436, 272 + th + 26, TAGF.size)]))
# 差し込みの絵と動画を用意する
INSD = os.path.join(tmp, "ins"); subprocess.run([sys.executable, os.path.join(HERE, "inserts_2d.py"), INSD, FONT], check=True, capture_output=True)
def _clip(name, src, dur):
    """src 秒からの dur 秒ぶんの絵（別の場面のコマ）を、1280×720・24 コマ/秒の短い動画に"""
    # v5「一瞬せりのシーンを映す」：元の場面の終わりで止める（足りない分は最後の絵で待つ）。次の場面が混ざらないように
    lim = min([T for T in SCENE_TS if T > src + 0.05] + [END]) - 0.15
    items = [(max(a, src), min(b, src + dur, lim), pth) for a, b, pth in allrows if b > src and a < min(src + dur, lim)]
    if not items: items = [(src, src + dur, _frame_at(src))]
    if items[-1][1] < src + dur: items.append((items[-1][1], src + dur, items[-1][2]))
    l = os.path.join(tmp, "ins_%s.txt" % name); o = os.path.join(tmp, "ins_%s.mp4" % name)
    with open(l, "w") as fo:
        for a, b, pth in items: fo.write("file '%s'\nduration %.4f\n" % (pth, b - a))
        fo.write("file '%s'\n" % items[-1][2])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", l, "-vf", "scale=1280:720,setsar=1,fps=24,format=yuv420p",
                    "-frames:v", str(max(1, round(dur * 24))), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", o], check=True)
    return o
def _xclip(name, part, src, dur):
    """差し込み専用の場面（s05i など。時刻は場面の外）の src 秒からの dur 秒。足りない分は最後の絵で待つ（v10「まとめで移動するのはおかしい」）"""
    d = next((d_ for d_ in DIRS if os.path.exists(os.path.join(d_, part + "_log.json"))), None)
    if d is None: raise SystemExit("差し込み専用の場面 %s の絵がない（PC で描く一覧に入れる）" % part)
    lg = json.load(open(os.path.join(d, part + "_log.json")))
    fs = sorted(glob.glob(os.path.join(d, part + "_[0-9]*.png")) + glob.glob(os.path.join(d, part + "_[0-9]*.jpg")))
    fr = [(lg["t0"] + int(os.path.basename(x)[len(part) + 1:-4]) / 24, x) for x in fs]
    seg_end = (int(src // 9.0) + 1) * 9.0                                   # 9 秒ごとの区切り（次の台）をこえない
    sel = [(t, x) for t, x in fr if src - 1e-6 <= t < min(src + dur, seg_end - 0.05)] or [min(fr, key=lambda q: abs(q[0] - src))]
    l = os.path.join(tmp, "ins_%s.txt" % name); o = os.path.join(tmp, "ins_%s.mp4" % name)
    with open(l, "w") as fo:
        for i, (t, x) in enumerate(sel):
            nt = sel[i + 1][0] if i + 1 < len(sel) else src + dur
            fo.write("file '%s'\nduration %.4f\n" % (x, max(1 / 24, nt - t)))
        fo.write("file '%s'\n" % sel[-1][1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", l, "-vf", "scale=1280:720,setsar=1,fps=24,format=yuv420p",
                    "-frames:v", str(max(1, round(dur * 24))), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", o], check=True)
    return o
# v5「差し込みの間に前の場面が一瞬映る」：差し込みどうし・差し込みと場面の切り替わりの間に、元の場面が短く（INS_GAP 秒未満）
#   のぞく所をなくす。①近い差し込みはつなぐ（前の差し込みは消さずに、次をその上に重ねて出す）
#   ②場面の始まり・終わりの近くの差し込みは、切り替わりまでのばす（切り替わりは差し込みの中で済ませ、元の場面の重ねは使わない）
INS_GAP, INS_FD = 2.0, 0.3
SCENE_TS = sorted(set([t for k, t in SCST.items() if k != "S00"] + [298.26]))
_ins = sorted([list(x) for x in INS if x[1] - x[0] >= 0.3], key=lambda x: x[0])
for _ in range(4):
    for x in _ins:
        for _T in SCENE_TS:
            if -INS_FD < x[0] - _T < INS_GAP: x[0] = _T - INS_FD                   # 場面の始まりから少しだけ元の場面 → 切り替わりから差し込み
            if -INS_FD < _T - x[1] < INS_GAP: x[1] = _T + INS_FD               # 切り替わりの直後に終わる差し込みも（差し込みのあと少しだけ元の場面 → 切り替わりまで差し込み。v5「会場の後に前の場面が一瞬」）
    for i in range(len(_ins) - 1):
        if _ins[i + 1][0] - _ins[i][1] < INS_GAP: _ins[i][1] = max(_ins[i][1], _ins[i + 1][0])
# ③ 元の場面は文の頭でカメラが切り替わることが多い。差し込みのあと次の文の頭まで 1.2 秒未満なら、その頭の 0.6 秒あとまでのばす。
#   文の頭から 1.2 秒未満で始まる差し込みは、文の頭から出す（切り替わった直後の絵を一瞬見せない。v5 の 1 コマずつの点検で見つけた）
SENT_TS = [p["start"] for p in P]   # 3D のカメラは、文の頭ちょうどか、その 0.4 秒前で切り替わる（場面による）。出始めは 0.4 秒前に、終わりは頭のあとに合わせて両方を覆う
for _ in range(3):
    for x in _ins:
        for _T in SENT_TS:
            if 0 <= _T - x[1] < 1.2: x[1] = _T + 0.6
            if -0.4 < x[0] - _T < 1.2: x[0] = min(x[0], _T - 0.4 - INS_FD)   # v6 の点検：10:15 に、0.4 秒前の切り替わりが 0.1 秒のぞいていた
    for i in range(len(_ins) - 1):
        if _ins[i + 1][0] - _ins[i][1] < INS_GAP: _ins[i][1] = max(_ins[i][1], _ins[i + 1][0])
INS_COVER = [(x[0], x[1]) for x in _ins]
def _covered(t): return any(a + 0.01 < t < b - 0.01 for a, b in INS_COVER)
if os.environ.get("BOARD_DUMP"):                                         # 絵コンテ表用：差し込み・札・小窓を書き出して終わる（make_board_table.py が読む）
    json.dump(dict(ins=[[round(x[0], 2), round(x[1], 2), x[2], x[3] if not isinstance(x[3], float) else round(x[3], 2)] for x in _ins],
                   ov=[[round(a_, 2), round(b_, 2), os.path.basename(p_)[3:-4], [bx[0] for bx in bxs if bx and isinstance(bx[0], str)]] for a_, b_, p_, bxs in OVERLAYS],
                   pips=[[round(a_, 2), round(b_, 2), str(t_), l_] for a_, b_, t_, l_ in PIPS]),
              open(os.environ["BOARD_DUMP"], "w"), ensure_ascii=False)
    sys.exit(0)
if os.environ.get("INS_DRY"):                                            # 差し込みの並びだけ見る
    for x in _ins: print("%6.2f %6.2f %-5s %s" % (x[0], x[1], x[2], x[3]))
    _c = sorted(set([0.0, END] + SCENE_TS + [a for a, b in INS_COVER] + [b for a, b in INS_COVER]))
    for a, b in zip(_c, _c[1:]):
        if b - a < INS_GAP and not any(a2 <= (a + b) / 2 <= b2 for a2, b2 in INS_COVER): print("PEEK %.2f-%.2f" % (a, b))
    sys.exit(0)
INSV = []   # (始まり, 終わり, ファイル, 動画か, 消え方)  消え方 True＝最後に溶けて消える／False＝次の差し込みが上に重なる
for k, (a, b, kind, arg) in enumerate(_ins):
    nxt = k + 1 < len(_ins) and _ins[k + 1][0] <= b + 1e-3
    if nxt: b = _ins[k + 1][0] + INS_FD + 0.25                              # 次が出きるまで残す（v5「12:28 一瞬なにかうつる」：ちょうど出きるコマで前の絵が消え、1 コマだけ下の場面が透けていた。0.25 秒余分に残す）
    if kind == "clip": INSV.append((a, b, _clip("c%d" % k, arg, b - a + 0.1), True, not nxt))
    elif kind == "xclip": INSV.append((a, b, _xclip("x%d" % k, arg[0], arg[1], b - a + 0.1), True, not nxt))
    elif kind == "still": INSV.append((a, b, _frame_at(arg), False, not nxt))
    else: INSV.append((a, b, os.path.join(INSD, "ins_%s.png" % arg), False, not nxt))
# 大きさの違う絵（3D の試し描き・2D・絵コンテ）を一度に並べると時刻がずれるので、続いている同じ場面ごとに
# 1280×720・24 コマ/秒の短い動画にしてから、つなぐ
runs = []
for a, b, pth in allrows:
    grp = os.path.dirname(pth) + "|" + os.path.basename(pth).split("_")[0]
    if runs and runs[-1][0] == grp and abs(runs[-1][2] - a) < 1e-3:
        runs[-1][2] = b; runs[-1][3].append((a, b, pth))
    else:
        runs.append([grp, a, b, [(a, b, pth)]])
REMUX = os.environ.get("REMUX")
if REMUX: runs = []
seg_list = os.path.join(tmp, "segs.txt")
with open(seg_list, "w") as fs_:
    for i, (grp, a, b, items) in enumerate(runs):
        l = os.path.join(tmp, "seg_%03d.txt" % i); sp = os.path.join(tmp, "seg_%03d.mp4" % i)
        with open(l, "w") as fo:
            for a2, b2, pth in items: fo.write("file '%s'\nduration %.4f\n" % (pth, b2 - a2))
            fo.write("file '%s'\n" % items[-1][2])
        n = round((b - a) * 24)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", l,
                        "-vf", "scale=1280:720,setsar=1,fps=24,format=yuv420p", "-frames:v", str(n),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", sp], check=True)
        fs_.write("file '%s'\n" % sp)
lst = os.path.join(tmp, "video.mp4")
if not REMUX: subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", seg_list, "-c", "copy", lst], check=True)

# ---------------- 効果音
sys.path.insert(0, HERE)
import sfx
sr = 48000
sfx_bus = np.zeros(int(END * sr), np.float32)
ev_all = []
for k, lg in logs.items():
    if not lg: continue
    ev_all += [(t, kd) for t, kd in lg.get("events", [])]
    ev_all += [(t, "step") for t in lg.get("steps", [])]
# 声（アニマティックの声：ピー入り、24 kHz）を 48 kHz に
_VW = W_ + "/animatic_tmp/voice_v11.wav"                              # v11：高い文を、まとめ（5 文ずつ）で読ませ直した声に差し替えた声（voice/tools/retake_batch_lines.py）。
#   v10 の voice_v10.wav（機械で高さを下げた声）は「声おかしすぎる」と言われたので使わない
if not os.path.exists(_VW): raise SystemExit("voice_v11.wav がない（voice/tools/README.md の作り方で作る）")
with wave.open(_VW) as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; vsr = w.getframerate()
v = np.interp(np.arange(int(len(v) * sr / vsr)) / sr, np.arange(len(v)) / vsr, v).astype(np.float32)
voice = np.zeros_like(sfx_bus); voice[:min(len(v), len(voice))] = v[:len(voice)]
_hs = int(0.01 * sr); _ve = np.abs(voice[:len(voice) // _hs * _hs]).reshape(-1, _hs).max(1)   # 10ms ごとの声の大きさ
def talking(t, d):
    a_, b_ = max(0, int(t / 0.01)), int((t + d) / 0.01) + 1
    return bool((_ve[a_:b_] > 0.02).any())
IMPORTANT = ("pi", "pipo", "win", "rise", "clatter", "lamp", "gate_up", "pop_ui", "hat", "towel", "dive")
moved, dropped, over = [], [], []
sys.path.insert(0, os.path.join(EP, "..", "..", "skill", "marurobo-video-production", "scripts"))
import maru_sfx                                                          # まるロボの気持ちの動きの電子音（maru_motions.md。3本目 v10 で足した）
_nos = {}
_played = []
for t, kd in ev_all:
    beep = False
    if kd.startswith("maru:"):                                          # まるロボの予定の音（maru_cmds：「maru:種類:強さ」）→ 共通の音を強さどおりに
        _, k_, st_ = kd.split(":"); x = maru_sfx.make(k_, float(st_), sr)
        if x is None: _nos[k_] = _nos.get(k_, 0) + 1; continue
        x = np.asarray(x, np.float32); beep = k_ not in ("takeoff", "land", "step", "step_turn") and float(st_) >= 0.3
    else:
        x = sfx.make(kd, sr)
        if x is None:
            x = maru_sfx.make(kd, 1.0, sr)
            if x is not None: x = np.asarray(x, np.float32)
        if x is None: _nos[kd] = _nos.get(kd, 0) + 1; continue
    # v10（4本目と同じ決まり）：大事な音・まるロボの電子音が声と重なるときは、前後 0.5 秒以内のいちばん近い声のすき間へずらす。
    #   ずらせないとき、まるロボの電子音は鳴らさない（声が大事）。ほかの大事な音は報告する
    hd = min(len(x) / sr, 0.35)                                         # 音の頭（はじめの 0.35 秒）が声のすき間に入ればよい（のびる尾は声の下で小さくなる）
    if (beep or kd in IMPORTANT) and talking(t, hd):
        for sh in sorted((k_ * 0.02 for k_ in range(-30, 31)), key=abs):   # 前後 0.6 秒まで
            if t + sh >= 0 and not talking(t + sh, hd):
                moved.append("%s %.1f→%.2f" % (kd, t, t + sh)); t += sh; break
        else:
            if beep: dropped.append("%s %.1f" % (kd, t)); continue
            over.append("%s %.1f" % (kd, t))
    _played.append((t, kd))
    i = int(t * sr); sfx_bus[i:i + len(x)] += x[:max(0, len(sfx_bus) - i)]
ev_all = _played
if _nos: print("【効果音】音のない種類：", _nos)
# 声のある所は効果音を 6 dB 下げる（上がり 0.12 秒・下がり 0.35 秒）
env = np.ones_like(sfx_bus)
for p in P:
    a, b = int((p["start"] - 0.12) * sr), int((p["end"] + 0.35) * sr); env[max(0, a):b] = 10 ** (-6 / 20)
k = int(0.05 * sr); env = np.convolve(env, np.ones(k) / k, mode="same")
# BGM（声のある所は 6 dB 下げる。効果音と同じ下げ方）
sys.path.insert(0, os.path.join(EP, "bgm"))
import bgm_bus
music = bgm_bus.make(END, SCST, sr)[:len(voice)]
mix = voice + sfx_bus * env * 0.5 + music * env
mix /= max(1.0, np.abs(mix).max() / 0.89)
with wave.open(tmp + "/mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
# v10：全体の大きさを -14 LUFS・-1.5 dBTP にそろえる（SKILL §7 の concat_full と同じ値。v9 までは -22.5 LUFS で小さかった）。2 回測って、ゆがませずに上げる
_m = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp + "/mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
_j = json.loads(_m[_m.rindex("{"):_m.rindex("}") + 1])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp + "/mix.wav", "-af",
                "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true" % (_j["input_i"], _j["input_tp"], _j["input_lra"], _j["input_thresh"], _j["target_offset"]),
                "-ar", str(sr), "-ac", "1", tmp + "/mix_ln.wav"], check=True)
os.replace(tmp + "/mix_ln.wav", tmp + "/mix.wav")

# ---------------- 字幕（アニマティックと同じ）
ev = json.load(open(os.path.join(EP, "animatic", "subs_events.json"), encoding="utf-8"))
def ts(x): return "%d:%02d:%05.2f" % (x // 3600, x % 3600 // 60, x % 60)
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Main,Noto Sans JP,56,&H00FFFFFF,&H00FFFFFF,&H00301A10,&H96000000,-1,0,0,0,100,100,1,0,1,5,2.2,2,50,50,40,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, c, t in ev: ass.append("Dialogue: 0,%s,%s,Main,,0,0,0,,%s" % (ts(a), ts(c), t.replace("\n", "\\N")))
open(tmp + "/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")

# ---------------- 組み立て（絵 → 札 → 字幕、声と効果音）
# 場面のつなぎを重ねる（QR回 v10 の指摘「ぶつっと変わる」の横展開）：前の場面の最後の絵を、次の場面の頭に重ねて消していく。
#   3D どうしは 0.35 秒、スマホの外と中・2D の場面との境目は 0.65 秒。声と字幕の時刻は変えない
XIN = {"S03", "S04", "S06b", "S09", "S10", "S11", "S20", "S21"}           # 前後で世界が変わる所（2D・スマホの中へ／外へ）
XF = [(t, 0.65 if k in XIN else 0.35) for k, t in SCST.items() if k != "S00"]
XF.append((298.26, 0.65))                                                    # 門の町（スマホの中）→ 外から見たスマホの画面
XF = sorted(x for x in XF if 0.5 < x[0] < END - 1 and not _covered(x[0]))   # 差し込みの中の切り替わりは重ねない（差し込みで隠れている）
inputs = ["-i", lst]
# 同じ絵が長く続く所は、ゆっくり寄る（QR回 v10「変わり映えしない」の横展開。動きの少ない所を測って選んだ：S05・S08 の門・S09・S14・S17〜S19・S20）。
#   3D の中の物に合わせた輪（S06 の穴・S08 の画面の点・S15 のつり広告）がある所は寄らない（輪がずれるため）
# v10「カメラが左右に揺れる」(2:13・13:33)・「2D が動いている」(6:23)・「寄りと引きのくり返し」(13:13)・「切り替えで一瞬変なのが映る」(13:01)：
#   組み立ての寄り（ffmpeg の zoompan は 1 ピクセル単位で切るので揺れる）と、寄りの切り替え（PUNCH）をやめた。
#   長い引きは、3D のカメラで別の角度のカットを作る（門・S15・S18）
ZOOM = []
PUNCH = []
_zt = "(in/24)"
_ze = "+".join("between(%s,%.3f,%.3f)*0.06*((%s-%.3f)/%.3f)" % (_zt, a, b, _zt, a, b - a) for a, b in ZOOM)
_ze += "".join("+between(%s,%.3f,%.3f)*%.3f" % (_zt, a, b, z - 1) for a, b, z, cx, cy in PUNCH)
_cx = "0.5" + "".join("+between(%s,%.3f,%.3f)*%.3f" % (_zt, a, b, cx - 0.5) for a, b, z, cx, cy in PUNCH)
_cy = "0.5" + "".join("+between(%s,%.3f,%.3f)*%.3f" % (_zt, a, b, cy - 0.5) for a, b, z, cx, cy in PUNCH)
fl = ["[0:v]scale=1280:720,fps=24,setsar=1[v0]"] if not (ZOOM or PUNCH) else ["[0:v]scale=1280:720,fps=24,setsar=1,zoompan=z='1+%s':x='max(0,min(iw-iw/zoom,iw*(%s)-(iw/zoom/2)))':y='max(0,min(ih-ih/zoom,ih*(%s)-(ih/zoom/2)))':d=1:s=1280x720:fps=24[v0]" % (_ze, _cx, _cy)]
cur = "v0"; nin = 1
for j, (T, dd) in enumerate(XF):
    _src = _frame_at(T - 0.1); _z = 1 + sum(0.06 * (T - 0.1 - a) / (b - a) for a, b in ZOOM if a <= T - 0.1 <= b)
    if _z > 1.001:                                                       # 寄っている場面の終わりは、重ねる絵も同じだけ寄せる（ずれて見えないように）
        _im = Image.open(_src).convert("RGB").resize((1280, 720), Image.LANCZOS); cw, ch = 1280 / _z, 720 / _z
        _im = _im.crop(((1280 - cw) / 2, (720 - ch) / 2, (1280 + cw) / 2, (720 + ch) / 2)).resize((1280, 720), Image.LANCZOS)
        _src = os.path.join(tmp, "xf_%d.png" % j); _im.save(_src)
    inputs += ["-loop", "1", "-t", "%.3f" % (dd + 3 / 24), "-i", _src]
    T0 = T - 2 / 24                                                       # 2 コマ前から重ね始める（v4「15:03 切り替わる時点滅」：1 コマ遅れて次の場面がそのまま見えていた）
    fl.append("[%d:v]scale=1280:720,format=rgba,fade=t=out:st=%.3f:d=%.3f:alpha=1,setpts=PTS+%.3f/TB[x%d]" % (nin, 2 / 24, dd, T0, j))
    fl.append("[%s][x%d]overlay=0:0:eof_action=pass:enable='between(t,%.3f,%.3f)'[c%d]" % (cur, j, T0, T + dd, j)); cur = "c%d" % j; nin += 1
for j, (a, b, pth, mv, fo_) in enumerate(INSV):
    dd = b - a
    inputs += (["-i", pth] if mv else ["-loop", "1", "-t", "%.3f" % dd, "-i", pth])
    _fo = (",fade=t=out:st=%.3f:d=%.3f:alpha=1" % (max(0, dd - INS_FD), INS_FD)) if fo_ else ""
    fl.append("[%d:v]scale=1280:720,format=rgba,fade=t=in:st=0:d=%.3f:alpha=1%s,setpts=PTS+%.3f/TB[n%d]" % (nin, INS_FD, _fo, a, j))
    fl.append("[%s][n%d]overlay=0:0:eof_action=pass:enable='between(t,%.3f,%.3f)'[d%d]" % (cur, j, a, b, j)); cur = "d%d" % j; nin += 1
for i, (a, b, pth, _) in enumerate(OVERLAYS):
    # v8 見直し：札は 0.25 秒でふわっと出て、0.2 秒で消える（他の回の決まり「札がいきなり出る」）
    inputs += ["-loop", "1", "-framerate", "24", "-t", "%.3f" % (b - a + 0.05), "-i", pth]
    _ex = "".join("*not(between(t,%.3f,%.3f))" % (c, d) for c, d in INS_COVER if c < b and a < d and not (c - 0.05 <= a < d))   # v5：差し込みの間は、元の場面の札・小窓を出さない。
    #   v10：差し込みが出ている間に出始める札（差し込みの絵に付けた札：数える輪・外れ／当たり）は、差し込みの上に出す（前は一緒に消えていた）
    fl.append("[%d:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st=%.3f:d=0.2:alpha=1,setpts=PTS+%.3f/TB[t%d]" % (nin, max(0.3, b - a - 0.2), a, i))
    fl.append("[%s][t%d]overlay=0:0:eof_action=pass:enable='between(t,%.3f,%.3f)%s'[o%d]" % (cur, i, a, b, _ex, i)); cur = "o%d" % i; nin += 1
fl.append("[%s]subtitles=%s:fontsdir=%s[vout]" % (cur, tmp + "/subs.ass", FONTS))
inputs += ["-i", tmp + "/mix.wav"]
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "%d:a" % nin,
       "-c:v", "libx264", "-preset", "medium", "-crf", os.environ.get("CRF", "27"), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", os.environ.get("ABR", "128k"), "-t", "%.2f" % END, OUT]
if REMUX:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", REMUX, "-i", tmp + "/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
           "-c:a", "aac", "-b:a", os.environ.get("ABR", "128k"), "-t", "%.2f" % END, OUT]
subprocess.run(cmd, check=True)

# ---------------- 点検
chk = []
chk.append("足りない場面（絵コンテの絵で埋めた）：%s" % (", ".join(missing) or "なし"))
for a, b, pth, bx in OVERLAYS:
    for text, x0, y0, x1, y1, fs in bx:
        if fs < 44: chk.append("札の字が小さい：%s（%d）" % (text, fs))
        subs_on = any(c > a and e < b for e, c, _ in ev)
        if subs_on and y1 > SUB_TOP: chk.append("札が字幕の帯にかかる：%s（%.1f〜%.1f 秒）" % (text, a, b))
for i, (a, b, *_r) in enumerate(OVERLAYS):
    for a2, b2, *_r2 in OVERLAYS[i + 1:]:
        if a < b2 and a2 < b:
            for t1_ in _r[1]:
                for t2_ in _r2[1]:
                    if not (t1_[3] < t2_[1] or t2_[3] < t1_[1] or t1_[4] < t2_[2] or t2_[4] < t1_[2]):
                        chk.append("札どうしが重なる：%s と %s" % (t1_[0], t2_[0]))
# v5：元の場面が短く（INS_GAP 秒未満）のぞく所。差し込み・場面の切り替わりで区切って測る
_cuts = sorted(set([0.0, END] + SCENE_TS + [a for a, b in INS_COVER] + [b for a, b in INS_COVER]))
_peek = []
for a, b in zip(_cuts, _cuts[1:]):
    m = (a + b) / 2
    if b - a < INS_GAP and not _covered(m) and not any(a2 <= m <= b2 for a2, b2 in INS_COVER):
        if a > 0.5 and b < END - 0.5: _peek.append("%d:%04.1f（%.1f 秒）" % (a // 60, a % 60, b - a))
chk.append("元の場面が一瞬のぞく所：%s" % ("／".join(_peek) or "なし"))
_ovi = ["%s（%.1f）" % (bx[0][0], a) for a, b, pth, bx in OVERLAYS if bx and any(a < b2 - 0.3 and a2 + 0.3 < b and not (a2 - 0.05 <= a < b2) for a2, b2 in INS_COVER)]
chk.append("差し込みの間は隠れる札（元の場面の札）：%s" % ("／".join(_ovi) or "なし"))
ov_sfx = []
for t, kd in ev_all:
    for p in P:
        big = kd in ("jump", "land", "pi", "pipo", "win", "rise", "clatter", "lamp", "gate_up") or (kd.startswith("maru:land:") and float(kd.split(":")[2]) >= 1.5)   # まるロボの着地は強いものだけ
        if p["start"] - 0.05 < t < p["end"] and big:
            ov_sfx.append("%.1f %s（%s）" % (t, kd, SID[p["no"]]["id"])); break
chk.append("声と重なる大きめの効果音：%d か所 %s" % (len(ov_sfx), "／".join(ov_sfx[:20])))
chk.append("声のすき間へずらした音：%d（%s）／声と重なるので鳴らさなかったまるロボの電子音：%s／ずらせなかった大事な音：%s" % (len(moved), "、".join(moved[:12]), "、".join(dropped) or "なし", "、".join(over) or "なし"))
gaps = [(P[i + 1]["start"] - P[i]["end"], SID[P[i + 1]["no"]]["id"]) for i in range(len(P) - 1)]
chk.append("2.2 秒以上の間：%s" % ([g for g in gaps if g[0] >= 2.2] or "なし"))
chk.append("1.0 秒未満の字幕：%s" % ([e for e in ev if e[1] - e[0] < 1.0] or "なし"))
open(OUT + "_check.txt", "w", encoding="utf-8").write("\n".join(chk) + "\n")
print("\n".join(chk))
print(OUT, "%.1f MB" % (os.path.getsize(OUT) / 1e6))
