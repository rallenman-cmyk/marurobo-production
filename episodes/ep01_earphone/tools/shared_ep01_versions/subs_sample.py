# 字幕の見本（直す前／直した後）：明るい図（第8章のゲーム）・暗い 3D（第7章の塔）・電車の中（冒頭）の 3 場面を、1080p で並べる
#   → review_page/img/subs_before_after.jpg
import os, sys, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subs_jp as SJ
from PIL import Image, ImageDraw, ImageFont
S = "/tmp/claude-0/-home-user/7b02fcaa-32db-5c5c-8b6c-1aa9f984eb4a/scratchpad"; W = S + "/work_subs"; FONTS = S + "/stage/av/fonts"
OLD_SUB = "Style: Sub,Noto Sans CJK JP,40,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2.6,0,2,60,60,46,1"
OLD_MAIN = "Style: Main,Noto Sans CJK JP,40,&H00FFFFFF,&H00FFFFFF,&H00302418,&H64000000,-1,0,0,0,100,100,0,0,1,3.2,0,2,60,60,46,1"
P = {p["no"]: p for p in json.load(open(S + "/stage/voice/achernar/placement.json", encoding="utf-8"))}


def frame_mp4(src_dir, prefix, idx, out):
    """連番の mp4（prefix0001-0100.mp4 …）から idx 番目のコマ（1 から）を 1920×1080 の PNG に"""
    for f in sorted(os.listdir(src_dir)):
        if not (f.startswith(prefix) and f.endswith(".mp4")): continue
        a, b = map(int, f[len(prefix):-4].split("-"))
        if a <= idx <= b:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(src_dir, f), "-vf", "select=eq(n\\,%d),scale=1920:1080:flags=lanczos" % (idx - a), "-frames:v", "1", out], check=True); return out
    raise SystemExit("no chunk for %d" % idx)


def burn(png, style, text, out):
    ass = os.path.join(W, "s.ass")
    open(ass, "w", encoding="utf-8").write("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 0", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        style, "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        "Dialogue: 1,0:00:00.00,0:00:05.00,%s,,0,0,0,,%s" % (style.split(",")[0].split(": ")[1], text), ""]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf", "subtitles=%s:fontsdir=%s" % (ass, FONTS), "-frames:v", "1", out], check=True)
    return out


rows = []
# ① 冒頭の電車（明るく、こまかい 3D）：6 番の文
f1 = frame_mp4(S + "/dl_pc/ch0102", "ch0102_", int((P[6]["start"] + 1.5) * 24) + 1, W + "/bg1.png")
rows.append(("冒頭・電車の中", f1, OLD_SUB, P[6]["text"], SJ.events(P[6]["start"], P[6]["end"] + .35, P[6]["text"])[0][2]))
# ② 第7章の塔（暗い 3D）：133 番の文（前は 1 行目が 22 文字）
L7 = json.load(open(S + "/dl_pc/ch07/ch07_log.json"))
f2 = frame_mp4(S + "/dl_pc/ch07", "ch07_stage_", int((P[133]["start"] + 2.0 - L7["t0"]) * 24) + 1, W + "/bg2.png")
rows.append(("第7章・塔の中", f2, OLD_MAIN, "イヤホンは、少し先の音のデータまで受け取り、\\N順番を待たせているんです。", SJ.events(P[133]["start"], P[133]["end"] + .35, P[133]["text"])[0][2]))
# ③ 第8章のゲームの図（明るい 2D）：172 番の文
G = json.load(open(S + "/work8/asm/ch08_game.json")); t3 = P[172]["start"] + 3.2
Image.open(S + "/work8/asm/game/g_%04d.png" % (int((t3 - G["t0"]) * 24) + 1)).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(W + "/bg3.png")
ev = [e for e in SJ.events(P[172]["start"], P[172]["end"] + .35, P[172]["text"]) if e[0] <= t3 < e[1]][0]
rows.append(("第8章・ゲームの図", W + "/bg3.png", OLD_MAIN, "その音を長く待たせれば、操作した瞬間と、\\N聞こえる瞬間が離れてしまいます。", ev[2]))

TW, TH, PAD, HEAD = 960, 540, 12, 64
font = ImageFont.truetype(S + "/stage/av/fonts/japanese.ttc", 30, index=0)
sheet = Image.new("RGB", (2 * TW + 3 * PAD, len(rows) * (TH + HEAD) + PAD), (24, 26, 32)); d = ImageDraw.Draw(sheet)
for r, (name, bg, old_style, old_txt, new_txt) in enumerate(rows):
    y = PAD + r * (TH + HEAD)
    a = burn(bg, old_style, old_txt, W + "/old_%d.png" % r); b = burn(bg, SJ.STYLE_MAIN, new_txt, W + "/new_%d.png" % r)
    d.text((PAD, y + 12), "%s：直す前" % name, font=font, fill=(200, 200, 200)); d.text((2 * PAD + TW, y + 12), "%s：直した後" % name, font=font, fill=(255, 220, 120))
    sheet.paste(Image.open(a).resize((TW, TH), Image.LANCZOS), (PAD, y + HEAD - 8)); sheet.paste(Image.open(b).resize((TW, TH), Image.LANCZOS), (2 * PAD + TW, y + HEAD - 8))
out = S + "/review_page/img/subs_before_after.jpg"; sheet.save(out, quality=90); print(out, sheet.size)
for r, row in enumerate(rows): os.system("cp %s/new_%d.png %s/review_page/img/subs_new_%d.png" % (W, r, S, r))
