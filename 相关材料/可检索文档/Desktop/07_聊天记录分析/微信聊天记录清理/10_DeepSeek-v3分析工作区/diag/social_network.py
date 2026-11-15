import json
from collections import defaultdict

# 读取深度分析结果
p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_contact_analysis\deep_contact_analysis.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)

ranking = d.get('ranking', [])

# 按角色分类
role_map = defaultdict(list)
for r in ranking:
    try:
        role = r['analysis']['analysis']['role']
        imp = r['analysis']['analysis']['importance']
        name = r['contact_name']
        msgs = r['message_count']
        role_map[role].append((name, imp, msgs))
    except:
        pass

# 输出角色分类
print("=== 社会关系网络 ===")
print()
for role in sorted(role_map.keys()):
    members = sorted(role_map[role], key=lambda x: -x[1])
    print(f"【{role}】({len(members)}人)")
    for name, imp, msgs in members[:5]:
        print(f"  {name:20s} imp={imp}  msgs={msgs}")
    if len(members) > 5:
        print(f"  ... 还有 {len(members)-5} 人")
    print()

# 按重要性分组
print("=== 重要性分层 ===")
imp_groups = defaultdict(list)
for r in ranking:
    try:
        imp = r['analysis']['analysis']['importance']
        name = r['contact_name']
        msgs = r['message_count']
        role = r['analysis']['analysis']['role']
        imp_groups[imp].append((name, msgs, role))
    except:
        pass

for imp in sorted(imp_groups.keys(), reverse=True):
    members = imp_groups[imp]
    print(f"\n重要性 {imp} ({len(members)}人):")
    for name, msgs, role in sorted(members, key=lambda x: -x[1])[:10]:
        print(f"  {name:25s} {msgs:5d}条  {role}")
    if len(members) > 10:
        print(f"  ... 还有 {len(members)-10} 人")