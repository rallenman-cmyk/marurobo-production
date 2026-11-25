"""（まるロボ：2026-11-25 に恋愛の tools/lovart.py から写した。サムネの絵はこれで描く。Gemini では描かない）
Lovart の画像生成を呼ぶ最小のプログラム（公式 lovartai/lovart-skill の agent_skill.py と同じ API・同じ署名）。

使い方:
  python3 tools/lovart.py mode                       … いまの生成モードと使えるモデル（料金はかからない）
  python3 tools/lovart.py upload 画像.png             … 見本画像を上げて URL を出す
  python3 tools/lovart.py gen 出力フォルダ プロンプト.txt [--ref URL ...] [--model generate_image_gpt_image_2] [--auto-confirm]
  python3 tools/lovart.py project URL ...             … 見本を登録したプロジェクトを作って ID を出す
  （gen に --project ID を付けると、そのプロジェクトで続けて頼む。見本の登録の上限を避けるため）
  python3 tools/lovart.py confirm 出力フォルダ スレッドID プロジェクトID 見積もり  … 止めていた1件を確認して進める

決まり:
- クレジットは使ってよく、使ったあとに報告する（2026-10-27 ユーザー決定）。--auto-confirm を付けると、
  高い操作の確認（pending_confirmation）が出ても確認して進め、見積もりのクレジットを記録する。付けないときは止める。
- 失敗・結果が分からないときに作り直さない。
- 使ったものは logs/lovart_usage.jsonl に1行ずつ残す。
鍵は環境変数 LOVART_ACCESS_KEY / LOVART_SECRET_KEY から読む。
"""
import hashlib, hmac, json, os, sys, time, urllib.error, urllib.parse, urllib.request, uuid

BASE = os.environ.get("LOVART_BASE_URL", "https://lgw.lovart.ai")
PREFIX = "/v1/openapi"
AK, SK = os.environ["LOVART_ACCESS_KEY"], os.environ["LOVART_SECRET_KEY"]
LOG = os.environ.get("MARU_LOVART_LOG") or ("/home/user/marurobo-production/logs/lovart_usage.jsonl" if os.path.isdir("/home/user/marurobo-production") else os.path.join(os.environ.get("MARU_WORK", "."), "logs", "lovart_usage.jsonl"))
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def sign(method, path):
    ts = str(int(time.time()))
    sig = hmac.new(SK.encode(), f"{method}\n{path}\n{ts}".encode(), hashlib.sha256).hexdigest()
    return {"X-Access-Key": AK, "X-Timestamp": ts, "X-Signature": sig,
            "X-Signed-Method": method, "X-Signed-Path": path}


def call(method, path, body=None, params=None):
    path = PREFIX + path
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    h = sign(method, path)
    h["Content-Type"] = "application/json"
    h["User-Agent"] = "LovartAgentSkill/1.0"
    if method == "POST":
        h["Idempotency-Key"] = uuid.uuid4().hex
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(6):  # 429（頼みすぎで断られた＝受け付けていない）のときだけ、待って頼み直す
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=120) as r:
                d = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            log({"event": "429 で断られた。待って頼み直す", "path": path, "attempt": attempt + 1})
            time.sleep(20 * (attempt + 1))
            h = sign(method, path); h["Content-Type"] = "application/json"; h["User-Agent"] = "LovartAgentSkill/1.0"
            if method == "POST":
                h["Idempotency-Key"] = uuid.uuid4().hex
    if isinstance(d, dict) and d.get("code", 0) != 0:
        raise RuntimeError(f"Lovart エラー {d.get('code')}: {d.get('message')}")
    return d.get("data", d)


def upload(local):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(local)}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + open(local, "rb").read() + f"\r\n--{b}--\r\n".encode()
    path = PREFIX + "/file/upload"
    h = sign("POST", path)
    h["Content-Type"] = f"multipart/form-data; boundary={b}"
    h["User-Agent"] = "LovartAgentSkill/1.0"
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data=body, headers=h, method="POST"), timeout=120) as r:
        d = json.loads(r.read().decode())
    if d.get("code") != 0:
        raise RuntimeError(f"アップロード失敗: {d.get('message')}")
    return d["data"]["url"]


def log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def wait(tid, timeout=900):
    end = time.time() + timeout
    status = "timeout"
    while time.time() < end:
        s = call("GET", "/chat/status", params={"thread_id": tid})["status"]
        if s in ("done", "abort"):
            time.sleep(5)
            status = call("GET", "/chat/status", params={"thread_id": tid})["status"]
            if status in ("done", "abort"):
                break
        time.sleep(3)
    return status


def collect(outdir, tid, rec):
    res = call("GET", "/chat/result", params={"thread_id": tid})
    rec["failures"] = res.get("failures") or []
    os.makedirs(outdir, exist_ok=True)
    files = []
    for it in res.get("items", []):
        for a in it.get("artifacts") or []:
            u = a.get("content", "")
            if not u:
                continue
            ext = os.path.splitext(u.split("?")[0])[-1] or ".png"
            p = os.path.join(outdir, hashlib.sha1(u.encode()).hexdigest()[:12] + ext)
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.lovart.ai/"})
            with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f:
                f.write(r.read())
            files.append(p)
    rec["files"] = files
    rec["text"] = " ".join((it.get("text") or "") for it in res.get("items", []))[:500]
    return res


def confirm(outdir, tid, pid, estimate):
    call("POST", "/chat/confirm", {"thread_id": tid})
    rec = {"project_id": pid, "thread_id": tid, "confirmed": True, "estimated_credits": estimate}
    rec["status"] = wait(tid)
    collect(outdir, tid, rec)
    log(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def new_project(refs):
    """見本を登録したプロジェクトを作る。登録は1分あたりの回数に上限がある（2026-10-27 code 1429）ので間を空ける。"""
    bad = [u for u in refs if not u.startswith("https://")]
    if bad:  # 見本の URL が空・不正なら、プロジェクトを作る前に止める
        sys.exit(f"見本の URL が不正です: {bad}")
    pid = call("POST", "/project/save", {"project_id": "", "canvas": "", "project_cover_list": [],
                                         "pic_count": 0, "project_type": 3})["project_id"]
    for i, u in enumerate(refs):  # 見本を先にプロジェクトへ登録する（公式の upload-artifact と同じ）
        if i:
            time.sleep(15)
        call("POST", "/artifact/upload", {"project_id": pid, "artifact_type": "image", "artifact_content": u})
    if refs:
        time.sleep(20)  # 10秒では「見本が見当たらない」と返ることがあった（2026-10-27、3件）
    return pid


def gen(outdir, prompt, refs, model, timeout=900, auto_confirm=False, project=None, _retried=False):
    # project を渡すと、見本を登録済みのプロジェクトで続けて頼む（登録の回数を減らす）
    pid = project or new_project(refs)
    body = {"prompt": prompt, "project_id": pid}
    if refs:
        body["attachments"] = refs
    if model:
        body["tool_config"] = {"prefer_tool_categories": {"IMAGE": [model]}}
    tid = call("POST", "/chat", body)["thread_id"]
    status = wait(tid, timeout)
    res = call("GET", "/chat/result", params={"thread_id": tid})
    pc = res.get("pending_confirmation")
    rec = {"project_id": pid, "thread_id": tid, "model": model, "status": status,
           "pending_confirmation": pc, "failures": res.get("failures") or []}
    if pc and not auto_confirm:
        rec["stopped"] = "高い操作の確認が出たので止めた（confirm していない）"
        log(rec)
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        return rec
    if pc:
        log(dict(rec, note="確認して進める"))
        return confirm(outdir, tid, pid, pc.get("estimated_cost"))
    collect(outdir, tid, rec)
    rec["estimated_credits"] = 0
    if not rec.get("files") and not rec["failures"] and not _retried:
        # 絵が返らず（頼む文だけが返り）、クレジットも使われなかったときだけ、同じ頼む文で1回だけ頼み直す（ルール11、2026-11-09 決定）
        rec["note"] = "絵が返らず0クレジット。同じ頼む文で1回だけ頼み直す"
        log(rec)
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        return gen(outdir, prompt, refs, model, timeout, auto_confirm, pid, _retried=True)
    log(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "mode":
        print(json.dumps(call("POST", "/mode/query", {}), ensure_ascii=False, indent=1))
    elif a[0] == "upload":
        print(upload(a[1]))
    elif a[0] == "gen":
        refs, model, auto, project, rest = [], None, False, None, a[3:]
        while rest:
            k = rest.pop(0)
            if k == "--project":
                project = rest.pop(0)
            elif k == "--ref":
                refs.append(rest.pop(0))
            elif k == "--model":
                model = rest.pop(0)
            elif k == "--auto-confirm":
                auto = True
        gen(a[1], open(a[2], encoding="utf-8").read(), refs, model, auto_confirm=auto, project=project)
    elif a[0] == "project":
        print(new_project(a[1:]))
    elif a[0] == "confirm":
        confirm(a[1], a[2], a[3], int(a[4]))
