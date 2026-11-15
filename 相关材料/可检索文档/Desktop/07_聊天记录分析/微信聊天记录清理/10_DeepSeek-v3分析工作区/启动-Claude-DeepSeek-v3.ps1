$ErrorActionPreference = 'Stop'
$workDir = 'C:\Users\wardc\Desktop\微信聊天记录清理\10_DeepSeek-v3分析工作区'

Set-Location -LiteralPath $workDir

Write-Host 'Claude Code + DeepSeek v4 Flash' -ForegroundColor Cyan
Write-Host '工作区：' $workDir
Write-Host '任务：构建 v3 执行器并运行最多 20 个分层样本；完成后暂停等待确认。'
Write-Host 'API Token 不会由本启动脚本显示或写入文件。' -ForegroundColor Yellow
Write-Host ''

& claude --model 'deepseek-v4-flash' --permission-mode 'acceptEdits' '请完整阅读 CLAUDE.md 和 START-HERE.md，按 START-HERE.md 开始执行。先验证安全边界，再构建 v3 执行器并完成最多20个片段的分层真实试运行。完成后停止并在窗口中汇报，不要启动全量。'

Write-Host ''
Write-Host 'Claude Code 已退出。窗口将保持打开，便于查看输出。' -ForegroundColor DarkYellow

