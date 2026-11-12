# 参考画像と描画を重ねる：半透明＋参考の輪郭（赤）
import sys
from PIL import Image, ImageFilter
ref_p, mine_p, out_p = sys.argv[1:4]
W, H = 1280, 720
ref = Image.open(ref_p).convert("RGB").resize((W, H), Image.LANCZOS)
mine = Image.open(mine_p).convert("RGB").resize((W, H), Image.LANCZOS)
edges = ref.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 38 else 0)
over = Image.blend(mine, ref, 0.45); over.paste(Image.new("RGB", (W, H), (230, 30, 40)), (0, 0), edges)
out = Image.new("RGB", (W, 2 * H)); out.paste(mine, (0, 0)); out.paste(over, (0, H)); out.save(out_p, quality=88)
