import sqlite3
import json
import os
import urllib.request
import time
from datetime import datetime

# 配置
DB_PATH = 'data/wechat-private-v2.sqlite3'
API_BASE = 'https://token-plan-cn.xiaomimimo.com/anthropic'
API_KEY = os.environ.get('MIMO_API_KEY', '')
MODEL = 'mimo-v2.5'

# 重要联系人列表（用户指定）
important_contacts = [
    {'name': '蔡峰峰', 'reason': '父亲'},
    {'name': '舒泽林', 'reason': '欠钱'},
    {'name': '郑英泽', 'reason': '欠钱'}
]

print('=== 重新分析重要联系人 ===')
print()

# 获取这些联系人的信息
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

analysis_tasks = []
for contact in important_contacts:
    name = contact['name']
    reason = contact['reason']
    
    # 获取联系人统计
    c.execute('''
        SELECT conversation_id, total_messages, sent_count, received_count, active_months
        FROM contact_summary 
        WHERE display_name = ?
    ''', (name,))
    
    result = c.fetchone()
    if result:
        conv_id, total, sent, received, months = result
        
        # 获取片段
        c.execute('''
            SELECT id, transcript, start_ts, end_ts, message_count
            FROM segments
            WHERE conversation_id = ?
            ORDER BY start_ts
        ''', (conv_id,))
        
        segments = c.fetchall()
        
        # 抽样（最多30个）
        sample_size = min(len(segments), 30)
        if len(segments) > sample_size:
            step = len(segments) / sample_size
            sampled = [segments[int(i * step)] for i in range(sample_size)]
        else:
            sampled = segments
        
        # 格式化
        texts = []
        for seg in sampled:
            seg_id, content, start, end, msg_count = seg
            if content:
                if len(content) > 500:
                    content = content[:500] + '...'
                start_time = datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M') if start else '未知'
                texts.append(f'[{start_time}] ({msg_count}条): {content}')
        
        formatted = '\n'.join(texts)
        
        analysis_tasks.append({
            'name': name,
            'reason': reason,
            'conv_id': conv_id,
            'total_msgs': total,
            'segments': len(segments),
            'sample_size': sample_size,
            'prompt': f'''分析以下微信聊天片段，提取关键信息。

聊天对象: {name}（{reason}）
聊天片段:
{formatted}

请返回JSON格式:
{{
  "contact_name": "{name}",
  "relationship_type": "父亲/欠钱/...",
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
        })
        
        print(f'{name}（{reason}）: {total}条消息, {len(segments)}个片段, 抽样{sample_size}个')
    else:
        print(f'{name}: 未找到')

conn.close()

print()
print(f'准备分析 {len(analysis_tasks)} 人')

# 保存任务
with open('layer2_important_tasks.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_tasks, f, ensure_ascii=False, indent=2)

print('任务已保存到 layer2_important_tasks.json')
