import json
p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_evolution\phase3_evolution\_phase3_ranking.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)
ranking = d.get('ranking', [])
print(f'共 {len(ranking)} 人')
print()
# 按 importance 分组
from collections import Counter
groups = Counter()
for r in ranking:
    imp = r.get('importance', 0)
    groups[imp] += 1
print('重要性分布:')
for imp in sorted(groups.keys(), reverse=True):
    print(f'  importance={imp}: {groups[imp]} 人')
print()
print('=== 完整排名（含理由） ===')
for r in ranking:
    imp = r['importance']
    name = r['name']
    reason = str(r.get('reason', ''))[:120]
    print(f'{r["rank"]:2d}. {name:25s} imp={imp}  {reason}')