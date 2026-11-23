# サムネの絵を Lovart（GPT Image 2）で描く入口（2026-11-23 決定。恋愛チャンネルと同じ Lovart を使う。前は Gemini の gemini-3-pro-image）
#   字は描かせない（SKILL.md §9）。絵だけを描かせ、字・札・矢印・赤い丸は各回の thumbs_*.py の comp で重ねる。
#   ・見本（まるロボのコマなど）は Lovart に上げ、URL を ../references/lovart_refs.json に覚えておく。
#     画像はリポジトリに入れない決まりなので、URL を残しておけば、次のセッションは画像なしで同じ見本を使える。
#   ・見本をそろえたプロジェクトも同じ json に覚えて、続けて頼む（見本の登録は 1 分あたりの回数に上限がある）。
#   ・返った絵は、元の絵（raw/）を残したうえで 2560×1440（16:9）に切りそろえて <名前>_<番号>.png にする（comp がこの大きさで組む）。
#     GPT Image 2 は 1920×1088 で返る（2026-11-23）。2560 幅に引きのばすので、Gemini の 2K より少しやわらかい。
#   使い方:
#     python3 thumb_lovart.py upload robot_front.png robot_34.png …      … 見本を上げて覚える（同じ中身は上げ直さない）
#     python3 thumb_lovart.py refs                                         … 覚えている見本の一覧
#     python3 thumb_lovart.py gen <出力フォルダ> <案の名前> <頼む文.txt> [--ref 画像か名前か URL …] [--stop-on-cost]
#   クレジットは恋愛と同じく、確認を待たずに使い、使った数をあとで報告する（2026-11-23 ユーザー決定）。
#   GPT Image 2 は 1 枚 23 クレジットほど（2026-11-23 の試し。使い放題は低い画質だけ）。--stop-on-cost で、使う前に止める。
#   --ref には、手元の画像・覚えた見本の名前（robot_front など）・https の URL のどれでもよい。
#   鍵は LOVART_ACCESS_KEY / LOVART_SECRET_KEY。使ったものは lovart.py がリポジトリの logs/lovart_usage.jsonl に残す。
import os, sys, json, glob, hashlib
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lovart  # noqa: E402

MODEL = os.environ.get("THUMB_LOVART_MODEL", "generate_image_gpt_image_2")
CACHE = os.path.normpath(os.path.join(HERE, "..", "references", "lovart_refs.json"))
W, H = 2560, 1440
# GPT Image 2 は横長を頼んでも 3:2 などで返ることがあるので、頼む文の頭で 16:9 をはっきり頼み、返ったあとも切りそろえる
HEAD = ("Generate ONE image. Landscape 16:9 (1920x1080 or 2560x1440), for a YouTube thumbnail background. "
        "Do not add any text, letters, numbers, logos or watermarks anywhere in the image.\n\n")


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    return {"refs": {}, "projects": {}}


def save(c):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
        f.write("\n")


def ref_url(x, c):
    """手元の画像は中身の sha1 で覚え、同じ中身は上げ直さない。名前・URL はそのまま引く"""
    if x.startswith("https://"):
        return x
    if x in c["refs"]:
        return c["refs"][x]["url"]
    if not os.path.exists(x):
        sys.exit(f"見本が見つからない（手元の画像でも、覚えた名前でもない）: {x}")
    h = hashlib.sha1(open(x, "rb").read()).hexdigest()[:16]
    for k, v in c["refs"].items():
        if v.get("sha1") == h:
            return v["url"]
    name = os.path.splitext(os.path.basename(x))[0]
    if name in c["refs"]:
        name = f"{name}_{h[:6]}"
    url = lovart.upload(x)
    c["refs"][name] = {"url": url, "sha1": h, "from": os.path.basename(x)}
    save(c)
    print(f"上げた: {name} → {url}")
    return url


def fit(src, dst):
    """16:9 に切りそろえる（足りない向きは切る。真ん中で切る）"""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w / h > W / H:
        nw = round(h * W / H); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w * H / W); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im.resize((W, H), Image.LANCZOS).save(dst)
    return (w, h)


def gen(outdir, name, prompt, refs=(), auto_confirm=True):
    c = load()
    urls = [ref_url(r, c) for r in refs]
    key = "|".join(sorted(urls))
    pid = c["projects"].get(key)
    if not pid:  # 見本をそろえたプロジェクトを作って覚える
        pid = lovart.new_project(urls)
        c["projects"][key] = pid
        save(c)
    raw = os.path.join(outdir, "raw")
    try:
        rec = lovart.gen(raw, HEAD + prompt, urls, MODEL, auto_confirm=auto_confirm, project=pid)
    except RuntimeError as e:  # 覚えていたプロジェクトが使えないときだけ、作り直して 1 回だけ頼む
        if "project" not in str(e).lower():
            raise
        pid = lovart.new_project(urls); c["projects"][key] = pid; save(c)
        rec = lovart.gen(raw, HEAD + prompt, urls, MODEL, auto_confirm=auto_confirm, project=pid)
    out = []
    k = len(glob.glob(os.path.join(outdir, name + "_*.png")))
    for f in rec.get("files") or []:
        k += 1
        dst = os.path.join(outdir, f"{name}_{k}.png")
        size = fit(f, dst)
        out.append(dst)
        print(f"{dst}（元の大きさ {size[0]}×{size[1]} → {W}×{H}）")
    if not out:
        print("絵が返らなかった。黙って頼み直さず、ユーザーに伝える（lovart.py の記録を見る）")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__ or "使い方はファイルの頭を見る")
    if a[0] == "upload":
        c = load()
        for p in a[1:]:
            print(ref_url(p, c))
    elif a[0] == "refs":
        for k, v in load()["refs"].items():
            print(k, v["url"])
    elif a[0] == "gen":
        outdir, name, ptxt, rest = a[1], a[2], a[3], a[4:]
        refs, auto = [], True
        while rest:
            k = rest.pop(0)
            if k == "--ref":
                refs.append(rest.pop(0))
            elif k == "--stop-on-cost":
                auto = False
        os.makedirs(outdir, exist_ok=True)
        gen(outdir, name, open(ptxt, encoding="utf-8").read(), refs, auto)
