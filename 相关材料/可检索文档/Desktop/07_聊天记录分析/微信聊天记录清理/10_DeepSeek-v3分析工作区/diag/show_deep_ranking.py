import json
from collections import Counter

p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_contact_analysis\deep_contact_analysis.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f'总联系人: {d["total_contacts"]}')
print(f'成功: {d["successful"]}')
print(f'失败: {d["failed"]}')
print()

ranking = d.get('ranking', [])
# Extract importance from nested analysis
for r in ranking:
    try:
        r['_importance'] = r['analysis']['analysis']['importance']
        r['_intimacy'] = r['analysis']['analysis']['intimacy']
        r['_role'] = r['analysis']['analysis']['role']
        r['_summary'] = r['analysis']['analysis'].get('summary', '')
    except (KeyError, TypeError):
        r['_importance'] = 0
        r['_intimacy'] = 0
        r['_role'] = '?'
        r['_summary'] = ''

groups = Counter()
for r in ranking:
    groups[r['_importance']] += 1

print('重要性分布:')
for imp in sorted(groups.keys(), reverse=True):
    print(f'  imp={imp}: {groups[imp]} 人')
print()

# Sort by importance desc, then message count desc
ranking.sort(key=lambda x: (-x['_importance'], -x['message_count']))
for i, r in enumerate(ranking[:50]):
    name = r['contact_name']
    imp = r['_importance']
    intimacy = r['_intimacy']
    role = r['_role']
    msgs = r['message_count']
    summary = r['_summary'][:100]
    print(f'{i+1:3d}. {name:25s} imp={imp} 亲密={intimacy}  msgs={msgs:5d}  角色={role}')
    if summary:
        print(f'     {summary}')
    print()