import json, os, sys

p2dir = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_evolution\phase2_patterns'
files = [f for f in os.listdir(p2dir) if f.endswith('.json') and not f.startswith('_')]
print(f'Phase 2 文件数: {len(files)}')
print()
print('=== 联系人话题+情感摘要 (Top 15) ===')
results = []
for fname in sorted(files):
    with open(os.path.join(p2dir, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    name = d.get('contact_name', fname)
    msgs = d.get('message_count', 0)
    p = d.get('patterns', {}).get('patterns', d.get('patterns', {}))
    rhythm = p.get('rhythm', {})
    ec = p.get('emotion_curve', {})
    topics = [t.get('topic', '?') for t in p.get('topics', [])[:3]]
    sp = p.get('self_projection', {})
    roles = sp.get('roles', [])
    growth = str(sp.get('growth', ''))[:80]
    results.append({
        'name': name, 'msgs': msgs,
        'freq': rhythm.get('frequency', '?'),
        'init': rhythm.get('initiator', '?'),
        'trend': ec.get('trend', '?'),
        'topics': topics, 'roles': roles, 'growth': growth,
    })

# Sort by message count
results.sort(key=lambda x: x['msgs'], reverse=True)
for i, r in enumerate(results[:15]):
    print(f'{i+1:2d}. {r["name"]:20s} {r["msgs"]:5d}条  互动:{r["freq"]} 情感:{r["trend"]}  角色:{r["roles"]}')
    print(f'    话题: {r["topics"]}')
    if r["growth"]:
        print(f'    成长: {r["growth"]}')
    print()
