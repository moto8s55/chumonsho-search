# ============================================================
#  既刊注文書 自動監視を「ログオン時に自動起動」するよう登録する
#  （Windowsタスクスケジューラーに登録。追加インストール不要）
#
#  使い方: このファイルを右クリック →「PowerShellで実行」
#          （または PowerShell で: powershell -ExecutionPolicy Bypass -File install_task.ps1）
#
#  解除したいとき:  Unregister-ScheduledTask -TaskName "既刊注文書_自動監視" -Confirm:$false
# ============================================================

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$watch = Join-Path $here "watch.py"
$taskName = "既刊注文書_自動監視"

# pythonw.exe（コンソール非表示）を探す。無ければ python.exe。
$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "python が見つかりません。Pythonをインストールし PATH を通してください。"; exit 1 }

$action  = New-ScheduledTaskAction -Execute $py -Argument "`"$watch`"" -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
  -Settings $settings -Description "既刊注文書フォルダを監視し検索ページを自動再生成する" -Force | Out-Null

Write-Host "[完了] タスク『$taskName』を登録しました。" -ForegroundColor Green
Write-Host "次回ログオンから自動で監視が始まります。今すぐ開始するには watch.bat を実行してください。"
Write-Host "解除: Unregister-ScheduledTask -TaskName `"$taskName`" -Confirm:`$false"
