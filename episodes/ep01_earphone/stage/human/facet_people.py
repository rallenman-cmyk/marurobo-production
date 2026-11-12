# 参考画像の作風（髪と服は面のカクカク、顔はなめらか、大きな黒目と太いまぶたの線）の人の設定
import styles
FACET = {"hair": 0.035, "top": 0.028, "pants": 0.030, "shoe": 0.10, "hood": 0.12, "cap": 0.20}
MAN = dict(hs=1.12, eye=1.24, iris=44.0, pupil=19.0, lid_up=31.0, lid_lo=37.0, nose=0.72, mouth_w=0.78, brow=1.65, cheek=0.9, jaw=0.98,
           chin=1.0, face_len=0.97, neck=1.1)
WOMAN = dict(hs=1.10, eye=1.30, iris=44.0, pupil=19.0, lid_up=32.0, lid_lo=38.0, nose=0.66, mouth_w=0.74, brow=1.25, cheek=0.92, jaw=0.90,
             chin=0.9, face_len=0.95, neck=1.0, width=0.97)
EYES = dict(iris1="#1A1311", iris2="#4A3328")
def H(kind, seed, **kw):
    d = dict(style="locks", lock_r=0.0170, lock_k=0.011, cap=0.009, cap_side=0.0045, seed=seed, swirl=0.6, locks=styles.LOCK_PRESETS[kind])
    d.update(kw); return d
BASE = dict(style="facet", quality="look", earbuds=True, eye_hl=True, lash=2, facet=FACET)
PEOPLE = {
    "A": dict(BASE, head=dict(MAN), hair=H("parted", 21, lock_r=0.0185), body=dict(shoulder=0.188, chest=1.04),
              outfit="jacket_turtle", pose="phone_both", screen="music.png",
              colors=dict(EYES, skin="#ECB792", hair="#16151A", top="#222839", inner="#191D2B", pants="#252A36", shoe="#2B2B2F", sole="#DCD7CE")),
    "B": dict(BASE, head=dict(MAN), hair=H("short", 21, lock_r=0.0175), body=dict(shoulder=0.186),
              outfit=None, hood=True, cap=True, pose="phone_both", screen="music.png",
              colors=dict(EYES, skin="#ECB792", hair="#16151A", top="#2A9D8F", pants="#34486E", shoe="#F1EFEA", sole="#D9D3C8", cap="#D49A22")),
    "P01": dict(BASE, head=dict(WOMAN), hair=H("bob", 7, lock_r=0.0225, cap=0.012, cap_side=0.009), body=dict(shoulder=0.170, hip=1.03, chest=0.96, arm=0.93),
                outfit="blazer", pose="phone_left", screen="news.png",
                colors=dict(EYES, skin="#F0C29F", hair="#33231C", top="#D7C7AC", inner="#23201E", pants="#2E2C30", shoe="#3A2E28", sole="#2A2422")),
    "P02": dict(BASE, head=dict(MAN, hs=1.10, jaw=1.05), hair=H("short", 4, lock_r=0.0150), body=dict(shoulder=0.186, belly=1.04),
                outfit="suit", glasses=True, pose="phone_left", screen="chat.png",
                colors=dict(EYES, skin="#E6B591", hair="#222024", top="#3A3F48", inner="#ECECEA", tie="#22252C", pants="#343840", shoe="#26221F", sole="#1E1B19")),
    "P03": dict(BASE, head=dict(MAN, hs=1.11), hair=H("crop", 9, lock_r=0.0150), body=dict(shoulder=0.182),
                outfit=None, pose="phone_both", screen="game.png",
                colors=dict(EYES, skin="#D9A57F", hair="#2A2220", top="#6E7C8E", pants="#3E4552", shoe="#ECEAE4", sole="#D9D3C8")),
    "P04": dict(BASE, head=dict(WOMAN), hair=H("bob", 12, lock_r=0.0220, cap=0.012, cap_side=0.009), body=dict(shoulder=0.169, hip=1.03, arm=0.94),
                outfit="blazer", pose="phone_left", screen="music.png",
                colors=dict(EYES, skin="#F0C8AA", hair="#4A3326", top="#8C7F9E", inner="#ECE6DC", pants="#2C2E34", shoe="#C9A27A", sole="#3C2E26")),
}
