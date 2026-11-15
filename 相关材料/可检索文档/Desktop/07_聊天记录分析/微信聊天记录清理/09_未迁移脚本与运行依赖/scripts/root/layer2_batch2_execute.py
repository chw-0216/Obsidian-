import json
import os
import urllib.request
import time

# 配置
API_BASE = 'https://token-plan-cn.xiaomimimo.com/anthropic'
API_KEY = os.environ.get('MIMO_API_KEY', '')
MODEL = 'mimo-v2.5'

# 加载任务
with open('layer2_batch2_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

print('=== 分析第二批重要联系人 ===')
print(f'待分析: {len(tasks)}人')
print()

def call_mimo_api(prompt, max_tokens=4096):
    """调用MiMo API"""
    url = f'{API_BASE}/v1/messages'
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
        'anthropic-version': '2023-06-01'
    }
    
    data = {
        'model': MODEL,
        'max_tokens': max_tokens,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except Exception as e:
        return {'error': str(e)}

# 执行分析
results = []
for task in tasks:
    name = task['name']
    reason = task['reason']
    print(f'分析 {name}（{reason}）...', end=' ')
    
    start_time = time.time()
    response = call_mimo_api(task['prompt'])
    elapsed = time.time() - start_time
    
    if 'error' in response:
        print(f'失败: {response["error"]}')
        results.append({
            'name': name,
            'reason': reason,
            'status': 'failed',
            'error': response['error']
        })
    else:
        content = response.get('content', [{}])[0].get('text', '')
        input_tokens = response.get('usage', {}).get('input_tokens', 0)
        output_tokens = response.get('usage', {}).get('output_tokens', 0)
        
        print(f'成功 ({elapsed:.1f}s, {input_tokens}+{output_tokens} tokens)')
        
        results.append({
            'name': name,
            'reason': reason,
            'status': 'success',
            'content': content,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'elapsed': elapsed
        })
    
    time.sleep(1)

# 保存结果
output_path = 'layer2_results/batch2_results.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n=== 完成 ===')
print(f'结果保存到: {output_path}')

# 统计
success_count = sum(1 for r in results if r['status'] == 'success')
total_input = sum(r.get('input_tokens', 0) for r in results)
total_output = sum(r.get('output_tokens', 0) for r in results)

print(f'成功: {success_count}/{len(results)}')
print(f'总Token: {total_input + total_output:,}')
