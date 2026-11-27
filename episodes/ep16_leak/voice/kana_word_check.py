# 言葉の読みちがい（1 音だけちがう：影→鍵 など）を探す。字幕の聞き取り（sub_hear）は似ている度 0.8 で見るので、1 音のちがいは通ってしまう
#   （16本目 9章 v22：38-05「影に錠を」が「かぎに」と読まれていたのを、sub_hear は 0 枚と数えた）
#   使い方：MARU_WORK=<作業フォルダ> GEMINI_API_KEY=... python3 kana_word_check.py <漢字> <ひらがな> [placement.json]
#   例：python3 kana_word_check.py 影 かげ → 「影」の入った文を全部、声だけでひらがなに書き起こし、「かげ」の数が台本の「影」の数より少ない文を出す
#   出た文は、3 回ずつ聞き直してから直す（1 回だけだと聞き取りのまちがいがある）
import os, sys, json, base64, urllib.request
from concurrent.futures import ThreadPoolExecutor
W = os.environ["MARU_WORK"]; D = W + "/stage/voice/achernar"
KJ, KN = sys.argv[1], sys.argv[2]
PL = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "placement.json")
MODEL = os.environ.get("HEAR_MODEL", "gemini-3-flash-preview")
P = [p for p in json.load(open(PL, encoding="utf-8")) if KJ in p["text"]]


def tr(no):
    b = base64.b64encode(open(D + "/line_%03d.wav" % no, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b}}, {"text": "この音声を、聞こえたとおりに、すべてひらがなだけで書き起こしてください。漢字は使わない。書き起こしだけを出力。"}]}]}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    for k in range(3):
        try: return json.load(urllib.request.urlopen(req, timeout=120))["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e: err = str(e)
    return "ERR " + err


with ThreadPoolExecutor(4) as ex: R = list(ex.map(lambda p: tr(p["no"]), P))
bad = 0
for p, r in zip(P, R):
    nk, ng = p["text"].count(KJ), r.count(KN)
    if ng < nk:
        bad += 1; print(p["no"], p["text"], "／", r.replace("\n", " ")[:60])
print("「%s」の文 %d、「%s」が足りない文 %d" % (KJ, len(P), KN, bad))
