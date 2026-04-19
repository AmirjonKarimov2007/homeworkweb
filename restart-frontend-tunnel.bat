@echo off
REM ========================================
REM Restart Frontend Cloudflare Tunnel
REM ========================================

taskkill /IM cloudflared.exe /F 2>nul 2>&1
timeout /t 3 cloudflared tunnel --url http://localhost:3000

echo.
echo ========================================
echo Frontend Tunnel yangilandi!
echo URL: https://tall-cartoon-bond-searched.trycloudflare.com/
echo ========================================
pause
