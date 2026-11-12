# 人の作風（見た目のパターン）。どれもオリジナル。現実の人間に寄せすぎない＝不気味の谷を避ける
# 共通の考え方：頭と目を大きく、鼻と口は簡単な形、肌の細かい凹凸はなし、色は明るめ
import hchar

BASE_POSE = dict(pose="phone_left", screen="music.png", earbuds=True)

STYLES = {
    "real": dict(label="今の版（参考）", note="現実の比率。目が小さく白目が見え、顔のしわ・頬のふくらみが現実的",
                 cfg=dict(hchar.HERO, style="real", quality="look")),
    "soft": dict(label="A ふんわり", note="丸くやわらかい形。大きな頭と目、ボタンのような鼻、つやを抑えた質感。絵本のような親しみ",
                 cfg=dict(style="soft", quality="look", earbuds=True,
                          head=dict(hs=1.42, cran=1.06, width=1.04, face_len=0.82, jaw=0.92, chin=0.82, cheek=1.25, cheek_z=-0.004,
                                    nose=0.58, muzzle=0.7, eye=1.45, eye_x=1.06, eye_z=-0.004, ear=0.95, brow=0.9, neck=1.10, mouth_w=0.9,
                                    iris=40.0, pupil=17.0, lid_up=37.0, lid_lo=38.0),
                          hair=dict(style="locks", lock_r=0.0215, lock_k=0.014, cap=0.010, cap_side=0.005, crown=(0.15, 0.40, 0.90), seed=3, swirl=0.5,
                                    locks=dict(front=[(-46, 21, 1.0, -12), (-20, 24, 1.1, -10), (6, 25, 1.1, -8), (30, 22, 0.95, -6)],
                                               side=[(64, 12, 1.0, 0), (-66, 10, 1.0, 0), (104, 2, 0.95, 0), (-106, 2, 0.95, 0)],
                                               back=[(140, -18, 1.0, 0), (180, -24, 1.05, 0), (-140, -18, 1.0, 0)])),
                          body=dict(shoulder=0.172, chest=1.06, belly=1.12, waist=1.10, hip=1.06, arm=1.15, thigh=1.12, finger=0.95, finger_r=1.25, palm=1.08),
                          colors=dict(skin="#F2C1A0", hair="#5A3A26", iris1="#4A2E1C", iris2="#8C5E36", top="#4FB3A9", pants="#3B4A63",
                                      shoe="#F4F1EA", sole="#E0B989"))),
    "film": dict(label="B くっきり", note="映画のCGアニメ風。形にメリハリ（広い肩・細い腰・はっきりした眉とあご）、大きな毛束。表情が伝わりやすい",
                 cfg=dict(style="film", quality="look", earbuds=True,
                          head=dict(hs=1.30, cran=1.03, width=0.98, face_len=0.94, jaw=1.06, chin=1.15, cheek=0.85, nose=0.92, muzzle=0.85,
                                    eye=1.28, eye_x=1.02, eye_z=0.0, ear=1.0, brow=1.3, neck=1.0, mouth_w=1.1,
                                    iris=36.0, pupil=15.0, lid_up=32.0, lid_lo=36.0),
                          hair=dict(style="locks", lock_r=0.0185, lock_k=0.009, cap=0.008, cap_side=0.0035, crown=(0.22, 0.45, 0.87), seed=5, swirl=0.75,
                                    locks=dict(front=[(-54, 19, 1.0, -28), (-32, 21, 1.1, -26), (-10, 23, 1.15, -24), (12, 24, 1.05, -22), (32, 21, 0.9, -18)],
                                               side=[(60, 14, 0.95, -6), (88, 12, 0.85, -4), (-64, 10, 0.95, 6), (-92, 10, 0.85, 4), (118, 0, 0.95, 0), (-120, 0, 0.95, 0)],
                                               back=[(150, -22, 1.0, 0), (180, -28, 1.05, 0), (-150, -22, 1.0, 0)])),
                          body=dict(shoulder=0.198, chest=1.10, belly=0.95, waist=0.90, hip=0.94, arm=1.02, thigh=1.0, finger=1.0, finger_r=1.05),
                          colors=dict(skin="#EDB48F", hair="#3A2418", iris1="#3A2414", iris2="#7A4E2A", top="#2F9C95", pants="#2E3A52",
                                      shoe="#EDEBE5", sole="#C9452F"))),
    "toy": dict(label="C おもちゃ", note="ソフビ人形のようなつやのある質感。大きな黒目、ひとかたまりの髪、ふっくらした手。小さなロボと同じ世界になじむ",
                cfg=dict(style="toy", quality="look", earbuds=True,
                         head=dict(hs=1.50, cran=1.08, width=1.02, face_len=0.80, jaw=0.95, chin=0.78, cheek=1.10, nose=0.52, muzzle=0.6,
                                   eye=1.30, eye_x=1.08, eye_z=-0.002, ear=0.85, brow=0.85, neck=1.08, mouth_w=0.85,
                                   iris=44.0, pupil=20.0, lid_up=40.0, lid_lo=40.0),
                         hair=dict(style="locks", lock_r=0.0235, lock_k=0.016, cap=0.011, cap_side=0.006, seed=7, swirl=0.4,
                                   locks=dict(front=[(-40, 22, 1.1, -10), (-14, 24, 1.2, -8), (12, 24, 1.15, -6), (34, 21, 1.0, -4)],
                                              side=[(66, 12, 1.0, 0), (-68, 10, 1.0, 0), (112, -2, 1.0, 0), (-114, -2, 1.0, 0)],
                                              back=[(162, -24, 1.1, 0), (-162, -24, 1.1, 0)])),
                         body=dict(shoulder=0.178, chest=1.04, belly=1.05, waist=1.05, hip=1.05, arm=1.12, thigh=1.10, finger=0.92, finger_r=1.25, palm=1.1),
                         colors=dict(skin="#F5C8A8", hair="#3B2A20", iris1="#2A1A10", iris2="#5A3820", top="#22A39A", pants="#34486E",
                                     shoe="#FFFFFF", sole="#E8A33C"))),
}


# ---- 毛束の髪型のひな形（乗客の変化づけ用。主人公の要素を組み替える）
LOCK_PRESETS = {
    "short": dict(front=[(-46, 21, 1.0, -12), (-20, 24, 1.1, -10), (6, 25, 1.1, -8), (30, 22, 0.95, -6)],
                  side=[(64, 12, 1.0, 0), (-66, 10, 1.0, 0), (104, 2, 0.95, 0), (-106, 2, 0.95, 0)],
                  back=[(140, -18, 1.0, 0), (180, -24, 1.05, 0), (-140, -18, 1.0, 0)]),
    "crop": dict(front=[(-36, 34, 0.8, -4), (-8, 37, 0.85, -2), (20, 35, 0.8, 0)],
                 side=[(70, 22, 0.75, 0), (-72, 22, 0.75, 0), (112, 8, 0.75, 0), (-112, 8, 0.75, 0)],
                 back=[(150, -10, 0.8, 0), (-150, -10, 0.8, 0)]),
    "bob": dict(front=[(-48, 12, 1.05, 18), (-20, 15, 1.10, 14), (10, 16, 1.10, -12), (38, 13, 1.05, -16)],
                side=[(62, -38, 1.35, -10), (-62, -38, 1.35, 10), (92, -52, 1.40, 0), (-92, -52, 1.40, 0)],
                back=[(124, -56, 1.40, 0), (156, -58, 1.45, 0), (-156, -58, 1.45, 0), (-124, -56, 1.40, 0)]),
    "parted": dict(front=[(-62, 14, 1.05, -30), (-38, 17, 1.15, -34), (-14, 20, 1.15, -36), (10, 24, 1.05, -38), (32, 27, 0.95, -32)],
                   side=[(66, 14, 0.95, -4), (-68, 8, 0.95, 4), (106, 2, 0.95, 0), (-108, 0, 0.95, 0)],
                   back=[(142, -18, 1.0, 0), (180, -24, 1.05, 0), (-142, -18, 1.0, 0)]),
}
