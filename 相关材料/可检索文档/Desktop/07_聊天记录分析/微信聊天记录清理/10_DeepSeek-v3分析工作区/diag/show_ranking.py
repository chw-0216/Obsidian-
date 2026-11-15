import json
p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_evolution\phase3_evolution\_phase3_ranking.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)
ranking = d.get('ranking', [])
print(f'共 {len(ranking)} 人')
print()
for r in ranking[:30]:
    print(f'{r["rank"]:2d}. {r["name"]:20s} importance={r["importance"]}')
    if r.get("reason"):
        print(f'    理由: {r["reason"][:100]}')