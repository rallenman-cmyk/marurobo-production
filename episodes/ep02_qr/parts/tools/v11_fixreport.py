import json,glob,os
exec(open('v11_explain.py').read())
cs={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob('fr/comments/*.json')}
m={x['id']:x['n'] for x in json.load(open('v10_comments_mapped.json'))}
m['cmwf6rkq5dzcgxe4b']=92
def nt(t): return None if t is None else round(t+(1.12 if t>=1628.458333 else 0.0),2)
items=[]
for k,c in sorted(cs.items(),key=lambda kv:(kv[1]['t'] is None, kv[1]['t'] or 0)):
    a,ex=E[m[k]]
    items.append(dict(comment_id=k,comment_rev=c['rev'],original_text=c['text'],original_t=c['t'],original_t_end=c.get('t_end'),
        action=a,explain=ex,reason=('' if a=='fixed' else '3D の動きの直しはパソコンで描き直すため、v12 で直します。'),
        new_version_id='MARU-EP02-v11',new_t=nt(c['t']),new_t_end=nt(c.get('t_end'))))
d=dict(created_at='2026-11-13T22:30:00Z',created_by='ai',from_version='MARU-EP02-v10',to_version='MARU-EP02-v11',project_id='MARU-EP02',items=items)
json.dump(d,open('fixreport_v11.json','w'),ensure_ascii=False,indent=1)
print(len(items),sum(i['action']=='fixed' for i in items))
