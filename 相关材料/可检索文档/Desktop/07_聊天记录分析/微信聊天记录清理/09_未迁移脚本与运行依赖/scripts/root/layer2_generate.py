import sqlite3
import json
import os
from datetime import datetime

# 配置
DB_PATH = 'data/wechat-private-v2.sqlite3'
PLAN_PATH = 'layer2_plan.json'
OUTPUT_DIR = 'layer2_results'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 加载分析计划
with open(PLAN_PATH, 'r', encoding='utf-8') as f:
    plan = json.load(f)

print('=== Layer 2: 轻量分析脚本 ===')
print(f'待分析: {len(plan)}人')
print(f'输出目录: {OUTPUT_DIR}')
print()

# 轻量分析prompt模板
LIGHTWEIGHT_PROMPT = '''分析以下微信聊天片段，提取关键信息。

聊天片段:
{segments}

请返回JSON格式:
{{
  "contact_name": "联系人昵称",
  "relationship_type": "朋友/家人/同事/暧昧/前任/导师/室友/...",
  "key_topics": ["话题1", "话题2", "话题3"],
  "communication_style": "一句话描述沟通风格",
  "emotional_tone": "积极/中性/消极/复杂",
  "important_events": ["事件1", "事件2"],
  "promises_commitments": ["承诺1"],
  "conflicts": ["冲突1"],
  "my_role": "我在关系中的角色",
  "their_role": "对方在关系中的角色",
  "closeness_score": 1-10,
  "analysis_confidence": 0.0-1.0
}}'''

def get_sampled_segments(conv_id, sample_size):
    """获取抽样的对话片段"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取片段，按时间排序，均匀抽样
    c.execute('''
        SELECT segment_id, content, start_time, end_time, message_count
        FROM segments
        WHERE conversation_id = ?
        ORDER BY start_time
    ''', (conv_id,))
    
    all_segments = c.fetchall()
    conn.close()
    
    if len(all_segments) <= sample_size:
        return all_segments
    
    # 均匀抽样
    step = len(all_segments) / sample_size
    sampled = []
    for i in range(sample_size):
        idx = int(i * step)
        sampled.append(all_segments[idx])
    
    return sampled

def format_segments(segments):
    """格式化片段为文本"""
    texts = []
    for seg in segments:
        seg_id, content, start, end, msg_count = seg
        if content:
            # 截断过长的内容
            if len(content) > 500:
                content = content[:500] + '...'
            texts.append(f'[{start}] ({msg_count}条): {content}')
    return '\n'.join(texts)

# 生成分析任务
print('=== 生成分析任务 ===')
tasks = []
for i, contact in enumerate(plan[:5], 1):  # 先处理前5人作为示例
    name = contact['name']
    conv_id = contact['conv_id']
    sample_size = contact['sample_size']
    
    # 获取抽样片段
    segments = get_sampled_segments(conv_id, sample_size)
    formatted = format_segments(segments)
    
    # 生成prompt
    prompt = LIGHTWEIGHT_PROMPT.format(segments=formatted)
    
    tasks.append({
        'index': i,
        'name': name,
        'conv_id': conv_id,
        'prompt': prompt,
        'segment_count': len(segments)
    })
    
    print(f'{i}. {name}: {len(segments)}个片段')

# 保存任务
with open(os.path.join(OUTPUT_DIR, 'tasks.json'), 'w', encoding='utf-8') as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)

print(f'\n已生成{len(tasks)}个分析任务')
print(f'任务保存到: {OUTPUT_DIR}/tasks.json')
print()
print('=== 下一步 ===')
print('需要调用MiMo API执行分析，是否继续？')
