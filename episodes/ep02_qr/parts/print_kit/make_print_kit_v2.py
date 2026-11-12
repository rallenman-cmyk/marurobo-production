# 実機実験の印刷キット（A4・300dpi・1マス6mm）と記録表
import json, math
from PIL import Image, ImageDraw, ImageFont
A=json.load(open('/home/user/qr_plan/parts/qrdata/qr_assets.json'))
DPI=300; MM=DPI/25.4; W,H=round(210*MM),round(297*MM)
FB='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; FR='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
f=lambda s,b=False: ImageFont.truetype(FB if b else FR, s, index=0)
MOD=6.0; mp=MOD*MM; N=21; Q=4
def page(title,lines=()):
    im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
    d.text((15*MM,12*MM),title,font=f(70,True),fill='black')
    y=27*MM
    for ln in lines:
        d.text((15*MM,y),ln,font=f(40),fill=(40,40,40)); y+=6.2*MM
    return im,d,y
def draw_qr(d,x0,y0,mat,dots=None,ticks=False,logo=None):
    tot=(N+2*Q)*mp
    d.rectangle([x0,y0,x0+tot,y0+tot],fill='white')
    for r in range(N):
        for c in range(N):
            if mat[r][c]:
                X=x0+(c+Q)*mp; Y=y0+(r+Q)*mp; d.rectangle([X,Y,X+mp-1,Y+mp-1],fill='black')
    if logo:
        r0,c0,k=logo; X=x0+(c0+Q)*mp; Y=y0+(r0+Q)*mp; L=k*mp
        d.rectangle([X,Y,X+L,Y+L],fill='white')
        cx,cy=X+L/2,Y+L/2; R=L*0.36
        d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(250,250,250),outline=(150,210,206),width=int(mp*0.25))
        d.ellipse([cx-R*0.35,cy-R*0.35,cx+R*0.35,cy+R*0.35],fill=(190,230,228))
    if dots:
        for r,c in dots:
            X=x0+(c+Q+0.5)*mp; Y=y0+(r+Q+0.5)*mp; R=mp*0.42
            d.ellipse([X-R,Y-R,X+R,Y+R],fill='black')
    if ticks:   # 余白の外側に、マスの位置の目盛り（位置合わせ用）
        for i in range(N+1):
            for (ax,ay,bx,by) in [(x0+(i+Q)*mp,y0-3*MM,x0+(i+Q)*mp,y0-1*MM),(x0-3*MM,y0+(i+Q)*mp,x0-1*MM,y0+(i+Q)*mp)]:
                d.line([ax,ay,bx,by],fill=(150,150,150),width=3)
        for v,col in [(16.5,(220,0,0)),(A['experiments']['robot_step']['center_rc'][0],(0,90,220))]:
            X=x0+(v+Q)*mp; Y=y0+(v+Q)*mp
            d.polygon([(X,y0-1*MM),(X-1.5*MM,y0-4.5*MM),(X+1.5*MM,y0-4.5*MM)],fill=col)
            d.polygon([(x0-1*MM,Y),(x0-4.5*MM,Y-1.5*MM),(x0-4.5*MM,Y+1.5*MM)],fill=col)
    return tot
def apply(mat,exp):
    m=[row[:] for row in mat]
    for r,c,v in A['experiments'][exp]['changed']: m[r][c]=v
    return m
H_=A['symbols']['HELLO_H']['matrix']; L_=A['symbols']['HELLO_L']['matrix']; M_=A['symbols']['MATANE_H']['matrix']
E=A['experiments']
def sim(e): return '　'.join(f"{k}:{'読める' if v else '読めない'}" for k,v in E[e]['sim'].items())
pages=[]
im,d,y=page('QRコード回　実機実験キット',[
 '目的：台本の【実機】の台詞を、スマホで本当に確かめる。結果が違ったら台詞を直す。',
 '印刷：A4・「実際のサイズ（100%）」で印刷。1マス＝6mm。縮小すると切り抜きと合わなくなる。',
 '読み取り：最低2つ。iPhone標準カメラ／Android（Googleレンズ等）／LINE など。',
 'かざし方：真上から、QR全体＋余白が画面の半分くらいに入る距離で3回ずつ。',
 '記録：最後のページの表に、○（すぐ読める）・△（時間がかかる／ときどき）・×（読めない）。',
 '',
 'ページ一覧',
 ' 2  基準のQR「HELLO」（レベルH）　…冒頭・目印の箱・予備の量の右側に使う',
 ' 3  比べる用「HELLO」（レベルL）　…予備の量の左側',
 ' 4  インクのしずく12か所の版',
 ' 5  ロゴ7×7の版　 6  ロゴ＋しずく1つの版',
 ' 7  切り抜き（まるロボの体の形・3×3の箱・5×5の箱×2）',
 ' 8  記録表　　（台本 v2.0 確定版の10条件）',
 '',
 'シミュレーション（PC上の3つの読み取りライブラリ）の予想は各ページに書いてある。',
 '実機で違う結果が出たら、それが正しい。台本の数字はそれに合わせて直す。',
 '',
 '■ まるロボの体の置き方（2ページ）',
 '余白の外の目盛りの赤い三角＝乗ったときの体の中心（16.5マス目）。',
 '青い三角＝一歩踏み込んだときの中心。切り抜いた楕円の十字を、縦横の三角に合わせる。',
 '予想：赤の位置＝壊れる箱6個で読める／青の位置＝10個で読めない。',
]); pages.append(im)
def qrpage(title,lines,mat,**kw):
    im,d,y=page(title,lines); x0=(W-(N+2*Q)*mp)/2; draw_qr(d,x0,max(y+8*MM,70*MM),mat,**kw); return im
pages.append(qrpage('2　基準のQR「HELLO」（レベルH・マスク2）',['冒頭（まるロボの体）・目印の箱（3×3）・予備の量（5×5の箱、右側）に使う。',
  f"予想：体＝赤の位置 {sim('robot_stand')}",f"　　　体＝青の位置 {sim('robot_step')}",f"　　　目印の真ん中に3×3の箱 {sim('finder_box3')}",f"　　　右下に5×5の箱 {sim('box5_H')}"],H_,ticks=True))
pages.append(qrpage('3　比べる用「HELLO」（レベルL）',['同じ文字・同じ大きさで、予備が7個だけの版。',f"予想：右下に5×5の箱 {sim('box5_L')}"],L_,ticks=True))
pass  # v2.0で削った：pages.append(qrpage('4　中身の箱8個を消した版',['中身の箱1〜8番のマスを白にして印刷してある。',f"予想：{sim('content_erase_8')}"],apply(H_,'content_erase_8')))
pass  # v2.0で削った：pages.append(qrpage('5　中身の箱9個を消した版',['中身の箱1〜9番のマスを白にして印刷してある。',f"予想：{sim('content_erase_9')}"],apply(H_,'content_erase_9')))
pages.append(qrpage('4　インクのしずく12か所の版',['白いマスに、丸いしずく（マスの8割の大きさ）を12か所。12個とも別の箱。','本物のペンで点を打つ場合も、同じ位置に。',f"予想：{sim('ink12')}"],H_,dots=E['ink12']['drops']))
pages.append(qrpage('5　ロゴ7×7の版',['真ん中7×7マスにロゴ（白地＋うすい色の顔）。濃い色のロゴにすると結果が変わる。',f"予想：{sim('logo7')}（壊れる箱8個＝直せる上限ちょうど）"],H_,logo=(7,7,7)))
pages.append(qrpage('6　ロゴ＋しずく1つの版',['5ページにしずくを1つ足した版。',f"予想：{sim('logo7_ink1')}"],H_,logo=(7,7,7),dots=[E['logo7_ink1']['drop']]))
# 切り抜き
im,d,y=page('7　切り抜き',['線で切る。白い厚紙がよい（体は白、箱も白で計算している）。','楕円の十字を、2ページの余白の外の三角（赤＝乗る・青＝一歩）に合わせて置く。'])
st=A['experiments']['robot_stand']; rx=st['ellipse_modules'][0]*mp/2; ry=st['ellipse_modules'][1]*mp/2
for i,(cx,cy) in enumerate([(55*MM,y+45*MM),(150*MM,y+45*MM)]):
    d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],outline='black',width=4)
    d.line([cx-rx,cy,cx+rx,cy],fill=(180,180,180),width=3); d.line([cx,cy-ry,cx,cy+ry],fill=(180,180,180),width=3)
    d.text((cx-rx,cy+ry+2*MM),'まるロボの体（上から見た形）'+(' 予備' if i else ''),font=f(34),fill='black')
y2=y+110*MM
for i,(k,lab) in enumerate([(3,'3×3の箱（目印の真ん中）'),(5,'5×5の箱（右下・L用）'),(5,'5×5の箱（右下・H用）')]):
    x=20*MM+i*62*MM; d.rectangle([x,y2,x+k*mp,y2+k*mp],outline='black',width=4); d.text((x,y2+k*mp+2*MM),lab,font=f(32),fill='black')
d.text((15*MM,y2+50*MM),'5×5の箱は、QRの右下の角（余白の内側の角）に箱の角を合わせる。',font=f(36),fill='black')
d.text((15*MM,y2+57*MM),'3×3の箱は、左上の目印の真ん中の黒い3×3マスにぴったり重ねる。',font=f(36),fill='black')
pages.append(im)
# 記録表
rows=[('2 体（赤の位置）','robot_stand'),('2 体（青の位置）','robot_step'),('2 目印に3×3の箱','finder_box3'),('2 右下に5×5の箱（H）','box5_H'),
      ('3 右下に5×5の箱（L）','box5_L'),('4 しずく12','ink12'),
      ('5 ロゴ','logo7'),('6 ロゴ＋しずく1','logo7_ink1'),('2 何もしない（基準）',None),('3 何もしない（L）',None)]
im,d,y=page('8　記録表',['○＝すぐ読める（1秒以内）　△＝時間がかかる・ときどき読める　×＝読めない（10秒）','端末とアプリ：①＿＿＿＿＿＿　②＿＿＿＿＿＿　③＿＿＿＿＿＿'])
cols=[15,82,112,137,162,187]; heads=['条件','予想','①','②','③','メモ']
yy=y+6*MM
for c,h in zip(cols,heads): d.text((c*MM,yy),h,font=f(36,True),fill='black')
yy+=8*MM
for lab,e in rows:
    d.line([15*MM,yy-1.5*MM,197*MM,yy-1.5*MM],fill=(170,170,170),width=2)
    d.text((15*MM,yy),lab,font=f(34),fill='black')
    exp_='—' if e is None else ('読める' if all(E[e]['sim'].values()) else '読めない')
    d.text((82*MM,yy),exp_,font=f(34),fill='black'); yy+=12*MM
pages.append(im)
pages[0].save('QR回_実機実験キット_A4_v2.pdf',save_all=True,append_images=pages[1:],resolution=DPI)
import csv
with open('QR回_実機実験_記録表_v2.csv','w',newline='',encoding='utf-8-sig') as fo:
    w=csv.writer(fo); w.writerow(['ページ・条件','実験ID','予想（シミュレーション）','壊れる箱の数','端末①','端末②','端末③','メモ'])
    for lab,e in rows: w.writerow([lab,e or '', '' if e is None else ('読める' if all(E[e]['sim'].values()) else '読めない'),'' if e is None else E[e]['n_bad'],'','','',''])
for i,p in enumerate(pages): p.resize((W//4,H//4)).save(f'/tmp/claude-0/-home-user/8cc26183-437c-5f90-a7e9-3b23d7f91ab2/scratchpad/pk2_{i+1:02d}.png')
print('ok',len(pages))
