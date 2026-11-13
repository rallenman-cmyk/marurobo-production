# PC の描画のかわりの試しの動画（コマ番号を色と字で埋め込む）。名前・区切りは run_pc_render.ps1 と同じ
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]
R = {'qrop4_': ('qrop4', [(1, 2022)]), 'qrc1t2_': ('qrc1', [(1, 252)]), 'qrc1w5_': ('qrc1', [(253, 6559)]), 'qrc1s2_': ('qrc1', [(1, 222)]),
     'qrc2w_': ('qrc2', [(1, 1924), (2987, 3836), (4185, 4339), (5212, 5516), (6346, 7036), (7165, 8452)]), 'qrc2t_': ('qrc2', [(8428, 9567), (9697, 10003)]),
     'qrc3w_': ('qrc3', [(1, 1514), (1737, 2010), (2315, 3211)]), 'qrc4f_': ('qrc4', [(279, 1006)]),
     'qrc4c_': ('qrc4', [(1146, 1319), (1666, 3076), (3655, 7234), (8611, 9582)]), 'qrc4w_': ('qrc4', [(1, 303), (982, 1170), (1295, 1448), (3052, 3347), (7796, 8184), (9724, 10568)]),
     'qrc5w_': ('qrc5', [(327, 816), (1391, 2237), (2817, 3339), (3495, 3603)])}
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 28)
for pid, (pre, (fold, rs)) in enumerate(R.items()):
    os.makedirs(os.path.join(OUT, fold), exist_ok=True)
    for a0, b0 in rs:
        for a in range(a0, b0 + 1, 100):
            b = min(a + 99, b0); p = os.path.join(OUT, fold, '%s%04d-%04d.mp4' % (pre, a, b))
            ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '320x180', '-r', '24', '-i', '-', '-c:v', 'libx264', '-qp', '0', '-pix_fmt', 'yuv444p', p], stdin=subprocess.PIPE)
            for f in range(a, b + 1):
                im = Image.new('RGB', (320, 180), ((f % 16) * 16, ((f // 16) % 16) * 16, (f // 256) * 6)); d = ImageDraw.Draw(im)
                d.rectangle((60, 60, 300, 130), fill='white'); d.text((70, 70), '%s %d' % (pre, f), font=F, fill='black'); ff.stdin.write(im.tobytes())
            ff.stdin.close(); ff.wait()
    print(pre, flush=True)
