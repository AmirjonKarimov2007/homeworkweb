@echo off
REM ========================================
REM Arabic Center CRM/LMS - Tunnel Launcher
REM ========================================

echo.
echo [1] Backend Tunnel
echo ---------------------------------------
cd /d C:\Users\alfatech.uz\Desktop\homeworkweb\backend
python -m venv\Scripts/activate
cloudflared tunnel --url http://localhost:8000
echo.

echo.
echo [2] Frontend Tunnel (restart existing)
echo ---------------------------------------
cd /d C:\Users\alfatech.uz\Desktop\homeworkweb\frontend
cloudflared tunnel --url http://localhost:3000
echo.

echo.
echo ========================================
echo Tunnels ishga tushdi!
echo ========================================
echo.
echo Backend URL  : https://manitoba-cam-notification-divisions.trycloudflare.com/
echo Frontend URL : https://tall-cartoon-bond-searched.trycloudflare.com/
echo.
echo Telegram Bot ni qo'shimcha o'rnatingiz:
echo   cd bot
echo   python main.py
echo.
echo ========================================
echo.
pause
