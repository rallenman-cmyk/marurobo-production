import json, hashlib, sys, importlib.util, os
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('s',os.path.join(here,'script_v0_1.py')); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
PID='MARU-QR'; LABEL='v0.1'; VID=PID+'-v0_1'; AT=sys.argv[1]
blocks=[]; md=['# まるロボ｜QRコード動画　台本 '+LABEL,'',s.HEADER.replace('\n','  \n'),'']
n=0
def c(ch,raw):
    global n; n+=1; blocks.append({'i':len(blocks),'k':'c','id':'N%03d'%n,'ch':ch,'raw':raw})
c('冒頭',s.HEADER)
for ch,head,scenes in s.CH:
    c(ch,head); md+=['---','',f'## {head}','']
    for sid,title,direction,lines in scenes:
        c(ch,f'S{sid}　{title}\n{direction}')
        md+=[f'### S{sid}　{title}','',*[f'- {l}' for l in direction.split('\n')],'']
        for k,(text,tags) in enumerate(lines,1):
            bid=f'{sid}-{k:02d}'
            blocks.append({'i':len(blocks),'k':'d','id':bid,'ch':ch,'sp':'ナレーション','tags':tags,'note':'','text':text})
            md.append(f'**{bid}** {"".join("【"+t+"】" for t in tags)}{text}  ')
        md.append('')
c('付記',s.APPENDIX); md+=['---','','## 付記','',*[f'- {l}' for l in s.APPENDIX.split('\n')[1:]]]
mdtxt='\n'.join(md)+'\n'
fn=os.path.join(os.path.dirname(here),'台本_v0_1.md'); open(fn,'w').write(mdtxt)
sha=hashlib.sha256(mdtxt.encode()).hexdigest()
d=[b for b in blocks if b['k']=='d']
ids=[b['id'] for b in d]; assert len(ids)==len(set(ids))
chapters=len({b['ch'] for b in blocks})
ver={'project':PID,'number':1,'label':LABEL,'based_on':None,'created_at':AT,'created_by':'ai','dialogue_count':len(d),'chapter_count':chapters,
     'blocks':blocks,'change_note':'初稿。構成案v1→台本v1（md）を、制作バイブルの台本ルール（ていねい語、たとえの宣言、実験の形、まとめは問い→答え、頭に載せて運ぶ）に合わせて直した版','file':'qr_plan/台本_v0_1.md','sha256':sha}
proj={'key':PID,'title':'QRコードは欠けてもなぜ読める？','channel':'まるロボ解説チャンネル','versions':[{'id':VID,'number':1,'label':LABEL,'created_at':AT,'created_by':'ai'}]}
json.dump(ver,open(os.path.join(here,'version_v0_1.json'),'w'),ensure_ascii=False)
json.dump(proj,open(os.path.join(here,'project.json'),'w'),ensure_ascii=False)
import re
narr=''.join(b['text'] for b in d).replace('（間）','')
print('dialogue',len(d),'chapters',chapters,'blocks',len(blocks),'narr chars',len(re.sub(r'\s','',narr)),'json bytes',os.path.getsize(os.path.join(here,'version_v0_1.json')),'sha',sha[:12])
