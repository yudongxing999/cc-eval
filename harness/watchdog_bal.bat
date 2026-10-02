@echo off
rem 看门狗：评分器不在跑且未完成时，重启 run_bal.bat（每 5 分钟由计划任务触发）
cd /d C:\Users\user\Documents\kimi\workspace\cc-eval\harness
if exist bal_complete.flag exit /b 0
powershell.exe -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*gguf_score_k*'}) {exit 0} else {exit 1}"
if %errorlevel%==0 exit /b 0
call run_bal.bat
echo done > bal_complete.flag
