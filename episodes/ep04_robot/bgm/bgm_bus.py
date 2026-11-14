# ロボットではありません回の BGM（2026-11-14 ユーザー「なんで BGM ないの」→ いま入れる）
#   曲は 3 本目と同じ B・C・D（3 本目の確認ページ https://claude.ai/artifact/JCZiLxFCQ9QDY8fRuvJMz4 の bgm_b/c/d.mp3。git には入れない）
#   作業フォルダの stage/bgm/ に置く。切り替え・大きさ・くり返しは 3 本目の bgm_bus.py をそのまま使う
#   B（基本）：S01〜S03 夜の買い物・問い、S07〜S11 昔のテスト・機械の目、S22〜S23 まとめ・オチ
#   C（抜き足差し足・にぎやかに試す）：S04〜S06 押す人を変える実験、S17〜S18 マスの床・端っこのマス
#   D（ジャズの探偵・はらはら）：S12〜S16 画面の中で足あとを調べる、S19〜S21 AI が追いかけてくる（2 回目は 40 秒目から）
#   使い方：import bgm_bus; music = bgm_bus.make(END, SCST, sr, work)   SCST＝場面ごとの始まりの秒
import os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location("bgm_bus_ep03", os.path.join(HERE, "..", "..", "ep03_ad", "bgm", "bgm_bus.py"))
B3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(B3)

PLAN = [("B", "S01"), ("C", "S04"), ("B", "S07"), ("D", "S12"), ("C", "S17"), ("D", "S19"), ("B", "S22")]
OFFSET = {("D", "S19"): 40.0, ("C", "S17"): 60.0}
RMS = 0.017   # v9：ユーザー「BGM もう少し音量下げて」→ 3 本目の 0.024 から 3 dB 下げた（声より約 20 dB 下）


def make(END, SCST, sr, work):
    B3.SRC = os.path.join(work, "stage", "bgm")
    B3.PLAN, B3.OFFSET, B3.RMS = PLAN, OFFSET, RMS
    return B3.make(END, SCST, sr)
