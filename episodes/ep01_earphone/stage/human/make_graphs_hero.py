# 主人公の動きテスト（8秒）の「動きの見える化」グラフ
# 使い方: python3 make_graphs_hero.py hero_motion_log.json out.png
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

log_path, out = sys.argv[1], sys.argv[2]
L = json.load(open(log_path))
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
font_manager.fontManager.addfont(FONT); plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
T_DROP = 3.0
t = L["t"]

fig, axes = plt.subplots(5, 1, figsize=(12, 13.2), dpi=100, sharex=True,
                         gridspec_kw=dict(height_ratios=[1.6, 1, 1, 1, 1], hspace=0.42))
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS); ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.axvline(T_DROP, color=AXIS, lw=0.9, ls="--", zorder=1)

ax = axes[0]; ax.set_title("反応の順番（0＝前の姿勢 → 1＝反応し終わり）", loc="left", color=INK, fontsize=13, pad=6)
ax.axvspan(T_DROP, T_DROP + 0.2, color="#efeee9", zorder=0)
ax.text(T_DROP + 0.03, 1.13, "反応時間0.2秒", color=INK2, fontsize=10, va="bottom")
ax.text(T_DROP - 0.06, 1.13, "音が途切れる", color=INK2, fontsize=10, va="bottom", ha="right")
for key, col, label, y_lab in (("gaze", BLUE, "目（0.08秒で跳ぶ）", 0.88), ("head", ORANGE, "頭（0.45秒）", 0.66),
                               ("torso", AQUA, "胴（0.6秒）", 0.44), ("reach", YELLOW, "手（0.75秒・躍度最小）", 0.22)):
    ax.plot(t, L[key], color=col, lw=2)
    # 線がその高さを越える時刻のすぐ右に名前を置く（重ならないよう高さをずらす）
    i = next(k for k in range(len(t)) if L[key][k] >= y_lab)
    ax.annotate(label, xy=(t[i], y_lab), xytext=(t[i] + 0.55, y_lab), color=INK, fontsize=10.5, va="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_ylim(-0.05, 1.25)

ax = axes[1]; ax.set_title("うなずき（度、＋が下向き）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["nod"], color=BLUE, lw=2)
ax.text(0.15, max(L["nod"]) * 1.05, "曲の2拍に1回（約78回/分）。首→頭の順に遅れて動く", color=INK2, fontsize=10, va="bottom")
ax.text(T_DROP + 0.45, max(L["nod"]) * 0.55, "曲が止まると約0.3秒で止まる", color=INK2, fontsize=10)
ax.set_ylim(min(0, min(L["nod"])) - 0.2, max(L["nod"]) * 1.45)

ax = axes[2]; ax.set_title("呼吸（0＝吐き切り → 1＝吸い切り）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["breath"], color=BLUE, lw=2); ax.set_ylim(-0.05, 1.3)
ax.text(0.15, 1.08, "毎分15回（吸う4割・吐く6割）", color=INK2, fontsize=10)
ax.text(T_DROP + 0.35, 1.08, "驚いた直後は約1秒止まる", color=INK2, fontsize=10)

ax = axes[3]; ax.set_title("まばたき（0＝開 → 1＝閉）", loc="left", color=INK, fontsize=13, pad=6)
ax.plot(t, L["blink"], color=BLUE, lw=2); ax.set_ylim(-0.05, 1.3)
ax.text(0.15, 1.08, "閉じる90ms → 40ms → 開く170ms。画面を見ている間は少なめ", color=INK2, fontsize=10)

ax = axes[4]; ax.set_title("電車の揺れで上半身が前後に傾く（度）", loc="left", color=INK, fontsize=13, pad=6)
sw = L["sway"]; ax.plot(t, sw, color=BLUE, lw=2); ax.axhline(0, color=AXIS, lw=0.9)
lo, hi = min(sw), max(sw); pad = max(0.3, (hi - lo) * 0.35); ax.set_ylim(lo - pad, hi + pad * 1.8)
ax.text(0.15, hi + pad * 0.6, "床の横揺れ（0.6〜1.8Hz）に、筋肉で支えた上半身（1.1Hz・減衰比0.55）が少し遅れて傾く", color=INK2, fontsize=10)
ax.set_xlabel("時間（秒）", color=INK2, fontsize=11); ax.set_xlim(0, 8)

fig.suptitle("主人公の動きテスト（物理と体の仕組みで計算した値）", x=0.06, ha="left", color=INK, fontsize=16, y=0.935)
fig.savefig(out, facecolor=SURF, bbox_inches="tight"); print("graph ok", out)
