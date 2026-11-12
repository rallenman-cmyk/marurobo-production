# スマホで見る確認ページ（動画と、1コマずつの絵コンテ）を作る
import json, html
SC = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; P = SC + "/review_page"
man = json.load(open(P + "/panels.json", encoding="utf-8"))
def mmss(t): m, s = divmod(t, 60); return "%d:%04.1f" % (m, s)
def frames(key):
    out = []
    for i, e in enumerate(man[key]):
        out.append(f'''<figure class="frame">
  <img src="img/{e["img"]}" alt="{html.escape(e["note"])}" loading="lazy" width="960" height="540">
  <figcaption><span class="tc">{mmss(e["t"])}</span><span class="no">{i + 1}/{len(man[key])}</span>
    <p class="note">{html.escape(e["note"])}</p><p class="line">{html.escape(e["line"])}</p></figcaption>
</figure>''')
    return "\n".join(out)
def video(name, cap):
    return f'''<div class="player"><video id="v_{name}" controls playsinline preload="metadata" poster="img/poster_{name}.jpg" src="media/{name}.mp4"></video></div>
<p class="vcap">{cap}</p>'''
def sk(name, t, label):
    """動画の中の時刻へ飛ぶリンク（押すと、その動画がその時刻から再生される）"""
    return f'<a class="seek" href="#v_{name}" data-v="v_{name}" data-t="{t}">{label}</a>'
def verdict(key):
    """OK・NG のボタン（押した結果は、このページの記録に残り、Claude が読む）"""
    return (f'<div class="verdict" data-key="{key}" hidden><span class="vq">見た結果：</span>'
            f'<button type="button" class="vb vok" data-v="ok">OK</button><button type="button" class="vb vng" data-v="ng">NG（直してほしい）</button>'
            f'<span class="vs" aria-live="polite"></span>'
            f'<div class="ngbox" hidden><textarea rows="3" placeholder="直してほしい所（例：0:24 のカットで、〜が分かりにくい）"></textarea>'
            f'<button type="button" class="vb vsend">NG を送る</button></div></div>')
CSS = """
.tgrid{display:grid;grid-template-columns:1fr;gap:14px}@media (min-width:760px){.tgrid{grid-template-columns:1fr 1fr}}.tcard{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px}.tcard img,.bimg{width:100%;height:auto;border-radius:8px;display:block}.tcard figcaption{font-size:.92rem;line-height:1.6;margin-top:8px;color:var(--ink)}.tcard small{color:var(--muted)}h3.sub{margin:22px 0 8px;font-size:1.05rem;color:var(--teal)}.bpack{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;margin:0 0 14px}.bpack h3{margin:0 0 8px;font-size:1.05rem}.bicon{display:flex;gap:12px;align-items:center;margin-top:10px}.bicon img{width:84px;height:84px;border-radius:50%;flex:none;box-shadow:0 0 0 1px var(--line)}.bicon p{margin:0;font-size:.92rem;line-height:1.6}.others{line-height:1.7;font-size:.94rem}
.fixreel{margin:14px 0 6px;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}.fixreel h3{margin:0 0 8px;font-size:1.02rem;color:var(--teal)}.fixlist{margin:10px 0 0;padding-left:1.5em;font-size:.92rem;line-height:1.65;color:var(--ink)}.fixlist b{color:var(--amber)}
/* 一列のカード：章ごとに「動画 → 1コマずつの絵コンテ」。スマホの縦画面で上から順に見る */
:root{--bg:#EEF2F4;--surface:#FFFFFF;--ink:#24303A;--muted:#5B6874;--teal:#1F5E66;--teal-soft:#DCEBED;--amber:#B5651D;--line:#D4DCE1;--shadow:0 1px 2px rgba(31,94,102,.08);
--f-head:"Zen Maru Gothic","Hiragino Maru Gothic ProN","Hiragino Sans","Yu Gothic",system-ui,sans-serif;--f-body:"Noto Sans JP","Hiragino Sans","Yu Gothic",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151C21;--surface:#1E272E;--ink:#E6ECEF;--muted:#A3B0BA;--teal:#7CC4CB;--teal-soft:#23383C;--amber:#E2A15E;--line:#2F3B43;--shadow:none;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#151C21;--surface:#1E272E;--ink:#E6ECEF;--muted:#A3B0BA;--teal:#7CC4CB;--teal-soft:#23383C;--amber:#E2A15E;--line:#2F3B43;--shadow:none;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.7}
.wrap{max-width:760px;margin:0 auto;padding-block:24px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}
header h1{font-family:var(--f-head);font-weight:700;font-size:1.6rem;line-height:1.3;margin:0;color:var(--teal);text-wrap:balance}
header p{margin:.4rem 0 0;color:var(--muted)}
.order{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:var(--shadow)}
.order h2{font-family:var(--f-head);font-size:1rem;margin:0 0 6px;letter-spacing:.04em;color:var(--muted)}
.order ol{margin:0;padding-left:1.4em;display:grid;gap:4px}
.order a{color:var(--teal);font-weight:700;text-decoration:none}
.order a:focus-visible,.order a:hover{text-decoration:underline}
.order small{color:var(--muted);font-weight:400}
section{display:grid;gap:12px;scroll-margin-top:16px}
section h2{font-family:var(--f-head);font-weight:700;font-size:1.3rem;margin:0;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
section h2 .when{font-family:var(--f-body);font-size:.85rem;font-weight:500;color:var(--muted);font-variant-numeric:tabular-nums}
.lead{margin:0;min-width:0}
.player{background:#000;border-radius:12px;overflow:hidden;aspect-ratio:16/9;max-width:100%}
.player video{width:100%;height:100%;display:block}
.vcap{margin:-4px 0 0;font-size:.85rem;color:var(--muted)}
details{background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
details>summary{cursor:pointer;padding:12px 16px;font-weight:700;color:var(--teal);list-style:none;display:flex;justify-content:space-between;gap:8px}
details>summary::-webkit-details-marker{display:none}
details>summary::after{content:"開く";font-weight:500;color:var(--muted);font-size:.85rem}
details[open]>summary::after{content:"閉じる"}
details>summary:focus-visible{outline:2px solid var(--teal);outline-offset:2px;border-radius:12px}
.frames{display:grid;gap:18px;padding:0 12px 14px}
.frame{margin:0;display:grid;gap:6px}
.frame img{width:100%;height:auto;aspect-ratio:16/9;border-radius:10px;display:block;background:var(--teal-soft)}
.frame figcaption{display:grid;grid-template-columns:auto 1fr;gap:2px 8px;align-items:baseline;min-width:0}
.tc{font-variant-numeric:tabular-nums;font-size:.8rem;font-weight:700;color:var(--surface);background:var(--teal);border-radius:6px;padding:1px 7px}
.no{font-size:.75rem;color:var(--muted);letter-spacing:.05em;justify-self:end}
.note{grid-column:1/-1;margin:0;font-weight:700;color:var(--teal);line-height:1.5}
.line{grid-column:1/-1;margin:0;color:var(--muted);font-size:.92rem;line-height:1.6}
.line::before{content:"「"}.line::after{content:"」"}
.cmp img{aspect-ratio:auto;height:auto}
.plain{grid-column:1/-1;margin:0;color:var(--muted);font-size:.92rem;line-height:1.6}
.ask{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:12px;padding:14px 16px;display:grid;gap:8px}
.ask h2{font-family:var(--f-head);font-size:1.1rem;margin:0;color:var(--amber)}
.ask ul{margin:0;padding-left:1.2em;display:grid;gap:6px}
footer{font-size:.8rem;color:var(--muted)}
:root{--ok:#1E7A45;--ok-bg:#DDF1E4;--re:#9A4F10;--re-bg:#FBE7D3;--new:#1F5FA8;--new-bg:#DCE8F7;--wip:#55606A;--wip-bg:#E6EAED}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ok:#8FD6A8;--ok-bg:#1F3A2A;--re:#F0B57A;--re-bg:#3D2A17;--new:#8DB8EE;--new-bg:#1C2D44;--wip:#B7C2CA;--wip-bg:#2A333A}}
:root[data-theme="dark"]{--ok:#8FD6A8;--ok-bg:#1F3A2A;--re:#F0B57A;--re-bg:#3D2A17;--new:#8DB8EE;--new-bg:#1C2D44;--wip:#B7C2CA;--wip-bg:#2A333A}
.board{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:var(--shadow);display:grid;gap:10px;scroll-margin-top:16px}
.board h2{font-family:var(--f-head);font-weight:700;font-size:1.2rem;margin:0;color:var(--teal);display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.board h2 .when{font-family:var(--f-body);font-size:.85rem;font-weight:500;color:var(--muted)}
.legend{margin:0;display:flex;flex-wrap:wrap;gap:6px}
.b{display:inline-block;padding:1px 10px;border-radius:999px;font-size:.8rem;font-weight:700;line-height:1.7;white-space:nowrap;font-family:var(--f-body)}
.b.ok{background:var(--ok-bg);color:var(--ok)}.b.re{background:var(--re-bg);color:var(--re)}.b.new{background:var(--new-bg);color:var(--new)}.b.wip{background:var(--wip-bg);color:var(--wip)}
.rows{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.row{border-top:1px solid var(--line);padding-top:8px}
.row > a{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px;text-decoration:none;color:var(--ink)}
.row > a:focus-visible{outline:2px solid var(--teal);outline-offset:2px;border-radius:6px}
.row .nm{font-weight:700;font-family:var(--f-head);font-size:1.05rem}
.row .tm{color:var(--muted);font-size:.85rem;font-variant-numeric:tabular-nums}
.row .b{margin-left:auto}
.row p{margin:2px 0 0;color:var(--muted);font-size:.9rem;line-height:1.6}
.todo{margin:0;padding:10px 12px;border-radius:10px;background:var(--re-bg);color:var(--ink);line-height:1.6}
.decided{margin:0;padding:0 16px 12px 2.2em;display:grid;gap:6px;font-size:.92rem}
[hidden]{display:none !important}
a.seek{color:var(--teal);font-weight:700;text-decoration:underline;text-underline-offset:3px;font-variant-numeric:tabular-nums;white-space:nowrap}
a.seek::before{content:"▶ ";font-size:.75em}
.verdict{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:6px}
.verdict .vq{font-size:.85rem;color:var(--muted)}
.vb{min-height:40px;padding:6px 16px;border-radius:10px;border:2px solid var(--line);background:var(--surface);color:var(--ink);font:inherit;font-weight:700;cursor:pointer}
.vb.vok[aria-pressed="true"]{background:var(--ok-bg);color:var(--ok);border-color:var(--ok)}
.vb.vng[aria-pressed="true"]{background:var(--re-bg);color:var(--re);border-color:var(--re)}
.vb:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
.vb:disabled{opacity:.55;cursor:default}
.vs{font-size:.85rem;color:var(--muted)}
.ngbox{flex-basis:100%;display:grid;gap:6px}
.ngbox textarea{width:100%;box-sizing:border-box;font:inherit;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
html{scroll-behavior:smooth}
"""
import os
HAVE_V7 = os.path.exists(P + "/media/ch04_check_v7.mp4")
HAVE_C3V8 = os.path.exists(P + "/media/ch03_check_v8_voice.mp4")   # 第3章：電車の場面がカメラの動く絵になった版
HAVE_V8 = os.path.exists(P + "/media/ch04_check_v8.mp4")            # 第4章 v8：スマホの台を大きく（案B）＋6:24 は ②
HAVE_C8V4 = os.path.exists(P + "/media/ch08_check_v4.mp4"); HAVE_OPV5 = os.path.exists(P + "/media/ch0102_check_v5.mp4"); HAVE_OPV6 = os.path.exists(P + "/media/ch0102_check_v6.mp4"); HAVE_C7V2 = os.path.exists(P + "/media/ch07_check_v2.mp4"); HAVE_C8V3 = os.path.exists(P + "/media/ch08_check_v3.mp4"); HAVE_SUM = os.path.exists(P + "/media/summary_check_v1.mp4"); HAVE_SUM2 = os.path.exists(P + "/media/summary_check_v2.mp4")   # v2：本番（PC の絵）・間を直した・新しい字幕
RENOTE = "11月9日：字幕と同じ文の札（上の方の字）を消した版に組み直しました（絵と声はそのまま）。"
HAVE_FIX = os.path.exists(P + "/media/fix_reel_1109b.mp4") and os.path.exists(P + "/media/fix_list_1109b.json")   # 11月9日 夜の直し（25か所＋効果音 2 つ）
FX = json.load(open(P + "/media/fix_list_1109b.json", encoding="utf-8")) if HAVE_FIX else None
SUBNOTE = "11月9日：メインの字幕を大きく（太いふち）し、1行25字・2行まで、改行を文の切れ目にそろえて組み直しました（長い文は声の区切りで次の字幕に）。"
def resubbed(f):                                                        # 新しい字幕で組み直した本番か（前の版 *_before_subs.mp4 より新しい）
    b = f.replace(".mp4", "_before_subs.mp4")
    return os.path.exists(f) and os.path.exists(b) and os.path.getmtime(f) > os.path.getmtime(b) + 1
SUBN = {k: (SUBNOTE if resubbed(f) else "") for k, f in [("ch03", SC + "/stage/final/ch03_final_1080.mp4"), ("ch04", SC + "/stage/final/ch04_final_1080.mp4"),
        ("ch05", SC + "/stage/ch03/ch5_final/ch05_final_1080.mp4"), ("ch06", SC + "/stage/final/ch06_final_1080.mp4")]}
HAVE_C6 = os.path.exists(P + "/media/ch06_check_v1.mp4"); HAVE_C7 = os.path.exists(P + "/media/ch07_check_v1.mp4"); HAVE_C8 = os.path.exists(P + "/media/ch08_check_v1.mp4")
CH04_NAV = '<li><a href="#ch04">第4章 v8（スマホを大きく・6:24 は ②）</a> <small>4分13秒・スマホが出る所と 6:24 を見てください</small></li>' if HAVE_V8 else '<li><a href="#ch04">第4章 ペアリング（v7 は OK。スマホを大きくした v8 は描き直し中）</a> <small>4分11秒</small></li>' if HAVE_V7 else '<li><a href="#ch04">第4章 ペアリング v6（v7 を描き直し中）</a> <small>4分11秒</small></li>'
CH04_V8 = f'''<section id="ch04">
  <h2>第4章 ペアリング v8 <span class="when">2:55.8〜7:09</span></h2>
  <p class="lead"><strong>スマホの台を大きくしました（案B：2.4m）。</strong>ケースの幅 1.20m に対して、本物のスマホとケースの大きさの比に近くなり、ひと目でスマホと分かります。寄りや高い所からの画では、画面の「Bluetooth」「ペアリング中…」まで見えます。<strong>6:24 の声は ②</strong>（「…青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません」）にして、その場面を 2.25 秒のばし、上の札も言葉に合わせて「青と赤」「白が2回」「うすい紫」の順に出します。3D は全コマ描き直しました。ほかは OK をいただいた v7 と同じです。</p>
  <figure class="frame cmp"><img src="img/ch04v8_phone_size.jpg" alt="スマホの台の大きさの比べ（今・案A・案B）" loading="lazy" width="1472" height="1432">
    <figcaption><p class="note">スマホの台の大きさ：左から 前（1.34m）・案A（2.0m）・案B（2.4m、決定）</p></figcaption></figure>
  {video("ch04_check_v8", "声入り。スマホの台を大きくし（案B）、6:24 を ② にしました。")}
</section>'''
CH04_SECTION = CH04_V8 if HAVE_V8 else f'''<section id="ch04">
  <h2>第4章 ペアリング v7 <span class="when">2:55.8〜7:07</span></h2>
  <p class="lead">v7 の直しは OK をいただきました。<strong>スマホの台を大きくした v8（案B）を描き直し中です（日本時間19時ごろに、ここを v8 に差し替えます）。</strong>下の動画は v7（スマホが小さい版）です。</p>
  <figure class="frame cmp"><img src="img/ch04v8_phone_size.jpg" alt="スマホの台の大きさの比べ（今・案A・案B）" loading="lazy" width="1472" height="1432">
    <figcaption><p class="note">スマホの台の大きさ：左から 今（1.34m）・案A（2.0m）・案B（2.4m、決定）</p>
    <p class="plain">ケースの幅は 1.20m。案B は本物のスマホとケースの大きさの比に近く、寄りや高い所からの画では画面の「Bluetooth」「ペアリング中…」まで見えます。</p></figcaption></figure>
  {video("ch04_check_v7", "声入り。3D は、開いたイヤホンケースで全コマ描き直しました。")}
  <details open>
    <summary>直したところ（前と後）</summary>
    <div class="frames">
      <figure class="frame cmp"><img src="img/ch04v7_cmp1.jpg" alt="○と△の出方の前と後" loading="lazy" width="1316" height="420">
        <figcaption><span class="tc">3:43.7</span><p class="note">○と△を、言葉に合わせて一つずつ・大きく</p>
        <p class="plain">「自分の組に」で自分の組が光り「丸印」で○、「隣の組に」→「三角印」で△。印は白い丸のシールで約2倍。効果音も印ひとつに1回です（前は0.25秒おきに4回）。</p></figcaption></figure>
      <figure class="frame cmp"><img src="img/ch04v7_cmp2.jpg" alt="薄い紫の札の前と後" loading="lazy" width="1316" height="420">
        <figcaption><span class="tc">6:24.7</span><p class="note">白が2回で薄い紫：中身を式で見せる</p>
        <p class="plain">隣が混ぜられるのは、見えた二つ（白＋青・白＋赤）だけ。混ぜると青と赤も入るので紫にはなりますが、白は色を薄めるだけなので、白が2回分のぶん薄い紫になります。二台の鍵は白が1回分なので濃い紫です。</p></figcaption></figure>
      <figure class="frame cmp"><img src="img/ch04v7_cmp3.jpg" alt="車内の印の前と後" loading="lazy" width="1316" height="420">
        <figcaption><span class="tc">6:54.4</span><p class="note">車内の印：記号をやめて、組ごとの色の鍵</p>
        <p class="plain">主人公は二台の鍵と同じ紫、隣の人は橙（ペアリングのあとの図と同じ色）、ほかの人は組ごとに別の色です。</p></figcaption></figure>
      <figure class="frame cmp"><img src="img/ch04v7_cmp4.jpg" alt="イヤホンケースの前と後" loading="lazy" width="1316" height="420">
        <figcaption><span class="tc">4:44.7</span><p class="note">イヤホンケース：ふたを開けて、中のイヤホンを見せる</p>
        <p class="plain">ふたは後ろで開き、中に白いイヤホンが2つ（耳の先は内向き）。薄い紫の場面は、札の下にケースのふたが見えるようカメラを少し上向きにしました。</p></figcaption></figure>
    </div>
  </details>
</section>''' if HAVE_V7 else f'''<section id="ch04">
  <h2>第4章 ペアリング v6 <span class="when">2:55.8〜7:07</span></h2>
  <p class="lead">よく見るペアリング画面 →「中では？」→ 3D の実験 → 「接続しました」と鍵のかかった荷物。いただいた4点（○△の出方・薄い紫・車内の印・イヤホンケース）は直していて、3D を描き直し中です。描き終わったら、ここを v7 に差し替えます。</p>
  {video("ch04_check_v6", "前の版（v6）です。")}
</section>'''
C3_BODY = ('''<p class="lead"><strong>OK をいただいた版から、電車の場面だけを新しくしました。</strong>前は静止画にゆっくり寄る形でしたが、時間が止まった車内を、カメラだけが動いて撮ります（1:21〜1:40 と 2:33.6〜2:37.8）。スマホの画面 → 耳のイヤホン → 画面の帯（音楽のデータ）→ 引いて止まった電波の波面、の順です。本番（PC で 1080p）は、この形で描きます。</p>
  ''' + video("ch03_check_v8_voice", "声入り。電車の場面のほかは、OK をいただいた版と同じです。")) if HAVE_C3V8 else ('''<p class="lead">「番号は、曲の順番です」で上に曲の順番の帯（03→04→05 が光る）。まるロボの動きは新しい時刻に合わせて描き直し、最後に「二つの疑問」の画を足しました。そのまま第4章の「まずは、一つ目の疑問から」へつながります。<strong>OK をいただきました。</strong>本番（PC で 1080p）の前に、電車の場面をカメラが動く絵にします。</p>
  ''' + video("ch03_check_v7_voice", "声入り。絵は OK をいただいた版と同じです。字幕は声の長さに合わせました。"))
page = f'''<title>まるロボ 確認ページ</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Zen+Maru+Gothic:wght@500;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
  <h1>Bluetooth イヤホンの回：確認用の動画と絵コンテ</h1>
  <p>声・字幕・効果音つきの確認用です（低画質）。<strong>いちばん上の「いまの状態」で、章ごとに OK か確認待ちかが分かります。</strong>章の名前を押すと、その章へ飛びます。</p>
</header>
<nav class="order" aria-label="見る順番">
  <h2>おすすめの見る順番</h2>
  <ol>
    <li><a href="#ask">見ていただきたいこと・決まったこと</a> <small>まとめの絵コンテ・今日決まったこと</small></li>
    {CH04_NAV if HAVE_V8 else ""}
    <li><a href="#ch0102">第1〜2章 v4（第2章の終わりだけ直した）</a> <small>1分21秒・1:14〜1:21 だけ見てください</small></li>
    <li><a href="#ch06">{"第6章 送り直し（3D・声入り）" if HAVE_C6 else "第6章 絵コンテ（OK 済み。3D を描いています）"}</a> <small>{"1分20秒" if HAVE_C6 else "15コマ"}</small></li>
    <li><a href="#ch07">{"第7章 バッファ（3D・声入り）" if HAVE_C7 else "第7章 絵コンテ（OK 済み。3D を描いています）"}</a> <small>{"2分51秒" if HAVE_C7 else "14コマ"}</small></li>
    <li><a href="#ch08">{"第8章 ゲームの例（声入り）" if HAVE_C8 else "第8章 絵コンテ（OK 済み。作っています）"}</a> <small>{"1分59秒" if HAVE_C8 else "19コマ"}</small></li>
    <li><a href="#summary">まとめ 絵コンテ（新しい）</a> <small>11コマ</small></li>
    {"" if HAVE_V8 else CH04_NAV}
    <li><a href="#ch03">{"第3章 v8（OK 済み）" if HAVE_C3V8 else "第3章（声入り・OK 済み）"}</a> <small>1分35秒</small></li>
    <li><a href="#ch05">第5章 v2（声入り・OK 済み）</a> <small>3分48秒・37コマ</small></li>
  </ol>
</nav>

{CH04_SECTION}

<section id="ch03">
  <h2>第3章 台本 v2 版 <span class="when">1:21〜2:55.8</span></h2>
  {C3_BODY}
</section>

<section id="ch05">
  <h2>第5章 電波の重なりと周波数の切り替え <span class="when">7:07〜10:55</span></h2>
  <p class="lead">窓＝電波のチャンネル。スマホとイヤホンは、使う窓へ光を向けます。二台が同じ窓を照らすと、荷物がその窓を通って届きます。この仕組みひとつで、章の最後まで進めます。</p>
  {video("ch05_check_v2_voice", "声入り。v2：荷物は、二台がつないだ光の道（スマホ → 光っている窓 → イヤホン）だけを通ります。ぶつかったときや窓が合わないときは、その場で落ちて届きません。最後の「？」は、その落ちた荷物に付けました。")}
  <details>
    <summary>絵コンテ 37コマ</summary>
    <div class="frames">
{frames("ch05")}
    </div>
  </details>
</section>

<section id="ch06">
  <h2>第6章 送り直し（再送） <span class="when">10:55〜12:15</span></h2>
  {(f'''<p class="lead">絵コンテどおり 3D で作りました。受付ボックスの中の「調べる門」が光りながら荷物をなぞり、受付の灯が赤（1回目）／緑（2回目）。スマホの台の窓の右に<strong>返事ランプ</strong>を付けました（まわりの24の小さな灯が順に点く＝返事を待つ時間、返事が届くとまんなかが緑）。返事の光は、受付の灯からスマホの返事ランプまで約71mを2.7秒で飛びます。絵コンテに足したカットは二つ：返事が来なかったあと<strong>まるロボが細い橋を渡ってスマホへ戻る</strong>所（来たときと逆向き）と、最後に<strong>巨大イヤホンの耳の先へカメラが飛び込み</strong>、第7章のイヤホンの中へつなぐ所です。曲は章のあいだずっと小さく鳴っていて、「今の音楽、聞いていましたか？」から少し大きくなります（まるロボの揺れは曲の拍に合わせました）。</p>
  <p class="lead"><strong>直しました（11月9日 0時台）：</strong></p>
  <ul class="plain"><li><strong>動画の {sk("ch06_check_v1", 7, "0:07")}（本編 11:02）</strong>「受け取る側は、」で、巨大イヤホンが丸ごと見える引きを入れ、札「受け取る側：イヤホン」を出してから、受付ボックスに寄ります（前は荷物を積んだ直後に受付ボックスのアップになり、どちら側か分かりにくかった）。</li><li><strong>動画の {sk("ch06_check_v1", 20.2, "0:20")}（本編 11:15）</strong>「返事が来ないので、スマホも、」は、巨大スマホが丸ごと見える引きから返事ランプへ寄り、札「送る側：スマホ」を出します。</li><li>まるロボが細い橋を渡る2つのカット（動画の {sk("ch06_check_v1", 26.7, "0:27")}・{sk("ch06_check_v1", 34.0, "0:34")}）で、始めの約1秒が暗い壁でふさがって見えていたのを直しました（カメラが運河の外の地面の中から動き始めていた）。</li></ul>
  ''' + video("ch06_check_v1", "声入り。本番と同じ光（低画質）。")) if HAVE_C6 else '<p class="lead">第3章の舞台で、六番の荷物を追いかけます。返事ランプ・待ち時間の輪・返事の合図（光）は、まだ 3D に無いので、絵の上に描いた仮のものです。</p>'}
  <details{"" if HAVE_C6 else " open"}>
    <summary>絵コンテ 15コマ</summary>
    <div class="frames">
{frames("ch06")}
    </div>
  </details>
</section>

<section id="ch07">
  <h2>第7章 バッファ <span class="when">12:15〜15:06</span></h2>
  {(f'''<p class="lead">イヤホンの中の部屋を 3D で作りました。鳴っている荷物は下の再生装置の口へゆっくり沈み（荷物一つ＝31秒）、待っている荷物はその上に積み重なって一緒に下がります。すき間なく次へ移るので、曲は途切れません。塔の左の柱の小さな灯が、たまっている量の目盛りです。<strong>絵コンテから一つ変えました</strong>：絵コンテでは、まるロボが中の通路まで 06 を運んでいましたが、第6章でまるロボは外で受付ボックスに荷物を渡しているので、06 は受付ボックスから中の昇降機で上がってくる形にしました（まるロボは中に出ません。戻したい場合はお知らせください）。後半は、最後の 08 が沈みきると再生装置が空になり、灯が消えて曲がぷつっと止まります。</p>
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk("ch07_check_v1", 0, "0:00 イヤホンの中")}・{sk("ch07_check_v1", 20.4, "0:20 塔と再生装置")}・{sk("ch07_check_v1", 41.3, "0:41 昇降機で 06 が届く")}・{sk("ch07_check_v1", 54.9, "0:55 バッファの札")}・{sk("ch07_check_v1", 69.3, "1:09 目盛り")}・{sk("ch07_check_v1", 104.1, "1:44 09 が届かない")}・{sk("ch07_check_v1", 130.8, "2:11 空になり、音が止まる")}・{sk("ch07_check_v1", 144.0, "2:24 二つを並べる")}・{sk("ch07_check_v1", 160.3, "2:40 電車")}</p>
  ''' + video("ch07_check_v1", "声入り。PC で描いた本番の絵を、確認用に小さくしたものです（左上の場面名・右上の注記は本番では消えます）。")) if HAVE_C7 else '<p class="lead">前半は OK をいただいた 30 秒の見本の舞台そのまま。後半の「09 が届かず、タワーが空になって音が途切れる」は見本に無い場面なので、絵の上に重ねた仮の絵です（番号や空の再生装置は 3D で描き直します）。</p>'}
  <details{"" if HAVE_C7 else " open"}>
    <summary>絵コンテ 14コマ</summary>
    <div class="frames">
{frames("ch07")}
    </div>
  </details>
</section>

<section id="ch08">
  <h2>第8章 ためる余裕と、すぐ鳴ること（ゲームの例） <span class="when">15:06〜17:05</span></h2>
  {(f'''<p class="lead">前半は第7章の塔です。空になった塔 →（時間を飛ばして）01〜03 が待っていて 04 が届く。塔がいっぱいになるまで再生装置は鳴らさず、灯は琥珀（ためている）。いっぱいになってから緑で鳴らし始めます。そのあとは 2D の図：時間の帯（少しためる／たくさんためる）とてんびん、ゲームのパンチ（ぴったり／音が遅れる。10分の1のゆっくり再生）、流れ・札・棒。最後は塔の画に戻って「今回は、音を待たせる時間に注目した」。</p>
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk("ch08_check_v2", 0, "0:00 空になった塔")}・{sk("ch08_check_v2", 9.0, "0:09 いっぱいで鳴らし始める")}・{sk("ch08_check_v2", 21.2, "0:21 時間の帯・てんびん")}・{sk("ch08_check_v2", 41.0, "0:41 ゲーム")}・{sk("ch08_check_v2", 47.4, "0:47 ぴったり合う場合")}・{sk("ch08_check_v2", 55.6, "0:55 音が遅れてくる場合")}・{sk("ch08_check_v2", 71.9, "1:12 操作してから音が決まる")}・{sk("ch08_check_v2", 97.9, "1:38 両方を考える")}・{sk("ch08_check_v2", 114.1, "1:54 塔に戻る")}</p>
  ''' + video("ch08_check_v2", "声入り。塔は PC で描いた本番の絵、図は 2D（確認用に小さくしたもの。左上の場面名・右上の注記は本番では消えます）。")) if HAVE_C8 else '<p class="lead">前半は第7章の貯蔵タワーで「もっとためれば？ → 余裕は増えるが、鳴るのが遅い」。後半は OK をいただいた案どおり、主人公と同じピクトグラムの人がゲームの中でパンチを出し、下の「操作 → 音」の時間の帯で、音が遅れて届く様子を見せます。ゲーム画面と時間の帯は 2D で作ります。</p>'}
  <details{"" if HAVE_C8 else " open"}>
    <summary>絵コンテ 19コマ</summary>
    <div class="frames">
{frames("ch08")}
    </div>
  </details>
</section>

<section id="summary">
  <h2>まとめ <span class="when">17:05〜18:15</span></h2>
  <p class="lead"><strong>絵コンテは OK をいただきました（札の文字はもう少し大きくします）。いま作っています。</strong>二つの疑問の答えと三つの工夫は、これまでの章の絵を並べてふり返ります（新しく作るのは並べ方と札だけ）。最後は止まった電車に戻り、まるロボが一時停止ボタンをもう一度押して時間を元に戻します（第2章の逆）。色と音が戻ると、主人公はまだ同じ曲で踊っていて、まわりの人がちらっと見ておしまい。電車の場面は、第1〜2章の舞台で新しく描きます（下の電車の絵は、第1〜2章の確認用の簡易描画を借りています）。</p>
  <details open>
    <summary>絵コンテ 11コマ</summary>
    <div class="frames">
{frames("summary")}
    </div>
  </details>
</section>

<section id="ch0102">
  <h2>第1〜2章 v4（声入り） <span class="when">0:00〜1:21</span></h2>
  <p class="lead">v4：第2章の終わり（1:14〜1:21）の無音を縮めました。「まずは、中をのぞいてみます。」をカメラがスマホへ寄り始める所（1:14.85）へ移し、1:18.2 から、まるロボがスマホの見やすい所へ横に4歩（足音。止まった世界で鳴るのはまるロボだけ）。音のない所は 7 秒 → 約 2 秒です。ほかは OK をいただいた版と同じです。</p>
  {video("ch0102_check_v4_voice", "声入り。この確認用の動画は簡易描画です（本番は第3章と同じ光で、PC で描きます）。")}
</section>

<aside class="ask" id="ask">
  <h2>見ていただきたいこと</h2>
  <ul>
    {'<li><a href="#ch04">第4章 v8</a>：大きくしたスマホの台（4:44 から）と、6:24 の ② の言い方・札の出る順。</li>' if HAVE_V8 else ''}
    {'<li><a href="#ch06">第6章</a>（3D・声入り、1分20秒）：直した 0:07・0:20 で、スマホ側／イヤホン側がひと目で分かるか。</li>' if HAVE_C6 else ''}
    <li><a href="#summary">まとめの絵コンテ</a>（11コマ）：この進め方でよいか。</li>
  </ul>
  <h2>決まったこと（11月8日）</h2>
  <ul>
    <li>第4章 6:24 は②（「…青と赤は入りますが、白が二回分入るので、薄い紫にしかなりません」）。その場面を 2.25 秒のばし、上の札も「青と赤」「白が2回」「うすい紫」の順に、言葉に合わせて出します。{"スマホを大きくした第4章 v8 に入れました（上の第4章）。" if HAVE_V8 else "スマホを大きくした第4章 v8 に入れて、21時ごろに載せます。"}<audio controls preload="none" src="media/ch04_624_compare.mp3" style="display:block;width:100%;margin-top:6px"></audio></li>
    <li>第2章の終わり（1:14〜1:21）：「まずは、中をのぞいてみます。」をカメラがスマホへ寄り始める所（1:14.85）へ移し、まるロボがスマホの見やすい所へ横に4歩（足音）。音のない所は 7 秒 → 約 2.4 秒に。直しました（下の第1〜2章 v4）。</li>
    <li>第3章 v8（電車の場面）・第5章・第1〜2章は OK。</li>
    <li>第6章（送り直し）・第7章（バッファ）・第8章（ゲームの例）は、絵コンテどおりに作ります。{"第6章は 3D でできました（上の第6章）。" if HAVE_C6 else "3D の舞台はできていて、確認用の動画を描いているところです（第6章は今夜、第7・8章は明日の朝の見込み）。"}</li>
    <li>第4章のスマホの台は案B（2.4m）。</li>
  </ul>
</aside>
<footer>動画は確認用の低画質です。本番は PC（RTX 3050）で描きます。</footer>
</div>
'''
# ---------------------------------------------------------------- いまの状態（2026-11-09〜）：章ごとの状態を一番上に。章は話の順に
import re, datetime
STAMP = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).strftime("%-m月%-d日 %-H:%M 時点")
STATUS = [   # （場所, 名前, 本編の時刻, 色, 札, 一行の説明, OK・NG のボタンの名前＝見てもらう版）
    ("ch0102", "第1〜2章", "0:00〜1:21", "new", "本番（まるロボ入り）→ 確認待ち", f"PC で描いた本番の絵で組みました（通路の床のまるロボ・新しい字幕）：{sk('ch0102_check_v6', 0.3, '0:00 見回す')}・{sk('ch0102_check_v6', 5.9, '0:06 動画を一緒に見上げる')}・{sk('ch0102_check_v6', 24.9, '0:25 みんなとノリノリ')}。最初の 2 か所のつなぎ目のブレ（ビュン）もなくしました（{sk('ch0102_check_v6', 3.0, '0:03')}・{sk('ch0102_check_v6', 5.2, '0:05')}）。", "ch0102_v6") if HAVE_OPV6 else
    (("ch0102", "第1〜2章", "0:00〜1:21", "new", "冒頭にまるロボ → 確認待ち", f"ご提案どおり、最初からまるロボを出しました（通路の床。網棚はつり革の陰で見えにくかったため）：{sk('ch0102_check_v5', 0.3, '0:00 見回す')}・{sk('ch0102_check_v5', 5.9, '0:06 動画を一緒に見上げる')}・{sk('ch0102_check_v5', 24.9, '0:25 みんなとノリノリ')}。まるロボが映るカットだけ簡易描画です。", "ch0102_v5")
     if HAVE_OPV5 else
     ("ch0102", "第1〜2章", "0:00〜1:21", "ok", "OK・本番完成", "本番（1080p）ができました。", None)),
    ("ch03", "第3章", "1:21〜2:55.8", "ok", "OK・本番完成", "本番（1080p）ができました。" + SUBN["ch03"], None),
    ("ch04", "第4章", "2:55.8〜7:09", "ok", "OK・本番完成", "本番（1080p・4分13秒）ができました。" + RENOTE + SUBN["ch04"], None),
    ("ch05", "第5章", "7:07〜10:55", "ok", "OK・本番完成", "本番（1080p）ができています。" + RENOTE + SUBN["ch05"], None),
    ("ch06", "第6章", "10:55〜12:15", "ok", "OK・本番完成", "本番（1080p・1分20秒）ができました。" + RENOTE + SUBN["ch06"], None),
    ("ch07", "第7章", "12:17〜15:08", "ok", "OK・本番完成", "本番（1080p・2分51秒・まるロボ入り）ができました。" + SUBNOTE, None),
    ("ch08", "第8章", "15:08〜17:07", "ok", "OK・本番完成", "本番（1080p・1分59秒・塔と天びんのまるロボ入り）ができました。" + SUBNOTE, None),
    ("summary", "まとめ", "17:05〜18:15", "re", "直した → 確認待ち", f"ご指摘の声の間を直しました：「二つ目の疑問は…」を 1.35 秒遅らせ、前の間（{sk('summary_check_v2', 17.8, '0:18〜')}）を 0.15 → 1.5 秒、後ろの間（{sk('summary_check_v2', 24.6, '0:25〜')}）を 2.55 → 1.2 秒に。字幕も新しい決まり（1行25字・文字を大きく）。電車の場面は PC で描いた本番の絵です。", "summary_v2") if HAVE_SUM2 else
    (("summary", "まとめ", "17:05〜18:15", "new", "はじめての確認待ち", f"二つの疑問の答えと三つの工夫を、各章の本番の絵でふり返ります（{sk('summary_check_v1', 3.3, '0:03')}）。最後は電車に戻り、まるロボが一時停止ボタンに跳び乗って時間が動き出す → 主人公はまだ同じ曲でノリノリ、まわりがちらっと見る（{sk('summary_check_v1', 53.8, '0:54')}・{sk('summary_check_v1', 61.4, '1:01')}）。", "summary_v1")
     if HAVE_SUM else
     ("summary", "まとめ", "17:05〜18:15", "wip", "作っている", "前半の札は、各章の本番の絵で作りました（文字を大きく）。最後の電車の場面をこちらで描いていて、確認用動画は今日 14時ごろここに載せます（本番の 1080p は PC で描きます）。", None)),
]
if HAVE_FIX:                                                           # 11月9日 夜の直し：章ごとの新しい時刻と、直した所
    _K = ["ch0102", "ch03", "ch04", "ch05", "ch06", "ch07", "ch08", "sum"]; _st = FX["starts"]
    def _mm(x): return "%d:%02d" % (int(x // 60), int(x % 60))
    _SPAN = {("summary" if k_ == "sum" else k_): "%s〜%s" % (_mm(_st[k_]), _mm(_st[_K[j_ + 1]] if j_ + 1 < len(_K) else FX["total"])) for j_, k_ in enumerate(_K)}
    _BY = {}
    for f_ in FX["fixes"]: _BY.setdefault("summary" if f_["ch"] == "sum" else f_["ch"], []).append(f_)
    STATUS = [((k, nm, _SPAN.get(k, tm), "re", "直した → 確認待ち", "11月9日 夜のご指摘を直しました：" + "／".join("%s（今 %s）%s" % (f_["old"], f_["new"], f_["what"]) for f_ in _BY[k]) + "。下の「直した所だけの確認動画」で見られます。", None)
               if k in _BY else (k, nm, _SPAN.get(k, tm), c, lab, note, key)) for k, nm, tm, c, lab, note, key in STATUS]
asd = re.search(r'<aside class="ask" id="ask">.*?</aside>\n', page, re.S)
decided = re.search(r'<h2>決まったこと[^<]*</h2>\s*<ul>(.*?)</ul>', asd.group(0), re.S).group(1) if asd else ""
decided = ('<li>冒頭：最初の 2 か所（全景 → 音楽を聴いている人 → 動画を見ている人）のつなぎ目のブレ（「ビュン」）をなくす。ほかのカット（同じ場面でカメラを振る所）とまとめはそのまま（11月9日）。</li><li>まとめ：0:20 の間（次の声まで短い）と 0:26 の間（長い）を直す（11月9日）。</li><li>メインの字幕は 1行25字まで・2行まで、文字はもう少し大きく（太い紺のふち）。長いものは次の字幕へ。改行は文の切れ目で（11月9日）。</li><li>第7章（まるロボ入り）・第8章 v4（天びんのまるロボ）は OK。冒頭からまるロボを出す（11月9日）。</li><li>第7章（と第8章の塔）にまるロボを出す：06 と一緒に入り、見守りながら一喜一憂。字幕と同じ文の札は、第4〜8章とまとめのすべてでなくす（11月9日）。</li><li>第4章 v8・第6章（直した版）は OK（11月9日）。</li><li>まとめの絵コンテは OK。札の文字はもう少し大きく（11月9日）。</li><li>3D の本番は PC で描く（3本同時）。受け渡しは Google ドライブ（11月9日）。</li>' + decided)
page = page.replace(asd.group(0), "") if asd else page
page = re.sub(r'<nav class="order".*?</nav>\n', '', page, flags=re.S)
head, rest = page.split("</header>", 1); head += "</header>\n"
blocks = {m.group(1): m.group(0) for m in re.finditer(r'<section id="(\w+)">.*?</section>', rest, re.S)}
V7, V8, VS = "ch07_check_v2", "ch08_check_v3", ("summary_check_v2" if HAVE_SUM2 else "summary_check_v1")
if HAVE_C7V2:
    blocks["ch07"] = f"""<section id="ch07">
  <h2>第7章 バッファ <span class="when">12:15〜15:06</span></h2>
  <p class="lead"><strong>11月9日のご指摘で作り直しました（まるロボ入り）。</strong>字幕と同じ文の札はなくしました（2:39 の札の重なりもなくなりました）。言葉「バッファ」は、塔の上の 3D の札を大きくして、声と同時に光らせます。まるロボは、第6章で送り直した 06 と一緒に手前から入ってきて、再生装置の前で見守ります：06 が間に合ってうなずく → 一歩下がって札を見上げる → 07 が上がるのを目で追う → 曲に合わせて揺れる → 09 が来ないと口をのぞき込み、目盛りを見て待つ → 残り一つでそわそわ → 音が止まった瞬間にびっくりして、がっくり。</p>
  <p class="lead"><strong>この動画は、動きを見るための簡易描画です</strong>（光・影・色は本番と違います）。本番の光での札は、動画の下の静止画です。OK なら、この動きのまま PC で本番を描きます。</p>
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk(V7, 0, "0:00 イヤホンの中")}・{sk(V7, 45.8, "0:46 まるロボが入ってくる")}・{sk(V7, 60.7, "1:01 下がって札を見上げる")}・{sk(V7, 63.7, "1:04 札「バッファ」が光る")}・{sk(V7, 69.7, "1:10 07 が上がるのを見る")}・{sk(V7, 84.8, "1:25 曲に合わせて揺れる")}・{sk(V7, 104.3, "1:44 09 が来ない")}・{sk(V7, 121.4, "2:01 残り一つ")}・{sk(V7, 135.0, "2:15 音が止まる")}・{sk(V7, 144.0, "2:24 二つを並べる")}・{sk(V7, 160.3, "2:40 電車")}</p>
  {video(V7, "声入り・簡易描画（光と色は本番と違います）。左上の場面名・右上の注記は本番では消えます。")}
  <figure class="frame cmp"><img src="img/ch07_sign_onoff.jpg" alt="本番の光での札「バッファ」。左は言葉の前、右は光ったところ" loading="lazy" width="1280" height="360">
    <figcaption><p class="note">本番の光（PC と同じ描き方）での札。左：言葉の前（暗い）、右：「…バッファです」で光ったところ。</p></figcaption></figure>
  <details>
    <summary>絵コンテ 14コマ</summary>
    <div class="frames">
{frames("ch07")}
    </div>
  </details>
</section>"""
if HAVE_OPV5:
    VO = "ch0102_check_v6" if HAVE_OPV6 else "ch0102_check_v5"
    blocks["ch0102"] = f"""<section id="ch0102">
  <h2>{"第1〜2章 本番（冒頭からまるロボ）" if HAVE_OPV6 else "第1〜2章 v5（冒頭からまるロボ）"} <span class="when">0:00〜1:21</span></h2>
  <p class="lead"><strong>最初の 3 秒から、まるロボが出るようにしました（ご提案：最初で離脱させないため）。</strong>初めは網棚の上で試しましたが、つり革の陰で目しか見えなかったので、明るい通路の床に置きました。ほかの章と同じく、音は出しません（足音は 0:50 から、今までどおり）。</p>
  <ul class="lead">
    <li><strong>0:00〜0:03</strong>：通路の真ん中で、こちらを向いて車内を見回す（アンテナの灯が 3 回光る）。字幕にはかかりません。</li>
    <li><strong>0:06「動画を見ている人」</strong>：すぐ横から、その人の動画を一緒に見上げる。</li>
    <li><strong>0:08〜0:12</strong>：奥のカメラから見ると、両側の乗客のスマホを見上げて、こちらを向く。</li>
    <li><strong>0:25〜0:30（みんなが踊る想像）</strong>：カメラの近くで、みんなと一緒にノリノリ → 0:30 に現実へ戻ると画面の外にいて、踊っているのは主人公だけ。</li>
    <li>0:50 から通路を歩いてきてボタンに跳び乗る所は、前と 1 コマも変わりません。</li>
  </ul>
  {('<p class="lead"><strong>この動画は本番（1080p・PC で描いた絵）を小さくしたものです。</strong>まるロボのカットも本番の光になりました。字幕は新しい決まり（1行25字・大きく）。最初の 2 か所（全景 → 音楽を聴いている人 → 動画を見ている人）のつなぎ目のブレ（ビュン）をなくしました。ほかのカットのカメラを振る所はそのままです。</p>') if HAVE_OPV6 else '''  <p class="lead"><strong>この動画は確認用です。</strong>まるロボが映るカット（0:00〜0:04・0:06〜0:13・0:25〜0:30）だけ簡易描画で、光と色は本番と違います。ほかのカットは前の本番の絵です。OK なら、この 3 か所を PC で本番の光で描き直します（約 15〜30 分）。</p>'''}
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk(VO, 0, "0:00 見回す")}・{sk(VO, 5.9, "0:06 動画を一緒に見上げる")}・{sk(VO, 7.6, "0:08 スマホを見上げる")}・{sk(VO, 24.9, "0:25 みんなとノリノリ")}・{sk(VO, 29.9, "0:30 現実：踊るのは主人公だけ")}・{sk(VO, 50.8, "0:51 通路を歩いてくる")}</p>
  {video(VO, "本番を 1280×720 に小さくしたもの（声・曲・字幕入り）。" if HAVE_OPV6 else "声入り。まるロボが映るカットだけ簡易描画（光と色は本番と違います）。左上の場面名・右上の注記は本番では消えます。")}
</section>"""
V8b = "ch08_check_v4"
if HAVE_C8V4:
    blocks["ch08"] = f"""<section id="ch08">
  <h2>第8章 ためる余裕と、すぐ鳴ること（ゲームの例） <span class="when">15:06〜17:05</span></h2>
  <p class="lead"><strong>天びんの 2 か所に、まるロボを乗せました（ご提案）。</strong>天びんは、まるロボの重さで傾く本物の天びんとして計算しています（重心が支点より下にあるので、立つ場所に合わせて傾き、少し遅れて、行き過ぎて戻ります）。坂になっても体はまっすぐで、足の裏が板に沿います。</p>
  <ul class="lead">
    <li><strong>0:27「…いつも両立するとは限りません」</strong>：左の「ためる」側で下の札を見る → 「すぐに音が出ることは」で右へ渡る → 上がってしまった左をふり返って、首をかしげる。</li>
    <li><strong>1:38「…その両方を考える必要があります」</strong>：左の「途切れにくい」側でうなずく → 右の「すぐ返ってくる」側へ走る → 止まりきれず、板も傾き続けて「おっとっと」→ 真ん中まで慎重に下がる → 板が水平に落ち着き、こちらを見てうなずく。</li>
  </ul>
  <p class="lead">天びんのまるロボは本番と同じ光で描いています（塔の場面は簡易描画）。前の版の直し（字幕と同じ文の札をなくし、残した字を大きく）と、塔の場面のまるロボも入っています。</p>
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk(V8b, 0, "0:00 空の塔を見上げる")}・{sk(V8b, 10.4, "0:10 鳴り始めて跳ねる")}・{sk(V8b, 21.2, "0:21 時間の帯")}・{sk(V8b, 26.7, "0:27 天びん（両立しない）")}・{sk(V8b, 41.0, "0:41 ゲーム")}・{sk(V8b, 47.4, "0:47 ぴったり合う場合")}・{sk(V8b, 55.6, "0:55 音が遅れてくる場合")}・{sk(V8b, 71.9, "1:12 操作してから音が決まる")}・{sk(V8b, 97.8, "1:38 天びん（おっとっと → 釣り合う）")}・{sk(V8b, 114.1, "1:54 塔に戻る")}</p>
  {video(V8b, "声入り。天びんのまるロボは本番と同じ光、塔の場面は簡易描画。左上の場面名・右上の注記は本番では消えます。")}
  <details>
    <summary>絵コンテ 19コマ</summary>
    <div class="frames">
{frames("ch08")}
    </div>
  </details>
</section>"""
elif HAVE_C8V3:
    blocks["ch08"] = f"""<section id="ch08">
  <h2>第8章 ためる余裕と、すぐ鳴ること（ゲームの例） <span class="when">15:06〜17:05</span></h2>
  <p class="lead"><strong>前の版の直し（字幕と同じ文の札をなくし、残した字を大きく）に、塔の場面のまるロボを足しました。</strong>まるロボは空になった塔を見上げて「もっとためれば？」と考え、04 が上がって届くのを見て、塔がいっぱいになって鳴り始めると小さく跳ねて、曲に合わせて揺れます。灯の横に出していた「鳴らし始める」の札は、字幕「…音を鳴らし始める。」と同じ言葉で、灯の右に立つまるロボにも重なったので、なくしました（灯が緑になって曲が鳴り、まるロボが跳ねるので伝わります）。塔の場面は動きを見るための簡易描画です（光と色は本番と違います）。後半の図は前の版と同じです。</p>
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk(V8, 0, "0:00 空の塔を見上げる")}・{sk(V8, 10.4, "0:10 鳴り始めて跳ねる")}・{sk(V8, 21.2, "0:21 時間の帯・てんびん")}・{sk(V8, 41.0, "0:41 ゲーム")}・{sk(V8, 47.4, "0:47 ぴったり合う場合")}・{sk(V8, 55.6, "0:55 音が遅れてくる場合")}・{sk(V8, 71.9, "1:12 操作してから音が決まる")}・{sk(V8, 97.9, "1:38 両方を考える")}・{sk(V8, 114.1, "1:54 塔に戻る")}</p>
  {video(V8, "声入り。塔は簡易描画（光と色は本番と違います）、図は 2D。左上の場面名・右上の注記は本番では消えます。")}
  <details>
    <summary>絵コンテ 19コマ</summary>
    <div class="frames">
{frames("ch08")}
    </div>
  </details>
</section>"""
if HAVE_SUM:
    blocks["summary"] = f"""<section id="summary">
  <h2>まとめ <span class="when">17:05〜18:15</span></h2>
  <p class="lead">OK をいただいた絵コンテのとおりに作りました。前半は、二つの疑問の答えと三つの工夫を、各章の本番の絵を並べてふり返ります（札の文字は大きく。字幕と同じ文は出しません）。最後は電車に戻り、まるロボが一時停止ボタンに跳び乗って時間を元に戻します（第2章の逆）。色と音が戻ると、主人公はまだ同じ曲でノリノリで、まわりの人がちらっと見ておしまい。</p>
  {('<p class="lead"><strong>11月9日に直したこと：</strong>0:20 の「二つ目の疑問は…」の前の間が短く、0:26 の後ろの間が長かったので、この文を 1.35 秒遅らせました（前 0.15 → 1.5 秒・後ろ 2.55 → 1.2 秒）。字幕は新しい決まり（1行25字・2行まで・文字を大きく）。この動画は本番（1080p・PC で描いた電車）を小さくしたものです。</p>') if HAVE_SUM2 else '<p class="lead"><strong>電車の場面は、本番と同じ光で小さく描いたものです</strong>（本番の 1080p は PC で描きます）。</p>'}
  <p class="lead"><strong>場面へ飛ぶ：</strong>{sk(VS, 0, "0:00 二つの疑問")}・{sk(VS, 3.3, "0:03 一つ目の答え")}・{sk(VS, 19.4, "0:19 二つ目の答え")}・{sk(VS, 36.0, "0:36 三つの工夫")}・{sk(VS, 53.8, "0:54 電車に戻る")}・{sk(VS, 55.6, "0:56 ボタンに跳び乗る")}・{sk(VS, 61.4, "1:01 まだこの曲")}・{sk(VS, 64.7, "1:05 おしまい")}</p>
  {video(VS, "本番を 1280×720 に小さくしたもの（声・曲・字幕入り）。" if HAVE_SUM2 else "声入り。電車の場面は本番と同じ光で小さく描いたもの。左上の場面名・右上の注記は本番では消えます。")}
  <details>
    <summary>絵コンテ 11コマ</summary>
    <div class="frames">
{frames("summary")}
    </div>
  </details>
</section>"""
tail = rest[rest.rfind("</section>") + len("</section>"):]
rows = "\n    ".join(f'<li class="row"><a href="#{k}"><span class="nm">{nm}</span><span class="tm">{tm}</span><span class="b {c}">{lab}</span></a><p>{note}</p>{verdict(key) if key else ""}</li>' for k, nm, tm, c, lab, note, key in STATUS)
waiting = [nm for k, nm, tm, c, lab, note, key in STATUS if c in ("re", "new")]
FULL = SC + "/stage/final/bluetooth_full_1080.mp4"
FULLNOTE = ('<p class="todo"><strong>通しの完成版ができました（11月9日）：</strong>18分17秒・1920×1080・音は -14 LUFS。ファイルはチャットでお送りしました。'
            'YouTube の章：0:00 電車の中の二つの疑問／1:21 音楽を届ける、小さな旅／2:55 届くことと、再生することは違う／7:09 途切れる理由と、周波数を変える工夫／'
            '10:57 送り直す（再送）／12:17 先に受け取って待たせる（バッファ）／15:08 ためれば解決？（遅れとの両立）／17:07 まとめ</p>') if os.path.exists(FULL) else ""
if HAVE_FIX:
    _tt = FX["total"]; _st = FX["starts"]
    FULLNOTE = (f'<p class="todo"><strong>通しの完成版を直しました（11月9日 夜）：</strong>{int(_tt // 60)}分{int(round(_tt % 60))}秒・1920×1080・音は -14 LUFS。ファイルはチャットでお送りしました。'
                f'YouTube の章：{_mm(_st["ch0102"])} 電車の中の二つの疑問／{_mm(_st["ch03"])} 音楽を届ける、小さな旅／{_mm(_st["ch04"])} 届くことと、再生することは違う／{_mm(_st["ch05"])} 途切れる理由と、周波数を変える工夫／'
                f'{_mm(_st["ch06"])} 送り直す（再送）／{_mm(_st["ch07"])} 先に受け取って待たせる（バッファ）／{_mm(_st["ch08"])} ためれば解決？（遅れとの両立）／{_mm(_st["sum"])} まとめ</p>'
                + '<div class="fixreel"><h3>直した所だけの確認動画（' + str(len(FX["fixes"])) + ' か所）</h3>'
                + video("fix_reel_1109b", "各所の左上に「前の時刻 → 今の時刻・直したこと」を出しています（音も本番のまま。声の前の間・足音・ドンの大きさも聞けます）。") + verdict("fix1109b")
                + '<ol class="fixlist">' + "".join('<li><b>%s</b> → 今 %s：%s</li>' % (html.escape(f_["old"]), f_["new"], html.escape(f_["what"])) for f_ in FX["fixes"]) + '</ol></div>')
board = f"""<section class="board" id="status">
  <h2>いまの状態 <span class="when">{STAMP}</span></h2>
  <p class="legend"><span class="b ok">OK・完成</span><span class="b re">直した → 確認待ち</span><span class="b new">確認待ち</span><span class="b wip">作っている</span></p>
  <ol class="rows">
    {rows}
  </ol>
  {FULLNOTE}
  <p class="todo"><strong>いま見ていただきたいもの：</strong>{"・".join(waiting) if waiting else "ありません"}（章の名前を押すと、その章へ飛びます）</p>
  <details><summary>字幕の直し（11月9日）：前と後の見本</summary><figure class="frame cmp"><img src="img/subs_before_after.jpg" alt="字幕の前と後。左が前、右が後。上から電車の中・第7章の塔・第8章の図" loading="lazy" width="1956" height="1824"><figcaption>左が前、右が直した後。文字を約1.25倍・太いふちにして、1行20字まで、改行は文の切れ目にしました。</figcaption></figure></details>
  <details><summary>これまでに決まったこと</summary><ul class="decided">{decided}</ul></details>
</section>"""
order = [k for k, *_ in STATUS]
for k, nm, tm, c, lab, note, key in STATUS:
    if k in blocks:
        blocks[k] = blocks[k].replace("</h2>", f' <span class="b {c}">{lab}</span></h2>', 1)
        if key:                                                        # 動画のすぐ下にも、同じ OK・NG のボタン
            m_ = re.search(r'<p class="vcap">.*?</p>', blocks[k], re.S)
            if m_: blocks[k] = blocks[k][:m_.end()] + "\n  " + verdict(key) + blocks[k][m_.end():]
SCRIPT = r"""<script>
document.addEventListener('click', function (e) {            // 時刻のリンク：その動画を、その時刻から再生する
  var a = e.target.closest && e.target.closest('a.seek'); if (!a) return;
  var v = document.getElementById(a.dataset.v); if (!v) return;
  e.preventDefault();
  var t = parseFloat(a.dataset.t) || 0;
  var go = function () { try { v.currentTime = t; } catch (_) {} var p = v.play(); if (p && p.catch) p.catch(function () {}); };
  v.scrollIntoView({behavior: 'smooth', block: 'center'});
  if (v.readyState >= 1) go(); else { v.addEventListener('loadedmetadata', go, {once: true}); v.load(); }
});
(async function () {                                            // OK・NG のボタン（このページの記録に残す）
  var boxes = Array.prototype.slice.call(document.querySelectorAll('.verdict'));
  if (!boxes.length || !window.claude || !window.claude.use) return;
  var db = null; try { db = await window.claude.use('db'); } catch (e) { db = null; }
  if (!db) return;
  var col = db.collection('reviews'); var state = {};
  boxes.forEach(function (b) { b.hidden = false; });
  function fmt(iso) { var d = new Date(iso); if (isNaN(d)) return ''; return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + d.getHours() + ':' + String(d.getMinutes()).padStart(2, '0'); }
  function render() {
    boxes.forEach(function (b) {
      var r = state[b.dataset.key];
      b.querySelector('.vok').setAttribute('aria-pressed', r && r.status === 'ok' ? 'true' : 'false');
      b.querySelector('.vng').setAttribute('aria-pressed', r && r.status === 'ng' ? 'true' : 'false');
      b.querySelector('.vs').textContent = !r ? '' : (r.status === 'ok' ? 'OK を受け取りました（' + fmt(r.at) + '）' : 'NG を受け取りました（' + fmt(r.at) + '）' + (r.note ? '：' + r.note : ''));
    });
  }
  var timer = setTimeout(function () { boxes.forEach(function (b) { var vs = b.querySelector('.vs'); if (!vs.textContent) vs.textContent = '記録にまだつながっていません（押すと保存を試します）'; }); }, 10000);
  col.onSnapshot(function (snap) { clearTimeout(timer); var st = {}; snap.docs.forEach(function (d) { st[d.id] = d.data(); }); state = st; render(); },
                 function (err) { clearTimeout(timer); boxes.forEach(function (b) { b.querySelector('.vs').textContent = '記録が使えません'; b.querySelectorAll('button').forEach(function (x) { x.disabled = true; }); }); });
  async function save(b, status, note) {
    var key = b.dataset.key; var bs = b.querySelectorAll('button'); bs.forEach(function (x) { x.disabled = true; });
    try { await col.doc(key).set({status: status, note: note || '', at: new Date().toISOString()}); }
    catch (e) { b.querySelector('.vs').textContent = '保存できませんでした（' + ((e && e.code) || 'error') + '）'; }
    bs.forEach(function (x) { x.disabled = false; });
  }
  boxes.forEach(function (b) {
    b.querySelector('.vok').addEventListener('click', function () { b.querySelector('.ngbox').hidden = true; save(b, 'ok', ''); });
    b.querySelector('.vng').addEventListener('click', function () { var nb = b.querySelector('.ngbox'); nb.hidden = false; nb.querySelector('textarea').focus(); });
    b.querySelector('.vsend').addEventListener('click', function () { var t = b.querySelector('textarea').value.trim(); b.querySelector('.ngbox').hidden = true; save(b, 'ng', t); });
  });
})();
</script>"""
tail = tail.replace("</footer>", "</footer>\n" + SCRIPT, 1)
HAVE_BRAND = os.path.exists(P + "/img/thumb/thumb_A.jpg") and os.path.exists(P + "/img/brand/banner_1_tanken.jpg")
BRAND = ""
if HAVE_BRAND:
    TH = [("A", "隣の曲　なぜ混ざらない？", "電車の中の主人公。1つ目の疑問をそのまま出す。", "電車で隣の人のイヤホンの曲が混ざらないのはなぜ？【Bluetoothのしくみ】"),
          ("B", "音が　とぎれる　本当の理由", "耳に手を当てる主人公の寄り。だれでも覚えのある「途切れ」から入る。", "ワイヤレスイヤホンの音が途切れる本当の理由【Bluetoothのしくみ】"),
          ("C", "イヤホンの中に　倉庫があった！", "バッファの塔と「バッファ」の札。中を見せる驚きで引く。", "イヤホンの中には“倉庫”がある｜音が途切れにくいしくみ"),
          ("D", "音楽は　荷物で届く", "荷物を運ぶまるロボと巨大イヤホン。たとえの面白さで引く。", "音楽は“荷物”で届いていた｜Bluetoothイヤホンのしくみ"),
          ("E", "イヤホンの　2つのナゾ", "まるロボの目のアップと二つの疑問。キャラクターを覚えてもらう。", "ワイヤレスイヤホン 2つのナゾを3Dでのぞく"),
          ("F", "電車の中で　時間を止めてみた", "一時停止ボタンに乗ったまるロボ。物語の入り口から引く。", "電車の中で時間を止めて、イヤホンのしくみを見に行く")]
    cards = "".join(f'''<figure class="tcard"><img src="img/thumb/thumb_{k}.jpg" alt="サムネ案{k}：{html.escape(t)}" loading="lazy" width="1280" height="720"><figcaption><b>案{k}</b>「{html.escape(t)}」<br>{html.escape(n)}<br><small>合わせるタイトルの例：{html.escape(ti)}</small></figcaption>{verdict("thumb_" + k)}</figure>''' for k, t, n, ti in TH)
    PK = [("1", "まるロボのしくみ探検", "banner_1_tanken", "icon_1_photo", "おすすめ。まるロボが機械の“なか”に入って探検する、このチャンネルの見せ方そのもの。「しくみ」で何のチャンネルか一目で分かる。バナーは本編の場面（荷物を運ぶまるロボと巨大イヤホン）、アイコンはまるロボの目の写真。"),
          ("2", "まるわかり！まるロボ", "banner_2_maruwakari", "icon_2_lens", "「まるわかり」と「まるロボ」の言葉遊びで覚えやすく、明るい。バナーは青緑の地に電波の輪、アイコンはまるロボの目を図にしたもの（小さくてもくっきり見える）。"),
          ("3", "まるロボラボ", "banner_3_labo", "icon_3_robot", "短く口に出しやすい（ロボ・ラボの音合わせ）。実験・検証の落ち着いた雰囲気。バナーは白い方眼（実験ノート）、アイコンは電車の中のまるロボ。")]
    packs = "".join(f'''<div class="bpack"><h3>案{k}「{html.escape(nm)}」</h3><img class="bimg" src="img/brand/{b}.jpg" alt="バナー案{k}" loading="lazy" width="1600" height="900"><details><summary>スマホ・パソコンで見える範囲</summary><img class="bimg" src="img/brand/{b}_guide.jpg" alt="見える範囲の線つき" loading="lazy" width="1280" height="720"><p class="vcap">黄色の枠：スマホでも見える範囲（文字はこの中）。赤の枠：パソコンで見える範囲。テレビでは全体が見えます。</p></details><div class="bicon"><img src="img/brand/{ic}.jpg" alt="アイコン案{k}" loading="lazy" width="400" height="400"><p>{html.escape(note)}</p></div>{verdict("brand_" + k)}</div>''' for k, nm, b, ic, note in PK)
    OTHER = [("なかみ探検 まるロボ", "「なかみ」を先に出す。探検の感じは案1と同じ。"),
             ("まるロボのしくみ図鑑", "分かりやすいが、「しくみ図鑑」は学研などの本のシリーズでよく使われる言葉。"),
             ("デジタルのなか探検隊", "まるロボの名前を入れない案。あとでキャラクターを増やしても使える。"),
             ("ミクロの配達便", "今回の荷物のたとえに寄った案。扱うテーマが広がると合わなくなるかも。")]
    BRAND = f'''<section id="branding">
  <h2>サムネ案とチャンネル案 <span class="when">11月9日</span></h2>
  <h3 class="sub">この動画のサムネ案（6）</h3>
  <p class="lead">本編の 3D（字幕なし）から作りました。1280×720。左上の小さな帯「Bluetoothイヤホンのしくみ」は、シリーズの目印です。おすすめは <b>B</b>（だれでも覚えのある「途切れ」と人の表情）と <b>A</b>（1つ目の疑問）、驚きで引くなら <b>C</b>。</p>
  <div class="tgrid">{cards}</div>
  <p style="margin:14px 0 4px"><img src="img/thumb/thumb_small.png" alt="スマホの一覧で見える大きさ（6 案を同じ大きさで並べたもの）" loading="lazy" width="670" height="266" style="display:block;width:100%;max-width:670px;height:auto;border-radius:8px"></p><p class="vcap">スマホの一覧で表示される大きさ（1 枚 約 210×118）。どれも大きな字は読めます。</p>
  <h3 class="sub">チャンネル案（名前・バナー・アイコンを 3 組）</h3>
  <p class="lead">テーマ（デジタル機器のしくみ）と見せ方（まるロボが中で体を張る・青緑のおもちゃ風）から考えました。名前・バナー・アイコンは組み合わせを入れ替えても使えます。</p>
  {packs}
  <h3 class="sub">ほかの名前の候補</h3>
  <ul class="others">{"".join("<li><b>" + html.escape(n) + "</b>：" + html.escape(w) + "</li>" for n, w in OTHER)}</ul>
  <p class="todo">「まるロボ」という名前のチャンネルやキャラクターは、ざっと調べた範囲では見つかりませんでした。YouTube のハンドル（@〜）が空いているかは、YouTube の画面で確かめてください。決まったら、バナーとアイコンは PC で専用の 3D を高画質に描き直せます（いまは本編のコマから作っています）。</p>
</section>'''
page = head + board + "\n\n" + (BRAND + "\n\n" if BRAND else "") + "\n\n".join(blocks[k] for k in order if k in blocks) + "\n" + tail
open(P + "/index.html", "w", encoding="utf-8").write(page)
print(len(page))
