# 門番の絵コンテに、字幕（チャンネルの決まり：1280×720 で 56・太字・紺のふち5・影）と 2D の札を重ねる
import sys
from PIL import Image, ImageDraw, ImageFont
F=sys.argv[1]  # フォントのフォルダ
B=ImageFont.truetype(F+'/NotoSansJP_700Bold.ttf',56)
L=ImageFont.truetype(F+'/NotoSansJP_700Bold.ttf',50)
NAVY=(20,36,72)
def sub(im,text):
    d=ImageDraw.Draw(im); rows=text.split('\n'); lh=72
    y0=im.height-40-lh*len(rows)
    for k,row in enumerate(rows):
        w=d.textlength(row,font=B); x=(im.width-w)/2; y=y0+k*lh
        d.text((x+3,y+4),row,font=B,fill=(0,0,0),stroke_width=5,stroke_fill=(0,0,0))
        d.text((x,y),row,font=B,fill='white',stroke_width=5,stroke_fill=NAVY)
def tag(im,text,cx,cy,bg=(255,255,255),fg=NAVY,tail=None):
    d=ImageDraw.Draw(im); bb=d.textbbox((0,0),text,font=L); w=bb[2]-bb[0]; th=bb[3]-bb[1]; h=th+30
    x0,y0=cx-w/2-22,cy-h/2; x1,y1=cx+w/2+22,cy+h/2
    if tail: d.polygon([(cx-16,y1-2),(cx+16,y1-2),tail],fill=bg)
    d.rounded_rectangle([x0,y0,x1,y1],18,fill=bg,outline=NAVY,width=4)
    d.text((x0+22-bb[0],cy-th/2-bb[1]),text,font=L,fill=fg)
for v,subtext,tags in [
  ('A','……消えてしまいました。',[('見張り番',1130,300,None)]),
  ('B','片目だけ、開きました！',[('Hey, Siri-al',600,120,(800,165))]),
  ('C','柱の上のランプが、\nオレンジに光っていますね。',[('Hey Siri',640,110,(640,215))]),
]:
    im=Image.open(f'raw/gate_{v}.png').convert('RGB')
    for t,cx,cy,tail in tags: tag(im,t,cx,cy,tail=tail)
    sub(im,subtext)
    im.save(f'gate_{v}_sub.png')
    im.resize((390,219),Image.LANCZOS).save(f'gate_{v}_390.png')
