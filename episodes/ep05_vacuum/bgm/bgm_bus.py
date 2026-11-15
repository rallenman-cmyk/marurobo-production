# 5本目（ロボット掃除機）の BGM。曲は 3本目・4本目と同じ B・C・D（3本目の確認ページ https://claude.ai/artifact/JCZiLxFCQ9QDY8fRuvJMz4 の bgm_b/c/d.mp3。git には入れない）
#   作業フォルダの stage/bgm/ に置く。切り替え（前の曲を 2.5 秒で消し、次を 2 秒で入れ、2 秒重ねる）・大きさ・くり返しは 3本目の bgm_bus.py をそのまま使う
#   B（基本・おだやか）：S01〜S05 地図が出た・先輩に会う／S09〜S12 光の物差し（不思議）／S26〜S27 まとめ・オチ
#   C（にぎやかに試す）：S06〜S08 昔の先輩・目の光を消して試す／S16〜S19 じゅうたん・カメラの先輩／S22〜S25 段差・よける
#   D（はらはら・なぞ）：S13〜S15 自分はどこ？（にわとりと卵）／S20〜S21 電気を消すと迷子
#   使い方：import bgm_bus; music = bgm_bus.make(END, SCST, sr, work)   SCST＝場面ごとの始まりの秒
import os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("B", "S01"), ("C", "S06"), ("B", "S09"), ("D", "S13"), ("C", "S16"), ("D", "S20"), ("C", "S22"), ("B", "S26")]
OFFSET = {("D", "S20"): 40.0, ("C", "S22"): 60.0}   # 曲 C・D は約 3 分（くり返さない）。同じ曲の 2 回目は途中から
RMS = 0.017   # 4本目 v9 で決めた大きさ（声より約 20 dB 下）


def make(END, SCST, sr, work):
    B3.SRC = os.path.join(work, "stage", "bgm")
    B3.PLAN, B3.OFFSET, B3.RMS = PLAN, OFFSET, RMS
    return B3.make(END, SCST, sr)
