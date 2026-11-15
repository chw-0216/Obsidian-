import json
import os

# 加载任务
with open('layer2_results/tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

print('=== Layer 2: 准备执行分析 ===')
print()

# 显示任务摘要
print('待分析的5人:')
for task in tasks:
    print(f'  {task["index"]}. {task["name"]}: {task["segment_count"]}个片段, {task["prompt_length"]:,}字符')

print()

# 估算token消耗
total_chars = sum(t['prompt_length'] for t in tasks)
est_input_tokens = total_chars // 4
est_output_tokens = est_input_tokens * 1.5  # 输出通常比输入长
total_tokens = est_input_tokens + est_output_tokens

print('=== Token估算 ===')
print(f'输入Token: ~{est_input_tokens:,}')
print(f'输出Token: ~{est_output_tokens:,}')
print(f'总计: ~{total_tokens:,} ({total_tokens/10000:.1f}万)')
print()

print('=== 执行选项 ===')
print('1. 执行全部5人（推荐）')
print('2. 只执行前2人（导师+父亲）')
print('3. 取消')
print()

# 保存配置供后续使用
config = {
    'tasks': tasks,
    'est_tokens': total_tokens,
    'status': 'ready'
}

with open('layer2_results/config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print('配置已保存到 layer2_results/config.json')
print()
print('要继续执行分析吗？')
