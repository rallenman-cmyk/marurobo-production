# カットのつなぎ目のブレ（モーションブラー）を消す（2026-11-09 ユーザー：冒頭の「音楽を聴いている人 → 動画を見ている人」がビュンとなる）
#   3D をモーションブラーつき（シャッター 0.5）で描くと、カメラが飛ぶカットの直前・直後の 2 コマに、前の位置から次の位置までのブレが入る
#   → 直前のコマ k は一つ前（k-1）、直後のコマ k+1 は一つ後（k+2）に差し替える（描き直しなし。1 コマの止まりは目に見えない）
#   本当にブレているか（同じカットのとなりのコマより鋭さが半分以下）を確かめてから差し替える
#   コマの番号：コマ i は本編の (i-1)/fps 秒。カットの時刻 t のとき k = round(t × fps)（k が前のカットの最後、k+1 が新しいカットの最初）
import numpy as np
from PIL import Image


def sharp(path):
    """鋭さ（ラプラシアンの分散。幅 480 に縮めて測る）"""
    im = Image.open(path).convert("L"); w, h = im.size; im = im.resize((480, max(1, int(480 * h / w))))
    a = np.asarray(im, dtype=float)
    lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    return float(lap.var())


def remap(path_of, cuts, ratio=0.5, log=print):
    """path_of(i) → コマ i の画像の場所。cuts：各カットの k（前のカットの最後のコマ）。→ {i: 代わりに使うコマ}"""
    m = {}
    for k in cuts:
        try:
            s = {i: sharp(path_of(i)) for i in (k - 1, k, k + 1, k + 2)}
        except Exception as ex:
            log("cut k=%d skip (%s)" % (k, ex)); continue
        if s[k] < ratio * s[k - 1]: m[k] = k - 1
        if s[k + 1] < ratio * s[k + 2]: m[k + 1] = k + 2
        log("cut k=%d  sharp %s  -> %s" % (k, " ".join("%.0f" % s[i] for i in sorted(s)), {a: b for a, b in m.items() if a in (k, k + 1)}))
    return m
