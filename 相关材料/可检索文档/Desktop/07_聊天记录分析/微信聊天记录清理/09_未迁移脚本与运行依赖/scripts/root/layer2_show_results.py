import json

# 加载结果
with open('layer2_results/analysis_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print('=== Layer 2: 分析结果 ===')
print()

for result in results:
    name = result['name']
    status = result['status']
    
    if status == 'success':
        content = result['content']
        
        # 尝试解析JSON
        try:
            # 提取JSON部分
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                print(f'【{name}】')
                print(f'  关系类型: {data.get(\"relationship_type\", \"未知\")}')
                print(f'  沟通风格: {data.get(\"communication_style\", \"未知\")}')
                print(f'  情感基调: {data.get(\"emotional_tone\", \"未知\")}')
                print(f'  亲密度: {data.get(\"closeness_score\", \"未知\")}/10')
                
                topics = data.get('key_topics', [])
                if topics:
                    print(f'  主要话题: {", ".join(topics[:3])}')
                
                events = data.get('important_events', [])
                if events:
                    print(f'  关键事件: {events[0]}')
                
                conflicts = data.get('conflicts', [])
                if conflicts:
                    print(f'  冲突: {conflicts[0]}')
                
                print(f'  我的角色: {data.get(\"my_role\", \"未知\")}')
                print(f'  对方角色: {data.get(\"their_role\", \"未知\")}')
                print(f'  分析置信度: {data.get(\"analysis_confidence\", \"未知\")}')
                print()
            else:
                print(f'【{name}】: JSON解析失败')
                print(content[:200])
                print()
        except json.JSONDecodeError as e:
            print(f'【{name}】: JSON解析错误 - {e}')
            print(content[:200])
            print()
    else:
        print(f'【{name}】: 分析失败 - {result.get(\"error\", \"未知错误\")}')
        print()

# 统计
print('=== Token使用统计 ===')
total_input = sum(r.get('input_tokens', 0) for r in results)
total_output = sum(r.get('output_tokens', 0) for r in results)
print(f'输入Token: {total_input:,}')
print(f'输出Token: {total_output:,}')
print(f'总计: {total_input + total_output:,}')
