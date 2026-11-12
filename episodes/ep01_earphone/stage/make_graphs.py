# 30秒サンプルの「動きの見える化」グラフ（静止画）
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

log_path, out = sys.argv[1], sys.argv[2]
j = json.load(open(log_path)); L = j["log"]; tm = j["timing"]
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
font_manager.fontManager.addfont(FONT); plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

t = [r["t"] for r in L]
def masked(key, cond): return [r[key] if cond(r) else None for r in L]
z04 = masked("z04", lambda r: r["t"] < 7.0)
z05 = masked("z05", lambda r: r["t"] < tm["end05"])
z06 = masked("z06", lambda r: r["t"] >= 7.4)
speed = [r["v"] for r in L]; lean = [r["lean_deg"] for r in L]; bob = [-r["drop_cm"] for r in L]

fig, axes = plt.subplots(4, 1, figsize=(12, 11.5), dpi=100, sharex=True, gridspec_kw=dict(height_ratios=[1.5, 1, 1, 1], hspace=0.38))
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS); ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.axvspan(tm["c0"], tm["c1"] + 0.8, color="#efeee9", zorder=0)
axes[1].text(tm["c0"] + 0.15, 1.52, "C案の光（タワーが空の間）", color=INK2, fontsize=10, va="bottom")

ax = axes[0]; ax.set_title("荷物の高さ（荷物の底, m）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, z04, color=BLUE, lw=2); ax.plot(t, z05, color=ORANGE, lw=2); ax.plot(t, z06, color=AQUA, lw=2)
ax.set_ylim(0, 5.0)
ax.text(0.3, 0.70, "4番（再生中）", color=INK, fontsize=10.5, va="bottom")
ax.text(1.0, 1.88, "5番（待機）", color=INK, fontsize=10.5, va="bottom")
ax.text(7.6, 4.35, "6番（まるロボの頭の上）", color=INK, fontsize=10.5, va="bottom")
ax.text(16.0, 1.88, "6番（タワーで待機）", color=INK, fontsize=10.5, va="bottom")
ax.annotate("扉が開き、0.82m落ちて\n跳ねる（反発係数0.25）", xy=(7.47, 1.0), xytext=(2.6, 2.75), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("漏斗から落ちて着地\n秒速6.1m・跳ね返り3回", xy=(14.76, 1.82), xytext=(16.8, 3.2), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("一定の速さで沈む＝一定の速さで再生", xy=(19.0, 1.0 - 0.0358 * (19.0 - 7.8)), xytext=(14.2, 0.12), color=INK2, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
for x in (7.0, tm["end05"]): ax.axvline(x, color=AXIS, lw=0.8, ls="--", zorder=1)

ax = axes[1]; ax.set_title("まるロボの速さ（m/s）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, speed, color=BLUE, lw=2); ax.set_ylim(0, 1.7)
ax.text(3.0, 0.12, "画面の外から歩いて登場", color=INK2, fontsize=10, va="bottom")
ax.axhline(1.45, color=AXIS, lw=0.9, ls="--"); ax.text(0.3, 1.49, "走りに変わる目安 1.45m/s（フルード数0.5）", color=INK2, fontsize=10)
ax.annotate("急ぎ足 1.3m/s", xy=(10.0, 1.3), xytext=(3.2, 0.95), color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("躍度最小の曲線で止まる\n（1.4秒・0.91m）", xy=(13.0, 0.35), xytext=(16.2, 0.75), color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))

ax = axes[2]; ax.set_title("前後の傾き（度、＋が前）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, lean, color=BLUE, lw=2); ax.set_ylim(-8, 4); ax.axhline(0, color=AXIS, lw=0.9)
ax.annotate("急ブレーキで後ろへ反る\n角度＝atan（加速度÷重力）", xy=(12.75, min(lean)), xytext=(15.6, -6.2), color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.text(8.0, 2.5, "歩いている間は少し前へ（＋2°）", color=INK2, fontsize=10)

ax = axes[3]; ax.set_title("胴体の上下（cm）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, bob, color=BLUE, lw=1.6); ax.set_ylim(-8, 2); ax.axhline(0, color=AXIS, lw=0.9)
ax.annotate("倒立振子：1歩ごとに最大6.4cm沈む\n（足を地面に固定し、腰と足の距離を脚の長さに保つ）", xy=(10.4, -6.0), xytext=(14.6, -6.6), color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_xlabel("時間（秒）", color=INK2, fontsize=11); ax.set_xlim(0, 30)

fig.suptitle("30秒サンプルの動き（物理の計算結果）", x=0.06, ha="left", color=INK, fontsize=16, y=0.945)
fig.savefig(out, facecolor=SURF, bbox_inches="tight"); print("graph ok", out)
