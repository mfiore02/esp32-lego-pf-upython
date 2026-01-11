@echo off
REM Deploy Controller Application to ESP32
REM Usage: deploy_controller.bat PORT
REM Example: deploy_controller.bat COM3

if "%1"=="" (
    echo Usage: deploy_controller.bat PORT
    echo Example: deploy_controller.bat COM3
    exit /b 1
)

set PORT=%1

echo ==========================================
echo Deploying Controller to %PORT%
echo ==========================================

REM Create lib directory
echo Creating /lib directory...
mpremote connect %PORT% fs mkdir /lib 2>nul

REM Copy all library modules
echo Copying library modules...
mpremote connect %PORT% fs cp lib/config_manager.py :/lib/config_manager.py
mpremote connect %PORT% fs cp lib/button.py :/lib/button.py
mpremote connect %PORT% fs cp lib/led.py :/lib/led.py
mpremote connect %PORT% fs cp lib/potentiometer.py :/lib/potentiometer.py
mpremote connect %PORT% fs cp lib/motor_driver.py :/lib/motor_driver.py
mpremote connect %PORT% fs cp lib/espnow_protocol.py :/lib/espnow_protocol.py
mpremote connect %PORT% fs cp lib/hardware.py :/lib/hardware.py

REM Copy controller main application
echo Copying controller application...
mpremote connect %PORT% fs cp controller/main.py :main.py

REM Reset device to start application
echo Resetting device...
mpremote connect %PORT% reset

echo.
echo ==========================================
echo Controller deployed successfully!
echo ==========================================
echo.
echo The controller will start automatically.
echo To monitor output, connect to REPL:
echo   mpremote connect %PORT% repl
echo.
echo To enter pairing mode:
echo   Hold the button during power-up
echo.
