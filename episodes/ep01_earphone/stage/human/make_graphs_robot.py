# まるロボの跳躍（冒頭のショットC）の「動きの見える化」グラフ
# 使い方: python3 make_graphs_robot.py opening_log.json out.png
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

L = json.load(open(sys.argv[1])); out = sys.argv[2]
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
font_manager.fontManager.addfont(FONT); plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE = "#2a78d6"
t = L["t"]; TT, TLAND, TF = L["T_TAKE"], L["T_LAND"], L["T_FREEZE"]
fig, axes = plt.subplots(3, 1, figsize=(12, 9.6), dpi=100, sharex=True, gridspec_kw=dict(height_ratios=[1.5, 1, 1], hspace=0.40))
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS); ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.axvspan(TT, TLAND, color="#efeee9", zorder=0); ax.axvline(TF, color=AXIS, lw=0.9, ls="--")

ax = axes[0]; ax.set_title("まるロボの足の高さ（m、電車の縮尺）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["root_z"], color=BLUE, lw=2); ax.set_ylim(-0.03, 0.55)
ax.text(TT + 0.02, 0.47, f"空中 {TLAND - TT:.2f}秒（放物線）", color=INK2, fontsize=10)
ax.annotate("重力は電車の縮尺に合わせて 9.81×1.65 m/s²\n頂点0.40m・踏み切りの速さ 3.6m/s", xy=(TT + 0.19, 0.40), xytext=(16.4, 0.36), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate(f"ボタンに着地（{L['V_IMPACT']:.1f}m/s）→ボタンが3cm沈む", xy=(TLAND, 0.178), xytext=(16.4, 0.12), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.text(TF + 0.05, 0.52, "時間が止まる", color=INK2, fontsize=10)

ax = axes[1]; ax.set_title("脚の縮み（部品の寸法、＋が縮む）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["crouch"], color=BLUE, lw=2); ax.axhline(0, color=AXIS, lw=0.9); ax.set_ylim(-0.06, 0.16)
ax.annotate("しゃがむ0.30秒 → ため → 蹴る0.12秒", xy=(TT - 0.2, 0.10), xytext=(13.2, 0.125), color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("着地の衝撃を脚で受け止める（ばね6Hz・減衰比0.5）", xy=(TLAND + 0.05, 0.08), xytext=(16.4, 0.11), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))

ax = axes[2]; ax.set_title("アンテナの揺れ（度）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["antenna"], color=BLUE, lw=2); ax.axhline(0, color=AXIS, lw=0.9)
lo, hi = min(L["antenna"]), max(L["antenna"]); ax.set_ylim(lo - 4, hi + 8)
ax.text(16.4, hi + 2, "上下の加速度で遅れて揺れる（ばね3.5Hz・減衰比0.18）。まるロボは時間の外にいるので、止まった後も動く", color=INK2, fontsize=10)
ax.set_xlabel("時間（秒）", color=INK2, fontsize=11); ax.set_xlim(13, 22)
fig.suptitle("まるロボの跳躍（物理の計算結果）", x=0.06, ha="left", color=INK, fontsize=16, y=0.95)
fig.savefig(out, facecolor=SURF, bbox_inches="tight"); print("graph ok", out)
