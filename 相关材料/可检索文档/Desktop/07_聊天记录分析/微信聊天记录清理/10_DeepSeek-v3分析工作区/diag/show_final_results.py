import sqlite3, json

c = sqlite3.connect(r'07_聊天记录分析\微信聊天记录清理\10_DeepSeek-v3分析工作区\data\scale\wechat-analysis-scale.sqlite3')
c.row_factory = sqlite3.Row

total = c.execute('SELECT COUNT(*) FROM v3_annotations').fetchone()[0]
success = c.execute('SELECT COUNT(*) FROM v3_annotations WHERE status=?', ('success',)).fetchone()[0]
failed = c.execute('SELECT COUNT(*) FROM v3_annotations WHERE status!=?', ('success',)).fetchone()[0]
print(f'标注总量: {total}')
print(f'成功: {success} ({round(success/total*100,1)}%)')
print(f'失败: {failed} ({round(failed/total*100,1)}%)')

tok = c.execute('SELECT SUM(input_tokens) as i, SUM(output_tokens) as o FROM v3_annotations WHERE status=?', ('success',)).fetchone()
print(f'输入token: {tok["i"]:,.0f}')
print(f'输出token: {tok["o"]:,.0f}')
print(f'总token: {tok["i"]+tok["o"]:,.0f}')

print()
print('=== 标注内容统计 ===')
ents = c.execute('SELECT SUM(entity_count) as e FROM v3_annotations WHERE status=?', ('success',)).fetchone()['e']
evts = c.execute('SELECT SUM(event_count) as e FROM v3_annotations WHERE status=?', ('success',)).fetchone()['e']
sigs = c.execute('SELECT SUM(relationship_signal_count) as s FROM v3_annotations WHERE status=?', ('success',)).fetchone()['s']
print(f'实体数: {ents:,}')
print(f'事件数: {evts:,}')
print(f'关系信号: {sigs:,}')

print()
print('=== 联系人覆盖 ===')
contacts = c.execute('''
    SELECT COUNT(DISTINCT c.display_name) as cnt
    FROM v3_annotations a
    JOIN segments s ON a.segment_id = s.id
    JOIN conversations c ON s.conversation_id = c.id
    WHERE a.status = 'success'
''').fetchone()['cnt']
print(f'已覆盖联系人数: {contacts}')

print()
print('=== Top 10 联系人标注量 ===')
rows = c.execute('''
    SELECT c.display_name, COUNT(*) as cnt, c.loaded_message_count as msgs
    FROM v3_annotations a
    JOIN segments s ON a.segment_id = s.id
    JOIN conversations c ON s.conversation_id = c.id
    WHERE a.status = 'success'
    GROUP BY c.id
    ORDER BY cnt DESC LIMIT 10
''').fetchall()
for r in rows:
    print(f'  {r["display_name"]:20s} {r["cnt"]:4d} 标注  {r["msgs"]:5d} 消息')

print()
print('=== 标注样本(1条) ===')
sample = c.execute('SELECT result_json FROM v3_annotations WHERE status=? LIMIT 1', ('success',)).fetchone()
obj = json.loads(sample['result_json']) if isinstance(sample['result_json'], str) else sample['result_json']
if isinstance(obj, dict):
    keys = list(obj.keys())
    print(f'字段: {keys}')
    for k in ['summary', 'topic', 'sentiment', 'content_function']:
        if k in obj:
            print(f'  {k}: {str(obj[k])[:120]}')
    if 'messages' in obj and isinstance(obj['messages'], list) and len(obj['messages']) > 0:
        m = obj['messages'][0]
        if isinstance(m, dict):
            for k in ['evidence_id', 'content_function', 'intent', 'emotion']:
                if k in m:
                    print(f'  message.{k}: {str(m[k])[:100]}')
elif isinstance(obj, list) and len(obj) > 0:
    first = obj[0]
    if isinstance(first, dict):
        print(f'字段: {list(first.keys())}')
        for k in ['summary', 'topic', 'sentiment']:
            if k in first:
                print(f'  {k}: {str(first[k])[:120]}')
