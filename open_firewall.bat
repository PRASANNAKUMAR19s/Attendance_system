@echo off
echo ====================================================
echo   Attendance System - Firewall Configuration
echo ====================================================
echo.
echo Requesting administrator privileges...
echo.

net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator.
    echo Opening Port 5000 for Mobile Access...
    powershell -Command "New-NetFirewallRule -DisplayName 'Attendance System Port 5000' -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow"
    echo.
    echo ====================================================
    echo SUCCESS! Port 5000 is now open.
    echo Try opening http://192.168.0.101:5000 on your mobile.
    echo ====================================================
) else (
    echo [ERROR] Please RIGHT-CLICK this file and select 'RUN AS ADMINISTRATOR'.
)
pause
