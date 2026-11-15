import json
raw = json.load(open(r'C:\Users\wardc\Desktop\_dsh_cleanup_work\session-list-raw.json', encoding='utf-8'))
items = raw.get('body', raw).get('json', raw).get('result', {}).get('value', {}).get('items', [])
print('items in saved list:', len(items))
ids = [it.get('sessionId','') for it in items]
for target in ['3ec7e7f1','c8634800']:
    hit = [i for i in ids if target in i]
    print(target, 'in list:', hit[:3])
