# -*- coding: utf-8 -*-
import re,sys,json
sys.stdout.reconfigure(encoding='utf-8')
hd={int(k):v for k,v in json.load(open('_hd2022_all.json',encoding='utf-8')).items()}
for q in [1,3,6,7,10,13,14,17,19,20]:
    b=hd[q]
    stem=b.split('选项：')[0].strip()
    head=b.split('正确答案')[0]
    o=[]
    for x in re.finditer(r'([ABCD])[\.、]\s*(.*?)(?=[ABCD][\.\n、]|\Z)',head,flags=re.S):
        o.append(f'{x.group(1)}. {re.sub(chr(10)," ",x.group(2)).strip()}')
    a=re.search(r'正确答案[:：]\s*([ABCD])',b)
    jie=b.split('解析：')[1].strip() if '解析：' in b else ''
    print(f'###常识 Q{q}  答案={a.group(1) if a else "?"}')
    print(stem)
    for l in o: print('   ',l[:110])
    print('   [解析]',jie[:300].replace('\n',' '))
    print()
