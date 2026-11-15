# NEXT-STEPS.md — 下一步操作
> 更新时间：2026-08-02 15:45

## 当前进程状态
- **旧同步执行器**：已停止（task byflxks1f），94 个标注已入库
- **异步执行器**：已编码并通过 Pass A/B/C 端到端验证，未全量部署
- **没有正在运行的标注进程**

## 什么时候安全停止旧执行器
- 旧执行器已停止，不需要再操作
- 已入库的 94 个标注永久保留

## 如何升级到异步连接池
1. aiohttp 已安装到 `vendor/` 目录
2. `src/async_executor.py` 已完成编码
3. 启动命令：`cd WeChat-MiMo-Analyzer && python src/async_executor.py`
4. 初始 32 workers，自动根据吞吐扩容

## 如何完成并发基准测试
- 已完成：32/64/96/128 各 100 次 API 调用
- 结果：32 workers 最佳（43K tok/min, 75% 成功率）
- 待做：192/256 workers 测试（等 128 稳定后）
- **关键问题**：所有级别成功率只有 75%，需要先修复 evidence_id 验证

## 如何验证新执行器不会漏标
1. 运行前记录 `SELECT COUNT(*) FROM aggressive_annotations`
2. 运行后检查数量是否只增不减
3. JSONL 分片文件可作为备份验证
4. 每个 Pass 独立验证 evidence_id 和数量一致性

## 如何恢复运行
```bash
# 方案A：用旧同步执行器（稳定但慢）
cd C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer
python src/aggressive_executor.py --batch-size 1 --workers 19 --max-retries 3

# 方案B：用新异步执行器（快但需先修复验证）
python src/async_executor.py
```

## 优先修复项
1. **evidence_id 验证**：在 Pass A prompt 中加「evidence_id 必须与输入的 id 完全一致，一字不差」
2. **或放宽验证**：改为前 12 字符前缀匹配
3. **重跑基准测试**：修复后重新测试 32/64/96/128
4. **全量部署**：确认成功率 >95% 后启动全量
