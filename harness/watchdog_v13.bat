@echo off
rem 看门狗 v1.3：评分器不在跑且未完成时重启 run_v13.bat（每 5 分钟触发）
cd /d C:\Users\user\Documents\kimi\workspace\cc-eval\harness
echo %date% %time% check >> watchdog_v13.log
if exist v13_complete.flag (echo flag-exists >> watchdog_v13.log & exit /b 0)
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*gguf_score_k*'}) {exit 0} else {exit 1}"
if %errorlevel%==0 (echo alive >> watchdog_v13.log & exit /b 0)
echo restart >> watchdog_v13.log
start "" /min cmd /c run_v13.bat
exit /b 0
