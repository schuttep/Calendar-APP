@echo off
REM Windows batch script to connect to Raspberry Pi Calendar App
REM Place this in your Windows calendar app folder for easy access

echo Raspberry Pi Calendar App - Remote Connection Menu
echo ===================================================
echo.
echo 1. SSH Connection (Command Line)
echo 2. VNC Connection (Remote Desktop)  
echo 3. Open File Share in Explorer
echo 4. Copy Files to Pi (SCP)
echo 5. Edit Config
echo 6. Show Pi Status
echo 7. Exit
echo.

set /p choice="Select option (1-7): "

if "%choice%"=="1" goto ssh
if "%choice%"=="2" goto vnc
if "%choice%"=="3" goto fileshare
if "%choice%"=="4" goto scp
if "%choice%"=="5" goto config
if "%choice%"=="6" goto status
if "%choice%"=="7" goto exit
goto menu

:ssh
if not exist "pi_config.txt" (
    echo Pi IP address not configured. Please run option 5 first.
    pause
    goto menu
)
for /f "tokens=2 delims==" %%a in ('findstr "PI_IP" pi_config.txt') do set PI_IP=%%a
echo Connecting to Pi via SSH...
ssh pi@%PI_IP%
pause
goto menu

:vnc
if not exist "pi_config.txt" (
    echo Pi IP address not configured. Please run option 5 first.
    pause
    goto menu
)
for /f "tokens=2 delims==" %%a in ('findstr "PI_IP" pi_config.txt') do set PI_IP=%%a
echo Opening VNC connection...
echo Connect your VNC viewer to: %PI_IP%:5900
start "" "vnc://%PI_IP%:5900"
pause
goto menu

:fileshare
if not exist "pi_config.txt" (
    echo Pi IP address not configured. Please run option 5 first.
    pause
    goto menu
)
for /f "tokens=2 delims==" %%a in ('findstr "PI_IP" pi_config.txt') do set PI_IP=%%a
echo Opening Pi file share...
start "" "\\%PI_IP%\calendar-app"
pause
goto menu

:scp
if not exist "pi_config.txt" (
    echo Pi IP address not configured. Please run option 5 first.
    pause
    goto menu
)
for /f "tokens=2 delims==" %%a in ('findstr "PI_IP" pi_config.txt') do set PI_IP=%%a
echo Copying calendar_app.py to Pi...
scp calendar_app.py pi@%PI_IP%:/home/pi/calendar-app-dev/
echo Copy complete. SSH to Pi and run sync-from-dev.sh to update.
pause
goto menu

:config
echo Current configuration:
if exist "pi_config.txt" type pi_config.txt
echo.
set /p pi_ip="Enter Pi IP address: "
echo PI_IP=%pi_ip% > pi_config.txt
echo Configuration saved.
pause
goto menu

:status
if not exist "pi_config.txt" (
    echo Pi IP address not configured. Please run option 5 first.
    pause
    goto menu
)
for /f "tokens=2 delims==" %%a in ('findstr "PI_IP" pi_config.txt') do set PI_IP=%%a
echo Checking Pi status...
ssh pi@%PI_IP% "sudo systemctl status calendar-app.service --no-pager"
pause
goto menu

:exit
echo Goodbye!
exit

:menu
goto :eof
