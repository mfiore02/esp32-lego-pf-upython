@echo off
REM Deploy HWIL test to ESP32 (Windows)
REM Usage: deploy_hwil_test.bat COM3 test_config_manager_hwil

if "%1"=="" (
    echo Usage: deploy_hwil_test.bat COM_PORT TEST_NAME
    echo Example: deploy_hwil_test.bat COM3 test_config_manager_hwil
    exit /b 1
)

if "%2"=="" (
    echo Usage: deploy_hwil_test.bat COM_PORT TEST_NAME
    echo Example: deploy_hwil_test.bat COM3 test_config_manager_hwil
    exit /b 1
)

set PORT=%1
set TEST=%2

echo Deploying %TEST% to %PORT%...

REM Create lib directory
mpremote connect %PORT% fs mkdir /lib 2>nul

REM Copy config_manager library
echo Copying lib/config_manager.py...
mpremote connect %PORT% fs cp lib/config_manager.py :/lib/config_manager.py

REM Copy HWIL test as main.py
echo Copying hwil/%TEST%.py to main.py...
mpremote connect %PORT% fs cp hwil/%TEST%.py :main.py

REM Reset device
echo Resetting device...
mpremote connect %PORT% reset

echo.
echo Test deployed! Connect to REPL with:
echo   mpremote connect %PORT% repl
