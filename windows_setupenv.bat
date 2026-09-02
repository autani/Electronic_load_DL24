@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

echo ========================================
echo  DL24 制御ソフト - 環境セットアップ
echo ========================================
echo.

call :find_python
if errorlevel 1 goto :fail

echo [OK] Python が見つかりました。
%PY% --version
echo.

echo pip を確認しています...
%PY% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip が見つからないため、付属ツールで導入を試みます...
    %PY% -m ensurepip --upgrade
    %PY% -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo [エラー] pip を利用できません。
        echo Python を python.org から入れ直し、pip を含めてインストールしてください。
        goto :fail
    )
)
echo [OK] pip が利用できます。
%PY% -m pip --version
echo.

echo venv を確認しています...
%PY% -c "import venv" >nul 2>&1
if errorlevel 1 (
    echo [エラー] venv モジュールがありません。
    echo Microsoft Store 版ではなく、https://www.python.org/downloads/ の Python 3 を
    echo 使い、「Add python.exe to PATH」にチェックを入れてインストールしてください。
    goto :fail
)
echo [OK] venv が利用できます。
echo.

if exist ".venv\Scripts\python.exe" (
    echo 既存の仮想環境 .venv を使います。
) else (
    echo 仮想環境 .venv を作成しています...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました。
        goto :fail
    )
    echo [OK] .venv を作成しました。
)
echo.

echo requirements.txt に従ってパッケージを入れています...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [エラー] pip の更新に失敗しました。
    goto :fail
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました。
    echo インターネット接続を確認して、もう一度このファイルを実行してください。
    goto :fail
)

echo.
echo ========================================
echo  セットアップが完了しました。
echo  次は windows_runapp.bat を実行してください。
echo ========================================
echo.
pause
exit /b 0

:fail
echo.
echo セットアップを中断しました。
pause
exit /b 1

:find_python
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3"
    exit /b 0
)
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    exit /b 0
)
python3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PY=python3"
    exit /b 0
)
echo [エラー] Python が見つかりません。
echo.
echo 1. https://www.python.org/downloads/ から Python 3 をインストールしてください。
echo 2. インストール画面で「Add python.exe to PATH」にチェックを入れてください。
echo 3. このウィンドウを閉じてから、もう一度 windows_setupenv.bat を実行してください。
exit /b 1
