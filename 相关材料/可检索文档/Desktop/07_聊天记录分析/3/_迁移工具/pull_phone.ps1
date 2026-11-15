# 手机数据拉取脚本 v2 (adb pull, ASCII暂存, base64处理中文名)
$ErrorActionPreference = 'Continue'
$adb = 'C:\Users\wardc\Desktop\platform-tools\adb.exe'
$dst = 'D:\phone_raw'
$log = 'D:\资料整理_2026-08-17\00_总清单\手机拉取日志.txt'
New-Item -ItemType Directory -Path $dst -Force | Out-Null
Remove-Item 'D:\资料整理_2026-08-17\13_手机_荣耀X60Pro' -Recurse -Force -ErrorAction SilentlyContinue

function Log([string]$m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -LiteralPath $log -Append -Encoding utf8 }
function ShellB64([string]$cmd) {
  $b = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($cmd))
  & $adb shell "echo $b | base64 -d | sh" 2>&1 | Out-String
}
function P([string]$dir, [string]$as) {
  Log "开始拉取 /sdcard/$dir -> $as"
  & $adb pull "/sdcard/$dir" "$dst\$as" *>> $log
  Log "完成 /sdcard/$dir rc=$LASTEXITCODE"
}

P 'DCIM' 'DCIM'
P 'Pictures' 'Pictures'
P 'Download' 'Download'
P 'Documents' 'Documents'
P 'Movies' 'Movies'
P 'Music' 'Music'
P 'Tencent' 'Tencent'
P 'Honor' 'Honor'
P 'HONOR Share' 'HONOR_Share'
P 'backup' 'backup'
P 'baidu' 'baidu'
P 'Foxit' 'Foxit'
P 'EditedOnlinePhotos' 'EditedOnlinePhotos'
P 'Podcasts' 'Podcasts'
P 'Sounds' 'Sounds'
P 'CloudDrive' 'CloudDrive'
P 'magicLinkDemo' 'magicLinkDemo'

# --- 中文名目录: 我的文件 ---
Log '--- 处理中文目录 我的文件 ---'
$r = ShellB64 'ls -la "/sdcard/我的文件/"'
Log "我的文件 内容列表: $r"
ShellB64 'cp -r "/sdcard/我的文件" "/sdcard/_wm_wj"' | Out-Null
& $adb pull '/sdcard/_wm_wj' "$dst\_wm_wj" *>> $log
Log "我的文件 拉取 rc=$LASTEXITCODE"
if (Test-Path "$dst\_wm_wj") { Rename-Item "$dst\_wm_wj" "$dst\我的文件" }
ShellB64 'rm -rf "/sdcard/_wm_wj"' | Out-Null

# --- 根目录中文名文件 ---
Log '--- 处理根目录中文文件 ---'
$rootFiles = ShellB64 'ls -p /sdcard/ | grep -v "/$" | grep -P "[^\x00-\x7F]"'
Log "根目录中文文件: $rootFiles"
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes('cp "/sdcard/2_央美美育浸润活动·科技与艺术专家研讨会专家费.xlsx" "/sdcard/_root_doc.xlsx"'))
& $adb shell "echo $b64 | base64 -d | sh" 2>&1 | Out-String
& $adb pull '/sdcard/_root_doc.xlsx' "$dst\_root_doc.xlsx" *>> $log
if (Test-Path "$dst\_root_doc.xlsx") { Rename-Item "$dst\_root_doc.xlsx" "$dst\2_央美美育浸润活动·科技与艺术专家研讨会专家费.xlsx" }
ShellB64 'rm -f "/sdcard/_root_doc.xlsx"' | Out-Null

Log '===== 全部拉取完成 ====='
