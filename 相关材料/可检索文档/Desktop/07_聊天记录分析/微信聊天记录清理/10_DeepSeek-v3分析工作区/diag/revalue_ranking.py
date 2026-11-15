"""
基于综合价值（情感价值 + 成长价值 + 资源价值）重新给 472 人打分排名。
每个维度 1-10 分，最终综合价值 = 情感*0.4 + 成长*0.3 + 资源*0.3
"""
import json
import math

p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_contact_analysis\deep_contact_analysis.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)

ranking = d.get('ranking', [])

# 角色→三维度评分映射
# 情感: 亲密感、信任、情感支持、情绪价值
# 成长: 自我认知提升、技能/视野拓展、人格塑造
# 资源: 人脉、机会、金钱、信息、实用价值

def score_contact(r):
    """根据角色和关系特征，从情感/成长/资源三维度打分"""
    try:
        a = r['analysis']['analysis']
    except:
        return 0, 0, 0, r['contact_name']
    
    role = a.get('role', '')
    intimacy = a.get('intimacy', 5)
    trust = a.get('emotional_tone', {}).get('trust_level', 5)
    msgs = r['message_count']
    name = r['contact_name']
    
    # 基础分
    emotional = 0
    growth = 0
    resource = 0
    
    # === 情感维度 ===
    if '恋人' in role:
        emotional = min(10, intimacy + 2)
    elif '暧昧' in role or '潜在恋人' in role or '潜在发展' in role:
        emotional = min(10, intimacy + 1)
    elif '家人' in role or '父子' in role or '大姑' in role or '小姑' in role or '奶奶' in role:
        emotional = 8 if intimacy >= 7 else 6
    elif '挚友' in role or '兄弟' in role or '知己' in role:
        emotional = min(10, intimacy + 1)
    elif '朋友' in role and '暧昧' not in role:
        emotional = intimacy
    elif '同学' in role and ('哥们' in role or '研友' in role):
        emotional = intimacy
    elif '导师' in role or '老师' in role:
        emotional = max(3, intimacy - 2)
    elif '客户' in role or '销售' in role or '服务' in role:
        emotional = 1
    else:
        emotional = max(1, intimacy - 2)
    
    # 信任度修正
    emotional = (emotional + trust) / 2
    
    # === 成长维度 ===
    if '导师' in role or '老师' in role:
        growth = 9 if intimacy >= 6 else 7
    elif '上级' in role or '学长' in role or '学姐' in role:
        growth = min(9, intimacy + 1)
    elif '家人' in role and ('父' in role or '母' in role):
        growth = 8
    elif '恋人' in role:
        growth = 8
    elif '暧昧' in role or '潜在恋人' in role:
        growth = 7
    elif '挚友' in role or '兄弟' in role:
        growth = 7
    elif '同学' in role and ('项目' in role or '合作' in role):
        growth = 7
    elif '朋友' in role and ('导师' in role):
        growth = 8
    elif '工具性自我' in role:
        growth = 9  # 自我知识体系构建
    elif '客户' in role or '销售' in role:
        growth = 2
    else:
        growth = 4
    
    # 消息量修正——深层互动更多意味着更多成长
    if msgs >= 3000: growth = min(10, growth + 1)
    elif msgs >= 1000: growth = min(10, growth + 0.5)
    
    # === 资源维度 ===
    if '导师' in role and ('导！' in name or '方列丰' in name):
        resource = 9
    elif '导师' in role or '老师' in role:
        resource = 8
    elif '客户' in role or '商业' in role or '合作' in role:
        resource = 7
    elif '校友' in role and ('活动' in role or '内推' in role or '职业' in role):
        resource = 6
    elif '上级' in role or '同事' in role:
        resource = 7
    elif '朋友' in role and ('导师' in role or '潜在客户' in role):
        resource = 7
    elif '家人' in role:
        resource = 3
    elif '暧昧' in role or '恋人' in role:
        resource = 3
    elif '工具性自我' in role:
        resource = 10
    elif '服务' in role or '销售' in role:
        resource = 4
    else:
        resource = 3
    
    # 综合
    composite = emotional * 0.4 + growth * 0.3 + resource * 0.3
    composite = round(composite, 1)
    
    return composite, emotional, growth, resource, name

# 评分
results = []
for r in ranking:
    comp, emo, gro, res, name = score_contact(r)
    results.append({
        'name': name,
        'composite': comp,
        'emotional': emo,
        'growth': gro,
        'resource': res,
        'msgs': r['message_count'],
        'role': r.get('analysis', {}).get('analysis', {}).get('role', '?'),
        'intimacy': r.get('analysis', {}).get('analysis', {}).get('intimacy', '?'),
    })

# 排序
results.sort(key=lambda x: -x['composite'])

# 输出
print("=" * 80)
print("社会关系网络 — 综合价值排名（情感*0.4 + 成长*0.3 + 资源*0.3）")
print("=" * 80)
print()

# 分层
from collections import Counter
tiers = Counter()
for r in results:
    c = r['composite']
    if c >= 8: tiers['T1 核心圈 (8-10)'] += 1
    elif c >= 6: tiers['T2 重要圈 (6-8)'] += 1
    elif c >= 4: tiers['T3 中间圈 (4-6)'] += 1
    elif c >= 2: tiers['T4 外围圈 (2-4)'] += 1
    else: tiers['T5 边缘圈 (0-2)'] += 1

print("圈层分布:")
for t in ['T1 核心圈 (8-10)', 'T2 重要圈 (6-8)', 'T3 中间圈 (4-6)', 'T4 外围圈 (2-4)', 'T5 边缘圈 (0-2)']:
    print(f"  {t}: {tiers[t]} 人")
print()

# 输出排名
tier = 0
for i, r in enumerate(results):
    if i == 0 or results[i-1]['composite'] >= 8 and r['composite'] < 8:
        tier += 1
        print(f"\n{'='*60}")
        print(f"  {'T1 核心圈' if tier==1 else 'T2 重要圈' if tier==2 else 'T3 中间圈' if tier==3 else 'T4 外围圈' if tier==4 else 'T5 边缘圈'}")
        print(f"{'='*60}")
    
    if tier <= 3:  # 只打印前3圈
        print(f"{i+1:3d}. {r['name']:25s} 综合={r['composite']:4.1f}  情感={r['emotional']:3.1f}  成长={r['growth']:3.1f}  资源={r['resource']:3.1f}  {r['msgs']:5d}条  {r['role']}")

# 保存到文件
with open('social_network_ranking.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\n已保存 {len(results)} 人排名到 social_network_ranking.json")