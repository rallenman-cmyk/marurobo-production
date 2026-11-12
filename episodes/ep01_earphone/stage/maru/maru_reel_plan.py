# まるロボの動きの見本リールの予定（動きの順番と字幕）。Blender の外でも中でも同じ予定を使う
import marumotion as mm

PLATFORM = dict(center=(-3.6, 0.0), size=(0.9, 0.9), height=0.30)     # 跳び乗る台（歩く道からはずれた所）
DOCK = dict(near=0.47, depth=1.0, height=1.03, width=1.1, mu=0.05)      # 荷物を受け取るローラーの台（ロボの後ろ、中心から手前の端まで 0.47m）
CARGO_Y = 3.0                                                           # 荷物の場面は別の場所（カットで移る）


def reel_plan():
    p = mm.Plan(pos=(0.0, 0.0), heading=180.0, seed=5)          # カメラ（−Y の側）のほうを向いて立つ
    p.idle(4.0, label="待機｜呼吸 ±0.8cm・0.25Hz／まばたき 3〜5秒ごと（閉2コマ・止1・開4）／体重移動")
    p.look_around(label="見回す｜目が先に跳び（約0.1秒）、0.12秒遅れて胴が追う。胴が追いつくと目は真ん中へ")
    p.walk_to((2.6, 0.0), speed=mm.V_WALK, label="歩く 1.0m/s｜足踏みで向きを変えてから。歩幅0.64m・毎秒3.1歩・上下4.5cm・横揺れ±5°・足は滑らない")
    p.turn_to(180.0, label="その場で向きを変える｜目→胴→足の順。片足ずつ最大35°の足踏み")
    p.nod(label="うなずく｜首がないので胴ぜんぶで：下げて0.2秒・戻して0.28秒×2")
    p.shake(label="首を振る｜胴を左右に12°ひねる→だんだん小さく")
    p.idle(0.8, shifts=False)
    p.surprise(label="驚く｜0.2秒の反応の遅れ→反射のまばたき→目を見開き、後ろへ5cm跳ぶ")
    p.idle(0.6, shifts=False)
    p.hops(n=3, label="喜んで跳ねる｜高さ6cm×3回。着地は脚で受け止めて次の跳びへ（加速度は物理どおり）")
    p.idle(0.6, shifts=False)
    p.think(label="考える→ひらめく｜目が斜め上→首をかしげる→光がゆっくり点滅→つま先で床をたたく")
    p.idle(0.5, shifts=False)
    p.peer(label="のぞき込む｜腰から前へ24°。レンズを前へ出して絞る（ピント合わせ）")
    p.walk_to((-2.4, 0.0), speed=mm.V_BRISK, label="急ぎ足 1.3m/s→止まる｜1.4秒・0.91mで止まる（最大の減速1.39m/s²＝後ろへ8°傾く）")
    p.turn_to(180.0)
    p.sigh(label="ほっとする｜吸って少し伸び→吐いて3cm沈む。アンテナが垂れ、目と光がゆるむ")
    cx, cy = PLATFORM["center"]
    p.jump_to((cx, cy), z1=PLATFORM["height"], label="台に跳び乗る（高さ30cm・1.2m先）｜しゃがみ（4.5cm）→脚を伸ばして蹴る→放物線→脚を伸ばして着き、受け止める")
    p.turn_to(180.0)
    p.hops(n=2, height=0.05, spin=12.0)
    p.idle(0.8, shifts=False)
    p.jump_to((-2.5, 0.0), z1=0.0, apex=0.12, label="跳び降りる（30cm）｜着いたときの速さ 約3m/s を脚で受け止める")
    p.idle(1.0, shifts=False)
    # ---- 荷物（カットして持たせる。別の場所）
    p.teleport((-2.6, CARGO_Y), -90.0); p.set_carry(True)
    p.idle(0.6, shifts=False)
    p.walk_to((0.2, CARGO_Y), speed=mm.V_WALK, label="荷物を運ぶ｜荷物はベルトのばねで前後に少し動く（2.2Hz）")
    p.turn_to(180.0, label="受け取る台に背を向ける")
    p.unload_back(dock=DOCK, label="荷物を後ろの台へ降ろす｜体を前へ6°（釣り合い）→荷台を後ろへ26°→荷物が滑って台へ（荷台の摩擦0.28・台はローラー）")
    p.sigh(label="ほっとする")
    p.idle(1.5)
    return p


PEDESTAL = dict(pos=(4.5, -0.6), height=0.55)            # 紹介する物を置く台（走り終わったロボの左前）


def extra_plan():
    """追加の動き（走る・首をかしげる・紹介する）の短い見本"""
    p = mm.Plan(pos=(-4.2, 0.0), heading=-90.0, seed=9)
    p.idle(1.2, shifts=False)
    p.run_to((3.8, 0.0), label="走る 2.0m/s｜1.45m/sを超えると走りに切り替わる。歩幅0.97m・毎秒4.1歩・両足が宙に浮く間あり（地面に着いている割合0.35）")
    p.turn_to(180.0)
    p.idle(0.6, shifts=False)
    p.confused(label="首をかしげる｜目を少し細めて上を見る→右へ10°かしげる→反対へ少し→戻る")
    p.idle(0.5, shifts=False)
    p.present(49.0, label="紹介する（これです）｜横の物を見る→アンテナの光を2回点滅→向き直って小さくうなずく")
    p.idle(0.8, shifts=False)
    p.greet(label="あいさつ｜ゆっくりまばたき→腰から前へ15°おじぎ→起きる。光があたたかくふくらむ")
    p.idle(0.8, shifts=False)
    p.rest(2.6, label="休む｜目の輪が細くなり、体が4cm沈んで前へ6°、光が落ちる")
    p.wake(label="起きる｜2回まばたき→目が開き、体が少し伸びて戻る")
    p.idle(1.5)
    return p
