# 安装定时同步任务 —— 每天9:00和21:00自动同步规则
$taskName = "进化中心自动同步"
$scriptPath = "I:\.evolution_center\测试集\同步规则.py"
$pythonPath = "python"

# 删除已存在的任务（如有）
schtasks /delete /tn $taskName /f 2>$null

# 创建新任务
schtasks /create /tn $taskName /tr "$pythonPath $scriptPath --auto" /sc daily /st 09:00 /du 24:00 /ri 720 /f

Write-Host "✅ 定时任务已安装: 每天9:00和21:00自动同步"
Write-Host "   查看: schtasks /query /tn '$taskName'"
Write-Host "   手动: python $scriptPath --auto"
