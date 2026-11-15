import sqlite3
import json

conn = sqlite3.connect('data/wechat-private-v2.sqlite3')
c = conn.cursor()

# 加载筛选结果
with open('layer1_selected.json', 'r', encoding='utf-8') as f:
    selected = json.load(f)

print('=== Layer 2: 轻量分析准备 ===')
print(f'待分析: {len(selected)}人')
print()

# 获取每个联系人的对话片段
print('=== 各联系人片段统计 ===')
print(f'{"排名":<4} {"昵称":<15} {"消息":<6} {"片段数":<8} {"抽样数":<8} {"预估Token":<10}')
print('-' * 60)

analysis_plan = []
for i, contact in enumerate(selected[:30], 1):
    name = contact['name']
    total = contact['total']
    
    # 获取对话ID
    c.execute('''
        SELECT conversation_id 
        FROM contact_summary 
        WHERE display_name = ?
    ''', (name,))
    result = c.fetchone()
    
    if result:
        conv_id = result[0]
        
        # 获取片段数量
        c.execute('''
            SELECT COUNT(*) 
            FROM segments 
            WHERE conversation_id = ?
        ''', (conv_id,))
        segment_count = c.fetchone()[0]
        
        # 根据消息量确定抽样数
        if total < 500:
            sample_size = min(segment_count, 20)
        elif total < 1000:
            sample_size = min(segment_count, 30)
        else:
            sample_size = min(segment_count, 40)
        
        # 估算token（每个片段约150tokens输入，200tokens输出）
        est_tokens = sample_size * 350
        
        print(f'{i:<4} {name:<15} {total:<6} {segment_count:<8} {sample_size:<8} {est_tokens:<10}')
        
        analysis_plan.append({
            'name': name,
            'conv_id': conv_id,
            'total_msgs': total,
            'segment_count': segment_count,
            'sample_size': sample_size,
            'est_tokens': est_tokens
        })

# 保存分析计划
with open('layer2_plan.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_plan, f, ensure_ascii=False, indent=2)

# 统计
total_segments = sum(p['segment_count'] for p in analysis_plan)
total_sample = sum(p['sample_size'] for p in analysis_plan)
total_tokens = sum(p['est_tokens'] for p in analysis_plan)

print(f'\n=== 总计 ===')
print(f'总片段数: {total_segments:,}')
print(f'抽样片段: {total_sample:,}')
print(f'预估Token: {total_tokens:,} ({total_tokens/10000:.1f}万)')
print(f'\n已保存到 layer2_plan.json')
