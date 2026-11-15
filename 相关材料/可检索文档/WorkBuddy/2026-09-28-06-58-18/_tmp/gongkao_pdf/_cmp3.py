# -*- coding: utf-8 -*-
import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
t=open('2022_guokao_fusheng_haedu.txt',encoding='utf-8').read()
t=re.sub(r'===== PAGE \d+ =====','',t)
t=re.sub(r'老师微信：xuxiaoru009 鲤见教育[^\n]*\n','',t)
t=re.sub(r'补充资料每日更新[^\n]*\n','',t)
t=re.sub(r'^\s*\d{1,3}\s*\n','',t,flags=re.M)
parts=re.split(r'^(\d{1,3})\.\s*$',t,flags=re.M)
hd={}
for i in range(1,len(parts)-1,2):
    hd[int(parts[i])]=parts[i+1]
print('HD 题数',len(hd),'max',max(hd))

def norm(s):
    s=re.sub(r'\s+','',s); s=s.replace('．','.').replace('、','.').replace('？','?').replace('（','(').replace('）',')')
    return s

def hd_parse(q):
    b=hd[q]
    stem=b.split('选项：')[0]
    head=b.split('正确答案')[0]
    o={}
    m=list(re.finditer(r'([ABCD])[\.、]\s*(.*?)(?=[ABCD][\.\n、]|\Z)',head,flags=re.S))
    for x in m: o[x.group(1)]=norm(x.group(2))
    a=re.search(r'正确答案[:：]\s*([ABCD])',b)
    return stem,o,(a.group(1) if a else None)

def ht_parse(txt):
    stem=re.split(r'【答案】',txt)[0]
    o={}
    m=list(re.finditer(r'([ABCD])[\.．、]\s*(.*?)(?=[ABCD][\.．、]|\Z)',stem,flags=re.S))
    for x in m: o[x.group(1)]=norm(x.group(2))
    a=re.search(r'【答案】\s*([ABCD])',txt)
    return stem,o,(a.group(1) if a else None)

for name,f in [('常识','_ht2022_changshi_q.json'),('言语','_ht2022_yanyu_q.json')]:
    ht={int(k):v for k,v in json.load(open(f,encoding='utf-8')).items()}
    print('='*24,name)
    for q in sorted(ht):
        if q not in hd: print(q,'HD-MISS'); continue
        hs,ho,ha=hd_parse(q); ts,to,ta=ht_parse(ht[q])
        if len(ho)<4 or len(to)<4: print(f'Q{q}: OPT-COUNT hd={len(ho)} ht={len(to)}'); continue
        ok=all(ho.get(k)==to.get(k) for k in 'ABCD')
        print(f'Q{q}: HD={ha} HT={ta} {"✔顺序一致" if ok else "★顺序不一致"} {"✔答案一致" if ha==ta else "★答案不一致"}')
