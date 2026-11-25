# Gemini を使った量を1回ずつ記録する（2026-11-25。ユーザー「ジェミニのapiのクレジット消費も激しい」。まるロボは記録がなく、何に使ったか分からなかったため）
#   記録先：$MARU_GEMINI_LOG → なければ リポジトリの logs/gemini_usage.jsonl（/home/user/marurobo-production があれば）→ なければ $MARU_WORK/logs/
#   作業の終わりに、記録をリポジトリの logs/ に入れて push する（container は片づけられると消えるため）
#   集計：python3 gemini_log.py sum
import os, sys, json, time, collections


def path():
    p = os.environ.get("MARU_GEMINI_LOG")
    if p: return p
    repo = "/home/user/marurobo-production"
    if os.path.isdir(repo): return os.path.join(repo, "logs", "gemini_usage.jsonl")
    return os.path.join(os.environ.get("MARU_WORK", "."), "logs", "gemini_usage.jsonl")


def log(model, kind, resp=None, **kw):
    """resp は Gemini の返事（dict）。usageMetadata（トークン数）を残す。kw に何の回の何か（ep・what・n など）を書く"""
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime()), "model": model, "kind": kind}
    if isinstance(resp, dict) and resp.get("usageMetadata"): rec["usage"] = resp["usageMetadata"]
    rec.update(kw)
    p = path(); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__" and sys.argv[1:2] == ["sum"]:
    c = collections.defaultdict(lambda: [0, 0, 0])
    for l in open(path(), encoding="utf-8"):
        r = json.loads(l); u = r.get("usage", {}); k = (r["at"][:10], r["model"], r["kind"])
        c[k][0] += 1; c[k][1] += u.get("promptTokenCount", 0); c[k][2] += u.get("candidatesTokenCount", 0)
    print("日付 | 型番 | 種類 | 回数 | 入力トークン | 出力トークン")
    for k, v in sorted(c.items()): print(" | ".join(map(str, k + tuple(v))))
