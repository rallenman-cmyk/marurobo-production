# 共通の部品：絵の具の混ぜ方（Blender なしで動く）
#   絵の具は「何の顔料がどれだけ入っているか」で表す（Paint）。色は顔料の量で重みを付けた、反射率の幾何平均（減法混色の近似）
#   ・混ぜる順番によらず、同じ量なら同じ色になる（足し算が入れ替えられる）→ 鍵共有のたとえ（絵の具の交換）の要の性質
#   ・混ぜた色から元の色を取り出すのは難しい（一方向）
import math

PIGMENTS = {                                  # sRGB（0〜255）。名前は画面の言葉にも使う
    "黄": (240, 198, 56), "青": (52, 102, 210), "赤": (204, 58, 118), "白": (245, 245, 242), "黒": (30, 30, 32),
}


def to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(x):
    x = max(0.0, min(1.0, x))
    return 255.0 * (x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055)


class Paint(dict):
    """顔料の量 {名前: 量}。+ で混ぜる（順番によらない）"""
    def __add__(self, other):
        out = Paint(self)
        for k, v in other.items(): out[k] = out.get(k, 0.0) + v
        return out

    def amount(self): return sum(self.values())

    def linear(self):
        """線形の RGB（0〜1）。反射率の重み付き幾何平均"""
        tot = self.amount()
        if tot <= 0: return (0.0, 0.0, 0.0)
        out = []
        for i in range(3):
            s = sum(v * math.log(max(to_lin(PIGMENTS[k][i]), 1e-4)) for k, v in self.items())
            out.append(math.exp(s / tot))
        return tuple(out)

    def srgb(self): return tuple(int(round(to_srgb(x))) for x in self.linear())

    def same_as(self, other, tol=1e-9):
        ks = set(self) | set(other)
        a, b = self.amount(), other.amount()
        return all(abs(self.get(k, 0) / a - other.get(k, 0) / b) < tol for k in ks)


def lerp_lin(c0, c1, u):
    """線形の色の間をなめらかに（混ざっていく途中の見た目）"""
    u = max(0.0, min(1.0, u)); return tuple(c0[i] + (c1[i] - c0[i]) * u for i in range(3))


if __name__ == "__main__":
    Y, B, R = Paint(黄=1.0), Paint(青=0.5), Paint(赤=0.5)
    send_a = Y + B; send_b = Y + R                    # スマホが送る色・イヤホンが送る色
    key_a = send_b + B; key_b = send_a + R            # 受け取った側が自分のひみつの色を足す
    print("send A", send_a.srgb(), "send B", send_b.srgb(), "key A", key_a.srgb(), "key B", key_b.srgb(), "same:", key_a.same_as(key_b))
