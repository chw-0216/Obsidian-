# -*- coding: utf-8 -*-
import json,re,sys,io
sys.stdout.reconfigure(encoding='utf-8')

t=open('2022_guokao_fusheng_haedu.txt',encoding='utf-8').read()
t=re.sub(r'===== PAGE \d+ =====','',t)
parts=re.split(r'^(\d{1,3})\.\s*$',t,flags=re.M)
hd={}
for i in range(1,len(parts)-1,2):
    try: hd[int(parts[i])]=parts[i+1]
    except: pass

def norm(s):
    s=re.sub(r'\s+','',s)
    s=s.replace('?','？').replace('．','.').replace('、','.').replace('（','(').replace('）',')')
    s=re.sub(r'老师微信.*$','',s)
    return s

def opts(text):
    text=re.split(r'【答案】',text)[0]
    m=list(re.finditer(r'([ABCD])[\.．、]\s*(.*?)(?=[ABCD][\.．、]|\Z)',text,flags=re.S))
    return {x.group(1):norm(x.group(2)) for x in m}

def ans(text):
    m=re.search(r'【答案】\s*([ABCD])',text)
    return m.group(1) if m else None

for name,f in [('常识','_ht2022_changshi_q.json'),('言语','_ht2022_yanyu_q.json')]:
    ht={int(k):v for k,v in json.load(open(f,encoding='utf-8')).items()}
    print('='*20,name)
    for q in sorted(ht):
        if q not in hd: print(q,'HD-MISS'); continue
        ho=opts(hd[q]); ha=ans(hd[q]); to=opts(ht[q]); ta=ans(ht[q])
        if not ho or not to: print(q,'OPT-EMPTY'); continue
        ok=all(ho.get(k)==to.get(k) for k in 'ABCD' if ho.get(k))
        same = ha==ta
        print(f'Q{q}: HD={ha} HT={ta} {"顺序一致" if ok else "★顺序不一致"} {"答案一致" if same else "★答案不一致"}')
