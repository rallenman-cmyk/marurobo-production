# サムネなどの絵を Gemini で描く（2026-11-25。ユーザー「ジェミニのapiのクレジット消費も激しい」）
#   下書き（draft）：安い型番 gemini-3.1-flash-image で描く（大きさの指定なし＝ふつうの大きさ）。案はたくさんこれで描く
#   清書（final）：gemini-3-pro-image の 2K。選ばれた1枚だけ、同じ頼む文で描き直す
#   字は描かせない（SKILL.md §9。字は Noto Sans JP の 900 で重ねる）。使った量は gemini_log に残る
# 使い方: python3 gemini_image.py draft|final 出力.png 頼む文.txt [見本1.png 見本2.jpg ...] [--ep=ep03 --what=サムネA]
import sys, os, json, base64, mimetypes, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from gemini_log import log
MODELS = {"draft": ("gemini-3.1-flash-image", {"aspectRatio": "16:9"}),
          "final": ("gemini-3-pro-image", {"aspectRatio": "16:9", "imageSize": "2K"})}


def gen(mode, out, prompt, refs=(), **kw):
    model, cfg = MODELS[mode]
    parts = [{"text": prompt}] + [{"inline_data": {"mime_type": mimetypes.guess_type(r)[0] or "image/png",
                                                   "data": base64.b64encode(open(r, "rb").read()).decode()}} for r in refs]
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": cfg}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try: res = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e: print("HTTP", e.code, e.read().decode("utf-8", "replace")[:400]); return None   # 402 などは黙って頼み直さない
    log(model, "image_" + mode, res, out=os.path.basename(out), **kw)
    for p in (res.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
        d = p.get("inlineData") or p.get("inline_data")
        if d: open(out, "wb").write(base64.b64decode(d["data"])); print("WROTE", out, model); return out
    print("絵が返らなかった", json.dumps(res, ensure_ascii=False)[:300]); return None


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    kw = dict(x[2:].split("=", 1) for x in sys.argv[1:] if x.startswith("--") and "=" in x)
    gen(a[0], a[1], open(a[2], encoding="utf-8").read(), a[3:], **kw)
