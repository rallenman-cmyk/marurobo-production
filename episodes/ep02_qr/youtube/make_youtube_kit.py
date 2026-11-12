# YouTube に出すための一式を、本番の組み立て（final test）から作る
#   python3 make_youtube_kit.py [本番の動画の _index.json] [その subs.ass]
#   → QR回_YouTube一式.md（概要欄・もくじの時刻・固定コメント）と qr_ep02_ja.srt（字幕）
#   長さが変わったら走らせ直すだけで、もくじの時刻と字幕がそろう
import os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
F = '/home/user/qr_plan/parts/v2/final'
IDX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(F, 'qr_ep02_final_test_index.json')
ASS = sys.argv[2] if len(sys.argv) > 2 else os.path.join(F, 'qr_ep02_final_test_work', 'subs.ass')
I = json.load(open(IDX, encoding='utf-8')); off = I['offsets']; total = I['total']
def mmss(t): t = int(t); return '%d:%02d' % (t // 60, t % 60)
def srt_t(t): ms = int(round(t * 1000)); return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
def ass_t(s): h, m, x = s.split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
# ---- 字幕（SRT）：本編の字幕（Main）だけ。確認用の札（Shot）は入れない
ev = []
for l in open(ASS, encoding='utf-8'):
    m = re.match(r'Dialogue: \d+,([^,]+),([^,]+),Main,[^,]*,\d+,\d+,\d+,[^,]*,(.*)', l.strip())
    if m:
        txt = re.sub(r'\{[^}]*\}', '', m.group(3)).replace('\\N', '\n').replace('（間）', '').strip()
        if txt: ev.append((ass_t(m.group(1)), ass_t(m.group(2)), txt))
ev.sort()
with open(os.path.join(HERE, 'qr_ep02_ja.srt'), 'w', encoding='utf-8') as f:
    for k, (a, b, t) in enumerate(ev, 1): f.write('%d\n%s --> %s\n%s\n\n' % (k, srt_t(a), srt_t(b), t))
# ---- もくじ（YouTube のチャプター：最初は 0:00、それぞれ 10 秒以上）
CH = [('op', '冒頭　隠しても読める？'), ('c1', '① 中に入る　この白黒には何が入っている？'), ('c2', '② 見つける　スマホはどこから読み始める？'),
      ('c3', '③ 読む　白黒がどうやって文字になる？'), ('c4', '④ 直す　消えた情報をどう戻す？'), ('c5', '⑤ どこまで隠したら読めなくなる？'), ('end', '結び　最初の疑問に戻る')]
toc = '\n'.join('%s %s' % (mmss(0 if k == 'op' else off[k]), name) for k, name in CH)
ts = sorted(off.values()); assert ts[0] == 0 and all(b - a >= 10 for a, b in zip(ts, ts[1:])), 'もくじの間が10秒未満'
DESC = f"""QRコードは、少し汚れていても、一部が隠れていても読めることがあります。
でも、たった3%の小さな汚れで読めなくなることも。いったい何が違うのでしょうか？
まるロボと一緒に、スマホが見ているQRコードの「中」に入って、確かめてみました。

▼もくじ
{toc}

▼参考にしたページ
・QRコードドットコム（デンソーウェーブ）「QRコードの道のり」 https://www.qrcode.com/history/
・同「誤り訂正機能」 https://www.qrcode.com/about/error_correction.html
・同「特許について」 https://www.qrcode.com/patent.html
・Wikipedia「QR code」 https://en.wikipedia.org/wiki/QR_code
・Wikipedia「Reed–Solomon error correction」 https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction

※動画の中の「どこまで隠すと読めないか」の結果は、パソコン上の3つの読み取りプログラム（ZXing・OpenCV・ZBar）で確かめたものです。スマホのアプリによって、読める・読めないは少し変わることがあります。
QRコードは株式会社デンソーウェーブの登録商標です。

#QRコード #しくみ #まるロボ"""
PIN = """【まとめ】
今回の「HELLO」のQRコードには、箱が26個ありました。
・文字の入った箱：9個
・もしものための予備の箱：17個
予備のおかげで、26個のうち8個までなら、壊れても元に戻せます。

体で隠しても読めたのは、壊れた箱が6個で、8個以内だったから。
たった3%のインクのしずくで読めなかったのは、しずくが12個の箱に散らばって、8個を超えたから。
「どれだけ隠したか」ではなく「いくつの箱が壊れたか」で決まる、というのがポイントです。

身の回りで、ロゴ入りや色つきなど、ちょっと変わったQRコードを見かけたら、ぜひコメントで教えてください！"""
md = f"""# QRコード回　YouTube 一式（本番の組み立ての試しの時刻：全体 {mmss(total)}）

このファイルは make_youtube_kit.py で作っています。長さが変わったら、走らせ直すと時刻と字幕がそろいます。

## タイトル（おすすめ）
**QRコードは欠けてもなぜ読める？ 中に入ってみたら「予備」が17個あった**
（ほかの案は QR回_YouTube案.md）

## 概要欄（そのまま貼る）
```
{DESC}
```

## 固定コメント（公開したら最初に書いて、固定する）
```
{PIN}
```

## 字幕ファイル
- qr_ep02_ja.srt（{len(ev)} 行・日本語）。YouTube Studio →「字幕」→「ファイルをアップロード」→「タイミングあり」で入れる。
- 動画に字幕が焼き込んであるので、自動字幕の代わりに、検索・翻訳・音を消して見る人のために入れる。

## 公開前に確かめること
- もくじの時刻：本番の動画で、それぞれの章の頭に合っているか（このファイルの時刻は本番の組み立ての試しのもの）
- サムネ：thumb_A〜F から選ぶ（本番の絵は PC の 3D のコマに差し替え）
- 概要欄の「登録商標」の一文が入っているか
"""
open(os.path.join(HERE, 'QR回_YouTube一式.md'), 'w', encoding='utf-8').write(md)
print('ok', len(ev), 'subs', mmss(total)); print(toc)
