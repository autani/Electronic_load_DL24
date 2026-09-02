@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
    echo [エラー] 仮想環境 .venv が見つかりません。
    echo 先に windows_setupenv.bat を実行して環境を用意してください。
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo [エラー] アプリケーションの起動に失敗しました。
    echo windows_setupenv.bat をもう一度実行してから試してください。
    echo.
    pause
    exit /b 1
)

exit /b 0
