# 会話と広告の回のサムネ案 第3弾（2026-11-13）：絵を Gemini の画像モデル（gemini-3-pro-image）で描き直し、字はこちらで載せる
#   ユーザー「チープすぎる絵はどうにかなる？」→ 3D の試し描きを見本に渡して、映画のアニメ風に描き直した（字は入れさせない）
#   絵を作る：scratchpad の ai/gen.py（見本の絵と指示 → p1〜p3.png。指示は ai/prompts.json。下にも写しを置く）
#   python3 thumbs3.py <絵のフォルダ> <出力フォルダ> <フォント.ttf>
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "thumbs2.py"), encoding="utf-8").read().split("TALK = ")[0])
made = []
# 1：夜の部屋。驚くまるロボ（右）とテントの広告のスマホ。字は左
im = bg("p1.png", zoom=1.0, bri=1.05); im = shade(im, "left", 0.50, 0.80)
im = ring(im, (2260, 770), 250, 440)
im = bubble(im, (70, 60, 980, 330), [[("さっき", NAVY), ("テント", RED2), ("の話を", NAVY)], [("しただけなのに…", NAVY)]], 92, (1120, 420))
im, _ = big(im, (80, 470), [("なぜ", WHITE)], 220)
im, _ = big(im, (80, 760), [("広告", YEL), ("に", WHITE)], 320)
im, _ = big(im, (80, 1140), [("出る？", WHITE)], 220)
made.append(save(im, "t3_1"))
# 2：光るスマホの広告を見つめる探偵まるロボ。字は左
im = bg("p3.png", zoom=1.0, bri=1.05); im = shade(im, "left", 0.42, 0.85)
im = ring(im, (1400, 720), 230, 300)
im, _ = big(im, (60, 200), [("話した", WHITE)], 230)
im, _ = big(im, (60, 480), [("内容が", WHITE)], 230)
im, _ = big(im, (60, 800), [("広告", YEL)], 330)
im, _ = big(im, (60, 1160), [("に!?", RED2)], 200)
made.append(save(im, "t3_2"))
# 3：電車で話す二人とまるロボ、上にテントの思い浮かべ。字は下
im = bg("p2.png", zoom=1.0, bri=1.03); im = shade(im, "bottom", 0.38, 0.95)
im = bubble(im, (60, 330, 760, 590), [[("キャンプ", NAVY)], [("行きたいね！", NAVY)]], 100, (860, 690))
im, _ = big(im, (W / 2, 1000), [("話した内容が", WHITE)], 180, anchor="c")
im, _ = big(im, (W / 2, 1200), [("なぜ ", WHITE), ("広告", YEL), ("に？", WHITE)], 210, anchor="c")
made.append(save(im, "t3_3"))
sheet = Image.new("RGB", (1280 * 2 + 30, 720 * 2 + 30), (240, 242, 244))
for i, p in enumerate(made): sheet.paste(Image.open(p), ((i % 2) * 1290, (i // 2) * 730))
sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2), Image.LANCZOS).save(OUT + "/sheet3_big.jpg", quality=88)
small = Image.new("RGB", (len(made) * 214 + 10, 140), (255, 255, 255))
for i, p in enumerate(made): small.paste(Image.open(p).resize((210, 118), Image.LANCZOS), (i * 214 + 4, 10))
small.save(OUT + "/sheet3_small.png"); print("\n".join(made))
