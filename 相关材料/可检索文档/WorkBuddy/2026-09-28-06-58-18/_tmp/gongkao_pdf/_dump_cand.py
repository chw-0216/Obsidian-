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
for i in range(1,len(parts)-1,2): hd[int(parts[i])]=parts[i+1]
json.dump({str(k):v for k,v in hd.items()},open('_hd2022_all.json','w',encoding='utf-8'),ensure_ascii=False)
for q in [22,27,33,34,36,37,39,40,43,44,51,52,53,54,55]:
    b=hd[q]
    stem=b.split('选项：')[0].strip()
    head=b.split('正确答案')[0]
    o=[]
    ms=list(re.finditer(r'([ABCD])[\.、]\s*(.*?)(?=[ABCD][\.\n、]|\Z)',head,flags=re.S))
    for x in ms: o.append(f'{x.group(1)}. {re.sub(chr(10)," ",x.group(2)).strip()}')
    a=re.search(r'正确答案[:：]\s*([ABCD])',b)
    print(f'###言语 Q{q}  答案={a.group(1) if a else "?"}')
    print(stem)
    for l in o: print('   ',l[:110])
    print()
