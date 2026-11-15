# 6本目（配膳ロボット）の BGM。曲は 3本目・4本目と同じ B・C・D（3本目の確認ページ https://claude.ai/artifact/JCZiLxFCQ9QDY8fRuvJMz4 の bgm_b/c/d.mp3。git には入れない）
#   作業フォルダの stage/bgm/ に置く。切り替え（前の曲を 2.5 秒で消し、次を 2 秒で入れ、2 秒重ねる）・大きさ・くり返しは 3本目の bgm_bus.py をそのまま使う
#   B（基本・おだやか）：S01〜S13 ファミレス・先輩に会う・席の点・天井の目印／S22 スープ／S26〜S30 顔・まとめ・オチ
#   C（にぎやかに試す）：S17〜S21 低い物・高い物・子どもの飛び出し／S23〜S25 通路を狭くする
#   D（不思議・なぞ）：S14〜S16 先輩の目で見たファミレス（暗い中の点）
#   使い方：import bgm_bus; music = bgm_bus.make(END, SCST, sr, work)   SCST＝場面ごとの始まりの秒
import os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("B", "S01"), ("D", "S14"), ("C", "S17"), ("B", "S22"), ("C", "S23"), ("B", "S26")]
OFFSET = {("C", "S23"): 60.0, ("B", "S22"): 0.0}   # 曲 C・D は約 3 分（くり返さない）。同じ曲の 2 回目は途中から
RMS = 0.017   # 4本目 v9 で決めた大きさ（声より約 20 dB 下）


def make(END, SCST, sr, work):
    B3.SRC = os.path.join(work, "stage", "bgm")
    B3.PLAN, B3.OFFSET, B3.RMS = PLAN, OFFSET, RMS
    return B3.make(END, SCST, sr)
