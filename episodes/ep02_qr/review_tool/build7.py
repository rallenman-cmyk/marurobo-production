import json, hashlib, sys, importlib.util, os, re
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('s',os.path.join(here,'script_v0_7.py')); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
PID='MARU-QR'; LABEL='v0.7'; VID=PID+'-v0_7'; AT=sys.argv[1]
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
        k=0
        expanded=[]
        for ln in lines:
            text,tags=ln[0],ln[1]
            if len(ln)>2: bid=ln[2]
            else: k+=1; bid=f'{sid}-{k:02d}'
            parts=[text]
            if len(text)>50:
                ps=[x for x in re.split(r'(?<=。)',text) if x]
                if len(ps)>=2 and all(x.count('「')==x.count('」') for x in ps): parts=ps
            for n,part in enumerate(parts):
                pid=bid if n==0 else bid+'bcdefg'[n-1]
                expanded.append((pid,part,tags))
        for bid,text,tags in expanded:
            note='　'.join(x for x in [('読み：HELLO＝ハロー' if 'HELLO' in text else ''),('読み：MATANE＝マタネ' if 'MATANE' in text else '')] if x)
            blocks.append({'i':len(blocks),'k':'d','id':bid,'ch':ch,'sp':'ナレーション','tags':tags,'note':note,'text':text})
            md.append(f'**{bid}** {"".join("【"+t+"】" for t in tags)}{text}  ')
        md.append('')
c('付記',s.APPENDIX); md+=['---','','## 付記','',*[f'- {l}' for l in s.APPENDIX.split('\n')[1:]]]
mdtxt='\n'.join(md)+'\n'
fn=os.path.join(os.path.dirname(here),'台本_v0_7.md'); open(fn,'w').write(mdtxt)
sha=hashlib.sha256(mdtxt.encode()).hexdigest()
d=[b for b in blocks if b['k']=='d']
ids=[b['id'] for b in d]; assert len(ids)==len(set(ids))
chapters=len({b['ch'] for b in blocks})
ver={'project':PID,'number':7,'label':LABEL,'based_on':PID+'-v0_6','created_at':AT,'created_by':'ai','dialogue_count':len(d),'chapter_count':chapters,
     'blocks':blocks,'change_note':'コメント13-02b（ここ分かりやすくして）を反映。読み方の帯に書いてある2つを、1つずつ言って札で見せる形に','file':'qr_plan/台本_v0_7.md','sha256':sha}
proj_unused={'key':PID,'title':'QRコードは欠けてもなぜ読める？','channel':'まるロボ解説チャンネル','versions':[{'id':VID,'number':1,'label':LABEL,'created_at':AT,'created_by':'ai'}]}
json.dump(ver,open(os.path.join(here,'version_v0_7.json'),'w'),ensure_ascii=False)

import re
narr=''.join(b['text'] for b in d).replace('（間）','')
print('dialogue',len(d),'chapters',chapters,'blocks',len(blocks),'narr chars',len(re.sub(r'\s','',narr)),'json bytes',os.path.getsize(os.path.join(here,'version_v0_7.json')),'sha',sha[:12])
