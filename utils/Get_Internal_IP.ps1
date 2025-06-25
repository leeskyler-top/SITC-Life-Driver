# 请求管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# hosts 文件路径
$hostsPath = "$env:windir\System32\drivers\etc\hosts"

# 目标域名
$domain = "twlife.leeskyler.top"

# API 地址
$apiUrl = "https://twlife.leeskyler.top/api/v1/security-history/internal-ip"

# 1. 删除现有的域名记录（如果存在）
$hostsContent = Get-Content $hostsPath -Raw
if ($hostsContent -match "(?m)^\s*\d+\.\d+\.\d+\.\d+\s+$domain") {
    # 备份原始 hosts 文件
    $backupPath = "$env:windir\System32\drivers\etc\hosts.backup_$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $hostsPath $backupPath -Force
    
    # 删除匹配的行
    $newContent = $hostsContent -replace "(?m)^\s*\d+\.\d+\.\d+\.\d+\s+$domain.*?\r?\n", ""
    $newContent | Set-Content $hostsPath -NoNewline
    
    Write-Host "已删除 hosts 文件中现有的 $domain 记录"
    
    # 清除 DNS 缓存以确保更改立即生效
    Clear-DnsClientCache
    Write-Host "已清除 DNS 缓存"
}

# 2. 调用 API 获取新的内网 IP
try {
    Write-Host "正在从 API 获取 $domain 的新内网 IP..."
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -ErrorAction Stop
    
    if ($response.status -eq "success" -and $response.data.internal_ip -match '^\d+\.\d+\.\d+\.\d+$') {
        $internalIp = $response.data.internal_ip
        
        # 3. 将新记录写入 hosts 文件
        $newEntry = "`r`n$internalIp`t$domain`r`n"
        Add-Content -Path $hostsPath -Value $newEntry -NoNewline
        
        Write-Host "成功更新 hosts 文件: $internalIp -> $domain"
        
        # 再次清除 DNS 缓存以确保新记录生效
        Clear-DnsClientCache
        Write-Host "已清除 DNS 缓存以确保新记录生效"
    } else {
        Write-Host "API 返回的 IP 地址格式无效或请求不成功"
        Write-Host "响应内容: $(ConvertTo-Json $response -Depth 5)"
    }
} catch {
    Write-Host "调用 API 失败: $_"
    Write-Host "将保留 hosts 文件中的现有配置"
}

# 暂停以便查看输出
Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")