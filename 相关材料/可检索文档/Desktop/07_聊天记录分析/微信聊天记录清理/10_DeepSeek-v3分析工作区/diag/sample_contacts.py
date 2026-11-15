import json
from collections import defaultdict

# 读取深度分析
p = r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\runs\deep_contact_analysis\deep_contact_analysis.json'
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)

ranking = d.get('ranking', [])

# 挑选关键样本，展示其分析摘要
samples = [
    '陈昶文', '导！急速回，三思回得体！！！', '甘泉', '沐茜妍',
    '薛伟东', '小苹果', '🍬🍬', 'Eloise', '李紫懿',
    '李佳杨', '077', '方列丰', '杨丁懿', 'Lyj', 'Parapluie',
    '文件传输助手', '蔡峰峰', '蔡黎明', '蔡晓梅', '奶奶',
    '舒泽林', '郑英泽', '笑一', '汪伊俊', '张雅婷'
]

for r in ranking:
    name = r['contact_name']
    if name not in samples:
        continue
    try:
        a = r['analysis']['analysis']
        imp = a['importance']
        role = a['role']
        intimacy = a['intimacy']
        evo = a.get('evolution_detail', '')[:150]
        summary = a.get('summary', '')[:200]
        emotions = a.get('emotional_tone', {})
        trust = emotions.get('trust_level', '?')
        tone = emotions.get('overall', '?')
        self_evo = a.get('self_evolution', '')[:200]
        
        print(f'{"="*60}')
        print(f'{name} | 模型imp={imp} | 角色={role} | 亲密度={intimacy} | 信任={trust} | 基调={tone}')
        print(f'  演化: {evo}')
        print(f'  自我成长: {self_evo}')
        print(f'  总结: {summary}')
        print()
    except:
        pass