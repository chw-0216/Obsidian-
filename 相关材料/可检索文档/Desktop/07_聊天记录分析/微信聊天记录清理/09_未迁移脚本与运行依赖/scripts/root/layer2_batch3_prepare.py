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

# 加载待分析列表
with open('layer2_remaining.json', 'r', encoding='utf-8') as f:
    remaining = json.load(f)

# 取前20人
contacts_to_analyze = remaining[:20]

print('=== 批量分析剩余联系人 ===')
print(f'待分析: {len(contacts_to_analyze)}人')
print()

# 获取这些联系人的信息
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

analysis_tasks = []
for contact in contacts_to_analyze:
    name = contact['name']
    total = contact['total']
    
    # 获取联系人统计
    c.execute('''
        SELECT conversation_id, total_messages, sent_count, received_count, active_months
        FROM contact_summary 
        WHERE display_name = ?
    ''', (name,))
    
    result = c.fetchone()
    if result:
        conv_id, total_msgs, sent, received, months = result
        
        # 获取片段
        c.execute('''
            SELECT id, transcript, start_ts, end_ts, message_count
            FROM segments
            WHERE conversation_id = ?
            ORDER BY start_ts
        ''', (conv_id,))
        
        segments = c.fetchall()
        
        # 抽样（最多20个，节省token）
        sample_size = min(len(segments), 20)
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
                if len(content) > 400:
                    content = content[:400] + '...'
                start_time = datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M') if start else '未知'
                texts.append(f'[{start_time}] ({msg_count}条): {content}')
        
        formatted = '\n'.join(texts)
        
        analysis_tasks.append({
            'name': name,
            'total_msgs': total_msgs,
            'segments': len(segments),
            'sample_size': sample_size,
            'prompt': f'''分析微信聊天片段，返回JSON:

聊天对象: {name}
消息数: {total_msgs}
片段:
{formatted}

返回格式:
{{"name":"{name}","relationship":"关系类型","topics":["话题1","话题2"],"style":"沟通风格","tone":"情感基调","events":["事件"],"conflicts":["冲突"],"my_role":"我的角色","their_role":"对方角色","closeness":1-10,"mbti":"推测MBTI"}}'''
        })

conn.close()

print(f'已准备 {len(analysis_tasks)} 个任务')

# 保存任务
with open('layer2_batch3_tasks.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_tasks, f, ensure_ascii=False, indent=2)

print('任务已保存到 layer2_batch3_tasks.json')
