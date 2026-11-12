# 参考画像に合わせた人（髪は大きな平らな面のかたまり、アーモンド形の目と目尻の線、太くまっすぐな眉、服は大きな面）
FACET = {"hair": 2600}
ANIME = dict(socket=False, nose_style="anime", brow_flat=True, eye=1.0, eye_in=0.50, aeye=1.30, eye_open=2.05, lash_w=1.55, nose_tip=0.78, mouth_h=1.7, lid_up=24.0, lid_lo=29.0)
MAN = dict(ANIME, hs=1.10, nose=0.95, mouth_w=1.30, brow=1.70, brow_arch=0.30, cheek=0.38, jaw=0.90, chin=0.93, face_len=1.04, muzzle=0.60, nose_drop=0.003, ear_z=0.006, jaw_fwd=0.012,
           ear=1.08, neck=0.98)
WOMAN = dict(ANIME, hs=1.08, aeye=1.44, lid_up=25.0, nose=0.82, mouth_w=1.20, brow=1.05, brow_arch=0.55, cheek=0.86, jaw=0.84, chin=0.84,
             face_len=0.90, muzzle=0.62, nose_drop=0.002, ear_z=0.006, jaw_fwd=0.010, neck=0.92, width=0.96)
EYES = dict(iris1="#1C1310", iris2="#5A3C2A", iris_top="#060404", iris_bot="#21140E", iris_k=1.50, sclera="#F2E4DA", iris_up=13.0)
BASE = dict(style="clay", quality="look", earbuds=True, eyes="anime", lapels=True, facet=FACET, blush=0.2)
def HAIR(**kw):
    d = dict(style="swept", seed=3)
    d.update(kw); return d
PEOPLE = {
    "M1": dict(BASE, sheet="M1", head=dict(MAN), hair=HAIR(), body=dict(shoulder=0.188, chest=1.04, arm=0.90, collar=0), outfit="jacket_turtle", pose="phone_both", screen="music.png", phone_c=(0.02, -0.30, 1.0),
               colors=dict(EYES, skin="#EE9A6A", hair="#2C2E40", top="#10172C", inner="#0B0F1E", pants="#1C2230", shoe="#2B2B2F", sole="#DCD7CE")),
    "W1": dict(BASE, sheet="W1", head=dict(WOMAN), hair=HAIR(style="bob", seed=7),
               body=dict(shoulder=0.168, hip=1.03, chest=0.95, arm=0.84, collar=0), outfit="blazer", pose="phone_left", screen="news.png", phone_c=(0.03, -0.29, 0.985),
               colors=dict(EYES, skin="#F2A574", hair="#4A2C26", top="#B08B6E", inner="#2A2024", pants="#3A3330", shoe="#3A2E28", sole="#2A2422")),
    "G1": dict(BASE, sheet="G1", head=dict(MAN, hs=1.09, jaw=1.06, ear_z=0.004, jaw_fwd=0.005), hair=HAIR(style="neat", seed=4),
               body=dict(shoulder=0.186, belly=1.03, arm=0.90, collar=0), outfit="suit", glasses=True, glasses_w=1.8, pose="phone_left", screen="chat.png", phone_c=(0.03, -0.29, 0.97),
               colors=dict(EYES, skin="#E2966A", hair="#2C2B31", top="#12172A", inner="#D9DCE3", tie="#141826", pants="#2A2E38", shoe="#26221F", sole="#1E1B19")),
    "X1": dict(BASE, head=dict(MAN, hs=1.10), hair=HAIR(seed=9), body=dict(shoulder=0.184),
               outfit="blazer", pose="phone_both", screen="game.png",
               colors=dict(EYES, skin="#D9A57F", hair="#22201F", top="#5E6B7E", inner="#E8E6E0", pants="#2E3440", shoe="#ECEAE4", sole="#D9D3C8")),
    "X2": dict(BASE, head=dict(WOMAN), hair=HAIR(style="bob", seed=12),
               body=dict(shoulder=0.168, hip=1.03, arm=0.93), outfit="blazer", pose="phone_left", screen="music.png",
               colors=dict(EYES, skin="#F0C8AA", hair="#4A3326", top="#8C7F9E", inner="#ECE6DC", pants="#2C2E34", shoe="#C9A27A", sole="#3C2E26")),
}
